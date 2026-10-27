# 데이터 출처와 수집 방법

- 데이터명: AirPassengers
- 의미: 국제 항공 승객 수의 월별 총계
- 기간: 1949년 1월~1960년 12월
- 관측 수: 144개
- 단위: 천 명. `value=112`는 112,000명
- 공식 설명: <https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/AirPassengers.html>
- CSV 배포: <https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master/csv/datasets/AirPassengers.csv>
- 배포 프로젝트: <https://github.com/vincentarelbundock/Rdatasets>
- 배포자의 이용 조건 설명: <https://github.com/vincentarelbundock/Rdatasets#license>
- 출처 확인일: 2026-10-26

공식 R 문서는 출처로 Box, Jenkins, Reinsel의 *Time Series Analysis: Forecasting and Control*, 3판(1994)을 제시한다.

## 원본 열

| 열 | 뜻 | 분석에서 사용 |
| --- | --- | --- |
| `rownames` | 원본 관측치의 행 번호 | 참고 |
| `time` | 소수 연도로 표현한 월 | 연·월 확인 |
| `value` | 월별 승객 수, 천 명 | 분석 대상 |

원본 CSV를 수정하지 않는다. `time`의 정수 부분은 연도이고 소수 부분에 12를 곱한 뒤 반올림하고 1을 더하면 월이 된다. 예: `1949.08333333333`은 1949년 2월이다.

## 수집과 재현

프로젝트의 `download_data.py`를 실행하면 CSV를 한 번 내려받아 이 폴더에 저장한다.
수집 시각, 다운로드 주소, 파일의 SHA-256 체크섬은 `source.json`에 저장한다. 체크섬은 이후 받은 파일이 같은 원본인지 비교하는 값이다.
`inspect_data.py`는 로컬 CSV만 읽으며 인터넷을 사용하지 않는다.

원본 파일의 열과 행 수가 예상과 다르면 저장을 중단한다. 배포 URL은 변경될 수 있으므로 오류가 나면 출처 페이지를 확인한다.

## 이용 조건과 한계

Rdatasets는 저장소 코드에 GPL-3를 적용하지만, 실제 데이터 각각의 라이선스가 명확히 확인되지 않았다고 설명한다. 데이터가 GPL-3, CC0 또는 퍼블릭 도메인이라고 단정하지 않는다.

출처를 명시해 학습 목적으로 분석하며, 공개 저장소에는 원본 CSV 대신 수집 코드와 출처를 제공한다. 원본 재배포·상업적 이용 전에는 이용 조건을 별도로 확인한다. `.gitignore`에 로컬 원본 CSV를 제외했다.

공식 설명은 조사 지역·항공사 범위를 자세히 제공하지 않는다. 데이터를 ‘전 세계 전체 항공 승객 수’로 확대해 표현하지 않는다. 과거 자료이므로 현재 항공 수요에 대한 결론으로 일반화하지 않는다.
