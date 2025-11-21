"""
PLC 통신 및 배치 처리 사용 예제
"""
from xg5000_client import XG5000Client, PLCAddress, DataType, Command, BatchRequest
from batch_processor import BatchProcessor
from batch_config import PLC_CONFIG, BATCH_JOBS


def example_basic_communication():
    """기본 PLC 통신 예제"""
    print("=== 기본 PLC 통신 예제 ===")
    
    try:
        with XG5000Client("192.168.1.2", 2004) as plc:
            # 단일 데이터 읽기
            value = plc.read(PLCAddress("D", 4001), DataType.WORD)
            print(f"D4001 읽기 결과: {value}")
            
            # 단일 데이터 쓰기
            success = plc.write(PLCAddress("D", 5001), 12345, DataType.WORD)
            print(f"D5001 쓰기 결과: {success}")
            
    except Exception as e:
        print(f"통신 오류: {e}")


def example_batch_communication():
    """배치 통신 예제"""
    print("\n=== 배치 통신 예제 ===")
    
    try:
        with XG5000Client("192.168.1.2", 2004) as plc:
            # 배치 읽기 요청
            read_requests = [
                BatchRequest(
                    address=PLCAddress("D", 4001),
                    data_type=DataType.WORD,
                    command=Command.READ
                ),
                BatchRequest(
                    address=PLCAddress("D", 4002),
                    data_type=DataType.WORD,
                    command=Command.READ
                ),
                BatchRequest(
                    address=PLCAddress("M", 100),
                    data_type=DataType.BIT,
                    command=Command.READ
                )
            ]
            
            # 배치 읽기 실행
            read_results = plc.batch_read(read_requests)
            print("배치 읽기 결과:")
            for address, value in read_results.items():
                print(f"  {address}: {value}")
            
            # 배치 쓰기 요청
            write_requests = [
                BatchRequest(
                    address=PLCAddress("D", 5001),
                    data_type=DataType.WORD,
                    command=Command.WRITE,
                    value=100
                ),
                BatchRequest(
                    address=PLCAddress("M", 200),
                    data_type=DataType.BIT,
                    command=Command.WRITE,
                    value=1
                )
            ]
            
            # 배치 쓰기 실행
            write_results = plc.batch_write(write_requests)
            print("배치 쓰기 결과:")
            for address, success in write_results.items():
                status = "성공" if success else "실패"
                print(f"  {address}: {status}")
                
    except Exception as e:
        print(f"배치 통신 오류: {e}")


def example_batch_processor():
    """배치 처리기 예제"""
    print("\n=== 배치 처리기 예제 ===")
    
    try:
        # 배치 처리기 생성
        processor = BatchProcessor(PLC_CONFIG)
        
        # PLC 연결
        if processor.connect():
            print("PLC 연결 성공!")
            
            # 모든 배치 작업 실행
            results = processor.execute_all_jobs(BATCH_JOBS)
            
            # 결과 요약 출력
            processor.print_summary()
            
            # 결과 저장
            processor.save_results_to_json("example_results.json")
            processor.save_results_to_csv("example_results.csv")
            
            # 연결 해제
            processor.disconnect()
        else:
            print("PLC 연결 실패!")
            
    except Exception as e:
        print(f"배치 처리기 오류: {e}")


def example_custom_job():
    """사용자 정의 배치 작업 예제"""
    print("\n=== 사용자 정의 배치 작업 예제 ===")
    
    from batch_config import BatchJob
    
    # 사용자 정의 배치 작업 생성
    custom_job = BatchJob(
        name="사용자_정의_작업",
        description="사용자가 정의한 배치 작업",
        read_requests=[
            BatchRequest(
                address=PLCAddress("D", 4001),
                data_type=DataType.WORD,
                command=Command.READ
            ),
            BatchRequest(
                address=PLCAddress("M", 100),
                data_type=DataType.BIT,
                command=Command.READ
            )
        ],
        write_requests=[
            BatchRequest(
                address=PLCAddress("D", 5001),
                data_type=DataType.WORD,
                command=Command.WRITE,
                value=200
            )
        ]
    )
    
    try:
        # 배치 처리기 생성
        processor = BatchProcessor(PLC_CONFIG)
        
        # PLC 연결
        if processor.connect():
            print("PLC 연결 성공!")
            
            # 사용자 정의 작업 실행
            result = processor.execute_job(custom_job)
            
            print(f"작업 상태: {result['status']}")
            print(f"읽기 결과: {result['read_results']}")
            print(f"쓰기 결과: {result['write_results']}")
            
            if result['errors']:
                print(f"오류: {result['errors']}")
            
            # 연결 해제
            processor.disconnect()
        else:
            print("PLC 연결 실패!")
            
    except Exception as e:
        print(f"사용자 정의 작업 오류: {e}")


def main():
    """메인 실행 함수"""
    print("PLC 통신 및 배치 처리 예제를 실행합니다...")
    print("주의: 실제 PLC가 연결되어 있어야 합니다.")
    print()
    
    # 예제 실행
    example_basic_communication()
    example_batch_communication()
    example_batch_processor()
    example_custom_job()
    
    print("\n모든 예제가 완료되었습니다.")


if __name__ == "__main__":
    main() 