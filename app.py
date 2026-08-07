from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from preprocess import GU_CENTROIDS

st.set_page_config(page_title="서울 노후주택 탐색기", page_icon="🏠", layout="wide")
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Nunito:wght@500;700;800&display=swap');
html, body, [class*="css"] {font-family: 'Gowun Dodum', sans-serif;}
.stApp {background:#EAF8FB;} h1,h2,h3 {font-family:'Nunito','Gowun Dodum',sans-serif; color:#263238;}
div[data-testid="stMetric"] {background:#fff; border-radius:18px; padding:14px; box-shadow:0 2px 9px #b8dce344;}
div[data-testid="stVerticalBlockBorderWrapper"] {background:#fff; border-radius:22px; border:0; box-shadow:0 2px 9px #b8dce344;}
</style>''', unsafe_allow_html=True)

DATA = Path(__file__).parent / "data" / "processed"
@st.cache_data
def load_data():
    return (pd.read_csv(DATA / "aged_housing_by_gu.csv"), pd.read_csv(DATA / "housing_supply_by_gu.csv"),
            pd.read_csv(DATA / "renewal_supply_priority_by_gu.csv"))

aged, supply, priority = load_data()
TYPE_ORDER = ["아파트", "단독주택", "다세대주택", "연립주택"]
AGE_COLORS = {"20년~30년미만": "#FFB3A7", "30년 이상": "#E94F4F"}
TYPE_COLORS = {"아파트":"#8D7AE8", "단독주택":"#88C7E8", "다세대주택":"#F5A5CF", "연립주택":"#F6D86B"}

st.title("🏠 서울 노후주택 · 정비·공급 탐색기")
st.caption("2015–2025년 자치구별 주택 노후화와 공급 규모를 함께 살펴보고 정비·공급 검토 지역을 찾습니다.")
ctrl1, ctrl2, ctrl3 = st.columns([2, 1, 2])
with ctrl1: selected_gu = st.selectbox("자치구 선택", ["서울시 전체"] + sorted(aged["자치구"].unique()))
with ctrl2: year = st.select_slider("연도", options=sorted(aged["연도"].unique()), value=int(aged["연도"].max()))
with ctrl3: types = st.multiselect("주택 유형", TYPE_ORDER, default=TYPE_ORDER)

view_aged = aged[(aged["연도"] == year) & aged["주택유형"].isin(types)].copy()
view_supply = supply[supply["연도"] == year]
if selected_gu != "서울시 전체":
    view_aged = view_aged[view_aged["자치구"] == selected_gu]
    view_supply = view_supply[view_supply["자치구"] == selected_gu]

old30 = view_aged.query("경과연수 == '30년 이상'")["노후주택수"].sum()
old20 = view_aged["노후주택수"].sum()
total_supply = view_supply["전체주택수"].sum()
k1,k2,k3,k4 = st.columns(4)
k1.metric("30년 이상 노후주택", f"{old30:,.0f}호")
k2.metric("20년 이상 노후주택", f"{old20:,.0f}호")
k3.metric("전체 주택 수", f"{total_supply:,.0f}호")
k4.metric("노후주택 비율", f"{old20/total_supply:.1%}" if total_supply else "–")

left, right = st.columns([1.15, 1])
with left:
    st.subheader("어디에 어떤 노후주택이 많은가?")
    map_df = (view_aged.groupby(["자치구", "주택유형", "경과연수"], as_index=False)["노후주택수"].sum())
    map_df[["위도", "경도"]] = map_df["자치구"].map(GU_CENTROIDS).apply(pd.Series)
    fig_map = px.scatter_map(map_df, lat="위도", lon="경도", size="노후주택수", color="주택유형",
        hover_name="자치구", hover_data={"경과연수":True,"노후주택수":":,","위도":False,"경도":False},
        color_discrete_map=TYPE_COLORS, zoom=9.1, center={"lat":37.5665,"lon":126.9780}, height=450)
    fig_map.update_layout(map_style="carto-positron", margin=dict(l=0,r=0,t=0,b=0), legend_title_text="주택 유형")
    st.plotly_chart(fig_map, use_container_width=True)
    st.caption("원자료의 공간 단위는 자치구입니다. 원의 크기는 노후주택 수, 색은 주택 유형입니다.")
with right:
    st.subheader("유형별 노후화 구성")
    bar = px.bar(view_aged, x="자치구", y="노후주택수", color="경과연수", facet_col="주택유형",
                 category_orders={"주택유형":TYPE_ORDER,"경과연수":["20년~30년미만","30년 이상"]},
                 color_discrete_map=AGE_COLORS, barmode="stack", height=450)
    bar.update_layout(margin=dict(l=10,r=10,t=35,b=5), legend_title_text="건축 경과연수")
    bar.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    st.plotly_chart(bar, use_container_width=True)

bottom_left, bottom_right = st.columns([1.35, 1])
with bottom_left:
    st.subheader("2015–2025 노후주택 추이")
    trend = aged[aged["주택유형"].isin(types)]
    if selected_gu != "서울시 전체": trend = trend[trend["자치구"] == selected_gu]
    trend = trend.groupby(["연도", "경과연수"], as_index=False)["노후주택수"].sum()
    line = px.line(trend, x="연도", y="노후주택수", color="경과연수", markers=True,
                   color_discrete_map=AGE_COLORS, category_orders={"경과연수":["20년~30년미만","30년 이상"]})
    line.update_layout(yaxis_title="주택 수(호)", xaxis_title="", legend_title_text="건축 경과연수", height=350)
    st.plotly_chart(line, use_container_width=True)
with bottom_right:
    st.subheader("정비·공급 검토 우선순위")
    score = priority[priority["연도"] == year].copy()
    if selected_gu != "서울시 전체": score = score[score["자치구"] == selected_gu]
    score = score.sort_values("정비공급우선지수", ascending=False)
    donut = px.pie(score, names="자치구", values="정비공급우선지수", hole=.62,
                   color="우선순위", color_discrete_map={"관찰":"#A9DDF0","검토":"#F6D86B","우선 검토":"#E94F4F"})
    donut.update_layout(height=350, margin=dict(l=0,r=0,t=10,b=0), legend_title_text="판정")
    st.plotly_chart(donut, use_container_width=True)

st.info("우선순위 지수는 같은 연도 자치구 간 상대 비교입니다. 노후주택 비율(60%)과 전체 주택 수가 작은 정도(40%)를 결합한 탐색용 지표이며, 실제 사업 선정에는 정비구역·안전진단·인구·토지이용 등 추가 검토가 필요합니다.")
with st.expander("데이터 출처와 해석"):
    st.markdown("- 서울특별시 통계: 건축 경과연수별 주택현황 (DT_201004_K010008)\n- 서울특별시 통계: 주택종류별 주택 (DT_201004_K010006)\n- 단위: 호, 빈집 포함. 원자료 기준 20년 이상 주택을 집계했습니다.")

