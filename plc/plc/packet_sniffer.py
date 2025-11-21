#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCP 패킷 스니핑 프로그램 (Scapy 기반)
192.168.1.19의 모든 포트로의 TCP 통신을 모니터링
"""

import time
import datetime
from typing import Optional
import argparse
import sys

try:
    from scapy.all import sniff, IP, TCP
    print("✅ Scapy 모듈 로드 성공")
except ImportError:
    print("❌ Scapy 모듈이 설치되지 않았습니다.")
    print("설치 방법: pip install scapy")
    sys.exit(1)

class TCPSniffer:
    """TCP 패킷 스니핑 클래스 (Scapy 기반)"""
    
    def __init__(self, target_ip: str = "192.168.1.19", target_port: Optional[int] = None):
        """
        TCP 스니퍼 초기화
        
        Args:
            target_ip: 모니터링할 대상 IP 주소
            target_port: 모니터링할 대상 포트 (None이면 모든 포트)
        """
        self.target_ip = target_ip
        self.target_port = target_port
        self.packet_count = 0
        
        # 전송/수신 통계
        self.sent_count = 0
        self.received_count = 0
        self.other_count = 0
        
        print(f"=== TCP 패킷 스니퍼 시작 (Scapy 기반) ===")
        print(f"대상 IP: {target_ip}")
        if target_port:
            print(f"대상 포트: {target_port}")
        else:
            print(f"대상 포트: 모든 포트")
        print(f"시작 시간: {datetime.datetime.now()}")
        print("=" * 50)
        if target_port:
            print(f"📡 {target_ip}:{target_port}만 대상으로 필터링")
        else:
            print(f"📡 {target_ip}의 모든 포트 대상으로 필터링")
        print("=" * 50)
    
    def show_packet(self, packet):
        """패킷 표시 함수 (Scapy sniff의 prn 콜백)"""
        try:
            # IP와 TCP 레이어 확인
            if IP in packet and TCP in packet:
                ip_layer = packet[IP]
                tcp_layer = packet[TCP]
                
                source_ip = ip_layer.src
                dest_ip = ip_layer.dst
                source_port = tcp_layer.sport
                dest_port = tcp_layer.dport
                
                # 192.168.1.19의 모든 포트 대상으로 필터링
                if not self._is_target_packet(source_ip, dest_ip, source_port, dest_port):
                    return
                
                # 패킷 카운트 증가
                self.packet_count += 1
                timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                # 방향 판단
                direction = self._determine_direction(source_ip, dest_ip, source_port, dest_port)
                
                # TCP 플래그 해석
                flags = tcp_layer.flags
                flag_names = self._parse_tcp_flags(flags)
                flags_str = ",".join(flag_names) if flag_names else "NONE"
                
                # 데이터 길이 계산
                data_length = len(tcp_layer.payload) if tcp_layer.payload else 0
                
                # 패킷 정보 출력
                print(f"[{timestamp}] 패킷 #{self.packet_count} {direction}")
                print(f"  방향: {source_ip}:{source_port} → {dest_ip}:{dest_port}")
                print(f"  크기: {len(packet)} bytes (Data: {data_length})")
                print(f"  플래그: {flags_str}")
                
                # 데이터가 있는 경우 출력
                if data_length > 0:
                    data = bytes(tcp_layer.payload)
                    print(f"  데이터: {data.hex()}")
                    if data_length > 64:
                        print(f"         ... (총 {data_length} bytes)")
                else:
                    print(f"  데이터: 없음 (헤더만)")
                
                print("-" * 50)
                
        except Exception as e:
            print(f"❌ 패킷 표시 오류: {e}")
    
    def _is_target_packet(self, source_ip: str, dest_ip: str, source_port: int, dest_port: int) -> bool:
        """대상 패킷인지 확인 (192.168.1.19의 모든 포트)"""
        target_ip = "192.168.1.19"
        
        # 포트가 지정된 경우: 해당 IP:포트와 일치하는지 확인
        if self.target_port:
            return (
                (source_ip == target_ip and source_port == self.target_port) or
                (dest_ip == target_ip and dest_port == self.target_port)
            )
        # 포트가 지정되지 않은 경우: 해당 IP의 모든 포트와 일치하는지 확인
        else:
            return (
                source_ip == target_ip or dest_ip == target_ip
            )
    
    def _determine_direction(self, source_ip: str, dest_ip: str, source_port: int, dest_port: int) -> str:
        """패킷 방향 판단 (192.168.1.19 대상)"""
        target_ip = "192.168.1.19"
        
        # 방향 판단 및 통계 업데이트
        if source_ip == target_ip:
            self.received_count += 1
            if self.target_port:
                return f"📥 수신 (PLC:{self.target_port} → 로컬)"
            else:
                return f"📥 수신 (PLC:{source_port} → 로컬)"
        elif dest_ip == target_ip:
            self.sent_count += 1
            if self.target_port:
                return f"📤 전송 (로컬 → PLC:{self.target_port})"
            else:
                return f"📤 전송 (로컬 → PLC:{dest_port})"
        else:
            self.other_count += 1
            return "🔄 기타 통신"
    
    def _parse_tcp_flags(self, flags: int) -> list:
        """TCP 플래그 해석"""
        flag_names = []
        if flags & 0x01:  # FIN
            flag_names.append("FIN")
        if flags & 0x02:  # SYN
            flag_names.append("SYN")
        if flags & 0x04:  # RST
            flag_names.append("RST")
        if flags & 0x08:  # PSH
            flag_names.append("PSH")
        if flags & 0x10:  # ACK
            flag_names.append("ACK")
        if flags & 0x20:  # URG
            flag_names.append("URG")
        return flag_names
    
    def start_sniffing(self, duration: Optional[int] = None, iface: Optional[str] = None):
        """패킷 스니핑 시작 (Scapy sniff 사용)"""
        if self.target_port:
            print(f"🔍 {self.target_ip}:{self.target_port} TCP 패킷 스니핑 시작...")
        else:
            print(f"🔍 {self.target_ip}의 모든 포트 TCP 패킷 스니핑 시작...")
        print("Ctrl+C로 중지하거나 지정된 시간 후 자동 종료")
        
        # 필터 문자열 생성
        if self.target_port:
            filter_str = f"tcp and host {self.target_ip}"
        else:
            filter_str = f"tcp and host {self.target_ip}"
        print(f"📡 필터: {filter_str}")
        
        if iface:
            print(f"🌐 네트워크 인터페이스: {iface}")
        
        try:
            # Scapy sniff 함수 사용
            if duration:
                print(f"⏰ {duration}초 동안 스니핑...")
                sniff(
                    iface=iface,
                    filter=filter_str,
                    prn=self.show_packet,
                    count=0,
                    timeout=duration
                )
            else:
                print("♾️ 무제한 스니핑 (Ctrl+C로 중지)")
                sniff(
                    iface=iface,
                    filter=filter_str,
                    prn=self.show_packet,
                    count=0
                )
                
        except KeyboardInterrupt:
            print("\n⏹️ 사용자에 의해 중지됨")
        except Exception as e:
            print(f"❌ 스니핑 중 오류 발생: {e}")
        finally:
            self.stop_sniffing()
    
    def stop_sniffing(self):
        """스니핑 중지 및 결과 요약"""
        print(f"\n📊 스니핑 결과 요약")
        print(f"총 캡처된 패킷: {self.packet_count}개")
        print(f"📤 전송 패킷: {self.sent_count}개")
        print(f"📥 수신 패킷: {self.received_count}개")
        print(f"🔄 기타 패킷: {self.other_count}개")
        print(f"종료 시간: {datetime.datetime.now()}")
        print("=" * 50)

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="TCP 패킷 스니퍼 (Scapy 기반 - 192.168.1.19의 모든 포트 대상)")
    parser.add_argument("--ip", default="192.168.1.19", help="대상 IP 주소 (기본값: 192.168.1.19)")
    parser.add_argument("--port", type=int, help="대상 포트 (지정하지 않으면 모든 포트)")
    parser.add_argument("--duration", type=int, help="스니핑 지속 시간 (초)")
    parser.add_argument("--iface", help="네트워크 인터페이스 (예: 'Realtek PCIe GbE Family Controller')")
    
    args = parser.parse_args()
    
    # 스니퍼 생성
    sniffer = TCPSniffer(args.ip, args.port)
    
    try:
        # 스니핑 시작
        sniffer.start_sniffing(args.duration, args.iface)
    except Exception as e:
        print(f"❌ 스니핑 중 오류 발생: {e}")
    finally:
        sniffer.stop_sniffing()

if __name__ == "__main__":
    main()
