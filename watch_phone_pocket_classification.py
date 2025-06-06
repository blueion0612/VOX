import os
from graphviz import Digraph

# --------------------------------------------------------------------------
# [중요] 한글 폰트 설정
# - Windows: 'Malgun Gothic'
# - macOS: 'AppleSDGothicNeo-Regular'
# - Linux: 'NanumGothic' (설치 필요)
# 사용 중인 OS에 맞는 폰트 이름을 KOREAN_FONT 변수에 지정하세요.
# --------------------------------------------------------------------------
KOREAN_FONT = 'Malgun Gothic'

def generate_pipeline_diagram(output_filename='pipeline_diagram_final'):
    """
    가독성을 개선하고 한글 깨짐을 수정한 파이프라인 다이어그램을 생성합니다.
    """
    # 1. 그래프 객체 생성 및 전역 스타일 설정
    g = Digraph(
        'Pipeline',
        graph_attr={
            'rankdir': 'TB',          # 방향: 위에서 아래로
            'splines': 'curved',      # 선 스타일: 부드러운 곡선
            'nodesep': '0.7',         # 노드 간 간격
            'ranksep': '1.2',         # 레벨(행) 간 간격
            'fontname': KOREAN_FONT,  # 전역 기본 폰트
            'fontsize': '16',
            'label': '실시간 포즈 추정 및 제스처 분류 파이프라인', # 전체 다이어그램 제목
            'labelloc': 't'           # 제목 위치: 상단
        }
    )
    # 노드와 엣지의 기본 스타일
    g.attr('node', style='rounded,filled', shape='box', fontname=KOREAN_FONT, fontsize='11')
    g.attr('edge', fontname=KOREAN_FONT, fontsize='10')

    # 2. 노드 정의
    # 외부 입력 및 제어
    with g.subgraph(name='cluster_input') as c:
        c.attr(style='invis') # 그룹 경계선 숨기기
        # rank='same'을 이용해 같은 라인에 노드를 배치
        with c.subgraph() as s:
            s.attr(rank='same')
            s.node('imu_source', '[스마트워치 IMU]\nUDP 패킷 수신', shape='cds', fillcolor='#D5E8D4')
            s.node('key_listener', '[사용자 입력]\nRight SHIFT 키', shape='diamond', fillcolor='#F8CECC')

    # 데이터 분배기
    g.node('broadcaster', 'Broadcaster\n(데이터 분배)', width='2.5')

    # 3. 포즈 추정 파이프라인 (파란색 그룹)
    with g.subgraph(name='cluster_pose') as c:
        c.attr(label='실시간 포즈 추정', color='#4E89AE', fontcolor='#4E89AE', style='rounded')
        c.node('kalman_q', 'kalman_q', shape='cylinder', fillcolor='#DAE8FC', width='2')
        c.node('estimator', 'WatchPhonePocketKalman\n(칼만 필터 NN)')
        c.node('msg_q', 'msg_q', shape='cylinder', fillcolor='#DAE8FC', width='2')
        c.node('publisher', 'PoseEstPublisherUDP')
        c.node('pose_out', '[실시간 관절 포즈]\nUDP 전송', shape='cds', fillcolor='#D5E8D4')
        
    # 4. 제스처 분류 파이프라인 (보라색 그룹)
    with g.subgraph(name='cluster_gesture') as c:
        c.attr(label='제스처 분류', color='#8E7CC3', fontcolor='#8E7CC3', style='rounded')
        c.node('gesture_raw_q', 'gesture_raw_q\n(임시 저장)', shape='cylinder', fillcolor='#E8DFF5', width='2')
        c.node('gesture_bundle_q', 'gesture_bundle_q\n(분류 대기)', shape='cylinder', fillcolor='#E8DFF5', width='2')
        c.node('classifier', 'GestureClassifier\n(분류 모델)')
        c.node('gesture_out', '[제스처 분류 결과]\nUDP 전송', shape='cds', fillcolor='#D5E8D4')

    # 5. 엣지(연결선) 정의
    # 입력 -> 분배기
    g.edge('imu_source', 'broadcaster', label='IMU 데이터')
    
    # 분배기 -> 각 파이프라인
    g.edge('broadcaster', 'kalman_q', label='상시 전송')
    g.edge('broadcaster', 'gesture_raw_q', label='녹화 중 전송', style='dashed')
    
    # 포즈 추정 흐름
    g.edge('kalman_q', 'estimator')
    g.edge('estimator', 'msg_q', label='Pose 메시지')
    g.edge('msg_q', 'publisher')
    g.edge('publisher', 'pose_out', label='UDP')
    
    # 제스처 분류 흐름
    g.edge('gesture_raw_q', 'gesture_bundle_q', label='Shift 해제 시 번들링')
    g.edge('gesture_bundle_q', 'classifier')
    g.edge('classifier', 'gesture_out', label='UDP')

    # 키보드 제어 흐름 (점선)
    # constraint='false'는 이 엣지가 노드 위치 계산에 영향을 주지 않도록 함
    g.edge('key_listener', 'broadcaster', label='녹화 제어', style='dashed', constraint='false')
    g.edge('key_listener', 'gesture_bundle_q', label='처리 트리거', style='dashed', constraint='false')

    # 6. 다이어그램 렌더링
    try:
        # cleanup=True는 소스 .gv 파일을 자동으로 삭제합니다.
        g.render(output_filename, view=True, format='png', cleanup=True)
        print(f"✅ 다이어그램 '{output_filename}.png'이 성공적으로 생성되었습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("Graphviz가 시스템에 설치되어 있고 PATH가 올바르게 설정되었는지,")
        print(f"그리고 '{KOREAN_FONT}' 폰트가 설치되어 있는지 확인해주세요.")

if __name__ == '__main__':
    generate_pipeline_diagram()