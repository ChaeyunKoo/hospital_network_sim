
import simpy

from traffic import (
    generate_alarm,
    generate_ecg,
    generate_general
)
from network import FIFO_Network, QoS_Network


SIM_TIME = 300.0
GENERAL_LOAD = 13  # 혼잡 조건(13Mbps)

def send_packets(env, network, packets): # 패킷을 네트워크에 도착시킴
    for packet in packets:
        # 패킷 생성 시각까지 대기
        yield env.timeout(max(0, packet[0] - env.now))

        # 네트워크에 패킷 도착
        network.arrive(packet)

def run_scenario(network_class, packets): # 시뮬레이션 환경 생성 및 패킷 전송
    env = simpy.Environment()
    network = network_class(env, rate_mbps=10)

    env.process(send_packets(env, network, packets))

    # 현재 단계에서는 테스트용 종료 시각 사용
    env.run(until=SIM_TIME + 10)

    received = len(network.received)
    dropped = len(network.dropped)

    avg_delay = (
        sum(delay for kind, delay in network.received) / received
        if received else 0
    )

    return received, dropped, avg_delay, network.received, network.dropped

def main():
    # 동일한 패킷 데이터를 두 시나리오에 사용
    alarm = generate_alarm(SIM_TIME)
    ecg = generate_ecg(SIM_TIME)
    general = generate_general(SIM_TIME, load_mbps=GENERAL_LOAD)
    
    packets = sorted(alarm + ecg + general)

    print(f"전체 생성 패킷: {len(packets)}")

    for name, network_class in [
        ("A: FIFO", FIFO_Network),
        ("B: QoS", QoS_Network)
    ]:
        received, dropped, avg_delay, received_packets, dropped_packets = run_scenario(
            network_class, packets
        )

        loss_ratio = dropped / len(packets) * 100

        print(f"\n[{name}]")
        print(f"수신 패킷: {received}")
        print(f"손실 패킷: {dropped}")
        print(f"평균 전송 지연: {avg_delay * 1000:.3f} ms")
        print(f"패킷 손실률: {loss_ratio:.2f}%")

        print("\n[트래픽별 평균 전송 지연]")

        for kind in ["Alarm", "ECG", "General"]:
            delays = [
                delay for packet_kind, delay in received_packets
                if packet_kind == kind
            ]

            if delays:
                avg = sum(delays) / len(delays)
                print(f"{kind}: {avg * 1000:.3f} ms")
            else:
                print(f"{kind}: 수신 패킷 없음")
        
        print("\n[트래픽별 패킷 손실률]")

        for kind in ["Alarm", "ECG", "General"]:
            # 해당 종류의 전체 생성 패킷 수
            generated_count = sum(
                1 for packet in packets if packet[1] == kind
            )

            # 해당 종류의 손실 패킷 수
            dropped_count = sum(
                1 for packet in dropped_packets if packet[1] == kind
            )

            # 손실률 = 손실 패킷 수 / 생성 패킷 수 × 100
            loss_ratio = (
                dropped_count / generated_count * 100
                if generated_count > 0 else 0
            )

            print(
                f"{kind}: {dropped_count}/{generated_count}개 손실 "
                f"({loss_ratio:.2f}%)"
            )


if __name__ == "__main__":
    main()