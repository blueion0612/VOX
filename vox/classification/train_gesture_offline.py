import os
import math
import argparse
import random
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, Subset
from scipy.signal import butter, filtfilt, resample_poly
from sklearn.model_selection import KFold
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt
from classifier import BiLSTMClassifier, GRUClassifier, SimpleCNNClassifier, CNNBiLSTMClassifier, SmallTCNClassifier
from sklearn.model_selection import StratifiedKFold
from tqdm import tqdm
from collections import Counter
from scipy.signal import butter, filtfilt
from scipy.interpolate import interp1d , Akima1DInterpolator


# =============================================================================
# 1. Preprocessing Utilities (same as online)
# =============================================================================
import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
from torch.utils.data import Dataset
import numpy as np
import math
from scipy.signal import butter, filtfilt, resample_poly

# =============================================================================
# 1. Preprocessing Utilities (same as online)
# =============================================================================
def lowpass_filter(data, fs, cutoff=5.0, order=4):
    nyq = 0.5 * fs
    b, a = butter(order, cutoff/nyq, btype='low')
    return filtfilt(b, a, data, axis=0)


def butter_highpass(cutoff, fs, order=4):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    return butter(order, normal_cutoff, btype='high', analog=False)


def remove_gravity(acc_data, fs):
    b, a = butter_highpass(cutoff=0.2, fs=fs, order=4)
    return filtfilt(b, a, acc_data, axis=0)


def minmax_scale(X):
    """
    Per-window min-max scaling to [-1,1]
    """
    mins = X.min(axis=0)
    maxs = X.max(axis=0)
    scales = np.where(maxs - mins == 0, 1, maxs - mins)
    return 2 * (X - mins) / scales - 1


def resample_window(timestamps, imu_data, target_fs=50, window_size=3.0):
    """
    Resample signal to target_fs without padding. Truncate if longer than window.
    Returns an array of shape (<=num_target, features).
    """
    raw_duration = timestamps[-1] - timestamps[0]
    duration = raw_duration if raw_duration > 0 else 1e-9
    num_target = int(math.ceil(window_size * target_fs))
    orig_fs = len(timestamps) / duration
    up = int(round(target_fs))
    down = int(round(orig_fs)) or 1
    resampled = resample_poly(imu_data, up, down, axis=0)
    # Truncate if longer
    if resampled.shape[0] > num_target:
        return resampled[:num_target]
    # Return shorter sequence without padding
    return resampled


# =============================================================================
# 2. Offline Dataset Definition
# =============================================================================
class OfflineGestureDataset(Dataset):
    """
    Each trial -> one fixed-length sample padded at return.
    CSV columns: user_id, trial_id, gesture_id, timestamp_s, acc_x,y,z, ang_vel_yaw,pitch,roll
    """
    LABEL_MAP = {12:0,13:1,14:2,15:2,16:2,17:2}

    def __init__(self, csv_path, window_size=3.0, target_fs=50):
        df = pd.read_csv(csv_path)
        df['label'] = df['gesture_id'].map(self.LABEL_MAP)
        self.user_ids = []
        self.samples = []  # list of (resampled_data, label)
        self.window_size = window_size
        self.target_fs = target_fs
        self.num_target = int(math.ceil(window_size * target_fs))

        for (user, trial, gid, src), grp in df.groupby(['user_id','trial_id','gesture_id','source']):
            grp = grp.sort_values('timestamp')
            t = grp['timestamp'].values
            acc = grp[['acc_x','acc_y','acc_z']].values
            gyro= grp[['w_yaw','w_pitch','w_roll']].values
            data = np.hstack([acc,gyro])
            rel_t= t - t[0]
            resampled = resample_window(rel_t, data, self.target_fs, self.window_size)
            self.user_ids.append(grp['user_id'].iloc[0])
            self.samples.append((resampled, grp['label'].iloc[0]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        resampled, y = self.samples[idx]
        # 1) gravity removal on accel only for actual data
        valid_len = resampled.shape[0]
        acc_hp = remove_gravity(resampled[:, :3], self.target_fs)
        data6 = np.hstack([acc_hp, resampled[:, 3:]])
        # 2) per-window min-max on actual data
        X_norm = minmax_scale(data6)
        # 3) pad at the end to fixed length
        pad_len = self.num_target - X_norm.shape[0]
        if pad_len > 0:
            pad = np.zeros((pad_len, X_norm.shape[1]))
            X_norm = np.vstack([X_norm, pad])
        else:
            X_norm = X_norm[:self.num_target]
        # return shape (C, T) and actual length for packing
        return torch.tensor(X_norm.T, dtype=torch.float32), torch.tensor(y, dtype=torch.long), valid_len

# =============================================================================
# 3. Training with 5-Fold CV and Metric Plotting
# =============================================================================
def train_cv_and_retrain(dataset, args):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # 5 folds × epochs 기록할 자료구조
    base = os.path.splitext(args.output)[0]
    all_fold_losses = []    # list of list: each sublist = [val_loss at epoch1…epochN]
    all_fold_f1s   = []     # same shape for f1_scores
    y_true_total, y_pred_total = [], []  # for aggregate confusion matrix
    # Print counts per label at start of training
    label_counts = {}
    for _, lbl in dataset.samples:
        label_counts[lbl] = label_counts.get(lbl, 0) + 1
    print("Label distribution across dataset:")
    for lbl, cnt in sorted(label_counts.items()):
        print(f"  Label {lbl}: {cnt}")
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=args.seed)
    y = np.array([label for _,label in dataset.samples])
    groups = np.array(dataset.user_ids)
    fold_metrics=[]
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(X=np.arange(len(dataset)), y=y), 1):
        # split
        fold_losses = []
        fold_accs   = []
        fold_f1s    = []
        train_ds = Subset(dataset, train_idx)
        val_ds   = Subset(dataset, val_idx)
        train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
        val_loader   = DataLoader(val_ds,   batch_size=args.batch_size, shuffle=False)

        # model & optimizer
        if args.model == 'bilstm':
            model = BiLSTMClassifier(6, 110, 1, 3)
            optimizer = torch.optim.SGD(model.parameters(), lr=args.lr, momentum=0.9)
        elif args.model == 'gru':
            model = GRUClassifier(6, (256, 128, 64), 3)
            optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
        elif args.model == 'simplecnn':
            model = SimpleCNNClassifier(6, 3)
            optimizer = torch.optim.Adam(model.parameters(), lr=args.lr) # CNN 계열은 Adam이 일반적으로 잘 동작
        elif args.model == 'cnnbilstm':
            model = CNNBiLSTMClassifier(6, 3)
            optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
        elif args.model == 'smalltcn':
            model = SmallTCNClassifier(6, 3)
            optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
        model.to(device)
        criterion = nn.CrossEntropyLoss()
        # train for a fixed number of iterations (mini-batch steps), not full epochs
        step = 0
        while step < args.iterations:
            model.train()
            for X, y, lengths in train_loader:
                X, y = X.to(device), y.to(device)
                lengths = lengths.cpu().long()
                optimizer.zero_grad()
                loss = criterion(model(X, lengths), y)
                loss.backward()
                optimizer.step()

                step += 1
                if step >= args.iterations:
                    break

            # after each “epoch” worth of data --- or after running out of loader --- run validation
            model.eval()
            val_loss = 0.0
            y_true, y_pred = [], []
            with torch.no_grad():
                for X, y, lengths in val_loader:
                    X, y = X.to(device), y.to(device)
                    lengths = lengths.cpu().long()
                    logits = model(X, lengths)
                    val_loss += criterion(logits, y).item() * X.size(0)
                    y_true.extend(y.cpu().numpy())
                    y_pred.extend(torch.argmax(logits,1).cpu().numpy())
            val_loss /= len(val_loader.dataset)
            acc = accuracy_score(y_true, y_pred)
            f1 = f1_score(y_true, y_pred, average='macro')

            # record & print per iteration-block
            fold_losses.append(val_loss)
            fold_accs.append(acc)
            fold_f1s.append(f1)
            # accumulate confusion only at the very last iteration
            if step == args.iterations:
                y_true_total.extend(y_true)
                y_pred_total.extend(y_pred)
            print(f"Fold {fold} | Iter {step} — Val Loss: {val_loss:.4f} | Acc: {acc:.4f} | F1: {f1:.4f}")

        all_fold_losses.append(fold_losses)
        all_fold_f1s.append(fold_f1s)
        last_loss = fold_losses[-1]
        last_acc  = fold_accs[-1]
        fold_metrics.append((fold, last_loss, last_acc))
    # Aggregate CV results
    losses = [m[1] for m in fold_metrics]
    accs   = [m[2] for m in fold_metrics]
    mean_loss, std_loss = np.mean(losses), np.std(losses)
    mean_acc,  std_acc  = np.mean(accs),  np.std(accs)
    print(f'\nCV Summary:')
    for f,l,a in fold_metrics:
        print(f'  Fold {f}: Loss={l:.4f}, Acc={a:.4f}')
    print(f'  Mean   : Loss={mean_loss:.4f}±{std_loss:.4f}, Acc={mean_acc:.4f}±{std_acc:.4f}')

    # 1) Loss curves
    plt.figure()
    for i, losses in enumerate(all_fold_losses, start=1):
       x = range(1, len(losses) + 1)
       plt.plot(x, losses, label=f'Fold {i}')
    plt.xlabel('Iteration Block')
    plt.ylabel('Validation Loss')
    plt.title('Val Loss vs Iteration Block (per Fold)')
    plt.legend()
    plt.savefig(f'{base}_loss_curve.png')

    # 2) F1 curves
    plt.figure()
    for i, f1s in enumerate(all_fold_f1s, start=1):
       x = range(1, len(f1s) + 1)
       plt.plot(x, f1s, label=f'Fold {i}')
    plt.xlabel('Iteration Block')
    plt.ylabel('Validation F1 Score')
    plt.title('Val F1 vs Iteration Block (per Fold)')
    plt.legend()
    plt.savefig(f'{base}_f1_curve.png')

    # 3) Confusion Matrix (aggregated across folds)
    cm = confusion_matrix(y_true_total, y_pred_total)
    plt.figure()
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.colorbar()
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, cm[i,j], ha='center', va='center', color='white')
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Aggregated Confusion Matrix')
    plt.savefig(f'{base}_confusion_matrix.png')

    # --- Retrain on full dataset ---
    print("\nRetraining on full dataset (no validation split)...")
    full_loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)
    if args.model == 'bilstm':
        final_model = BiLSTMClassifier(6, 110, 1, 3)
        final_optimizer = torch.optim.SGD(final_model.parameters(), lr=args.lr, momentum=0.9)
    elif args.model == 'gru':
        final_model = GRUClassifier(6, (256, 128, 64), 3)
        final_optimizer = torch.optim.Adam(final_model.parameters(), lr=args.lr)
    elif args.model == 'simplecnn':
        final_model = SimpleCNNClassifier(6, 3)
        final_optimizer = torch.optim.Adam(final_model.parameters(), lr=args.lr)
    elif args.model == 'cnnbilstm':
        final_model = CNNBiLSTMClassifier(6, 3)
        final_optimizer = torch.optim.Adam(final_model.parameters(), lr=args.lr)
    elif args.model == 'smalltcn':
        final_model = SmallTCNClassifier(6, 3)
        final_optimizer = torch.optim.Adam(final_model.parameters(), lr=args.lr)
    final_model.to(device)
    criterion = nn.CrossEntropyLoss()

    # train final for a fixed number of iterations (mini-batch steps)
    step2 = 0
    while step2 < args.iterations:
        final_model.train()
        for X, y, lengths in full_loader:
            X, y = X.to(device), y.to(device)
            lengths = lengths.cpu().long()
            final_optimizer.zero_grad()
            loss = criterion(final_model(X, lengths), y)
            loss.backward()
            final_optimizer.step()
            step2 += 1
            if step2 >= args.iterations:
                break

    # evaluate on training set
    final_model.eval()
    total_loss = 0.0
    all_true, all_pred = [], []
    with torch.no_grad():
        for X,y, lengths in full_loader:
            X,y = X.to(device), y.to(device)
            lengths = lengths.cpu().long()
            logits = final_model(X, lengths)
            total_loss += criterion(logits, y).item() * X.size(0)
            all_true.extend(y.cpu().numpy())
            all_pred.extend(torch.argmax(logits,1).cpu().numpy())
    final_loss = total_loss / len(full_loader.dataset)
    final_acc  = accuracy_score(all_true, all_pred)
    print(f'\nFinal model trained on all data | Loss: {final_loss:.4f} | Acc: {final_acc:.4f}')

    # save final model
    torch.save({'model': final_model.state_dict()}, args.output)
    print(f"Saved final model to {args.output}")

# =============================================================================
# 5. CLI
# =============================================================================
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--csv', required=True)
    parser.add_argument('--model', choices=['bilstm', 'gru', 'simplecnn', 'cnnbilstm', 'smalltcn'], default='bilstm')
    parser.add_argument('--batch-size', type=int, default=100)
    parser.add_argument('--lr', type=float, default=3e-2)
    parser.add_argument('--epochs', type=int, default=200)
    parser.add_argument('--iterations', type=int, default=200,help='number of mini-batch update steps (not full epochs)')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--fs', type=float, default=50.0)
    parser.add_argument('--window', type=float, default=3.0)
    parser.add_argument('--output', type=str, default='gesture_model.pth')
    args=parser.parse_args()
    
    if args.output == 'gesture_model.pth':
        args.output = f'offline_gesture_{args.model}.pth'
    
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(args.seed)
    if args.model == 'bilstm':
        args.batch_size = args.batch_size or 100
        args.lr = args.lr or 3e-2
        args.iterations = args.iterations or 200
    elif args.model == 'gru':
        args.batch_size = args.batch_size or 64
        args.lr = args.lr or 3e-4
        args.iterations = args.iterations or 100
    elif args.model == 'simplecnn':
        args.batch_size = args.batch_size or 100
        args.lr = args.lr or 1e-2
        args.iterations = args.iterations or 200
    elif args.model == 'cnnbilstm':
        args.batch_size = args.batch_size or 64
        args.lr = args.lr or 3e-4
        args.iterations = args.iterations or 100
    elif args.model == 'smalltcn':
        args.batch_size = args.batch_size or 64
        args.lr = args.lr or 1e-3
        args.iterations = args.iterations or 150
    print("Training & evaluation start.")
    train_cv_and_retrain(OfflineGestureDataset(args.csv, args.window, args.fs), args)
    print("Training & evaluation complete.")