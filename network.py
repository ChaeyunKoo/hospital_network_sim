import simpy

class FIFO_Network:
    def __init__(self, env, rate_mbps=10, buffer_size=100):
        self.env = env

        # 네트워크 처리율: Mbps -> bps
        self.rate = rate_mbps * 1_000_000

        # 전송 중인 패킷을 제외한 대기 공간
        self.buffer_size = buffer_size

        # FIFO 대기열
        self.queue = simpy.Store(env)

        # 전송 상태 및 통계
        self.busy = False
        self.received = []
        self.dropped = []

        # 패킷을 계속 처리하는 프로세스 시작
        env.process(self.transmit())

    def arrive(self, packet): # 패킷이 네트워크에 도착했을 때 호출됨
        # 전송 중이고 대기열까지 가득 찼다면 폐기
        if self.busy and len(self.queue.items) >= self.buffer_size:
            self.dropped.append(packet)
            return

        # 패킷을 FIFO 대기열에 추가
        self.queue.put(packet)

    def transmit(self): # 패킷을 FIFO 대기열에서 하나씩 꺼내 전송
        while True:
            # 대기열에 패킷이 들어올 때까지 기다렸다가
            # 가장 먼저 들어온 패킷 꺼내기
            packet = yield self.queue.get()

            self.busy = True

            # 패킷 크기인 packet[2](Bytes)를 전송 시간(초)으로 변환
            size_bits = packet[2] * 8
            transmission_time = size_bits / self.rate

            # 전송 시간만큼 기다린 후 패킷을 전송
            yield self.env.timeout(transmission_time)

            # 기본 경로 지연 5ms 추가
            self.env.process(self.deliver(packet))

            self.busy = False

    def deliver(self, packet): # 경로 지연 5ms 후 패킷 수신 처리
        yield self.env.timeout(0.005)

        # 생성부터 최종 수신까지 걸린 시간
        # 이때 packet[0]은 패킷 생성 시각
        delay = self.env.now - packet[0]
        self.received.append((packet[1], delay))


class QoS_Network: # 우선순위 기반 QoS 네트워크
    def __init__(self, env, rate_mbps=10, buffer_size=100):
        self.env = env
        self.rate = rate_mbps * 1_000_000
        self.buffer_size = buffer_size

        # ⭐우선순위 대기열
        # 일반적인 Store가 들어온 순서대로 항목을 꺼내는 반면,
        # PriorityStore는 우선순위가 높은(=낮은 숫자) 항목부터 꺼냄
        self.queue = simpy.PriorityStore(env)

        self.busy = False
        self.received = []
        self.dropped = []
        # 패킷이 같은 우선순위일 때 먼저 도착한 패킷부터 처리하기 위한 순서 번호
        self.sequence = 0 

        env.process(self.transmit())

    def arrive(self, packet):
        # 버퍼가 가득 차면 새 패킷 폐기
        if self.busy and len(self.queue.items) >= self.buffer_size:
            self.dropped.append(packet)
            return

        # Alarm > ECG > General
        priorities = {
            "Alarm": 0,
            "ECG": 1,
            "General": 2
        }
        # 패킷 종류(packet[1])에 맞는 우선순위를 가져옴
        priority = priorities[packet[1]]

        # 같은 우선순위라면 먼저 도착한 패킷부터 처리
        item = (priority, self.sequence, packet)
        self.sequence += 1

        self.queue.put(item)

    def transmit(self):
        while True:
            # 가장 우선순위가 높은 패킷 꺼내기
            priority, sequence, packet = yield self.queue.get()

            self.busy = True

            size_bits = packet[2] * 8
            transmission_time = size_bits / self.rate

            yield self.env.timeout(transmission_time)

            # 전송 완료 후 경로 지연 적용
            self.env.process(self.deliver(packet))

            self.busy = False

    def deliver(self, packet):
        yield self.env.timeout(0.005)

        delay = self.env.now - packet[0]
        self.received.append((packet[1], delay))