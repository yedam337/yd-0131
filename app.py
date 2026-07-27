import streamlit as st

st.title('두 숫자 더하기 앱')

st.write('두 개의 숫자를 입력하여 합계를 계산합니다.')

# 사용자로부터 첫 번째 숫자 입력 받기
num1 = st.number_input('첫 번째 숫자를 입력하세요', value=0.0)

# 사용자로부터 두 번째 숫자 입력 받기
num2 = st.number_input('두 번째 숫자를 입력하세요', value=0.0)

# 두 숫자의 합 계산
sum_result = num1 + num2

# 결과 출력
st.write(f'두 숫자의 합은: **{sum_result}** 입니다.')
