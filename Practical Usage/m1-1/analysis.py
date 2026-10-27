"""월별 패턴, 장기 추세와 연중 변동 폭을 분석하고 그래프 2개를 저장한다."""

import json
import os
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean, quantiles

from inspect_data import load_observations


ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))

import matplotlib

matplotlib.use("Agg")  # 별도 창을 띄우지 않고 이미지 파일로 저장한다.
from matplotlib import font_manager, pyplot as plt
from matplotlib import dates as mdates


def summarize(observations):
    by_month = defaultdict(list)
    by_year = defaultdict(list)
    for year, month, passengers in observations:
        by_month[month].append(passengers)
        by_year[year].append((month, passengers))

    if not by_year or any(len(values) != 12 for values in by_year.values()):
        raise ValueError("각 연도에 1~12월이 모두 있어야 비교할 수 있습니다.")
    if set(by_month) != set(range(1, 13)):
        raise ValueError("1~12월 중 빠진 달이 있습니다.")
    if any(len(values) != len(by_year) for values in by_month.values()):
        raise ValueError("달마다 비교하는 연도 수가 다릅니다.")

    # 핵심 계산: 모든 연도의 같은 달 승객 수를 모아 평균을 구한다.
    monthly = []
    for month in range(1, 13):
        values = by_month[month]
        monthly.append({
            "month": month,
            "count": len(values),
            "average_thousands": mean(values),
        })

    yearly = []
    for year, values in sorted(by_year.items()):
        low = min(value for _, value in values)
        high = max(value for _, value in values)
        yearly.append({
            "year": year,
            "lowest_months": [month for month, value in values if value == low],
            "highest_months": [month for month, value in values if value == high],
        })
    return {"unit": "thousands of passengers", "monthly": monthly, "yearly": yearly}


def save_chart(summary):
    available_fonts = {font.name for font in font_manager.fontManager.ttflist}
    korean_font = next((font for font in ("AppleGothic", "Malgun Gothic", "NanumGothic", "Noto Sans CJK KR") if font in available_fonts), None)
    if korean_font:
        plt.rcParams["font.family"] = korean_font
    plt.rcParams["axes.unicode_minus"] = False

    monthly = summary["monthly"]
    lowest = min(monthly, key=lambda row: row["average_thousands"])
    highest = max(monthly, key=lambda row: row["average_thousands"])
    years = summary["yearly"]
    period = f"{years[0]['year']}–{years[-1]['year']}"
    values = [row["average_thousands"] for row in monthly]
    colors = ["#2563EB" if row == lowest else "#D97706" if row == highest else "#BBC8D8" for row in monthly]

    fig, ax = plt.subplots(figsize=(12, 6.6), dpi=180)
    fig.patch.set_facecolor("#F8FAFC")
    ax.set_facecolor("#F8FAFC")
    bars = ax.bar(range(1, 13), values, color=colors, width=0.68, zorder=3)
    ax.bar_label(bars, labels=[f"{value:.1f}" for value in values], padding=7, fontsize=10)
    ax.set_xticks(range(1, 13), [f"{month}월" if korean_font else str(month) for month in range(1, 13)])
    ax.set_ylabel("평균 승객 수 (천 명)" if korean_font else "Average passengers (thousands)", labelpad=12)
    ax.set_ylim(0, max(values) * 1.2)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#DDE3EB", linewidth=0.8)
    ax.tick_params(axis="both", length=0, labelsize=10, pad=9)
    for spine in ax.spines.values():
        spine.set_visible(False)

    title = f"월별 평균 승객 수가 가장 적은 달은 {lowest['month']}월" if korean_font else f"Month {lowest['month']} has the lowest average passenger count"
    subtitle = f"{period} | 각 달 {len(years)}개 관측치 | 파랑: 최저 평균, 주황: 최고 평균" if korean_font else f"{period} | {len(years)} observations per month | Blue: lowest, orange: highest"
    note = "월별 총계의 12년 평균입니다. 월마다 일수가 다르며, 일평균으로 보정하지 않았습니다." if korean_font else "12-year averages of monthly passenger totals. Month lengths differ; values are not adjusted per day."
    fig.text(0.09, 0.93, title, fontsize=21, weight="normal" if korean_font else "bold", color="#17243A")
    fig.text(0.09, 0.872, subtitle, fontsize=11, color="#52637A")
    fig.text(0.09, 0.075, note, fontsize=10, color="#52637A")
    fig.text(0.09, 0.038, "Source: R AirPassengers / Rdatasets", fontsize=9, color="#64748B")
    fig.subplots_adjust(left=0.09, right=0.97, top=0.81, bottom=0.19)

    output = ROOT / "images" / "01_monthly_average.png"
    output.parent.mkdir(exist_ok=True)
    fig.savefig(output, facecolor=fig.get_facecolor())
    plt.close(fig)
    return output


def analyze_full(observations):
    values = [value for _, _, value in observations]
    series = []
    by_year = defaultdict(list)
    for index, (year, month, value) in enumerate(observations):
        by_year[year].append(value)
        series.append({
            "month": f"{year}-{month:02d}",
            "passengers_thousands": value,
            "moving_average_12": mean(values[index - 11:index + 1]) if index >= 11 else None,
        })

    annual = []
    for year, year_values in sorted(by_year.items()):
        average = mean(year_values)
        width = max(year_values) - min(year_values)
        annual.append({
            "year": year,
            "average_thousands": average,
            "minimum_thousands": min(year_values),
            "maximum_thousands": max(year_values),
            "range_thousands": width,
            "range_to_average_percent": width / average * 100,
        })

    # 이상치 후보를 찾되 자동 삭제하지 않는다. 전체 기간 기준의 한계는 리포트에 기록한다.
    q1, _, q3 = quantiles(values, n=4, method="inclusive")
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    candidates = [row for row in series if row["passengers_thousands"] < lower or row["passengers_thousands"] > upper]
    return {
        "observations": len(observations),
        "unit": "thousands of passengers",
        "moving_average_window": 12,
        "series": series,
        "annual": annual,
        "outlier_screen": {
            "method": "global 1.5 IQR; inclusive quartiles; candidates only, no automatic deletion",
            "q1": q1, "q3": q3, "iqr": iqr,
            "lower_bound": lower, "upper_bound": upper,
            "candidates": candidates,
            "removed_count": 0,
        },
        "first_to_last_year_average_change_percent": (annual[-1]["average_thousands"] / annual[0]["average_thousands"] - 1) * 100,
    }


def save_trend_chart(full):
    korean = plt.rcParams["font.family"][0] != "sans-serif"
    series = full["series"]
    dates = [date.fromisoformat(row["month"] + "-01") for row in series]
    values = [row["passengers_thousands"] for row in series]
    averages = [row["moving_average_12"] for row in series]
    fig, ax = plt.subplots(figsize=(12, 6.6), dpi=180)
    fig.patch.set_facecolor("#F8FAFC")
    ax.set_facecolor("#F8FAFC")
    ax.plot(dates, values, color="#7D96B8", linewidth=1.5, label="월별 승객 수" if korean else "Monthly passengers")
    ax.plot(dates, averages, color="#D97706", linewidth=2.8, label="12개월 이동평균" if korean else "Trailing 12-month mean")
    ax.set_ylim(0, max(values) * 1.12)
    ax.set_ylabel("승객 수 (천 명)" if korean else "Passengers (thousands)", labelpad=12)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(axis="y", color="#DDE3EB", linewidth=0.8)
    ax.tick_params(axis="both", length=0, labelsize=10, pad=9)
    ax.legend(loc="upper left", frameon=False, fontsize=11)
    for spine in ax.spines.values():
        spine.set_visible(False)
    annual = full["annual"]
    ratio = annual[-1]["average_thousands"] / annual[0]["average_thousands"]
    title = f"{annual[0]['year']}~{annual[-1]['year']}년: 연평균 승객 수 {ratio:.2f}배" if korean else f"Annual mean passenger count rose {ratio:.2f} times"
    subtitle = "매달의 출렁임과 장기 증가 흐름을 함께 비교" if korean else "Monthly changes and long-term growth"
    note = "이동평균은 해당 월을 포함한 최근 12개월 평균입니다. 처음 11개월은 계산하지 않습니다." if korean else "Trailing mean includes the current month. The first 11 months have no moving average."
    fig.text(0.09, 0.93, title, fontsize=21, color="#17243A")
    fig.text(0.09, 0.872, subtitle, fontsize=11, color="#52637A")
    fig.text(0.09, 0.075, note, fontsize=10, color="#52637A")
    fig.text(0.09, 0.038, "Source: R AirPassengers / Rdatasets", fontsize=9, color="#64748B")
    fig.subplots_adjust(left=0.09, right=0.97, top=0.81, bottom=0.19)
    output = ROOT / "images" / "02_trend_moving_average.png"
    fig.savefig(output, facecolor=fig.get_facecolor())
    plt.close(fig)
    return output


def main():
    observations = load_observations()
    summary = summarize(observations)
    image = save_chart(summary)
    evidence = ROOT / "evidence" / "02_monthly_summary.json"
    evidence.parent.mkdir(exist_ok=True)
    evidence.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    full = analyze_full(observations)
    trend_image = save_trend_chart(full)
    full_evidence = ROOT / "evidence" / "03_full_analysis.json"
    full_evidence.write_text(json.dumps(full, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("월별 평균 비교 / 단위: 천 명")
    for row in summary["monthly"]:
        print(f"{row['month']:2d}월: {row['average_thousands']:7.3f} / 관측 수: {row['count']}")
    print("\n연도별 최소 승객 수가 나타난 달 (공동 최소 포함):")
    for row in summary["yearly"]:
        print(f"{row['year']}년: {row['lowest_months']}")
    print(f"\n그래프 저장: {image.relative_to(ROOT)}")
    print(f"계산 근거 저장: {evidence.relative_to(ROOT)}")
    print(f"추세 그래프 저장: {trend_image.relative_to(ROOT)}")
    print(f"전체 분석 근거 저장: {full_evidence.relative_to(ROOT)}")
    print(f"연평균 승객 수 증가율: {full['first_to_last_year_average_change_percent']:.3f}%")
    print(f"이상치 후보: {len(full['outlier_screen']['candidates'])}개 / 삭제: 0개")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        raise SystemExit(f"분석 중단: {error}") from error
