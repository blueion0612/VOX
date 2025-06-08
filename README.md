스마트워치 기반 제스처 인식 프로그램 Vox의 ReadME Trial입니다.

0. Setup

0-1. 기본 선행 연구는 wear_mocap을 참조하였고, 스마트워치 및 스마트폰의 어플리케이션은 해당 Github 기반 설치가 필요합니다.

0-2. 스마트워치와 스마트폰은 블루투스 페어링, 스마트폰과 연산 서버용 컴퓨터는 동일 Wifi내 연결이 되어있어야 합니다.
    Broadcasting 기반 IMU sensor Listen을 하기 때문입니다.

0-3. 웹서비스의 주소는 아래와 같습니다:
    https://voxkr.xyz/



1. 폴더 구성 설명

1-1. Data 
1-1-1. Offline 폴더는 공개 데이터세트인 6DMG: ANew6DMotion Gesture Database를 포함하고 있습니다.
    기존 Matlab 기반 C++ 환경에서만 사용 가능한 mat 파일을 파이썬 코드에서 활용할 수 있도록, CSV 변환을 하였습니다.
    mat_to_csv.py를 통해 동일 과정을 사용 및 다른 레이블 및 제스처를 csv로 생성 가능합니다.

1-1-2. Online 폴더는 직접 스마트워치를 착용하고 녹화한 학습용 CSV가 위치합니다. 
    imu_record_trials.py를 통해 스마트워치로부터 제스처 데이터 녹화 및 레이블과 착용자의 기입이 가능합니다.

1-1-3. Test 폴더는 직접 스마트워치를 착용하고 녹화한 테스트용 csv가 위치합니다.

1-2. Model
1-2-1. Offline 폴더에는 각 모델 별 공개 데이터세트를 기반으로 오프라인 학습을 진행한 결과가 위치합니다.
    vox\classification\train_gesture_offline.py를 통해 학습하였습니다.
    상세 모델 폴더에는 Plot 시각화 결과가 위치하고, log_txt에는 학습 당시 프롬프트 결과창이 기입되어 있습니다.

1-2-2. Online
    3개의 Online 폴더에는 스마트워치 IMU 데이터의 전처리를 각각 Raw 그 자체로, HPF 적용 시, HPF와 LPF 모두 적용시 결과가 기입되어 있습니다.
    현재 가장 일반화가 잘 된 결과는 HPF로 판단되어, 해당 기법을 기반으로 학습 및 실시간 분류기 코드가 구성되어 있습니다. 
    즉, Raw 혹은 HPF와 LPF 모두 적용 모델을 구동하기 위해서는 코드의 수정이 필요합니다.

1-3. vox
1-3-1. classification
    분류기의 모델 구조, 오프라인 학습, 온라인 학습, 전체 모델별 비교용 코드가 위치합니다.

1-3-2. data_deploy
    사전 학습된 필터의 가중치가 위치합니다. 선행 연구의 스켈레톤 구조가 위치합니다.

1-3-3. data_types
    수신되는 데이터의 인덱스와 스켈레톤 매핑 정보가 위치치합니다.

1-3-4. estimate
    Pose estimation용 코드가 위치합니다.

1-3-5. stream
    listener에는 IMU로부터 수신받는 코드, publisher에는 외부 UDP 송신 코드가 존재합니다.



2. 구동 방법

2-1. CMD 창을 실행시킵니다.

2-2. cd ...\vox

2-3. ipconfig
    현재 스마트폰과 연산 서버가 연결된 ip의 값을 확인합니다.

2-4. 해당 ip값을 스마트폰 어플리케이션에 입력하고 주머니에 넣습니다. 
    페어링된 스마트워치에서도 wear_mocap 앱을 구동 후 "Pocket"을 선택합니다.

2-5. 정자세로 손을 90도 올리고 시계를 보는 자세를 취하면 초기 정렬이 완료되고, "stream IMU"를 눌러 스트리밍을 시작합니다.

2-6. Unity 프로그램을 실행합니다.

2-7. python C:\Capstone\vox\watch_phone_pocket_classification.py <your IP> Model\Online_with_HPF\online_gesture_cnnbilstm.pth cnnbilstm
    해당 모델과 종류는 변경 가능합니다.
    README 예제에선 가장 성능이 좋은 모델을 구동하겠습니다.

2-8. 실시간 스트리밍 중 Pose Estimation이 Unity에 곧바로 전송됩니다.

2-9. Right Shift를 꾹 누른 상태로 제스처를 행동합니다.
    --- Start Gesture Recording ---
    ...
    --- End Gesture Recording. Processing... ---

2-10. 분류된 결과가 UDP 포켓을 통해 사전 설정한 서버로 전송됩니다.

2-11. 프로그램 종료 시 엔터를 입력합니다.


3. 모델 정량 평가

3-1. 코드 구동 방법
python vox\classification\evaluate_models.py --csv Data\Test\vxo_gesture.csv --models Model\Online_with_HPF\online_gesture_bilstm.pth Model\Online_with_HPF\online_gesture_gru.pth Model\Online_with_HPF\online_gesture_simplecnn.pth Model\Online_with_HPF\online_gesture_cnnbilstm.pth Model\Online_with_HPF\online_gesture_smalltcn.pth --model-types bilstm gru simplecnn cnnbilstm smalltcn

3-2. 설명
- 모델 성능 지표
- Macro F1: 클래스별 성능을 균등하게 반영한 종합적인 분류 성능 점수 (1에 가까울수록 좋음).
- Accuracy: 전체 데이터 중 올바르게 예측한 샘플의 단순 비율.
- Loss: 모델의 예측이 정답과 얼마나 다른지를 나타내는 값 (낮을수록 좋음).

- 모델 복잡도 및 효율성 지표
- Params(M): 모델의 복잡도와 메모리 요구량을 나타내는 학습 파라미터의 총 개수 (단위: 백만).
- FLOPs(G): 모델이 1회 예측에 필요한 연산량으로, 하드웨어에 무관한 계산 비용 (단위: Giga).
- Size(MB): 학습된 모델 파일이 디스크에서 차지하는 실제 저장 공간 크기.
- Infer(ms): 샘플 1개를 예측하는 데 걸리는 실제 시간으로, 직접적인 속도 지표 (단위: 밀리초).

- 확신도 관련 지표
- Conf(V/X/Circle): 특정 클래스로 예측했을 때, 모델이 보인 평균적인 자신감(확률).
- MinCorrConf: 정답을 맞힌 예측 중 모델의 확신도가 가장 낮았던 경우의 값.
- MaxCorrConf: 정답을 맞힌 예측 중 모델의 확신도가 가장 높았던 경우의 값.