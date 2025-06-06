#!/usr/bin/env python3
"""
evaluate_models.py

여러 학습된 모델(.pth)을 불러와 단일 테스트 CSV에 대해 성능을 평가하고,
다양한 정량적 지표를 종합하여 비교 분석 결과를 출력합니다.
"""
import argparse
import time
import os
import torch
from torch.utils.data import DataLoader, Dataset
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
import math
from scipy.signal import butter, filtfilt, resample_poly

from thop import profile

from classifier import BiLSTMClassifier, GRUClassifier, SimpleCNNClassifier, CNNBiLSTMClassifier, SmallTCNClassifier

# =============================================================================
# 1. Preprocessing Utilities (fine_tune_online.py와 동일)
# =============================================================================
def butter_highpass(cutoff, fs, order=4):
    nyq = 0.5 * fs
    return butter(order, cutoff / nyq, btype='high', analog=False)

def remove_gravity(acc_data, fs):
    b, a = butter_highpass(cutoff=0.2, fs=fs, order=4)
    return filtfilt(b, a, acc_data, axis=0)

def minmax_scale(X: np.ndarray) -> np.ndarray:
    mins = X.min(axis=0)
    maxs = X.max(axis=0)
    scales = np.where(maxs - mins == 0, 1, maxs - mins)
    return 2 * (X - mins) / scales - 1
    
def resample_window(data, orig_fs, fs, window_size):
    up = int(round(fs)); down = int(round(orig_fs)) or 1
    out = resample_poly(data, up, down, axis=0)
    num_tgt = int(math.ceil(window_size * fs))
    return out[:num_tgt] if out.shape[0] > num_tgt else out
def lowpass_filter(data, fs, cutoff=5.0, order=4):
    nyq = 0.5 * fs
    b, a = butter(order, cutoff/nyq, btype='low')
    return filtfilt(b, a, data, axis=0)
# =============================================================================
# 2. Online Dataset Definition
# =============================================================================
class OnlineGestureDataset(Dataset):
    LABEL_MAP = {12:0,13:1,14:2,15:2,16:2,17:2}
    def __init__(self, csv_path, window_size=3.0, fs=50.0):
        df = pd.read_csv(csv_path)
        df['t_full_s'] = (df['sw_h']*3600 + df['sw_m']*60 + df['sw_s'] + df['sw_ns']*1e-9)
        if 'gesture_id' in df.columns:
            df['label'] = df['gesture_id'].map(self.LABEL_MAP)
        df['label'] = df['label'].astype(int)

        self.fs = fs
        self.window = window_size
        self.num_tgt = int(math.ceil(window_size * fs))
        self.samples = []

        for (_, trial_df) in df.groupby(['user_id','trial_id','label']):
            label = int(trial_df['label'].iloc[0])
            grp = trial_df.sort_values('t_full_s')
            t = grp['t_full_s'].values
            dur = t[-1]-t[0] if t[-1]>t[0] else 1e-9
            orig_fs = len(t)/dur

            acc_x=-grp['sw_lacc_y'].values; acc_y=grp['sw_lacc_z'].values; acc_z=-grp['sw_lacc_x'].values
            acc = np.vstack([acc_x, acc_y, acc_z]).T
            w_yaw=grp['sw_gyro_z'].values; w_pitch=-grp['sw_gyro_y'].values; w_roll=-grp['sw_gyro_x'].values
            gyro = np.vstack([w_yaw, w_pitch, w_roll]).T
            data = np.hstack([acc, gyro])


            res = resample_window(data, orig_fs, self.fs, self.window)
            acc_hp = remove_gravity(res[:,:3], self.fs) 
            feat = np.hstack([acc_hp, res[:,3:]])

            norm = minmax_scale(feat)

            L = norm.shape[0]
            if L < self.num_tgt:
                pad = np.zeros((self.num_tgt-L,6))
                norm = np.vstack([norm, pad])
                length = L
            else:
                norm = norm[:self.num_tgt]
                length = self.num_tgt

            X = torch.tensor(norm.T, dtype=torch.float32)
            self.samples.append((X, label, length))

    def __len__(self): return len(self.samples)
    def __getitem__(self, idx): return self.samples[idx]

# =============================================================================
# 3. 모델 분석 및 평가 함수
# =============================================================================
def load_model_for_eval(path: str, model_type: str, device: str = 'cpu'):
    if model_type == 'bilstm': model = BiLSTMClassifier(6, 110, 1, 3)
    elif model_type == 'gru': model = GRUClassifier(6, (256, 128, 64), 3)
    elif model_type == 'simplecnn': model = SimpleCNNClassifier(6, 3)
    elif model_type == 'cnnbilstm': model = CNNBiLSTMClassifier(6, 3)
    elif model_type == 'smalltcn': model = SmallTCNClassifier(6, 3)
    else: raise ValueError(f"Unknown model_type: {model_type}")
    
    ckpt = torch.load(path, map_location=device)
    model.load_state_dict(ckpt['model'])
    model.to(device).eval()
    return model

def analyze_and_evaluate(model_path: str, model_type: str, loader: DataLoader, args):
    device = torch.device(args.device)
    model = load_model_for_eval(model_path, model_type, args.device)
    criterion = torch.nn.CrossEntropyLoss()
    
    params = sum(p.numel() for p in model.parameters() if p.requires_grad) / 1e6
    file_size = os.path.getsize(model_path) / (1024 * 1024)
    dummy_input = torch.randn(1, 6, int(args.fs * args.window)).to(device)
    dummy_len = torch.tensor([int(args.fs * args.window)]).long()
    macs, _ = profile(model, inputs=(dummy_input, dummy_len), verbose=False)
    flops = macs * 2 / 1e9

    all_true, all_pred, all_confs = [], [], []
    total_loss, total_inference_time_ns = 0.0, 0
    
    with torch.no_grad():
        for X, y, lengths in loader:
            X = X.to(device)
            lengths = lengths.cpu()
            
            start_time = time.perf_counter_ns()
            logits = model(X, lengths)
            end_time = time.perf_counter_ns()

            total_inference_time_ns += (end_time - start_time)
            total_loss += criterion(logits, y.to(device)).item() * X.size(0)
            
            probs = torch.softmax(logits, dim=1)
            confidence, preds_tensor = torch.max(probs, 1)
            
            all_true.extend(y.numpy().tolist())
            all_pred.extend(preds_tensor.cpu().numpy().tolist())
            all_confs.extend(confidence.cpu().numpy().tolist())

    all_true, all_pred, all_confs = np.array(all_true), np.array(all_pred), np.array(all_confs)
    num_samples = len(loader.dataset)
    avg_loss = total_loss / num_samples
    avg_time_ns = total_inference_time_ns / num_samples
    throughput = 1e9 / avg_time_ns if avg_time_ns > 0 else 0
    
    accuracy = accuracy_score(all_true, all_pred)
    f1 = f1_score(all_true, all_pred, average='macro', zero_division=0)
    report_str = classification_report(all_true, all_pred, target_names=['V','X','Circle'], zero_division=0)
    cm = confusion_matrix(all_true, all_pred, labels=[0,1,2])

    avg_confs_per_class = {}
    for i, label_name in enumerate(['V', 'X', 'Circle']):
        pred_indices = np.where(all_pred == i)[0]
        avg_confs_per_class[label_name] = np.mean(all_confs[pred_indices]) if len(pred_indices) > 0 else 0.0

    correct_indices = np.where(all_pred == all_true)[0]
    min_correct_conf, max_correct_conf = (np.min(all_confs[correct_indices]), np.max(all_confs[correct_indices])) if len(correct_indices) > 0 else (0.0, 0.0)

    results = {
        "Model Type": model_type, "Params (M)": params, "FLOPs (G)": flops, "Size (MB)": file_size,
        "Accuracy": accuracy, "Macro F1": f1, "Loss": avg_loss,
        "Inference Time (ms/sample)": avg_time_ns / 1e6, "Throughput (samples/s)": throughput,
        "Classification Report String": report_str, "Confusion Matrix": cm,
        "Avg Confidence": avg_confs_per_class, "Min Correct Confidence": min_correct_conf, "Max Correct Confidence": max_correct_conf
    }
    return results

# =============================================================================
# 4. 메인 실행 함수
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Evaluate and compare multiple gesture models.")
    parser.add_argument('--csv', required=True, help='Evaluation CSV file path.')
    parser.add_argument('--models', required=True, nargs='+', help='List of trained model .pth file paths.')
    parser.add_argument('--model-types', required=True, nargs='+', choices=['bilstm','gru','simplecnn','cnnbilstm','smalltcn'], help='List of model types corresponding to --models.')
    parser.add_argument('--fs', type=float, default=50.0)
    parser.add_argument('--window', type=float, default=3.0)
    parser.add_argument('--batch-size', type=int, default=64)
    parser.add_argument('--device', default='cpu', help='Device to run evaluation on (e.g., cpu, cuda).')
    args = parser.parse_args()

    if len(args.models) != len(args.model_types):
        raise ValueError("The number of models and model-types must be the same.")

    dataset = OnlineGestureDataset(csv_path=args.csv, window_size=args.window, fs=args.fs)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False)
    
    all_results = []
    for model_path, model_type in zip(args.models, args.model_types):
        print(f"\n--- Evaluating Model: {model_type} ({os.path.basename(model_path)}) ---")
        try:
            results = analyze_and_evaluate(model_path, model_type, loader, args)
            all_results.append(results)
            # 개별 모델 결과 출력
            print(results["Classification Report String"])
            print("Confusion Matrix:")
            print(results["Confusion Matrix"])
            print("\nConfidence Metrics:")
            for label, conf in results["Avg Confidence"].items():
                print(f"  - Avg. Confidence for '{label}': {conf:.2%}")
            print(f"  - Max Confidence (Correct): {results['Max Correct Confidence']:.2%}")
            print(f"  - Min Confidence (Correct): {results['Min Correct Confidence']:.2%}")
        except Exception as e:
            print(f"Failed to evaluate {model_type}: {e}")

    
    # 헤더 정의 (모든 지표 포함)
    headers = [
        "Model Type", "Macro F1", "Accuracy", "Loss", "Params(M)", "FLOPs(G)", "Size(MB)", 
        "Infer(ms)", "Conf(V)", "Conf(X)", "Conf(Circle)", "MinCorrConf", "MaxCorrConf"
    ]
    header_format_string = (
        "{:<15} | {:<10} | {:<10} | {:<10} | {:<10} | {:<10} | {:<10} | "
        "{:<10} | {:<10} | {:<10} | {:<12} | {:<12} | {:<12}"
    )
    
    # 정렬을 위한 라인 너비 계산
    line_width = len(header_format_string.format(*headers))
    title = "COMPREHENSIVE MODEL COMPARATIVE ANALYSIS"

    print("\n\n" + "="*line_width)
    print(title.center(line_width))
    print("="*line_width)
    
    # 헤더 출력
    print(header_format_string.format(*headers))
    print("-" * line_width)

    # 결과 데이터 출력
    row_format_string = (
        "{:<15} | {:<10.4f} | {:<10.4f} | {:<10.4f} | {:<10.3f} | {:<10.3f} | {:<10.2f} | "
        "{:<10.3f} | {:<10.2%} | {:<10.2%} | {:<12.2%} | {:<12.2%} | {:<12.2%}"
    )
    # F1 스코어 기준으로 정렬하여 출력
    for res in sorted(all_results, key=lambda x: x["Macro F1"], reverse=True):
        print(row_format_string.format(
            res["Model Type"],
            res["Macro F1"],
            res["Accuracy"],
            res["Loss"],
            res["Params (M)"],
            res["FLOPs (G)"],
            res["Size (MB)"],
            res["Inference Time (ms/sample)"],
            res["Avg Confidence"]['V'],
            res["Avg Confidence"]['X'],
            res["Avg Confidence"]['Circle'],
            res["Min Correct Confidence"],
            res["Max Correct Confidence"]
        ))
    print("="*line_width)

if __name__ == "__main__":
    main()