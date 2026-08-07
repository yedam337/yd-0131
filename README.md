# 서울 노후주택 · 정비·공급 탐색기

서울시 자치구별 노후주택(20–30년 미만/30년 이상)과 전체 주택 수를 결합해 정비·공급 검토 지역을 탐색하는 Streamlit 대시보드입니다.

## 포함 기능

- 자치구·연도·주택유형 선택에 연동되는 지도, 막대그래프, 시계열
- 20–30년 미만은 연한 코랄, 30년 이상은 레드로 표현한 누적 막대그래프
- 주택유형별 공간 분포(자치구 중심점 기반), 노후화 구성, 2015–2025 추이
- 노후주택 비율과 전체 주택 수를 결합한 탐색용 정비·공급 우선순위

## Colab에서 전처리

1. `preprocess.py`를 Colab에 업로드하거나 GitHub 저장소를 clone합니다.
2. 두 Excel 원자료를 `data/raw/`에 올립니다.
3. 아래를 실행합니다.

```python
!pip -q install pandas openpyxl
!python preprocess.py --raw-dir data/raw --output-dir data/processed
```

## 로컬/Streamlit 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## GitHub 게시

```bash
git init
git add .
git commit -m "Create Seoul aging housing dashboard"
git branch -M main
git remote add origin https://github.com/사용자명/저장소명.git
git push -u origin main
```

Streamlit Community Cloud에서는 이 저장소를 선택하고 `app.py`를 엔트리포인트로 지정합니다.

## 데이터 출처

- 서울특별시 통계, [건축 경과연수별 주택현황](https://stat.eseoul.go.kr/statHtml/statHtml.do?orgId=201&tblId=DT_201004_K010008&conn_path=I3), 통계표 ID `DT_201004_K010008`
- 서울특별시 통계, [주택종류별 주택](https://stat.eseoul.go.kr/statHtml/statHtml.do?orgId=201&tblId=DT_201004_K010006&conn_path=I3), 통계표 ID `DT_201004_K010006`

## 해석 유의사항

이 앱의 우선순위는 정책 의사결정용 확정 판정이 아닌 1차 탐색 지표입니다. 실제 재개발·재건축 또는 신규 공급 대상 선정에는 정비계획, 안전진단, 사업성, 인구·가구 변화, 공공시설 및 토지이용 조건을 추가로 검토해야 합니다.

