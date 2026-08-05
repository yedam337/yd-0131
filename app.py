import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="서울시 행정동별 출동건수", layout="wide")

CITY_HALL = {"lat": 37.5663, "lon": 126.9779}


def find_data_file() -> Path:
    """Streamlit Cloud와 로컬 모두에서 데이터 파일을 찾는다."""
    app_dir = Path(__file__).resolve().parent
    candidates = [
        app_dir / "dong_emergency_count.geojson",  # GitHub 저장소 최상단 권장
        app_dir / "data" / "dong_emergency_count.geojson",  # 이전 폴더 구조 지원
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    st.error(
        "`dong_emergency_count.geojson` 파일을 찾을 수 없습니다. "
        "GitHub 저장소의 app.py와 같은 위치에 파일을 올려 주세요."
    )
    st.stop()


@st.cache_data
def load_geojson(path: Path) -> dict:
    """GeoJSON과 행정동 속성 데이터를 한 번만 불러온다."""
    with path.open(encoding="utf-8") as file:
        return json.load(file)


geojson = load_geojson(find_data_file())
records = pd.DataFrame(feature["properties"] for feature in geojson["features"])
records["emergency_count"] = pd.to_numeric(records["emergency_count"])

st.title("서울시 행정동별 출동건수")
st.caption("행정동을 가리키면 행정동명과 행정동 코드를 확인할 수 있습니다.")

show_mokdong_only = st.toggle("목동만 보기", value=False)

# '목1동'부터 '목5동'까지를 정확히 선택해 '면목동'을 제외한다.
if show_mokdong_only:
    map_records = records[records["ADM_NM"].str.match(r"^목[1-5]동$")].copy()
    st.caption("목동 5개 행정동을 표시하고 있습니다.")
else:
    map_records = records.copy()

fig = px.choropleth_mapbox(
    map_records,
    geojson=geojson,
    locations="ADM_CD",
    featureidkey="properties.ADM_CD",
    color="emergency_count",
    color_continuous_scale=[(0, "#ffffff"), (1, "#e31a1c")],
    range_color=(records["emergency_count"].min(), records["emergency_count"].max()),
    custom_data=["ADM_NM", "ADM_CD", "emergency_count"],
    opacity=0.78,
    center=CITY_HALL,
    zoom=10.5,
    mapbox_style="carto-positron",
    labels={"emergency_count": "출동건수"},
)

fig.update_traces(
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"
        "행정동 코드: %{customdata[1]}<br>"
        "출동건수: %{customdata[2]:,.0f}<extra></extra>"
    ),
    marker_line_width=0.5,
    marker_line_color="#666666",
)
fig.update_layout(
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    coloraxis_colorbar={"title": "출동건수"},
)

st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})
