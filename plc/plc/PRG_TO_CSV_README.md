# XG5000 PRG to CSV 변환기

XG5000 PLC의 PRG 파일을 CSV 형식으로 변환하는 Python 프로그램입니다.

## 기능

- PRG 파일의 각 라인을 공백 기준으로 토큰 분리
- 빈 라인과 주석 라인 자동 제거
- 라인 번호 포함 (선택사항)
- 다양한 CSV 구분자 지원
- 간단한 변환 모드 지원
- **자동 인코딩 감지** (UTF-8, CP949, EUC-KR 등)
- **수동 인코딩 지정** 옵션

## 사용법

### 기본 사용법

```bash
# 기본 변환 (라인 번호 포함, 자동 인코딩 감지)
python prg_to_csv_converter.py program.prg

# 출력 파일명 지정
python prg_to_csv_converter.py program.prg output.csv

# 간단한 변환 모드 (원본 토큰 그대로)
python prg_to_csv_converter.py --simple program.prg

# 구분자 변경 (탭으로 구분)
python prg_to_csv_converter.py --delimiter=\t program.prg

# 특정 인코딩 지정 (한국어 파일의 경우)
python prg_to_csv_converter.py --encoding=cp949 program.prg
python prg_to_csv_converter.py --encoding=euc-kr program.prg
```

### 옵션

- `--simple`: 간단한 변환 모드 (라인 번호 없이 원본 토큰 그대로)
- `--delimiter=<구분자>`: CSV 구분자 지정 (기본값: 쉼표)
- `--encoding=<인코딩>`: 파일 인코딩 지정 (예: cp949, euc-kr, utf-8)

### 지원하는 인코딩

프로그램은 다음 인코딩을 자동으로 시도합니다:
- UTF-8 (기본값)
- CP949 (한국어 Windows)
- EUC-KR (한국어 Unix/Linux)
- ISO-8859-1
- Latin1
- ASCII

## 예제

### 입력 PRG 파일 (program.prg)
```
LD M100
AND M101
OUT Y000
LD M102
OR M103
OUT Y001
```

### 출력 CSV 파일 (program.csv)
```csv
Line,Token1,Token2,Token3
1,LD,M100,
2,AND,M101,
3,OUT,Y000,
4,LD,M102,
5,OR,M103,
6,OUT,Y001,
```

### 간단한 변환 모드 (--simple)
```csv
LD,M100
AND,M101
OUT,Y000
LD,M102
OR,M103
OUT,Y001
```

## 인코딩 문제 해결

### 자동 감지
프로그램이 자동으로 파일 인코딩을 감지합니다:
```bash
python prg_to_csv_converter.py online-data.prg
```

### 수동 지정
자동 감지가 실패한 경우 특정 인코딩을 지정할 수 있습니다:
```bash
# 한국어 Windows 환경
python prg_to_csv_converter.py --encoding=cp949 online-data.prg

# 한국어 Unix/Linux 환경
python prg_to_csv_converter.py --encoding=euc-kr online-data.prg
```

### 일반적인 인코딩 문제 해결
1. **CP949 오류**: `--encoding=cp949` 옵션 사용
2. **EUC-KR 오류**: `--encoding=euc-kr` 옵션 사용
3. **기타 인코딩**: 파일을 메모장 등에서 UTF-8로 저장 후 재시도

## 파일 구조

- `prg_to_csv_converter.py`: 메인 변환 프로그램
- `PRG_TO_CSV_README.md`: 이 파일

## 요구사항

- Python 3.6 이상
- 표준 라이브러리만 사용 (추가 설치 불필요)

## 주의사항

- 입력 파일은 UTF-8 인코딩을 권장합니다
- 빈 라인과 주석 라인(`//`, `;`로 시작)은 자동으로 제거됩니다
- 출력 파일이 이미 존재하면 덮어씁니다
- 인코딩 문제 발생 시 자동 감지 기능이 다양한 인코딩을 시도합니다
