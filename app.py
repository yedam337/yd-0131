import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(layout='wide')

st.title('글로벌 COVID-19 시계열 분석 앱')

@st.cache_data
def load_data():
    # Streamlit Cloud 환경에서 파일을 찾을 수 있도록 경로를 설정합니다.
    # 실제 kagglehub 경로 대신, 파일을 앱과 함께 배포했다고 가정합니다.
    # 예를 들어, 'full_grouped.csv'가 app.py와 같은 디렉토리에 있다면 아래와 같이 로드합니다.
    # 데이터셋이 매우 커서 Streamlit 앱에 직접 포함하기 어렵다면, 
    # Google Cloud Storage나 다른 클라우드 스토리지에서 데이터를 로드하도록 코드를 수정해야 합니다.
    try:
        df = pd.read_csv('full_grouped.csv')
    except FileNotFoundError:
        st.error("데이터 파일을 찾을 수 없습니다. 'full_grouped.csv'가 앱과 같은 디렉토리에 있는지 확인하세요.")
        st.stop()
    
    df['Date'] = pd.to_datetime(df['Date'])
    return df

df = load_data()

# 국가 선택 드롭다운
country_list = ['All Countries'] + sorted(df['Country/Region'].unique().tolist())
selected_country = st.sidebar.selectbox('국가를 선택하세요:', country_list)

if selected_country == 'All Countries':
    # 모든 국가의 합계 데이터
    plot_df = df.groupby('Date')[['Confirmed', 'Deaths', 'Recovered', 'Active']].sum().reset_index()
    title_prefix = '전세계'
else:
    # 선택된 국가의 데이터
    plot_df = df[df['Country/Region'] == selected_country].reset_index(drop=True)
    title_prefix = selected_country

# 'Active' 케이스 계산 (데이터에 이미 'Active' 컬럼이 있는 경우 제외)
if 'Active' not in plot_df.columns:
    plot_df['Active'] = plot_df['Confirmed'] - plot_df['Deaths'] - plot_df['Recovered']


# Plotly Express를 사용하여 시계열 그래프 생성
afghanistan_melted = plot_df.melt(id_vars=['Date'], 
                                      value_vars=['Confirmed', 'Deaths', 'Recovered', 'Active'],
                                      var_name='Case Type', 
                                      value_name='Count')

fig = px.line(afghanistan_melted, 
              x='Date', 
              y='Count', 
              color='Case Type',
              title=f'{title_prefix} COVID-19 확진, 사망, 회복, 격리 환자 추이',
              labels={'Date': '날짜', 'Count': '환자 수', 'Case Type': '유형'})

fig.update_layout(hovermode='x unified')
st.plotly_chart(fig, use_container_width=True)
"""

# Colab 환경에서 파일로 저장
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(streamlit_app_code_full)
