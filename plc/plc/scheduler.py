"""
PLC 배치 작업 스케줄러
"""
import time
import threading
import schedule
from datetime import datetime, timedelta
from typing import Optional, Callable
import signal
import sys

from batch_processor import BatchProcessor
from batch_config import PLC_CONFIG, BATCH_JOBS


class BatchScheduler:
    """PLC 배치 작업 스케줄러"""
    
    def __init__(self, config: PLC_CONFIG, jobs: list = None):
        """
        스케줄러 초기화
        
        Args:
            config: PLC 연결 설정
            jobs: 실행할 배치 작업 리스트 (None이면 기본 작업 사용)
        """
        self.config = config
        self.jobs = jobs or BATCH_JOBS
        self.processor = None
        self.running = False
        self.scheduler_thread = None
        
        # 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        print(f"\n시그널 {signum} 수신. 스케줄러를 종료합니다...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """스케줄러 시작"""
        if self.running:
            print("스케줄러가 이미 실행 중입니다.")
            return
        
        self.running = True
        print("배치 스케줄러를 시작합니다...")
        
        # 스케줄러 스레드 시작
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        # 메인 루프
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n사용자에 의해 중단되었습니다.")
            self.stop()
    
    def stop(self):
        """스케줄러 중지"""
        if not self.running:
            return
        
        self.running = False
        print("스케줄러를 중지합니다...")
        
        if self.processor:
            self.processor.disconnect()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
    
    def _run_scheduler(self):
        """스케줄러 실행 (별도 스레드)"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                print(f"스케줄러 실행 중 오류: {e}")
                time.sleep(5)
    
    def add_job(self, job_func: Callable, interval: str, job_name: str = None):
        """
        작업 추가
        
        Args:
            job_func: 실행할 함수
            interval: 실행 간격 (예: "1.minutes", "30.seconds", "1.hours")
            job_name: 작업 이름
        """
        if interval.endswith('.seconds'):
            seconds = int(interval.split('.')[0])
            schedule.every(seconds).seconds.do(job_func).tag(job_name or 'default')
        elif interval.endswith('.minutes'):
            minutes = int(interval.split('.')[0])
            schedule.every(minutes).minutes.do(job_func).tag(job_name or 'default')
        elif interval.endswith('.hours'):
            hours = int(interval.split('.')[0])
            schedule.every(hours).hours.do(job_func).tag(job_name or 'default')
        elif interval.endswith('.days'):
            days = int(interval.split('.')[0])
            schedule.every(days).days.do(job_func).tag(job_name or 'default')
        else:
            raise ValueError(f"지원하지 않는 간격 형식: {interval}")
        
        print(f"작업이 추가되었습니다: {job_name or 'default'} - {interval}")
    
    def remove_job(self, job_name: str):
        """작업 제거"""
        schedule.clear(job_name)
        print(f"작업이 제거되었습니다: {job_name}")
    
    def list_jobs(self):
        """등록된 작업 목록 출력"""
        jobs = schedule.get_jobs()
        if not jobs:
            print("등록된 작업이 없습니다.")
            return
        
        print("\n=== 등록된 작업 목록 ===")
        for job in jobs:
            print(f"작업: {job.job_func.__name__}")
            print(f"다음 실행: {job.next_run}")
            print(f"간격: {job.interval}")
            print(f"태그: {job.tags}")
            print("-" * 30)
    
    def execute_batch_jobs(self):
        """배치 작업 실행"""
        try:
            # 배치 처리기 생성 및 연결
            self.processor = BatchProcessor(self.config)
            
            if not self.processor.connect():
                print("PLC 연결에 실패했습니다.")
                return
            
            print(f"\n[{datetime.now()}] 배치 작업 실행 시작")
            
            # 모든 배치 작업 실행
            results = self.processor.execute_all_jobs(self.jobs)
            
            # 결과 요약 출력
            self.processor.print_summary()
            
            # 결과 저장
            self.processor.save_results_to_json()
            self.processor.save_results_to_csv()
            
            print(f"[{datetime.now()}] 배치 작업 실행 완료")
            
        except Exception as e:
            print(f"배치 작업 실행 중 오류: {e}")
        
        finally:
            # 연결 해제
            if self.processor:
                self.processor.disconnect()
                self.processor = None


def create_scheduler_with_default_jobs():
    """기본 작업이 포함된 스케줄러 생성"""
    scheduler = BatchScheduler(PLC_CONFIG)
    
    # 기본 작업 추가
    scheduler.add_job(
        scheduler.execute_batch_jobs,
        "5.minutes",
        "plc_batch_job"
    )
    
    return scheduler


def main():
    """메인 실행 함수"""
    print("PLC 배치 스케줄러를 시작합니다...")
    
    # 스케줄러 생성
    scheduler = create_scheduler_with_default_jobs()
    
    # 등록된 작업 목록 출력
    scheduler.list_jobs()
    
    try:
        # 스케줄러 시작
        scheduler.start()
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
    finally:
        scheduler.stop()
        print("스케줄러가 종료되었습니다.")


if __name__ == "__main__":
    main() 