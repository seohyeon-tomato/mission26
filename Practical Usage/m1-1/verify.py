"""원본 재계산과 별도 임시 폴더 재실행으로 제출 결과를 확인한다."""

import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent


def close(actual, expected):
    if not math.isclose(actual, float(expected), rel_tol=1e-10, abs_tol=1e-10):
        raise ValueError(f"계산 대조 실패: {actual} != {expected}")


def main():
    checks = []
    raw = (ROOT / "data/AirPassengers.csv").read_bytes()
    source = json.loads((ROOT / "data/source.json").read_text())
    if hashlib.sha256(raw).hexdigest() != source["sha256"]:
        raise ValueError("원본 파일이 수집 당시와 다릅니다.")
    rows = list(csv.DictReader(raw.decode().splitlines()))
    if len(rows) != 144:
        raise ValueError("원본 관측 수가 144개가 아닙니다.")
    values = [Decimal(row["value"]) for row in rows]
    checks.append("원본 144개와 수집 당시 체크섬 일치")

    monthly = json.loads((ROOT / "evidence/02_monthly_summary.json").read_text())
    full = json.loads((ROOT / "evidence/03_full_analysis.json").read_text())
    grouped = defaultdict(list)
    for index, value in enumerate(values):
        grouped[index % 12 + 1].append(value)
    for row in monthly["monthly"]:
        group = grouped[row["month"]]
        if row["count"] != len(group) or len(group) != 12:
            raise ValueError("월별 관측 수가 다릅니다.")
        close(row["average_thousands"], sum(group) / len(group))
    checks.append("월별 평균 12개를 원본의 Decimal 계산과 독립 대조")

    if len(full["series"]) != 144:
        raise ValueError("시계열 결과 길이가 다릅니다.")
    for index, row in enumerate(full["series"]):
        if index < 11:
            if row["moving_average_12"] is not None:
                raise ValueError("처음 11개월은 이동평균을 비워야 합니다.")
        else:
            close(row["moving_average_12"], sum(values[index - 11:index + 1]) / 12)
    checks.append("12개월 이동평균 133개와 시작 11개월 공백 대조")

    for index, row in enumerate(full["annual"]):
        year_values = values[index * 12:(index + 1) * 12]
        average = sum(year_values) / 12
        width = max(year_values) - min(year_values)
        close(row["average_thousands"], average)
        close(row["range_thousands"], width)
        close(row["range_to_average_percent"], width / average * 100)
    close(full["first_to_last_year_average_change_percent"], (sum(values[-12:]) / sum(values[:12]) - 1) * 100)
    checks.append("연도별 평균·변동 폭·상대 변동 폭과 전체 증가율 대조")

    screen = full["outlier_screen"]
    for key, expected in {"q1": 180, "q3": 360.5, "iqr": 180.5, "lower_bound": -90.75, "upper_bound": 631.25}.items():
        close(screen[key], expected)
    if screen["candidates"] or screen["removed_count"]:
        raise ValueError("이 자료의 이상치 후보와 삭제 수는 0이어야 합니다.")
    low = Counter(month for row in monthly["yearly"] for month in row["lowest_months"])
    if low != Counter({11: 6, 2: 4, 1: 2}) or monthly["yearly"][0]["highest_months"] != [7, 8]:
        raise ValueError("연도별 최저 월 또는 공동 최고 월 결과가 다릅니다.")
    checks.append("이상치 경계·보존 정책·연도별 극값과 공동 최고 월 확인")

    with tempfile.TemporaryDirectory(prefix="m1-1-reproduce-") as directory:
        clean = Path(directory)
        (clean / "data").mkdir()
        for name in ("analysis.py", "inspect_data.py"):
            shutil.copy2(ROOT / name, clean / name)
        shutil.copy2(ROOT / "data/AirPassengers.csv", clean / "data/AirPassengers.csv")
        subprocess.run([sys.executable, str(clean / "analysis.py")], cwd=clean, check=True, capture_output=True, text=True)
        for name in ("02_monthly_summary.json", "03_full_analysis.json"):
            if json.loads((clean / "evidence" / name).read_text()) != json.loads((ROOT / "evidence" / name).read_text()):
                raise ValueError("별도 폴더에서 분석 결과가 달라졌습니다.")
        for name in ("01_monthly_average.png", "02_trend_moving_average.png"):
            for base in (ROOT, clean):
                with Image.open(base / "images" / name) as image:
                    if image.size != (2160, 1188):
                        raise ValueError("이미지 크기가 다릅니다.")
                    image.verify()
    checks.append("별도 임시 폴더에서 두 JSON 결과 일치, 그래프 2개 재생성·PNG 확인")

    links = 0
    for path in (ROOT / "README.md", ROOT / "REPORT.md", ROOT / "data/README.md"):
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
            if "://" not in link:
                target = (path.parent / link.split("#")[0]).resolve()
                own_evidence = ROOT / "evidence/03_final_verification.txt"
                if not target.exists() and target != own_evidence:
                    raise ValueError(f"문서 링크가 없습니다: {path.name}: {link}")
                links += 1
    checks.append(f"문서의 로컬 링크 {links}개 확인")
    text = "실행 환경: Python " + sys.version.split()[0] + "\n" + "\n".join("통과: " + check for check in checks) + "\n"
    (ROOT / "evidence/03_final_verification.txt").write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
