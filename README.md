스마트워치 기반 제스처 인식 프로그램 Vox의 ReadME Trial입니다.

0. Setup

0-1. 기본 선행 연구는 wear_mocap을 참조하였고, 스마트워치 및 스마트폰의 어플리케이션은 해당 Github 기반 설치가 필요합니다.
https://github.com/wearable-motion-capture

0-2. 스마트워치와 스마트폰은 블루투스 페어링, 스마트폰과 연산 서버용 컴퓨터는 동일 Wifi내 연결이 되어있어야 합니다.
    Broadcasting 기반 IMU sensor Listen을 하기 때문입니다.

0-3. 웹서비스의 주소는 아래와 같습니다:
    https://voxkr.xyz/


1. 구동 방법

1-1. CMD 창을 실행시킵니다.

1-2. cd ...\vox

1-3. ipconfig
    현재 스마트폰과 연산 서버가 연결된 ip의 값을 확인합니다.

1-4. 해당 ip값을 스마트폰 어플리케이션에 입력하고 주머니에 넣습니다. 
    페어링된 스마트워치에서도 wear_mocap 앱을 구동 후 "Pocket"을 선택합니다.

1-5. 정자세로 손을 90도 올리고 시계를 보는 자세를 취하면 초기 정렬이 완료되고, "stream IMU"를 눌러 스트리밍을 시작합니다.

1-6. Unity 프로그램을 실행합니다.

1-7. python C:\Capstone\vox\watch_phone_pocket_classification.py <your IP> Model\Online_with_HPF\online_gesture_cnnbilstm.pth cnnbilstm
    해당 모델과 종류는 변경 가능합니다.
    README 예제에선 가장 성능이 좋은 모델을 구동하겠습니다.

1-8. 실시간 스트리밍 중 Pose Estimation이 Unity에 곧바로 전송됩니다.

1-9. Right Shift를 꾹 누른 상태로 제스처를 행동합니다.
    --- Start Gesture Recording ---
    ...
    --- End Gesture Recording. Processing... ---

1-10. 분류된 결과가 UDP 포켓을 통해 사전 설정한 서버로 전송됩니다.

1-11. 프로그램 종료 시 엔터를 입력합니다.


2. 모델 정량 평가

2-1. 코드 구동 방법
python vox\classification\evaluate_models.py --csv Data\Test\vxo_gesture.csv --models Model\Online_with_HPF\online_gesture_bilstm.pth Model\Online_with_HPF\online_gesture_gru.pth Model\Online_with_HPF\online_gesture_simplecnn.pth Model\Online_with_HPF\online_gesture_cnnbilstm.pth Model\Online_with_HPF\online_gesture_smalltcn.pth --model-types bilstm gru simplecnn cnnbilstm smalltcn

2-2. 설명
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


3. 제출물 폴더 구성 설명

3-0. 간단 요약
3-0-1. AI 및 Python 스크립트 (담당: 이유현)
- Data/: 학습 및 테스트에 사용된 데이터 폴더입니다.
- Offline/: 공개 데이터셋(6DMG)을 CSV로 변환한 데이터가 있습니다.
- Online/: 스마트워치로 직접 녹화한 학습용 데이터가 있습니다.
- Test/: 모델 성능 평가에 사용된 별도의 테스트 데이터가 있습니다.
- Model/: 딥러닝 모델의 학습된 가중치(.pth) 파일이 저장된 폴더입니다. 
- Online_with_HPF/ 폴더 내 모델이 최종적으로 사용된 버전입니다.
- vox/: 프로젝트의 핵심 Python 소스 코드입니다.
- classification/: 모델 구조 정의 및 학습/평가 스크립트가 있습니다.
- estimate/: 자세 추정을 위한 칼만 필터 코드가 있습니다.
- stream/: IMU 데이터 수신 및 UDP 전송 코드가 있습니다.
- watch_phone_pocket_classification.py: 실시간 분류를 위한 메인 실행 스크립트입니다.

3-0-2. Unity 시각화 및 웹 프론트엔드 (담당: 유대용)
- arm-pose-visualization-main/: Unity 기반 3D 자세 시각화 프로젝트 소스입니다.
- Assets/: C# 스크립트, 3D 모델, 씬(Scene) 등 주요 리소스를 포함합니다.
- voxUnity/: 웹에서 시각화를 표시하기 위한 WebGL 빌드 결과물이 저장되어 있습니다.
- CapstoneVOX-main/webserver/frontend/: 웹 대시보드 프론트엔드 소스입니다.
- html/, js/, css/: 소대별 상태 대시보드를 구성하는 HTML, JavaScript, CSS 파일이 각각 들어있습니다.

3-3. 백엔드 서버 및 배포 (담당: 백승호)
- src/: Spring Boot 기반 Java 백엔드 애플리케이션의 전체 소스 코드입니다.
- main/java/org/vox/capstonedesign1/:
- controller: 외부 요청을 처리하는 API 컨트롤러를 포함합니다.
- service: UDP 데이터 처리, 제스처 신호 관리 등 핵심 비즈니스 로직을 구현합니다.
- repository: 데이터베이스와 상호작용하는 JPA Repository 인터페이스를 정의합니다.
- domain: 데이터베이스 테이블과 매핑되는 JPA 엔티티를 정의합니다.
- main/resources/: 정적 웹 리소스 및 서버 설정(application.yml) 파일이 있습니다.
- test/: 단위 테스트 코드를 포함합니다.
- .github/: GitHub Actions를 이용한 CI/CD(배포 자동화) 워크플로우 설정이 있습니다.
- build.gradle: 프로젝트 의존성 및 빌드 방법을 정의하는 Gradle 설정 파일입니다.
- 실행 파일: 프로젝트 빌드 시 최종 배포용 파일은 build/libs/capstone1-1.0.jar로 생성됩니다.

[이유현]
3-1. Data 
3-1-1. Offline 폴더는 공개 데이터세트인 6DMG: ANew6DMotion Gesture Database를 포함하고 있습니다.
    기존 Matlab 기반 C++ 환경에서만 사용 가능한 mat 파일을 파이썬 코드에서 활용할 수 있도록, CSV 변환을 하였습니다.
    mat_to_csv.py를 통해 동일 과정을 사용 및 다른 레이블 및 제스처를 csv로 생성 가능합니다.

3-1-2. Online 폴더는 직접 스마트워치를 착용하고 녹화한 학습용 CSV가 위치합니다. 
    imu_record_trials.py를 통해 스마트워치로부터 제스처 데이터 녹화 및 레이블과 착용자의 기입이 가능합니다.

3-1-3. Test 폴더는 직접 스마트워치를 착용하고 녹화한 테스트용 csv가 위치합니다.


3-2. Model
3-2-1. Offline 폴더에는 각 모델 별 공개 데이터세트를 기반으로 오프라인 학습을 진행한 결과가 위치합니다.
    vox\classification\train_gesture_offline.py를 통해 학습하였습니다.
    상세 모델 폴더에는 Plot 시각화 결과가 위치하고, log_txt에는 학습 당시 프롬프트 결과창이 기입되어 있습니다.

3-2-2. Online
    3개의 Online 폴더에는 스마트워치 IMU 데이터의 전처리를 각각 Raw 그 자체로, HPF 적용 시, HPF와 LPF 모두 적용시 결과가 기입되어 있습니다.
    현재 가장 일반화가 잘 된 결과는 HPF로 판단되어, 해당 기법을 기반으로 학습 및 실시간 분류기 코드가 구성되어 있습니다. 
    즉, Raw 혹은 HPF와 LPF 모두 적용 모델을 구동하기 위해서는 코드의 수정이 필요합니다.


3-3. vox
3-3-1. classification
   분류기의 모델 구조, 오프라인 학습, 온라인 학습, 전체 모델별 비교용 코드가 위치합니다.

3-3-2. data_deploy
    사전 학습된 필터의 가중치가 위치합니다. 선행 연구의 스켈레톤 구조가 위치합니다.

3-3-3. data_types
    수신되는 데이터의 인덱스와 스켈레톤 매핑 정보가 위치합니다.

3-3-4. estimate
    Pose estimation용 칼만 필터의 코드가 위치합니다.

3-3-5. stream
    listener에는 IMU로부터 수신받는 코드, publisher에는 외부 UDP 송신 코드가 존재합니다.




[유대용]
3-4. arm-pose-visualization-main 폴더는 Unity 기반 자세 시각화 프로젝트 전체가 포함되어 있습니다.

3-4-1. Assets 폴더는 Unity 프로젝트의 주요 리소스를 포함합니다.  
    Animation/: Unity 캐릭터 애니메이션 에셋 (Idle.anim, ArmatureController 등)  
    Data/: 골격 구조 정의 파일 (Skeleton_27.xml)  
    Models/: FBX 모델 파일 (Ch20_nonPBR.fbx, Armature.fbx 등)  
    Plugins/WebGL/websocket.jslib: WebSocket 연결용 jslib 라이브러리  
    Resources/: 런타임 동적 로드 리소스 (Prefab, Texture, Material 등)  
    Scenes/: Unity Scene 파일 (MainVis.unity, VisWithCam.unity 등)  
    Scripts/: Unity C# 스크립트 (Draw, FruitGame, Listener, SkeletonMapper 등)  
    Shader/: 사용자 정의 쉐이더 파일 (JointsMcPred.shader 등)  

3-4-2. ProjectSettings 폴더는 Unity 프로젝트 설정 파일을 포함합니다. (GraphicsSettings.asset, TagManager.asset 등)  

3-4-3. Packages 폴더는 프로젝트에서 사용하는 Unity 패키지 정의 및 버전 정보를 담고 있습니다. (manifest.json 등)  

3-4-4. README.md 파일은 Unity 시각화 프로젝트 설명 문서를 제공합니다.  


3-5. arm-pose-visualization-main/voxUnity 폴더는 Unity WebGL 빌드 결과물이 저장되어 있습니다.

3-5-1. Build 폴더는 WebGL 실행을 위한 데이터 및 스크립트 파일을 포함합니다.  
    voxUnity.data: WebGL 에셋 데이터 파일  
    voxUnity.framework.js: WebGL 실행 프레임워크 JS  
    voxUnity.loader.js: WebGL 부트로더 JS  
    voxUnity.wasm: WebAssembly 실행 코드  

3-5-2. TemplateData 폴더는 WebGL 실행 정적 리소스를 포함합니다. (unity-logo-dark.png, fullscreen-button.png, style.css 등)  

3-5-3. index.html 파일은 Unity WebGL 콘텐츠 임베드용 HTML 페이지입니다.  

3-5-4. web.config 파일은 WebGL 콘텐츠 서빙 시 웹 서버 설정을 포함합니다.  


3-6. CapstoneVOX-main/webserver/frontend 폴더는 웹 시각화 및 테스트용 프론트엔드 리소스를 포함합니다.

3-6-1. css 폴더는 스타일시트를 포함합니다.  
    forunity.css: Unity WebGL 콘텐츠 스타일  
    index.css: 메인페이지 기본 스타일  
    styles.css: 공통 레이아웃·컴포넌트 스타일  

3-6-2. html 폴더는 웹 시각화용 HTML 파일을 포함합니다.  
    forunity.html: WebGL 테스트용 iframe 페이지  
    index.html: 요원 소대 선택 메인 인터페이스  
    squad1.html / squad2.html / squad3.html: 소대별 상태 대시보드  
    squad1_test.html / squad2_test.html / squad3_test.html: 테스트용 대시보드 페이지  

3-6-3. js 폴더는 자바스크립트 로직을 포함합니다.  
    forunity.js: WebGL iframe 제어 스크립트  
    scripts.js: 공통 UI 제어 및 이벤트 바인딩  
    squad1.js / squad2.js / squad3.js: 소대별 API 요청 및 렌더링 스크립트  

3-6-4. py 폴더는 Python 스크립트 및 샘플 데이터를 포함합니다.  
    motiontest.py: CSV 파싱 후 UDP 전송 테스트 스크립트  
    pose_log.csv / recorded_data.csv: 샘플 동작 예측 데이터  
    sendpose.py: 구조 단순화된 UDP 전송 스크립트  
    sendpose_websocket.py: WebSocket 형식 데이터 전송 스크립트  
    websocket_server.py: WebGL 연동용 WebSocket 서버 테스트 코드  



[백승호]
3-7. .github 폴더는 GitHub Actions 워크플로우 설정을 포함합니다.  
3-7-1. workflows 폴더는 CI/CD 파이프라인 자동화를 위한 워크플로우 정의 파일을 담고 있습니다.  
    ec2cicd.yml: EC2 배포 자동화(Continuous Deployment) 워크플로우 설정 파일입니다.  


3-8. .idea 폴더는 인텔리제이(IDE) 프로젝트 설정 파일을 포함하며, 실제 실행에 필요한 코드는 없습니다.  


3-9. capstone1 폴더는 Gradle 기반 자바 서버 프로젝트 빌드 결과물을 포함합니다.  
3-9-1. .gradle, build, gradle, tmp 폴더는 Gradle 임시 파일, 의존성 캐시 및 빌드 출력물을 저장합니다.  
3-9-2. build/libs/capstone1-1.0.jar 파일은 최종 배포용 실행 JAR 파일입니다.  
3-9-3. build/classes/java/main/org/vox/capstonedesign1/ 폴더는 컴파일된 `.class` 파일을 저장합니다.  
3-9-4. reports 폴더는 빌드 및 테스트 리포트를 보관합니다.  
3-9-5. test-results 폴더는 단위 테스트 실행 결과(리포트, 바이너리 등)를 저장합니다.  

3-10. gradle 폴더는 Gradle 래퍼(wrapper) 설정을 포함합니다.  
3-10-1. wrapper 폴더는 Gradle 래퍼 파일을 저장합니다.  
    gradle-wrapper.jar: 지정된 Gradle 버전을 자동으로 다운로드·실행하는 실행 파일입니다.  
    gradle-wrapper.properties: 래퍼 버전 및 설정 정보를 포함합니다.  


3-11. src 폴더는 애플리케이션 소스 코드 및 리소스를 포함합니다.  
3-11-1. main/java/org/vox/capstonedesign1 폴더는 핵심 애플리케이션 코드를 담고 있습니다.  
3-11-1-1. controller 패키지는 HTTP 요청 처리 컨트롤러(AgentViewController, HomeController, SquadViewController, StreamController, UnityViewController)를 포함합니다.  
3-11-1-2. domain 패키지는 JPA 엔티티(Agent, AgentSignal, Device, EstimatedStatus, Squad)를 정의합니다.  
3-11-1-3. dto 패키지는 데이터 전송 객체(AgentSignalLogResponse, AgentSignalRequest, AgentViewResponse, SquadViewResponse)를 정의합니다.  
3-11-1-4. repository 패키지는 JPA Repository 인터페이스(AgentRepository, AgentSignalRepository, DeviceRepository, EstimatedStatusRepository, SquadRepository)를 제공합니다.  
3-11-1-5. service 패키지는 비즈니스 로직(AgentService, AgentSignalService, DeviceService, SquadService, UdpReceiveService)을 구현합니다.  
3-11-1-6. util 패키지는 유틸리티 및 설정 클래스를 포함합니다.  
    calculator/ 폴더에는 FrequencyCalculator가 있습니다.  
    configuration/ 폴더에는 UdpSocketConfig 및 WebSocketConfig가 있습니다.  
    handler/ 폴더에는 AgentSignalHandler, UdpMessageHandler, UnityWebSocketHandler가 있습니다.  
    sql/ 폴더에는 ddl.sql이 있습니다.  
3-11-1-7. Main, SpringBootProjectApplication 파일은 스프링 부트 애플리케이션의 진입점입니다.  

3-11-2. main/resources 폴더는 정적 자원 및 템플릿을 포함합니다.  
    static/ 폴더에는 `css/styles.css`와 Unity WebGL 빌드 산출물(`webgl/Build*`, `TemplateData/`)이 있습니다.  
    templates/ 폴더에는 `hlsPlayer.html`, `mainPage.html`, `squadDetail.html`, `squadList.html`, `unity-view.html`, `application.yml`이 위치합니다.  

3-11-3. test 폴더는 테스트 코드 및 리소스를 포함합니다.  
    `java/org/vox/capstonedesign1/...` 경로에는 UdpReceiveServiceTest, DeviceServiceTest 등 단위 테스트 코드가 있습니다.  
    resources/mockito-extensions 폴더에는 Mockito 테스트 설정 파일이 있습니다.  
    application-test.yml 파일은 테스트 환경 전용 스프링 설정을 포함합니다.  

3-11-4. 최상위 빌드 파일은 프로젝트 루트 설정 및 환경 구성 파일을 포함합니다.  
    build.gradle, gradlew, gradlew.bat, settings.gradle: Gradle 빌드 스크립트를 정의합니다.  
    .gitignore 파일은 Git 무시 파일 패턴을 지정합니다.  
    capstone1.iml 파일은 IntelliJ 프로젝트 설정을 포함합니다.  
    README.md 파일은 프로젝트 개요 및 빌드·실행 가이드를 제공합니다.  