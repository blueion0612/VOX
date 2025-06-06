from scipy.io import loadmat
import numpy as np

# 예시 .mat 파일 경로
mat_file = 'C:/Capstone/arm-pose-estimation-main/mat/matL/g13_D2_t03.mat' # 실제 파일 경로로 변경
data = loadmat(mat_file)
gest_matrix = data['gest']
timestamps = gest_matrix[0, :] # 타임스탬프 행

duration = timestamps[-1] - timestamps[0]
num_samples = len(timestamps)
avg_sampling_interval = duration / (num_samples -1) if num_samples > 1 else 0
estimated_sampling_rate = 1 / avg_sampling_interval if avg_sampling_interval > 0 else 0

print(f"File: {mat_file}")
print(f"Number of samples (n): {num_samples}")
print(f"First timestamp: {timestamps[0]}")
print(f"Last timestamp: {timestamps[-1]}")
print(f"Duration of this trial: {duration:.3f} seconds")
if estimated_sampling_rate > 0:
    print(f"Estimated sampling rate: {estimated_sampling_rate:.2f} Hz")
    print(f"Average sampling interval: {avg_sampling_interval*1000:.2f} ms")
    
if 'gest' in data:
    gest_matrix = data['gest']
    timestamps = gest_matrix[0, :]
    print(f"--- Timestamps for {mat_file} ---")
    print(timestamps)
    print(f"Min timestamp: {np.min(timestamps)}, Max timestamp: {np.max(timestamps)}")

    if len(timestamps) > 1:
        intervals = np.diff(timestamps)
        print("Intervals between timestamps:")
        print(intervals)
        print(f"Min interval: {np.min(intervals)}, Max interval: {np.max(intervals)}, Avg interval: {np.mean(intervals)}")
    else:
        print("Not enough timestamps to calculate intervals.")
else:
    print(f"'gest' matrix not found in {mat_file}")
