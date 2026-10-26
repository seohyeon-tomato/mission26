"""공개 CSV를 한 번 내려받는다. API 키와 외부 라이브러리가 필요 없다."""

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


SOURCE_URL = (
    "https://raw.githubusercontent.com/vincentarelbundock/"
    "Rdatasets/master/csv/datasets/AirPassengers.csv"
)
DATA_DIR = Path(__file__).resolve().parent / "data"


def main():
    with urlopen(SOURCE_URL, timeout=30) as response:
        content = response.read()

    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    rows = list(reader)
    if reader.fieldnames != ["rownames", "time", "value"] or len(rows) != 144:
        raise ValueError("배포 파일의 열 또는 행 수가 바뀌었습니다. 원본 출처를 확인하세요.")

    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "AirPassengers.csv").write_bytes(content)
    metadata = {
        "dataset": "AirPassengers",
        "source_url": SOURCE_URL,
        "documentation_url": (
            "https://stat.ethz.ch/R-manual/R-devel/"
            "library/datasets/html/AirPassengers.html"
        ),
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "rows": len(rows),
        "unit": "thousands of passengers",
    }
    (DATA_DIR / "source.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"다운로드 완료: {len(rows)}개 관측치")
    print("저장 위치: data/AirPassengers.csv")


if __name__ == "__main__":
    try:
        main()
    except (URLError, TimeoutError, OSError, ValueError) as error:
        raise SystemExit(f"수집 중단: {error}") from error
