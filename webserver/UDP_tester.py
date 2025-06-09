import socket
import struct
import time

DEST_IP = "3.38.247.200"
DEST_PORT = 9999

# generate_data 함수를 직접 입력받는 로직으로 대체
def get_manual_data():
    """ 사용자로부터 직접 레이블을 입력받아 [double, int, int] 형식으로 반환 """
    while True:
        try:
            label_input = input("전송할 레이블 입력 (0, 1, 2): ")
            predicted_label = int(label_input)
            if predicted_label in [0, 1, 2]:
                ts = time.time()
                return [ts, 1, predicted_label]
            else:
                print("0, 1, 2 중에서만 입력하세요.")
        except ValueError:
            print("숫자만 입력하세요.")

def main():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("수동으로 데이터를 입력하여 전송합니다. (종료: Ctrl+C)")

    try:
        while True:
            data = get_manual_data()
            packed = struct.pack('<dii', *data)
            udp_socket.sendto(packed, (DEST_IP, DEST_PORT))
            print(f"Sent: {data}")
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
    finally:
        udp_socket.close()
        print("송신 완료!")

if __name__ == "__main__":
    main()