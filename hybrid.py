from network import FIFO_Network, QoS_Network

class Hybrid_Network:
    def __init__(self, env, use_qos=False):
        self.env = env

        # 5G 경로: Alarm과 ECG 전송
        if use_qos:
            self.critical = QoS_Network(env, rate_mbps=10)
        else:
            self.critical = FIFO_Network(env, rate_mbps=10)

        # Wi-Fi 경로: General 전송
        self.general = FIFO_Network(env, rate_mbps=10)

    def arrive(self, packet): # 패킷 도착 시 처리
        # 패킷 종류(packet[1])에 따라 전송 경로 선택
        kind = packet[1]

        if kind in ("Alarm", "ECG"):
            self.critical.arrive(packet)

        elif kind == "General":
            self.general.arrive(packet)

        else:
            raise ValueError(f"알 수 없는 패킷 종류: {kind}")

    @property
    def received(self): # 수신 패킷 목록 반환
        # 두 경로의 수신 결과 합치기
        return self.critical.received + self.general.received

    @property
    def dropped(self): # 손실 패킷 목록 반환
        # 두 경로의 손실 결과 합치기
        return self.critical.dropped + self.general.dropped