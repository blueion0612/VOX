# import asyncio
# import websockets
# import pandas as pd

# df = pd.read_csv("pose_log.csv", on_bad_lines="skip", engine="python")

# async def send_data(websocket):
#     for _, row in df.iterrows():
#         try:
#             values = row.tolist()

#             # UDP 방식과 동일한 순서로 추출
#             hand_q = [values[50], values[51], values[52], values[49]]  # [qx, qy, qz, qw]
#             hand_p = [values[5], values[6], values[7]]

#             larm_q = [values[10], values[11], values[12], values[9]]
#             larm_p = [values[13], values[14], values[15]]

#             uarm_q = [values[28], values[29], values[30], values[27]]
#             uarm_p = [values[31], values[32], values[33]]

#             hips_q = [values[36], values[37], values[38], values[35]]

#             floats = (
#                 hand_q + hand_p +
#                 larm_q + larm_p +
#                 uarm_q + uarm_p +
#                 hips_q
#             )

#             msg = ",".join(map(str, floats))
#             await websocket.send(msg)
#             await asyncio.sleep(0.033)

#         except Exception as e:
#             print("Skipping:", e)

# async def main():
#     print("WebSocket server ready at ws://localhost:8765")
#     async with websockets.serve(send_data, "localhost", 8765):
#         await asyncio.Future()

# if __name__ == "__main__":
#     asyncio.run(main())


import asyncio
import websockets
import pandas as pd

df = pd.read_csv("pose_log.csv", on_bad_lines="skip", engine="python")

async def send_data(websocket):
    print("WebSocket connection opened.")
    while True:
        for _, row in df.iterrows():
            try:
                values = row.tolist()

                hand_q = [values[50], values[51], values[52], values[49]]
                hand_p = [values[5], values[6], values[7]]

                larm_q = [values[10], values[11], values[12], values[9]]
                larm_p = [values[13], values[14], values[15]]

                uarm_q = [values[28], values[29], values[30], values[27]]
                uarm_p = [values[31], values[32], values[33]]

                hips_q = [values[36], values[37], values[38], values[35]]

                floats = (
                    hand_q + hand_p +
                    larm_q + larm_p +
                    uarm_q + uarm_p +
                    hips_q
                )

                msg = ",".join(map(str, floats))
                await websocket.send(msg)
                await asyncio.sleep(0.033)

            except Exception as e:
                print("Skipping:", e)

        print("CSV playback loop restarted.")

async def main():
    print("WebSocket server ready at ws://localhost:8765")
    async with websockets.serve(send_data, "localhost", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
