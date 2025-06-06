import os
import argparse
import csv
import threading
from datetime import datetime
import queue
import pandas as pd

from wear_mocap_ape import config
from wear_mocap_ape.data_types import messaging
from wear_mocap_ape.stream.listener.imu import ImuListener

# =============================================================================
# Single-CSV IMU Trial Recorder
# =============================================================================
# Records all labeled trials into one CSV file. No label in filename;
# prompts for label, then Enter to start/stop recording, appends rows with label.

def record_trials(ip, output_csv, window_size=3.0):
    # Prepare output directory
    os.makedirs(os.path.dirname(output_csv) or '.', exist_ok=True)

    # Build CSV header: user_id, trial_id, timestamp_s, raw fields…, label
    lookup = messaging.WATCH_PHONE_IMU_LOOKUP
    max_idx = max(lookup.values())
    raw_headers = [None] * (max_idx + 1)
    for name, idx in lookup.items():
        raw_headers[idx] = name
    headers = ['user_id', 'trial_id', 'timestamp_s'] + raw_headers + ['label']

    # 1) 기존 파일이 있으면 마지막 trial_id를 가져와서 이어쓰기
    if os.path.exists(output_csv):
        # 기존 CSV 읽어서 가장 큰 trial_id 찾기
        df_exist = pd.read_csv(output_csv)
        trial_num = int(df_exist['trial_id'].max())
        mode = 'a'
    else:
        trial_num = 0
        mode = 'w'

    # 2) 파일 열기 (append 또는 write)
    with open(output_csv, mode, newline='') as f:
        writer = csv.writer(f)
        # 새로 만드는 파일이라면 헤더 쓰기
        if mode == 'w':
            writer.writerow(headers)
            f.flush()

        # IMU 리스너 시작
        listener = ImuListener(
            ip=ip,
            msg_size=messaging.watch_phone_imu_msg_len,
            port=config.PORT_LISTEN_WATCH_PHONE_IMU
        )
        sensor_q = listener.listen_in_thread()

        print("=== IMU Trial Recorder (Single CSV) ===")
        print("Each trial: type label (integer), Enter to start, Enter to stop recording.")
        print("Type 'q' to finish and close CSV.")
        try:
            while True:
                user_in = input("Label for next trial (or 'q' to quit): ")
                if user_in.strip().lower() == 'q':
                    break
                if not user_in.strip().isdigit():
                    print("Invalid input. Enter a numeric label or 'q'.")
                    continue
                label = int(user_in.strip())
                trial_num += 1

                print(f"--- Trial {trial_num} labeled '{label}' ---")
                input("Press Enter to START recording...")
                # ↓ 녹화 시작 전까지 쌓인 예전 데이터를 모두 비워줘서
                #    Enter부터 Enter까지 구간만 남도록 합니다.
                try:
                    while True:
                        sensor_q.get_nowait()
                except queue.Empty:
                    pass
                print(f"Recording for label {label}. Press Enter again to STOP.")

                rows = []
                start_time = datetime.now()
                stop_event = threading.Event()

                def recorder_loop():
                    while not stop_event.is_set():
                        try:
                            raw = sensor_q.get(timeout=0.01)
                        except queue.Empty:
                            continue
                        # comp_time since trial start
                        comp_t = (datetime.now() - start_time).total_seconds()
                        # ensure list
                        raw_list = list(raw)
                        # prepend user_id and trial_id
                        rows.append(['recorded_user', trial_num, comp_t] + raw_list + [label])

                t = threading.Thread(target=recorder_loop, daemon=True)
                t.start()
                input()  # stop trigger
                stop_event.set()
                t.join()

                # Write collected rows
                for row in rows:
                    writer.writerow(row)
                f.flush()
                print(f"Saved {len(rows)} samples for label {label} \n")

        finally:
            listener.terminate()
            print(f"Recording complete. Trials recorded: {trial_num}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Record all IMU trials into one CSV with labels.')
    parser.add_argument('--ip',      required=True, help='Local IP for IMU listener')
    parser.add_argument('--out-csv', required=True, help='Path to output CSV file')
    parser.add_argument('--window',  type=float, default=3.0, help='Maximum trial duration (sec)')
    args = parser.parse_args()
    record_trials(args.ip, args.out_csv, args.window)
