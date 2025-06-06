import os
import argparse
import random
import math
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, Subset
from sklearn.model_selection import StratifiedKFold
from scipy.signal import resample_poly, butter, filtfilt
from sklearn.metrics import f1_score, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt

from classifier import BiLSTMClassifier, GRUClassifier, SimpleCNNClassifier, CNNBiLSTMClassifier, SmallTCNClassifier

# ----------------------------------------------------------------------------
# 1. Preprocessing utilities 
# ----------------------------------------------------------------------------
def butter_highpass(cutoff, fs, order=4):
    nyq = 0.5 * fs
    return butter(order, cutoff/nyq, btype='high', analog=False)

def remove_gravity(acc_data, fs):
    b, a = butter_highpass(0.2, fs, order=4)
    return filtfilt(b, a, acc_data, axis=0)

def minmax_scale(X):
    mins = X.min(axis=0)
    maxs = X.max(axis=0)
    scales = np.where(maxs - mins == 0, 1, maxs - mins)
    return 2*(X - mins)/scales - 1

def resample_window(data, orig_fs, target_fs, window_size):
    up = int(round(target_fs)); down = int(round(orig_fs)) or 1
    out = resample_poly(data, up, down, axis=0)
    num_tgt = int(math.ceil(window_size * target_fs))
    return out[:num_tgt] if out.shape[0] > num_tgt else out

# ----------------------------------------------------------------------------
# 2. Dataset with axis mapping 
# ----------------------------------------------------------------------------
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

            acc_x = -grp['sw_lacc_y'].values; acc_y = grp['sw_lacc_z'].values; acc_z = -grp['sw_lacc_x'].values
            acc = np.vstack([acc_x, acc_y, acc_z]).T
            w_yaw = grp['sw_gyro_z'].values; w_pitch = -grp['sw_gyro_y'].values; w_roll = -grp['sw_gyro_x'].values
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

# ----------------------------------------------------------------------------
# 3. Fine-tune entrypoint
# ----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Fine-tune gesture models with 5-fold CV and final testing.")
    parser.add_argument('--train-csv', required=True)
    parser.add_argument('--test-csv', required=True)
    parser.add_argument('--pretrained', required=True)
    parser.add_argument('--model', choices=['bilstm','gru','simplecnn','cnnbilstm','smalltcn'], required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--batch-size', type=int, default=None)
    parser.add_argument('--lr', type=float, default=None)
    parser.add_argument('--iterations', type=int, default=None)
    parser.add_argument('--epochs', type=int, default=25, help="Number of epochs to calculate iterations for CV phase.")
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--fs', type=float, default=50.0)
    parser.add_argument('--window', type=float, default=3.0)
    args = parser.parse_args()


    if args.model == 'gru':
        args.lr = args.lr or 1e-4
        args.batch_size = args.batch_size or 32
        args.iterations = args.iterations or 200
    else:
        args.lr = args.lr or 3e-4
        args.batch_size = args.batch_size or 32
        args.iterations = args.iterations or 150

    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(args.seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    base_output_name = os.path.splitext(args.output)[0]

 
    full_train_dataset = OnlineGestureDataset(args.train_csv, args.window, args.fs)
    test_dataset       = OnlineGestureDataset(args.test_csv,  args.window, args.fs)
    test_loader        = DataLoader(test_dataset,  batch_size=args.batch_size, shuffle=False)

    print("="*50)
    print(f"### 1단계: {args.model} 모델 5-Fold 교차 검증 시작 ###")
    print("="*50)

    # --- 1단계: 5-Fold 교차 검증 ---
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=args.seed)
    y_labels = np.array([sample[1] for sample in full_train_dataset.samples])
    
    all_fold_val_losses = []
    all_fold_val_f1s = []
    fold_final_metrics = []

    num_cv_epochs = args.epochs # CV에서는 iterations 대신 epochs 사용

    for fold, (train_idx, val_idx) in enumerate(skf.split(np.zeros(len(y_labels)), y_labels), 1):
        print(f"\n--- Fold {fold}/5 ---")
        train_subset = Subset(full_train_dataset, train_idx)
        val_subset   = Subset(full_train_dataset, val_idx)
        train_loader = DataLoader(train_subset, batch_size=args.batch_size, shuffle=True)
        val_loader   = DataLoader(val_subset,   batch_size=args.batch_size, shuffle=False)

        # 각 Fold마다 사전 학습된 모델을 새로 로드
        if args.model == 'bilstm': model = BiLSTMClassifier(6,110,1,3)
        elif args.model == 'gru': model = GRUClassifier(6,(256,128,64),3)
        elif args.model == 'simplecnn': model = SimpleCNNClassifier(6, 3)
        elif args.model == 'cnnbilstm': model = CNNBiLSTMClassifier(6, 3)
        elif args.model == 'smalltcn': model = SmallTCNClassifier(6, 3)
        
        ckpt = torch.load(args.pretrained, map_location=device)
        model.load_state_dict(ckpt['model'])
        model.to(device)

        # 동결 해제 전략 적용
        for param in model.parameters(): param.requires_grad = False
        try:
            if args.model == 'simplecnn':
                for param in model.fc1.parameters(): param.requires_grad = True
                for param in model.fc2.parameters(): param.requires_grad = True
            elif args.model == 'gru':
                for param in model.gru2.parameters(): param.requires_grad = True
                for param in model.gru3.parameters(): param.requires_grad = True
                for param in model.fc.parameters(): param.requires_grad = True
            elif args.model in ['bilstm', 'cnnbilstm', 'smalltcn']:
                for param in model.fc.parameters(): param.requires_grad = True
        except AttributeError as e:
            print(f"ERROR: Could not find a layer for unfreezing. Details: {e}"); exit()

        optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=args.lr)
        criterion = nn.CrossEntropyLoss()
        
        fold_losses, fold_f1s = [], []
        
        for epoch in range(1, num_cv_epochs + 1):
            model.train()
            for X, y, lengths in train_loader:
                X, y = X.to(device), y.to(device)
                logits = model(X, lengths.cpu().long())
                loss = criterion(logits, y)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            
            model.eval()
            val_loss, all_t, all_p = 0.0, [], []
            with torch.no_grad():
                for X_v, y_v, len_v in val_loader:
                    X_v, y_v = X_v.to(device), y_v.to(device)
                    logits_v = model(X_v, len_v.cpu().long())
                    val_loss += criterion(logits_v, y_v).item() * X_v.size(0)
                    all_t.extend(y_v.cpu().numpy()); all_p.extend(logits_v.argmax(1).cpu().numpy())
            
            val_loss /= len(val_subset)
            val_f1 = f1_score(all_t, all_p, average='macro', zero_division=0)
            fold_losses.append(val_loss); fold_f1s.append(val_f1)
            print(f"  Fold {fold} | Epoch {epoch}/{num_cv_epochs} | Val Loss: {val_loss:.4f}, Val F1: {val_f1:.4f}")

        all_fold_val_losses.append(fold_losses)
        all_fold_val_f1s.append(fold_f1s)
        fold_final_metrics.append({'loss': fold_losses[-1], 'f1': fold_f1s[-1]})

    mean_f1 = np.mean([m['f1'] for m in fold_final_metrics])
    std_f1 = np.std([m['f1'] for m in fold_final_metrics])
    print("\n--- 5-Fold CV Summary ---")
    print(f"Mean Validation F1: {mean_f1:.4f} ± {std_f1:.4f}\n")

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    for i, losses in enumerate(all_fold_val_losses, 1):
        plt.plot(range(1, len(losses) + 1), losses, label=f'Fold {i}')
    plt.xlabel('Epoch'); plt.ylabel('Validation Loss'); plt.title('CV Validation Loss'); plt.legend()
    plt.subplot(1, 2, 2)
    for i, f1s in enumerate(all_fold_val_f1s, 1):
        plt.plot(range(1, len(f1s) + 1), f1s, label=f'Fold {i}')
    plt.xlabel('Epoch'); plt.ylabel('Validation F1 Score'); plt.title('CV Validation F1 Score'); plt.legend()
    plt.tight_layout()
    plt.savefig(f"{base_output_name}_cv_curves.png")
    plt.close()

    if args.model == 'bilstm': final_model = BiLSTMClassifier(6,110,1,3)
    elif args.model == 'gru': final_model = GRUClassifier(6,(256,128,64),3)
    elif args.model == 'simplecnn': final_model = SimpleCNNClassifier(6, 3)
    elif args.model == 'cnnbilstm': final_model = CNNBiLSTMClassifier(6, 3)
    elif args.model == 'smalltcn': final_model = SmallTCNClassifier(6, 3)
    
    ckpt = torch.load(args.pretrained, map_location=device)
    final_model.load_state_dict(ckpt['model'])
    final_model.to(device)


    for param in final_model.parameters(): param.requires_grad = False
    
    try:
        if args.model == 'simplecnn':
            print("Unfreezing for SimpleCNN: model.fc1, model.fc2")
            for param in final_model.fc1.parameters(): param.requires_grad = True
            for param in final_model.fc2.parameters(): param.requires_grad = True
        elif args.model == 'gru':
            print("Unfreezing for GRU: model.gru2, model.gru3, and model.fc")
            for param in final_model.gru2.parameters(): param.requires_grad = True
            for param in final_model.gru3.parameters(): param.requires_grad = True
            for param in final_model.fc.parameters(): param.requires_grad = True
        elif args.model in ['bilstm', 'cnnbilstm', 'smalltcn']:
            print(f"Unfreezing for {args.model}: model.fc")
            for param in final_model.fc.parameters(): param.requires_grad = True
    except AttributeError as e:
        print(f"ERROR: Could not find a layer for unfreezing. Details: {e}")
        exit()

    optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, final_model.parameters()), lr=args.lr)
    criterion = nn.CrossEntropyLoss()
    
    full_train_loader = DataLoader(full_train_dataset, batch_size=args.batch_size, shuffle=True)
    
    eval_interval = max(1, args.iterations // 10) or 1
    eval_steps, eval_losses, eval_accs, eval_f1s = [], [], [], []
    
    step = 0
    while step < args.iterations:
        final_model.train()
        for X, y, lengths in full_train_loader:
            if step >= args.iterations: break
            X, y = X.to(device), y.to(device)
            logits = final_model(X, lengths.cpu().long())
            loss = criterion(logits, y)
            optimizer.zero_grad(); loss.backward(); optimizer.step()
            step += 1

            if step % eval_interval == 0 or step >= args.iterations:
                final_model.eval()
                all_t, all_p, total_loss = [], [], 0.0
                with torch.no_grad():
                    for X_t,y_t,lengths_t in test_loader:
                        X_t, y_t = X_t.to(device), y_t.to(device)
                        logits_t = final_model(X_t, lengths_t.cpu().long())
                        total_loss += criterion(logits_t, y_t).item() * X_t.size(0)
                        preds = logits_t.argmax(1)
                        all_t.extend(y_t.cpu().numpy()); all_p.extend(preds.cpu().numpy())
                
                test_loss = total_loss / len(test_dataset)
                test_acc = accuracy_score(all_t, all_p)
                test_f1  = f1_score(all_t, all_p, average='macro', zero_division=0)
                eval_steps.append(step)
                eval_losses.append(test_loss)
                eval_accs.append(test_acc)
                eval_f1s.append(test_f1)
                print(f"Step {step}/{args.iterations} - Test Loss: {test_loss:.4f}, Accuracy: {test_acc:.4f}, F1: {test_f1:.4f}")
                final_model.train()

    print("\nFinal evaluation on the model from the last iteration...")
    final_model.eval()
    all_t, all_p, total_loss = [], [], 0.0
    with torch.no_grad():
        for X,y,lengths in test_loader:
            X, y = X.to(device), y.to(device)
            logits = final_model(X, lengths.cpu().long())
            total_loss += criterion(logits, y).item() * X.size(0)
            preds = logits.argmax(1)
            all_t.extend(y.cpu().numpy()); all_p.extend(preds.cpu().numpy())

    test_loss = total_loss / len(test_dataset)
    test_acc = accuracy_score(all_t, all_p)
    test_f1  = f1_score(all_t, all_p, average='macro', zero_division=0)
    test_cm  = confusion_matrix(all_t, all_p, labels=list(range(3)))

    print(f"\n=== Final Test Results for {args.model} ===")
    print(f"Test Loss       : {test_loss:.4f}")
    print(f"Test Accuracy   : {test_acc:.4f}")
    print(f"Macro F1 score  : {test_f1:.4f}")
    print("Confusion Matrix:")
    print(test_cm)
    
    # 최종 테스트 결과 그래프 저장
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.imshow(test_cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Final Confusion Matrix'); plt.colorbar()
    thresh = test_cm.max() / 2.
    for i in range(test_cm.shape[0]):
        for j in range(test_cm.shape[1]):
            plt.text(j, i, format(test_cm[i, j], 'd'), ha="center", va="center", color="white" if test_cm[i, j] > thresh else "black")
    plt.xlabel('Predicted'); plt.ylabel('True')
    
    plt.subplot(1, 2, 2)
    plt.plot(eval_steps, eval_losses, label='Test Loss')
    plt.plot(eval_steps, eval_accs, label='Test Accuracy')
    plt.plot(eval_steps, eval_f1s,  label='Test Macro F1')
    plt.xlabel('Iteration'); plt.ylabel('Metric Value'); plt.title('Test Metrics over Iterations'); plt.legend(); plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{base_output_name}_final_results.png")
    
    torch.save({'model': final_model.state_dict()}, args.output)
    print(f"\nSaved final model to {args.output}")

if __name__=='__main__':
    main()