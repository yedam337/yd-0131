"""서울시 주택 통계 원자료를 Streamlit 대시보드용 tidy CSV로 변환한다."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

TYPES = ["단독주택", "아파트", "연립주택", "다세대주택"]
AGE_GROUPS = ["20년~30년미만", "30년 이상"]

# 자치구 중심점(자치구 단위 원자료를 지도에서 표시하기 위한 좌표)
GU_CENTROIDS = {
    "종로구": (37.5735, 126.9790), "중구": (37.5636, 126.9979), "용산구": (37.5326, 126.9900),
    "성동구": (37.5635, 127.0370), "광진구": (37.5385, 127.0823), "동대문구": (37.5744, 127.0399),
    "중랑구": (37.6063, 127.0925), "성북구": (37.5894, 127.0167), "강북구": (37.6396, 127.0257),
    "도봉구": (37.6688, 127.0471), "노원구": (37.6542, 127.0568), "은평구": (37.6028, 126.9292),
    "서대문구": (37.5791, 126.9368), "마포구": (37.5663, 126.9019), "양천구": (37.5170, 126.8665),
    "강서구": (37.5509, 126.8495), "구로구": (37.4954, 126.8874), "금천구": (37.4519, 126.9020),
    "영등포구": (37.5264, 126.8963), "동작구": (37.5124, 126.9393), "관악구": (37.4784, 126.9516),
    "서초구": (37.4837, 127.0324), "강남구": (37.5172, 127.0473), "송파구": (37.5145, 127.1059),
    "강동구": (37.5301, 127.1238),
}


def load_sheet(path: Path) -> pd.DataFrame:
    """잘못 저장된 Excel dimension 태그를 우회해 실제 셀 범위를 읽는다."""
    return pd.read_excel(path, sheet_name="데이터", header=None, engine="openpyxl")


def find_file(raw_dir: Path, keyword: str) -> Path:
    matches = list(raw_dir.glob(f"*{keyword}*.xlsx"))
    if not matches:
        raise FileNotFoundError(f"'{keyword}'가 포함된 xlsx 파일을 {raw_dir}에서 찾지 못했습니다.")
    return matches[0]


def years_in_row(frame: pd.DataFrame, header_row: int) -> dict[int, int]:
    years = {}
    for col, value in frame.iloc[header_row].items():
        try:
            year = int(str(value).strip())
        except (TypeError, ValueError):
            continue
        if 2000 <= year <= 2100 and year not in years:
            years[year] = col
    return years


def clean_gus(frame: pd.DataFrame, name_col: int, start_row: int) -> pd.DataFrame:
    result = frame.iloc[start_row:, [name_col]].copy()
    result.columns = ["자치구"]
    result["자치구"] = result["자치구"].ffill().astype(str).str.strip()
    return result[result["자치구"].isin(GU_CENTROIDS)]


def parse_aged(aged_path: Path) -> pd.DataFrame:
    raw = load_sheet(aged_path)
    starts = years_in_row(raw, 0)
    gus = clean_gus(raw, 1, 3)
    records = []
    for year, start in starts.items():
        for age_idx, age_group in enumerate(AGE_GROUPS):
            block = start + age_idx * 6
            for type_idx, housing_type in enumerate(TYPES, start=1):
                values = raw.loc[gus.index, block + type_idx]
                for gu, value in zip(gus["자치구"], values):
                    records.append({"연도": year, "자치구": gu, "주택유형": housing_type,
                                    "경과연수": age_group, "노후주택수": int(pd.to_numeric(value, errors="coerce") or 0)})
    return pd.DataFrame(records)


def parse_supply(supply_path: Path) -> pd.DataFrame:
    raw = load_sheet(supply_path)
    starts = years_in_row(raw.iloc[:, :102], 0)  # 동 단위 부가 연도(2010/2015/2020)는 제외
    starts = {year: start for year, start in starts.items() if 2015 <= year <= 2025}
    gus = clean_gus(raw, 1, 4)
    records = []
    for year, start in starts.items():
        for gu, value in zip(gus["자치구"], raw.loc[gus.index, start]):
            records.append({"연도": year, "자치구": gu,
                            "전체주택수": int(pd.to_numeric(value, errors="coerce") or 0)})
    return pd.DataFrame(records)


def make_priority(aged: pd.DataFrame, supply: pd.DataFrame) -> pd.DataFrame:
    summary = (aged.groupby(["연도", "자치구"], as_index=False)["노후주택수"].sum()
               .merge(supply, on=["연도", "자치구"], how="left"))
    summary["노후주택비율"] = summary["노후주택수"] / summary["전체주택수"]
    # 같은 연도 내 백분위: 노후 비율↑ + 총 주택수↓ = 상대적 정비·공급 검토 우선순위
    summary["정비공급우선지수"] = summary.groupby("연도")["노후주택비율"].rank(pct=True) * 60 + \
                             (1 - summary.groupby("연도")["전체주택수"].rank(pct=True)) * 40
    summary["우선순위"] = pd.cut(summary["정비공급우선지수"], [-1, 45, 70, 101],
                                labels=["관찰", "검토", "우선 검토"])
    return summary


def main(raw_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    aged = parse_aged(find_file(raw_dir, "건축+경과연수"))
    supply = parse_supply(find_file(raw_dir, "주택종류별+주택"))
    priority = make_priority(aged, supply)
    aged.to_csv(output_dir / "aged_housing_by_gu.csv", index=False, encoding="utf-8-sig")
    supply.to_csv(output_dir / "housing_supply_by_gu.csv", index=False, encoding="utf-8-sig")
    priority.to_csv(output_dir / "renewal_supply_priority_by_gu.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([{"출처": "서울특별시 통계: 건축 경과연수별 주택현황 (DT_201004_K010008)",
                   "URL": "https://stat.eseoul.go.kr/statHtml/statHtml.do?orgId=201&tblId=DT_201004_K010008&conn_path=I3"},
                  {"출처": "서울특별시 통계: 주택종류별 주택 (DT_201004_K010006)",
                   "URL": "https://stat.eseoul.go.kr/statHtml/statHtml.do?orgId=201&tblId=DT_201004_K010006&conn_path=I3"}]).to_csv(output_dir / "sources.csv", index=False, encoding="utf-8-sig")
    print(f"완료: {len(aged):,}개 노후주택 레코드, {len(supply):,}개 공급 레코드")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    main(args.raw_dir, args.output_dir)

