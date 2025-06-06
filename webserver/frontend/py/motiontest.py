import socket, struct, pandas as pd, time

df = pd.read_csv("pose_log.csv", on_bad_lines="skip", engine="python")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ip, port = "127.0.0.1", 50003

for _, row in df.iterrows():
    f = row.tolist()

    # 첫 세트만 전송 (Quaternion: f[1:5], Position: f[5:8])
    qx, qy, qz, qw = f[2], f[3], f[4], f[1]  # (x,y,z,w)
    px, py, pz = f[5], f[6], f[7]

    values = [qx, qy, qz, qw, px, py, pz,
                qx, qy, qz, qw, px, py, pz,
                qx, qy, qz, qw, px, py, pz]

    msg = struct.pack("f" * len(values), *values)
    sock.sendto(msg, (ip, port))
    time.sleep(0.03)

print("✅ Data sent!")
