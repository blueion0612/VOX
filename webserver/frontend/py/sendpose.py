# import socket
# import time
# import struct

# # CSV 파일 경로
# csv_path = "pose_log.csv"

# # UDP 설정
# UDP_IP = "127.0.0.1"
# UDP_PORT = 50003
# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# with open(csv_path, "r") as f:
#     for line in f:
#         # 헤더 또는 빈 줄 건너뛰기
#         if not line.strip() or not any(char.isdigit() for char in line):
#             continue

#         try:
#             # 문자열 → float 리스트
#             values = [float(v) for v in line.strip().split(",")]

#             # float → 4바이트 단위 직렬화
#             data = b''.join([struct.pack("f", v) for v in values])

#             # UDP 전송
#             sock.sendto(data, (UDP_IP, UDP_PORT))
#             print(f"Sent {len(data)} bytes")

#             time.sleep(0.033)  # 30 FPS 속도로 전송
#         except Exception as e:
#             print("Skipping invalid line:", e)


import socket
import time
import struct

csv_path = "pose_log.csv"

UDP_IP = "127.0.0.1"
UDP_PORT = 50003
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

with open(csv_path, "r") as f:
    for line in f:
        if not line.strip() or not any(char.isdigit() for char in line):
            continue

        try:
            values = [float(v) for v in line.strip().split(",")]

            # ✨ 손목 회전 쿼터니언 인덱스 조정 (예시: val_49~val_52)
            wrist_q = values[49:53]  # [qw, qx, qy, qz]

            # 회전 순서 Unity용 (x, y, z, w)
            data = bytearray()
            data.extend(struct.pack("f", wrist_q[1]))  # x
            data.extend(struct.pack("f", wrist_q[2]))  # y
            data.extend(struct.pack("f", wrist_q[3]))  # z
            data.extend(struct.pack("f", wrist_q[0]))  # w

            # 나머지 값은 그대로 전송
            data.extend(b''.join([struct.pack("f", v) for v in values[4:]]))

            sock.sendto(data, (UDP_IP, UDP_PORT))
            print(f"Sent {len(data)} bytes")

            time.sleep(0.033)  # 30 FPS
        except Exception as e:
            print("Skipping invalid line:", e)
