from pathlib import Path
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pydeck as pdk
from preprocess import GU_CENTROIDS

st.set_page_config(page_title="서울시 노후주택 정비 수요 탐색", page_icon="🏚️", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Nunito:wght@600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Gowun Dodum',sans-serif}.stApp{background:#EEF9FB}
h1,h2,h3{font-family:'Nunito','Gowun Dodum',sans-serif;color:#263238}
[data-testid="stMetric"]{background:#fff;border-radius:18px;padding:15px;box-shadow:0 3px 10px #42808d20}
</style>""",unsafe_allow_html=True)

DATA=Path(__file__).parent/"data"/"processed"
TYPES=["아파트","다세대주택","연립주택","단독주택"]
TC={"아파트":"#D9485F","다세대주택":"#F08A8D","연립주택":"#F6B6A6","단독주택":"#3AA76D"}
AC={"20년~30년미만":"#F6B6A6","30년 이상":"#D9485F"}

@st.cache_data
def load():
    files=["aged_housing_by_gu.csv","housing_supply_by_gu.csv"]
    missing=[f for f in files if not (DATA/f).exists()]
    if missing: raise FileNotFoundError("필수 파일 누락: "+", ".join("data/processed/"+f for f in missing))
    return (pd.read_csv(DATA/files[0],encoding="utf-8-sig"),
            pd.read_csv(DATA/files[1],encoding="utf-8-sig"))

def score(aged,supply):
    old=(aged[aged["경과연수"].eq("30년 이상")].groupby(["연도","자치구"],as_index=False)["노후주택수"].sum()
         .rename(columns={"노후주택수":"30년이상노후주택수"}))
    s=old.merge(supply,on=["연도","자치구"])
    s["30년이상노후주택비율"]=s["30년이상노후주택수"]/s["전체주택수"]
    s["비율점수"]=s.groupby("연도")["30년이상노후주택비율"].rank(pct=True)*100
    s["규모점수"]=s.groupby("연도")["30년이상노후주택수"].rank(pct=True)*100
    s["정비수요탐색지수"]=(s["비율점수"]+s["규모점수"])/2
    return s

def bar(df,age,housing_type,title):
    d=df[df["경과연수"].eq(age)&df["주택유형"].eq(housing_type)]
    f=px.bar(d,x="자치구",y="노후주택수",title=title,color_discrete_sequence=[TC[housing_type]])
    f.update_layout(xaxis_title="자치구",yaxis_title="노후주택 수(호)",showlegend=False,height=430, xaxis=dict(tickangle=0,tickfont=dict(size=8),automargin=True))
    return f

def line(df,title):
    d=df.groupby(["연도","경과연수"],as_index=False)["노후주택수"].sum()
    f=px.line(d,x="연도",y="노후주택수",color="경과연수",markers=True,title=title,color_discrete_map=AC)
    f.update_layout(xaxis_title="연도",yaxis_title="주택 수(호)",legend_title_text="건축연수",
                    legend=dict(orientation="h",y=-.22,x=1,xanchor="right"),height=410)
    return f

aged,supply=load()
years=sorted(aged["연도"].unique()); gus=sorted(aged["자치구"].unique())
st.title("🏚️ 서울시 노후주택 현황 기반 정비 수요 탐색")
st.caption("💡 2015년~2025년 자치구별 주택 노후도와 주택 규모를 함께 살펴봄으로써 추가적인 공간·사업성 조사가 필요한 정비 수요 탐색 지역을 찾습니다.")
a,b,c=st.columns([1.4,1,2.2])
with a: gu=st.selectbox("자치구",["서울시 전체"]+gus)
with b: year=st.select_slider("연도",options=years,value=max(years))
with c: types=st.multiselect("주택 유형",TYPES,default=TYPES)
v=aged[aged["연도"].eq(year)&aged["주택유형"].isin(types)]
vs=supply[supply["연도"].eq(year)]
if gu!="서울시 전체": v=v[v["자치구"].eq(gu)];vs=vs[vs["자치구"].eq(gu)]

st.divider()
title_left,title_middle,title_right=st.columns([1,1.25,1.25])
with title_left: st.header("🗺️ #1. 서울시 노후주택의 공간적 분포")
with title_middle: st.header("📊 #2. 자치구별 노후화 주택 유형 구성")
map_col,chart_20_col,chart_30_col=st.columns([1,1.25,1.25])

with map_col:
    m=v.groupby(["자치구","주택유형"],as_index=False)["노후주택수"].sum()
    m[["위도","경도"]]=m["자치구"].map(GU_CENTROIDS).apply(pd.Series)
    color_lookup={name: [int(TC[name][i:i+2],16) for i in (1,3,5)]+[190] for name in TYPES}
    m["색상"]=m["주택유형"].map(color_lookup)
    m["반경"]=(m["노후주택수"]/max(m["노후주택수"].max(),1)*1900+360)
    dot_layer=pdk.Layer("ScatterplotLayer",data=m,get_position="[경도, 위도]",get_radius="반경",
        get_fill_color="색상",pickable=True,stroked=True,get_line_color=[255,255,255,230],line_width_min_pixels=1)
    layers=[dot_layer]
    geo_path=Path(__file__).parent/"data"/"seoul_outer_boundary.geojson"
    if geo_path.exists():
        try:
            boundary=json.loads(geo_path.read_text(encoding="utf-8"))
            layers.insert(0,pdk.Layer("GeoJsonLayer",boundary,stroked=True,filled=True,
                get_fill_color=[226,241,244,30],get_line_color=[71,94,105,185],
                get_line_width=240,line_width_min_pixels=2,pickable=False))
        except (json.JSONDecodeError,UnicodeDecodeError):
            pass
    view=pdk.ViewState(latitude=37.5665,longitude=126.9780,zoom=10.25,pitch=0)
    st.pydeck_chart(pdk.Deck(layers=layers,initial_view_state=view,
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        tooltip={"html":"<b>{자치구}</b><br/>{주택유형}<br/>노후주택 수: {노후주택수}호"}),
        use_container_width=True,height=485)
    st.caption("원 크기: 노후주택 수 · 원 색상: 주택 유형")

allv=aged[aged["연도"].eq(year)&aged["주택유형"].isin(types)]
with chart_20_col:
    type_20=st.radio("주택 유형",TYPES,horizontal=True,key="type_20")
    st.plotly_chart(bar(allv,"20년~30년미만",type_20,"20년 이상~30년 미만: "+type_20),use_container_width=True)
with chart_30_col:
    type_30=st.radio("주택 유형",TYPES,horizontal=True,key="type_30")
    st.plotly_chart(bar(allv,"30년 이상",type_30,"30년 이상: "+type_30),use_container_width=True)

metric_cols=st.columns(4)
n30=v.loc[v["경과연수"].eq("30년 이상"),"노후주택수"].sum()
n20=v.loc[v["경과연수"].eq("20년~30년미만"),"노후주택수"].sum()
total=vs["전체주택수"].sum()
metric_cols[0].metric("전체 주택 수",f"{total:,.0f}호")
metric_cols[1].metric("노후주택 비율",f"{(n30+n20)/total:.1%}" if total else "–")
metric_cols[2].metric("20년 이상~30년 미만 노후주택",f"{n20:,.0f}호")
metric_cols[3].metric("30년 이상 노후주택",f"{n30:,.0f}호")

st.divider();st.header("📈 #3. 2015년~2025년 노후주택 수 추세")
l,r=st.columns(2); trend=aged[aged["주택유형"].isin(types)]
idx=gus.index(gu) if gu in gus else 0
tgu=st.session_state.get("trend_gu",gus[idx])
with l: st.plotly_chart(line(trend,"서울시 노후주택 수 추세"),use_container_width=True)
with r: st.plotly_chart(line(trend[trend["자치구"].eq(tgu)],tgu+" 노후주택 수 추세"),use_container_width=True)
st.selectbox("자치구별 추세",gus,index=gus.index(tgu),key="trend_gu")

st.divider();st.header("🎯 #4. 정비 수요 우선 순위 탐색")
latest_year=max(years)
all_priority=score(aged,supply).query("연도 == @latest_year").sort_values("정비수요탐색지수",ascending=False).reset_index(drop=True)
all_priority["순위"]=all_priority.index+1
scope=st.radio("순위 차트 범위",["상위 5개 자치구","전체 25개 자치구"],horizontal=True,key="rank_scope")
rank_data=all_priority.head(5) if scope=="상위 5개 자치구" else all_priority
rank_data=rank_data.sort_values("정비수요탐색지수",ascending=True)
rank_data["색상"]=px.colors.sample_colorscale("Reds",[.45+.5*i/max(len(rank_data)-1,1) for i in range(len(rank_data))])
chart_col,rank_col,formula_col=st.columns([1.35,.7,1.15])
with chart_col:
    fig=go.Figure(go.Bar(
        x=rank_data["정비수요탐색지수"],y=rank_data["자치구"],orientation="h",
        marker_color=rank_data["색상"],customdata=rank_data[["순위","자치구"]],
        text=rank_data["순위"].astype(str)+"위  "+rank_data["정비수요탐색지수"].map(lambda x:f"{x:.1f}"),
        textposition="outside",
        hovertemplate="<b>%{customdata[1]}</b><br>순위: %{customdata[0]}위<br>탐색지수: %{x:.1f}<extra></extra>",
    ))
    fig.update_layout(
        title=str(latest_year)+"년 "+scope+" 정비 수요 탐색지수",
        xaxis_title="정비 수요 탐색지수",yaxis_title="",height=585,
        margin=dict(l=10,r=55,t=55,b=30),showlegend=False,
    )
    st.plotly_chart(fig,use_container_width=True)
with rank_col:
    st.markdown("#### # 서울시 구별 정비 수요 우선 탐색 순위")
    st.dataframe(
        all_priority[["순위","자치구","정비수요탐색지수"]].rename(columns={"정비수요탐색지수":"지수"}),
        hide_index=True,use_container_width=True,height=550,
        column_config={"지수":st.column_config.NumberColumn(format="%.1f")},
    )
with formula_col:
    st.subheader("# 지수 산정식")
    st.markdown("| 구성요소 | 산정 방법 | 가중치 |\n|---|---|---:|\n| 집중도 | 30년 이상 노후주택 비율의 상대순위 | 50% |\n| 대응 물량 | 30년 이상 노후주택 수의 상대순위 | 50% |")
    st.code("정비 수요 탐색지수 = 집중도 점수 × 0.5 + 대응 물량 점수 × 0.5")
    st.caption("본 지수는 30년 이상 노후주택의 집중도(비율)와 정비 대응 물량(수)을 동등하게 반영한 탐색용 상대지수이다. 두 지표의 실증적 중요도 차이를 확인하기 어려워 5:5의 산술 평균 분석 가정을 적용하였다. 상위 5개 자치구는 법정 정비구역 혹은 사업 가능 후보지가 아니라, 추가적인 공간·사업성 조사가 우선적으로 필요한 정비 수요 탐색 지역임을 밝힌다.")
st.caption("참고: 실제 정비사업 가능 여부는 노후도 외에 과소필지, 도로 접도, 호수밀도, 안전성, 정비계획 및 사업성 등을 별도로 검토해야 합니다.")

with st.expander("데이터 출처와 해석"):
    st.markdown("""- 서울특별시 통계, [건축 경과연수별 주택현황](https://stat.eseoul.go.kr/statHtml/statHtml.do?orgId=201&tblId=DT_201004_K010008&conn_path=I3), 통계표 ID DT_201004_K010008
- 서울특별시 통계, [주택종류별 주택](https://stat.eseoul.go.kr/statHtml/statHtml.do?orgId=201&tblId=DT_201004_K010006&conn_path=I3), 통계표 ID DT_201004_K010006
- 서울시, [재개발 사업 및 정비계획 입안 대상 지역 안내](https://cleanup.seoul.go.kr/cleanup/view/redevelop.do)
- 단위는 호이며 빈집을 포함합니다. 원자료는 20년 이상 주택을 대상으로 집계합니다.""")
