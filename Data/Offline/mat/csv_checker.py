import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import ks_2samp

def load_and_tag(csv_path, tag):
    df = pd.read_csv(csv_path)
    if 'timestamp' in df.columns and 'timestamp_s' not in df.columns:
        df = df.rename(columns={'timestamp': 'timestamp_s'})
    df['dataset'] = tag
    return df

def compare_sampling(df, tag):
    # timestamp_s 간격 분포
    dt = df['timestamp_s'].diff().dropna()
    print(f"[{tag}] Sampling interval: mean={dt.mean():.4f}s  std={dt.std():.4f}s  min={dt.min():.4f}s  max={dt.max():.4f}s")
    return dt

def compare_stats(df, sensor_cols):
    stats = df[sensor_cols].agg(['mean','std']).T
    stats.columns = ['mean','std']
    return stats

def compare_distributions(train, test, sensor_cols, alpha=0.01):
    print("\n=== KS-test for per-channel distribution differences ===")
    for col in sensor_cols:
        stat, p = ks_2samp(train[col].dropna(), test[col].dropna())
        diff = "DIFFERENT" if p < alpha else "similar"
        print(f"  {col:10s}: KS-stat={stat:.3f}, p={p:.3e} → {diff}")

def recommend_preprocessing(stats_train, stats_test, sensor_cols):
    print("\n=== Recommendation ===")
    for col in sensor_cols:
        m1, s1 = stats_train.loc[col]
        m2, s2 = stats_test.loc[col]
        shift = abs(m1 - m2)
        rel = shift / (s1+1e-6)
        if rel > 0.5:
            print(f"- {col}: mean shift {shift:.2f} ({rel:.1f}×train-std) → apply offset correction or gravity removal")
        elif abs(s1 - s2)/s1 > 0.3:
            print(f"- {col}: std ratio train/test {s2/s1:.2f} → consider global scaling or variance normalization")
    print("")

# ——— 1) CSV 로드 및 태깅 ———
train_csv = '6DMG_VXO_light.csv'
test_csv  = 'vxo_gesture.csv'
csv1 = load_and_tag(train_csv, 'train')
csv2 = load_and_tag(test_csv,  'test')

# ——— 2) 공통 컬럼 정리 ———
sensor_cols = ['sw_lacc_x','sw_lacc_y','sw_lacc_z',
               'sw_gyro_x','sw_gyro_y','sw_gyro_z']
cols = ['dataset','label','timestamp_s'] + sensor_cols
df = pd.concat([csv1[cols], csv2[cols]], ignore_index=True)

# ——— 3) 수집 환경 비교 (샘플링) ———
dt_train = compare_sampling(csv1, 'train')
dt_test  = compare_sampling(csv2, 'test')

# ——— 4) 레이블별·채널별 기초 통계 ———
print("\n=== Per-label & per-dataset summary ===")
grp = df.groupby(['dataset','label'])[sensor_cols]
stats = grp.agg(['mean','std']).round(3)
print(stats)

# ——— 5) 전체 분포 차이 KS-test ———
compare_distributions(csv1, csv2, sensor_cols)

# ——— 6) 통계 기반 전처리 추천 ———
# 여기서는 레이블 전체 합친 통계 사용
stats_train = csv1[sensor_cols].agg(['mean','std']).T
stats_test  = csv2[sensor_cols].agg(['mean','std']).T
recommend_preprocessing(stats_train, stats_test, sensor_cols)

# ——— 7) 레이블별 평균 시계열 시각화 ———
for lbl in sorted(df['label'].unique()):
    plt.figure(figsize=(8,3))
    for ds in ['train','test']:
        sub = df[(df['dataset']==ds) & (df['label']==lbl)].copy()
        sub['t_int'] = sub['timestamp_s'].astype(int)
        mean_curve = sub.groupby('t_int')[sensor_cols].mean()
        plt.plot(mean_curve.index, mean_curve['sw_lacc_x'], label=f'{ds} acc_x')
    plt.title(f'Label {lbl} — Accel X Mean Curve')
    plt.xlabel('Time (s)')
    plt.ylabel('Accel X')
    plt.legend()
    plt.tight_layout()

plt.show()
