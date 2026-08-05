# 서울시 행정동별 출동건수 지도

Plotly Choropleth map으로 행정동별 출동건수를 흰색(낮음)부터 빨간색(높음)까지 표시하는 Streamlit 앱입니다.

## 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 열린 지도는 처음에 서울시청을 중심으로 표시됩니다. 상단의 **목동만 보기** 토글을 켜면 목1동~목5동만 볼 수 있습니다.

## Streamlit Community Cloud 배포

1. 이 폴더 전체를 새 GitHub 저장소에 올립니다. `data/dong_emergency_count.geojson`도 반드시 포함하세요.
2. [Streamlit Community Cloud](https://share.streamlit.io/)에서 **Create app**을 선택합니다.
3. 저장소, 브랜치, Main file path로 `app.py`를 지정한 후 배포합니다.
