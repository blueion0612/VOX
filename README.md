스마트워치 기반 제스처 인식 프로그램 Vox의 ReadME Trial입니다.

0) Setup

1. 기본 선행 연구는 wear_mocap을 참조하였고, 스마트워치 및 스마트폰의 어플리케이션은 해당 Github 기반 설치가 필요합니다.

2. 스마트워치와 스마트폰은 블루투스 페어링, 스마트폰과 연산 서버용 컴퓨터는 동일 Wifi내 연결이 되어있어야 합니다.
    Broadcasting 기반 IMU sensor Listen을 하기 때문입니다.



1) 폴더 구성 설명

1. Data 
1-1. Offline 폴더는 공개 데이터세트인 6DMG: ANew6DMotion Gesture Database를 포함하고 있습니다.
    기존 Matlab 기반 C++ 환경에서만 사용 가능한 mat 파일을 파이썬 코드에서 활용할 수 있도록, CSV 변환을 하였습니다.
    mat_to_csv.py를 통해 동일 과정을 사용 및 다른 레이블 및 제스처를 csv로 생성 가능합니다.

1-2. Online 폴더는 직접 스마트워치를 착용하고 녹화한 학습용 CSV가 위치합니다. 
    imu_record_trials.py를 통해 스마트워치로부터 제스처 데이터 녹화 및 레이블과 착용자의 기입이 가능합니다.

1-3. Test 폴더는 직접 스마트워치를 착용하고 녹화한 테스트용 csv가 위치합니다.

2. Model
2-1. Offline 폴더에는 각 모델 별 공개 데이터세트를 기반으로 오프라인 학습을 진행한 결과가 위치합니다.
    vox\classification\train_gesture_offline.py를 통해 학습하였습니다.
    상세 모델 폴더에는 Plot 시각화 결과가 위치하고, log_txt에는 학습 당시 프롬프트 결과창이 기입되어 있습니다.

2-2. Online
    3개의 Online 폴더에는 스마트워치 IMU 데이터의 전처리를 각각 Raw 그 자체로, HPF 적용 시, HPF와 LPF 모두 적용시 결과가 기입되어 있습니다.
    현재 가장 일반화가 잘 된 결과는 HPF로 판단되어, 해당 기법을 기반으로 학습 및 실시간 분류기 코드가 구성되어 있습니다. 
    즉, Raw 혹은 HPF와 LPF 모두 적용 모델을 구동하기 위해서는 코드의 수정이 필요합니다.

3. vox
3-1. classification
    분류기의 모델 구조, 오프라인 학습, 온라인 학습, 전체 모델별 비교용 코드가 위치합니다.

3-2. data_deploy
    사전 학습된 필터의 가중치가 위치합니다. 선행 연구의 스켈레톤 구조가 위치합니다.

3-3. data_types
    수신되는 데이터의 인덱스와 스켈레톤 매핑 정보가 위치치합니다.

3-4. estimate
    Pose estimation용 코드가 위치합니다.

3-5. stream
    listener에는 IMU로부터 수신받는 코드, publisher에는 외부 UDP 송신 코드가 존재합니다.



2) 구동 방법

1. CMD 창을 실행시킵니다.

2. cd ...\vox

3. ipconfig
    현재 스마트폰과 연산 서버가 연결된 ip의 값을 확인합니다.

4. 해당 ip값을 스마트폰 어플리케이션에 입력하고 주머니에 넣습니다. 
    페어링된 스마트워치에서도 wear_mocap 앱을 구동 후 "Pocket"을 선택합니다.

5. 정자세로 손을 90도 올리고 시계를 보는 자세를 취하면 초기 정렬이 완료되고, "stream IMU"를 눌러 스트리밍을 시작합니다.

6. Unity 프로그램을 실행합니다.

7. python C:\Capstone\vox\watch_phone_pocket_classification.py 192.168.219.193 Model\Online_with_HPF\online_gesture_cnnbilstm.pth cnnbilstm
    해당 모델과 종류는 변경 가능합니다.
    README 예제에선 가장 성능이 좋은 모델을 구동하겠습니다.

8. 실시간 스트리밍 중 Pose Estimation이 Unity에 곧바로 전송됩니다.

9. Right Shift를 꾹 누른 상태로 제스처를 행동합니다.
    --- Start Gesture Recording ---
    ...
    --- End Gesture Recording. Processing... ---

10. 분류된 결과가 UDP 포켓을 통해 사전 설정한 서버로 전송됩니다.

11. 프로그램 종료 시 엔터를 입력합니다.