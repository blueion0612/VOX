import argparse
import logging
import queue
import threading
from datetime import datetime
import socket
import struct
import numpy as np
import torch
from pynput import keyboard
from scipy.signal import resample_poly, butter, filtfilt

# 기존 import
from wear_mocap_ape import config
from wear_mocap_ape.data_types import messaging
from wear_mocap_ape.estimate.watch_phone_pocket_kalman import WatchPhonePocketKalman
from wear_mocap_ape.stream.listener.imu import ImuListener
from wear_mocap_ape.stream.publisher.pose_est_udp import PoseEstPublisherUDP

from vox.classification.classifier import BiLSTMClassifier, GRUClassifier, SimpleCNNClassifier, CNNBiLSTMClassifier, SmallTCNClassifier
# --- 1. 제스처 분류를 위한 전처리 유틸리티 ---
def butter_highpass(cutoff, fs, order=4):
    nyq = 0.5 * fs
    return butter(order, cutoff / nyq, btype='high', analog=False)

def remove_gravity(acc_data, fs):
    b, a = butter_highpass(0.2, fs, order=4)
    return filtfilt(b, a, acc_data, axis=0)

def minmax_scale(X):
    mins = X.min(axis=0)
    maxs = X.max(axis=0)
    scales = np.where(maxs - mins == 0, 1, maxs - mins)
    return 2 * (X - mins) / scales - 1

# --- 2. 실시간 제스처 분류기 클래스 ---
class GestureClassifier(threading.Thread):
    # [수정] __init__에서 gesture_ip와 gesture_port를 인자로 받음
    def __init__(self, model_path: str, model_type: str, gesture_bundle_q: queue.Queue, gesture_ip: str, gesture_port: int):
        super().__init__(daemon=True)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # ▼▼▼▼▼ 모델 로드 부분을 if/elif/else 구조로 수정 ▼▼▼▼▼
        print(f"Attempting to load model architecture: {model_type}")
        if model_type == 'bilstm':
            self.model = BiLSTMClassifier(input_size=6, hidden_size=110, num_layers=1, num_classes=3)
        elif model_type == 'gru':
            self.model = GRUClassifier(input_size=6, hidden_sizes=(256, 128, 64), num_classes=3)
        elif model_type == 'simplecnn':
            self.model = SimpleCNNClassifier(num_channels=6, num_classes=3)
        elif model_type == 'cnnbilstm':
            self.model = CNNBiLSTMClassifier(num_channels=6, num_classes=3)
        elif model_type == 'smalltcn':
            self.model = SmallTCNClassifier(in_channels=6, num_classes=3)
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        ckpt = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(ckpt['model'])
        self.model.to(self.device).eval()
        logging.info(f"Gesture classifier model '{model_type}' loaded from {model_path} on {self.device}")
        
        self.gesture_bundle_q = gesture_bundle_q
        self._terminate = threading.Event()

        self.gesture_ip = gesture_ip
        self.gesture_port = gesture_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run(self):
        while not self._terminate.is_set():
            try:
                raw_rows = self.gesture_bundle_q.get(timeout=1)
                if not raw_rows: continue

                logging.info(f"Processing gesture with {len(raw_rows)} data points.")
                processed_tensor, valid_len = self.preprocess_data(raw_rows)
                
                with torch.no_grad():
                    logits = self.model(processed_tensor.to(self.device), torch.tensor([valid_len]))
                    probs = torch.softmax(logits, dim=1)
                    confidence, predicted_label_tensor = torch.max(probs, 1)

                predicted_label = predicted_label_tensor.item()
                label_map = {0: 'V', 1: 'X', 2: 'Circle'}
                label_name = label_map.get(predicted_label, "Unknown")

                print("\n" + "="*30)
                print(f" Gesture Detected: {label_name} ")
                print(f" Confidence: {confidence.item():.2%} ")
                print("="*30)

                # [수정] UDP 패킷을 직접 생성하고 즉시 전송 및 출력
                timestamp = datetime.now().timestamp()  # 8바이트 double
                device_id = 1                           # 4바이트 int
                # predicted_label은 이미 4바이트 int 입니다.
                
                # CMD 창에는 사람이 보기 편하도록 원래 데이터 리스트를 출력합니다.
                human_readable_data = [timestamp, device_id, predicted_label]
                print(f"[INFO] 제스처 UDP 패킷 발신 -> {self.gesture_ip}:{self.gesture_port} | 내용물: {human_readable_data}")

                # '<dii' = Little-Endian, double, int, int (총 16바이트)
                bytes_to_send = struct.pack('<dii', timestamp, device_id, predicted_label)
                self.sock.sendto(bytes_to_send, (self.gesture_ip, self.gesture_port))

            except queue.Empty:
                continue
    # preprocess_data와 stop 메서드는 수정할 필요 없습니다.
    def preprocess_data(self, rows):
        """ fine_tune_online.py와 동일한 전처리를 수행 """
        data = np.array(rows)
        # smartwatch 데이터는 [10], [11], [12] (자이로), [16], [17], [18] (가속도) 컬럼을 사용합니다.
        # 이 인덱스는 watch_phone_imu_msg msg-format에 따라 정의되어 있습니다.
        acc_x = -data[:, 17]; acc_y = data[:, 18]; acc_z = -data[:, 16]
        w_yaw = data[:, 12]; w_pitch = -data[:, 11]; w_roll = -data[:, 10]
        imu_data = np.vstack([acc_x, acc_y, acc_z, w_yaw, w_pitch, w_roll]).T

        target_fs, window_size = 50.0, 3.0
        num_target = int(window_size * target_fs)
        
        duration = np.sum(data[:, 0]) # sw_dt
        orig_fs = len(rows) / duration if duration > 0 else target_fs
        up, down = int(round(target_fs)), int(round(orig_fs)) or 1
        resampled = resample_poly(imu_data, up, down, axis=0)

        acc_hp = remove_gravity(resampled[:, :3], target_fs)
        feat = np.hstack([acc_hp, resampled[:, 3:]])
        norm = minmax_scale(feat)
        # norm = minmax_scale(resampled)
        
        L = norm.shape[0]
        length = min(L, num_target)
        if L < num_target:
            pad = np.zeros((num_target - L, 6))
            norm = np.vstack([norm, pad])
        else:
            norm = norm[:num_target]
            
        return torch.tensor(norm.T, dtype=torch.float32).unsqueeze(0), length

    def stop(self):
        self._terminate.set()
        self.sock.close() # [추가] 스레드 종료 시 소켓 닫기

# --- 3. 메인 실행 함수 ---
def run_watch_phone_pocket_kalman(ip: str, smooth: int, stream_mc: bool, gesture_model: str, model_type: str):
    
    # --- Pose Estimation 파이프라인 (기존과 동일) ---
    lstn = ImuListener(ip=ip, msg_size=messaging.watch_phone_imu_msg_len, port=config.PORT_LISTEN_WATCH_PHONE_IMU)
    imu_q = lstn.listen_in_thread()
    kalman_q = queue.Queue()
    est = WatchPhonePocketKalman(model_path=config.PATHS["deploy"] / "kalman" / "SW-v3.8-model-436400", smooth=smooth, num_ensemble=48, window_size=10, add_mc_samples=stream_mc)
    msg_q = est.process_in_thread(kalman_q)
    
    # Pose Estimation 결과를 로컬 IP로 보내는 Publisher (이름을 pub_pose로 명확화)
    pub_pose = PoseEstPublisherUDP(
        ip=ip,
        port=config.PORT_PUB_LEFT_ARM
    )
    pub_pose.publish_in_thread(msg_q)

    # --- 제스처 분류용 큐 및 제어 이벤트 ---
    gesture_raw_q = queue.Queue()
    gesture_bundle_q = queue.Queue()
    is_recording = threading.Event()

    # --- 데이터 분배기 스레드 (기존과 동일) ---
    def broadcaster(in_q, q1, q2, rec_event):
        while True:
            try:
                raw_imu = in_q.get(timeout=1)
                q1.put(raw_imu)
                if rec_event.is_set():
                    q2.put(raw_imu)
            except queue.Empty:
                continue
    broadcaster_thread = threading.Thread(target=broadcaster, args=(imu_q, kalman_q, gesture_raw_q, is_recording), daemon=True)
    broadcaster_thread.start()

    # --- 제스처 분류기 스레드 ---
    # [수정] 제스처 UDP 전송에 필요한 IP와 포트를 직접 전달
    classifier = GestureClassifier(
        model_path=gesture_model, 
        model_type=model_type, 
        gesture_bundle_q=gesture_bundle_q,
        gesture_ip="3.38.247.200", 
        gesture_port=9999
    )
    classifier.start()

    # --- 키보드 리스너 설정 ---
    # 이 부분은 수정할 필요 없습니다.
    current_gesture_data = []
    RECORD_KEY = keyboard.Key.shift_r
    def on_press(key):
        if key == RECORD_KEY and not is_recording.is_set():
            is_recording.set()
            with gesture_raw_q.mutex:
                gesture_raw_q.queue.clear()
            current_gesture_data.clear()
            print("--- Start Gesture Recording ---")
    def on_release(key):
        nonlocal current_gesture_data
        if key == RECORD_KEY and is_recording.is_set():
            is_recording.clear()
            print("--- End Gesture Recording. Processing... ---")
            while not gesture_raw_q.empty():
                try:
                    current_gesture_data.append(gesture_raw_q.get_nowait())
                except queue.Empty:
                    break
            if current_gesture_data:
                gesture_bundle_q.put(list(current_gesture_data))
            current_gesture_data.clear()
    key_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    key_listener.start()

    # --- 메인 스레드 종료 대기 ---
    print("\n" + "="*50)
    print("      Real-time Pose Estimation & Gesture Recognition")
    print("="*50)
    print(f"Pose Estimation is now running.")
    print(f"Hold [Right SHIFT] key to record a gesture.")
    input("[TERMINATION TRIGGER] press enter to exit\n")


    # --- 모든 스레드 종료 ---
    key_listener.stop()
    lstn.terminate()
    est.terminate()
    pub_pose.terminate()  # pub_pose는 그대로 종료
    classifier.stop()     # classifier 종료 (내부적으로 소켓도 닫힘)
    classifier.join()
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('ip', type=str, help='Put your local IP here.')
    parser.add_argument('gesture_model', type=str, help='Path to your fine-tuned gesture model .pth file.')
    parser.add_argument(
        'model_type', 
        type=str, 
        choices=['bilstm', 'gru', 'simplecnn', 'cnnbilstm', 'smalltcn'],
        help='Type of the gesture model architecture.'
    )
    parser.add_argument('smooth', nargs='?', type=int, default=5, help='Smooth predicted trajectories')
    args = parser.parse_args()
    
    run_watch_phone_pocket_kalman(
        ip=args.ip, 
        smooth=args.smooth, 
        stream_mc=True, 
        gesture_model=args.gesture_model,
        model_type=args.model_type 
    )