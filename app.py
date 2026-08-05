import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pyproj import Transformer


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


def find_facility_file() -> Path:
    """소방시설 엑셀 파일을 GitHub 저장소에서 찾는다."""
    app_dir = Path(__file__).resolve().parent
    candidates = [
        app_dir / "seoul_fire_facilities.xlsx",  # GitHub 배포용 권장 파일명
        app_dir / "서울시 소방서,안전센터,구조대 위치정보.xlsx",
        app_dir / "data" / "seoul_fire_facilities.xlsx",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    st.error(
        "`seoul_fire_facilities.xlsx` 파일을 찾을 수 없습니다. "
        "GitHub 저장소의 app.py와 같은 위치에 파일을 올려 주세요."
    )
    st.stop()


@st.cache_data
def load_geojson(path: Path) -> dict:
    """GeoJSON과 행정동 속성 데이터를 한 번만 불러온다."""
    with path.open(encoding="utf-8") as file:
        return json.load(file)


@st.cache_data
def load_fire_facilities(path: Path) -> pd.DataFrame:
    """EPSG:5186 평면좌표를 WGS84 경위도 좌표로 변환한다."""
    facilities = pd.read_excel(path)
    required_columns = {"서ㆍ센터ID", "서ㆍ센터명", "유형구분명", "X좌표", "Y좌표"}
    missing = required_columns.difference(facilities.columns)
    if missing:
        raise ValueError(f"필수 열이 없습니다: {', '.join(sorted(missing))}")

    facilities = facilities.dropna(subset=["X좌표", "Y좌표"]).copy()
    facilities["X좌표"] = pd.to_numeric(facilities["X좌표"], errors="coerce")
    facilities["Y좌표"] = pd.to_numeric(facilities["Y좌표"], errors="coerce")
    facilities = facilities.dropna(subset=["X좌표", "Y좌표"])

    transformer = Transformer.from_crs("EPSG:5186", "EPSG:4326", always_xy=True)
    facilities["lon"], facilities["lat"] = transformer.transform(
        facilities["X좌표"].to_numpy(), facilities["Y좌표"].to_numpy()
    )
    facilities["지도유형"] = facilities["유형구분명"].eq("소방서").map(
        {True: "소방서", False: "안전센터·구조대"}
    )
    return facilities


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

st.divider()
st.header("서울시 소방시설 위치")
st.caption("원본 EPSG:5186 좌표를 WGS84 경위도(EPSG:4326)로 변환해 표시합니다.")

try:
    facilities = load_fire_facilities(find_facility_file())
except ValueError as error:
    st.error(f"소방시설 데이터를 읽을 수 없습니다: {error}")
    st.stop()

facility_map = go.Figure()
style_by_type = {
    "소방서": {"color": "#e31a1c", "size": 11},
    "안전센터·구조대": {"color": "#111111", "size": 8},
}

for facility_type, style in style_by_type.items():
    subset = facilities[facilities["지도유형"] == facility_type]
    facility_map.add_trace(
        go.Scattermapbox(
            lon=subset["lon"],
            lat=subset["lat"],
            mode="markers",
            name=facility_type,
            marker={"size": style["size"], "color": style["color"], "opacity": 0.9},
            customdata=subset[["서ㆍ센터명", "서ㆍ센터ID", "유형구분명"]],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "시설 ID: %{customdata[1]}<br>"
                "유형: %{customdata[2]}<extra></extra>"
            ),
        )
    )

facility_map.update_layout(
    mapbox={"style": "open-street-map", "center": CITY_HALL, "zoom": 10.1},
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    legend={"title": "시설 유형", "orientation": "h", "y": 0.02, "x": 0.01},
    height=620,
)
st.plotly_chart(facility_map, use_container_width=True, config={"scrollZoom": True})
