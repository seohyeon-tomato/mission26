"""1단계: 원본을 바꾸지 않고 기간, 개수, 누락과 월 순서를 확인한다."""

import csv
import math
import sys
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parent / "data" / "AirPassengers.csv"


def load_observations(data_file=DATA_FILE):
    if sys.version_info < (3, 10):
        raise ValueError("Python 3.10 이상으로 실행하세요. 이 컴퓨터에서는 python3.12를 사용합니다.")

    with data_file.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != ["rownames", "time", "value"]:
            raise ValueError("예상한 원본 열(rownames, time, value)이 없습니다.")
        rows = list(reader)

    if len(rows) < 100:
        raise ValueError("미션에 필요한 관측치 100개가 확보되지 않았습니다.")

    missing = sum(not row.get(column, "").strip() for row in rows for column in reader.fieldnames)
    if missing:
        raise ValueError(f"빈 값 {missing}개를 발견했습니다. 처리 기준을 정한 뒤 진행하세요.")

    observations = []
    for row in rows:
        time = float(row["time"])
        value = float(row["value"])
        if not math.isfinite(time) or not math.isfinite(value) or value <= 0:
            raise ValueError("날짜 또는 승객 수에 유효하지 않은 값이 있습니다.")
        year = int(time)
        month = round((time - year) * 12) + 1
        if not 1 <= month <= 12 or not math.isclose(time, year + (month - 1) / 12, abs_tol=1e-7):
            raise ValueError("월로 해석할 수 없는 time 값이 있습니다.")
        observations.append((year, month, value))

    month_numbers = [year * 12 + month - 1 for year, month, _ in observations]
    if len(set(month_numbers)) != len(month_numbers):
        raise ValueError("같은 월이 중복되어 있습니다.")
    if month_numbers != list(range(month_numbers[0], month_numbers[-1] + 1)):
        raise ValueError("월이 빠져 있거나 날짜 순서가 잘못되어 있습니다.")

    return observations


def main():
    observations = load_observations()
    first, last = observations[0], observations[-1]
    print(f"실행 환경: Python {sys.version.split()[0]}")
    print("데이터: AirPassengers / 단위: 천 명")
    print(f"관측 수: {len(observations)}개 (한 행 = 한 달)")
    print(f"기간: {first[0]}-{first[1]:02d} ~ {last[0]}-{last[1]:02d}")
    print("빈 값: 0개 / 중복 월: 0개 / 빠진 월: 0개")
    print("승객 수: 모두 양수 / 이상치 여부는 다음 분석 단계에서 판단")
    print("\n첫 5개 관측치:")
    for year, month, value in observations[:5]:
        print(f"  {year}-{month:02d}: {value:g}천 명 = {value * 1000:,.0f}명")
    print("\n1단계 확인 완료. 다음은 분석 질문과 데이터 처리 기준을 정하는 단계입니다.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        raise SystemExit(f"점검 중단: {error}") from error
