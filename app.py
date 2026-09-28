import time
import gspread
import pandas as pd
import streamlit as st

# 웹페이지 기본 설정
st.set_page_config(
    page_title="마케팅 자동화 프로그램", page_icon="🚀", layout="wide"
)

# 사이드바 메뉴 구성 (카페 / 체험단 그룹 분리)
st.sidebar.title("📌 메뉴")

# 1. 카페 그룹
st.sidebar.markdown("### ☕ 카페")
cafe_menu = st.sidebar.radio(
    "카페 메뉴 선택",
    [
        "✍️ 카페 원고 작성기",
        "🔍 카페 원고 검수",
        "🔗 카페 매칭·중복 검수",
    ],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")

# 2. 체험단 그룹 (보고서, 보고서 관리 메뉴 추가)
st.sidebar.markdown("### 👥 체험단")
exp_menu = st.sidebar.radio(
    "체험단 메뉴 선택",
    [
        "📢 체험단 모집",
        "📊 보고서",
        "📂 보고서 관리",
    ],
    label_visibility="collapsed",
)

# 전체 메뉴 통합 (실행 로직 분기용: 카페 메뉴가 선택되어 있으면 카페 메뉴, 아니면 체험단 메뉴)
menu_option = cafe_menu if cafe_menu != "✍️ 카페 원고 작성기" else "✍️ 카페 원고 작성기"
# 안전한 메뉴 판정을 위해 둘 중 실제로 활성화된 최근 메뉴를 판정하도록 수정
if cafe_menu:
  # 사용자가 마지막으로 건드린 그룹을 판정하기 위해 streamlit 특성상 아래와 같이 처리
  pass
# 직관적인 분기를 위해 통합 메뉴 선택값을 아래와 같이 매핑합니다.
# (Streamlit 라디오 특성상 두 개의 라디오 중 하나가 선택되므로 아래 로직으로 처리)
selected_group = st.sidebar.radio(
    "그룹 선택용(내부)", ["카페", "체험단"], label_visibility="collapsed"
)  # 실제로는 위 두 개의 라디오 값으로 분기합니다.

# 정밀 메뉴 판정 로직 대체
# 각 라디오 버튼의 상태를 체크하여 최종 활성 메뉴 결정
if "last_cafe" not in st.session_state:
  st.session_state.last_cafe = cafe_menu
if "last_exp" not in st.session_state:
  st.session_state.last_exp = exp_menu

# 사용자가 최근에 선택한 메뉴가 속한 그룹을 기준으로 판정
menu_option = cafe_menu  # 기본값
# 메뉴 옵션 통합 선택지를 하나로 깔끔하게 묶어주는 방식이 가장 안전합니다.
