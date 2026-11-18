import random  # 불규칙한 패킷 발생 간격을 만들기 위한 라이브러리

# 패킷을 생성할 시간 (초)
SIM_TIME = 300.0

def generate_alarm(duration, devices=10, seed=100): # 각 장치가 평균 30초 간격으로 Alarm 패킷을 발생시키도록 구현
    # 같은 시드를 사용하면 매번 동일한 난수 순서가 생성됨
    rng = random.Random(seed)
    packets = []  # 생성된 Alarm 패킷을 저장할 리스트

    # 각 환자감시장치에서 독립적으로 Alarm 발생
    for device in range(devices):
        t = 0.0  # 현재 장치의 패킷 생성 시각

        while True:
            # 평균 30초 간격으로 불규칙하게 발생(지수 분포를 따르는 난수 생성)
            # 1/30은 초당 평균 발생 횟수
            t += rng.expovariate(1 / 30)

            # 시뮬레이션 시간이 끝나면 생성 중단
            if t >= duration:
                break

            # (생성 시각, 종류, 패킷 크기, 장치 번호)
            packets.append((t, "Alarm", 200, device))

    return packets


def generate_ecg(duration, devices=10): # 각 장치가 0.1초마다 ECG 패킷을 발생시키도록 구현
    packets = []
    interval = 0.1  # 장치당 ECG 패킷 발생 주기: 0.1초

    # 장치 한 대가 생성할 패킷 개수
    # 300초 / 0.1초 = 3,000개
    count = round(duration / interval)

    for device in range(devices):
        # 여러 장치의 전송 시작 시점을 분산 -> 여러 장치가 동시에 전송하지 않도록 함
        # 장치 0: 0.00초, 장치 1: 0.01초 ...
        offset = device * interval / devices

        for i in range(count):
            # i번째 패킷의 생성 시각 계산
            t = offset + i * interval

            # 시뮬레이션 시간 이내의 패킷만 저장
            if t < duration:
                packets.append((t, "ECG", 500, device))

    return packets


def generate_general(duration, load_mbps=1, seed=200): # 각 장치가 평균 1Mbps의 General 트래픽을 발생시키도록 구현
    rng = random.Random(seed)
    packets = []
    packet_size = 1000  # 패킷 크기: 1,000 Bytes

    # Mbps를 초당 패킷 발생 개수로 변환
    # 1Mbps라면 평균 125패킷/초
    rate = load_mbps * 1_000_000 / (packet_size * 8)

    t = 0.0

    while True:
        # 지수분포를 사용해 불규칙한 발생 간격 생성
        t += rng.expovariate(rate)

        if t >= duration:
            break

        # General은 통합 트래픽 발생원으로 설정 (장치 0)
        packets.append((t, "General", packet_size, 0))

    return packets


# 세 종류의 트래픽 생성
alarm = generate_alarm(SIM_TIME)
ecg = generate_ecg(SIM_TIME)
general = generate_general(SIM_TIME)

# 생성된 패킷을 하나로 합치고 생성 시각순으로 정렬
packets = sorted(alarm + ecg + general)

# 트래픽 종류별 패킷 개수 출력
print("Alarm:", len(alarm))
print("ECG:", len(ecg))
print("General:", len(general))

# print("\n처음 생성된 패킷 10개:")

# # 처음 10개 패킷의 정보 출력
# for t, kind, size, device in packets[:10]:
#     # .4f: 소수점 4자리, :7s: 문자열을 7칸 너비로 표시
#     print(f"{t:.4f}초 | {kind:7s} | {size} Bytes | 장치 {device}")