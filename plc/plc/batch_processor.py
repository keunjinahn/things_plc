"""
PLC 배치 처리기
"""
import time
import json
import csv
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

from xg5000_client import XG5000Client
from batch_config import PLCConfig, BatchJob, DATA_MAPPING, THRESHOLDS


class BatchProcessor:
    """PLC 배치 처리기"""
    
    def __init__(self, config: PLCConfig):
        """
        배치 처리기 초기화
        
        Args:
            config: PLC 연결 설정
        """
        self.config = config
        self.client = None
        self.results_history = []
        
        # 결과 저장 디렉토리 생성
        self.output_dir = Path("batch_results")
        self.output_dir.mkdir(exist_ok=True)
    
    def connect(self) -> bool:
        """PLC 연결"""
        try:
            self.client = XG5000Client(
                ip=self.config.ip,
                port=self.config.port,
                timeout=self.config.timeout
            )
            return self.client.connect()
        except Exception as e:
            print(f"PLC 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """PLC 연결 해제"""
        if self.client:
            self.client.disconnect()
    
    def execute_job(self, job: BatchJob) -> Dict[str, Any]:
        """
        단일 배치 작업 실행
        
        Args:
            job: 실행할 배치 작업
            
        Returns:
            실행 결과
        """
        if not job.enabled:
            return {"status": "skipped", "reason": "작업이 비활성화됨"}
        
        result = {
            "job_name": job.name,
            "description": job.description,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "read_results": {},
            "write_results": {},
            "errors": []
        }
        
        try:
            # 읽기 작업 실행
            if job.read_requests:
                read_results = self.client.batch_read(job.read_requests)
                result["read_results"] = read_results
                
                # 데이터 검증
                for address, value in read_results.items():
                    if value is not None:
                        self._validate_data(address, value, result)
            
            # 쓰기 작업 실행
            if job.write_requests:
                write_results = self.client.batch_write(job.write_requests)
                result["write_results"] = write_results
                
                # 실패한 쓰기 작업 확인
                failed_writes = [addr for addr, success in write_results.items() if not success]
                if failed_writes:
                    result["errors"].append(f"쓰기 실패: {failed_writes}")
                    result["status"] = "partial_failure"
            
            # 결과 히스토리에 추가
            self.results_history.append(result)
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            print(f"작업 실행 중 오류: {e}")
        
        return result
    
    def execute_all_jobs(self, jobs: List[BatchJob]) -> List[Dict[str, Any]]:
        """
        모든 배치 작업 실행
        
        Args:
            jobs: 실행할 배치 작업 리스트
            
        Returns:
            모든 작업의 실행 결과
        """
        results = []
        
        for job in jobs:
            print(f"작업 실행 중: {job.name}")
            result = self.execute_job(job)
            results.append(result)
            
            # 작업 간 딜레이
            time.sleep(self.config.retry_delay)
        
        return results
    
    def _validate_data(self, address: str, value: int, result: Dict[str, Any]):
        """
        데이터 값 검증
        
        Args:
            address: PLC 주소
            value: 읽은 값
            result: 결과 딕셔너리
        """
        if address in THRESHOLDS:
            threshold = THRESHOLDS[address]
            min_val = threshold["min"]
            max_val = threshold["max"]
            unit = threshold["unit"]
            
            if value < min_val or value > max_val:
                warning_msg = f"{address} 값이 임계값을 벗어남: {value}{unit} (범위: {min_val}-{max_val}{unit})"
                result["errors"].append(warning_msg)
                print(f"경고: {warning_msg}")
    
    def save_results_to_json(self, filename: Optional[str] = None) -> str:
        """
        결과를 JSON 파일로 저장
        
        Args:
            filename: 파일명 (None이면 자동 생성)
            
        Returns:
            저장된 파일 경로
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"batch_results_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results_history, f, ensure_ascii=False, indent=2)
        
        print(f"결과가 저장되었습니다: {filepath}")
        return str(filepath)
    
    def save_results_to_csv(self, filename: Optional[str] = None) -> str:
        """
        결과를 CSV 파일로 저장
        
        Args:
            filename: 파일명 (None이면 자동 생성)
            
        Returns:
            저장된 파일 경로
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"batch_results_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 헤더 작성
            writer.writerow([
                "작업명", "설명", "타임스탬프", "상태", 
                "읽기_주소", "읽기_값", "읽기_의미",
                "쓰기_주소", "쓰기_성공", "쓰기_의미",
                "오류"
            ])
            
            # 데이터 작성
            for result in self.results_history:
                # 읽기 결과 처리
                read_data = []
                for addr, value in result.get("read_results", {}).items():
                    meaning = DATA_MAPPING.get(addr, "알 수 없음")
                    read_data.append([addr, value, meaning])
                
                # 쓰기 결과 처리
                write_data = []
                for addr, success in result.get("write_results", {}).items():
                    meaning = DATA_MAPPING.get(addr, "알 수 없음")
                    write_data.append([addr, success, meaning])
                
                # 데이터가 없는 경우 빈 행 추가
                if not read_data and not write_data:
                    writer.writerow([
                        result["job_name"],
                        result["description"],
                        result["timestamp"],
                        result["status"],
                        "", "", "",
                        "", "", "",
                        "; ".join(result.get("errors", []))
                    ])
                else:
                    # 읽기 데이터가 있는 경우
                    for i, (read_addr, read_val, read_meaning) in enumerate(read_data):
                        write_info = write_data[i] if i < len(write_data) else ["", "", ""]
                        writer.writerow([
                            result["job_name"] if i == 0 else "",
                            result["description"] if i == 0 else "",
                            result["timestamp"] if i == 0 else "",
                            result["status"] if i == 0 else "",
                            read_addr, read_val, read_meaning,
                            write_info[0], write_info[1], write_info[2],
                            "; ".join(result.get("errors", [])) if i == 0 else ""
                        ])
                    
                    # 추가 쓰기 데이터가 있는 경우
                    for i in range(len(read_data), len(write_data)):
                        write_info = write_data[i]
                        writer.writerow([
                            "", "", "", "",
                            "", "", "",
                            write_info[0], write_info[1], write_info[2],
                            ""
                        ])
        
        print(f"결과가 CSV로 저장되었습니다: {filepath}")
        return str(filepath)
    
    def print_summary(self):
        """결과 요약 출력"""
        if not self.results_history:
            print("실행된 작업이 없습니다.")
            return
        
        print("\n=== 배치 처리 결과 요약 ===")
        print(f"총 실행 작업 수: {len(self.results_history)}")
        
        success_count = sum(1 for r in self.results_history if r["status"] == "success")
        error_count = sum(1 for r in self.results_history if r["status"] == "error")
        partial_count = sum(1 for r in self.results_history if r["status"] == "partial_failure")
        
        print(f"성공: {success_count}")
        print(f"부분 실패: {partial_count}")
        print(f"실패: {error_count}")
        
        # 오류가 있는 작업 출력
        error_jobs = [r for r in self.results_history if r["errors"]]
        if error_jobs:
            print("\n오류가 발생한 작업:")
            for job in error_jobs:
                print(f"  - {job['job_name']}: {job['errors']}")


def main():
    """메인 실행 함수"""
    from batch_config import PLC_CONFIG, BATCH_JOBS
    
    # 배치 처리기 생성
    processor = BatchProcessor(PLC_CONFIG)
    
    try:
        # PLC 연결
        if not processor.connect():
            print("PLC 연결에 실패했습니다.")
            return
        
        print("PLC 연결 성공!")
        
        # 모든 배치 작업 실행
        results = processor.execute_all_jobs(BATCH_JOBS)
        
        # 결과 요약 출력
        processor.print_summary()
        
        # 결과 저장
        processor.save_results_to_json()
        processor.save_results_to_csv()
        
    except Exception as e:
        print(f"배치 처리 중 오류: {e}")
    
    finally:
        # PLC 연결 해제
        processor.disconnect()


if __name__ == "__main__":
    main() 