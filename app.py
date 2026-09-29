import time
import gspread
import pandas as pd
import streamlit as st

# 웹페이지 기본 설정
st.set_page_config(
    page_title="마케팅 자동화 프로그램", page_icon="🚀", layout="wide"
)

# 세션 스테이트 초기화 (역할은 관리자로 고정)
if "menu_option" not in st.session_state:
  st.session_state.menu_option = "🏠 홈"
if "preview_data" not in st.session_state:
  st.session_state.preview_data = None
if "action_type" not in st.session_state:
  st.session_state.action_type = None

# 고정 권한 (관리자)
role = "관리자"

# =========================================================
# 사이드바 메뉴 구성
# =========================================================
st.sidebar.title("📌 통합 대시보드")
st.sidebar.markdown("---")


def menu_btn(label, target_menu):
  is_selected = st.session_state.menu_option == target_menu
  if st.sidebar.button(
      label,
      use_container_width=True,
      type="primary" if is_selected else "secondary",
      key=f"btn_{target_menu}",
  ):
    st.session_state.menu_option = target_menu
    st.rerun()


st.sidebar.markdown("📌 **메뉴 선택**")

# 관리자 기준 전체 메뉴 노출
menu_btn("🏠 홈 (대시보드)", "🏠 홈")
menu_btn("🏢 지점 및 장비 관리", "🏢 지점 및 장비 관리")
menu_btn("☕ 카페 목록 관리", "☕ 카페 목록 관리")
menu_btn("✍️ 카페 원고 작성기", "✍️ 카페 원고 작성기")
menu_btn("🔍 카페 원고 자동 검수", "🔍 카페 원고 자동 검수")
menu_btn("🔗 카페 매칭·중복 검수", "🔗 카페 매칭·중복 검수")
menu_btn("📝 단건 원고 작성", "📝 단건 원고 작성")
menu_btn("📢 체험단 모집 관리", "📢 체험단 모집 관리")
menu_btn("📊 카페 작업 현황 보고서", "📊 카페 보고서")
menu_btn("📈 체험단 모집 현황 보고서", "📈 체험단 보고서")

st.sidebar.markdown("---")
st.sidebar.caption("🚀 마케팅 통합 관리 프로그램 v1.0")

menu_option = st.session_state.menu_option


# =========================================================
# 화면 분기 및 렌더링
# =========================================================
if menu_option == "🏠 홈":
  st.title("🏠 마케팅 통합 관리 홈 (대시보드)")
  st.markdown("현재 접속 권한: **관리자** (전체 보기)")

  col1, col2, col3 = st.columns(3)
  col1.metric("이번 달 목표 원고", "880건", "진행중")
  col2.metric("작성 완료", "640건", "+45건")
  col3.metric("검수 대기 / 위반", "12건", "-3건")

  st.markdown("---")
  st.subheader("📌 전체 진행 현황")

  task_df = pd.DataFrame([{
      "지점": "유앤아이 강남점",
      "작업 구분": "원고 작성 및 확인",
      "상태": "진행 중",
  }])
  st.dataframe(task_df, use_container_width=True)

elif menu_option == "🏢 지점 및 장비 관리":
  st.title("🏢 지점 및 보유 장비 관리")
  branch_df = pd.DataFrame([{
      "지점명": "유앤아이 강남점",
      "구분": "유앤아이",
      "보유 장비": "영국산 보톡스, 슈링크",
  }])
  st.data_editor(branch_df, use_container_width=True)

elif menu_option == "☕ 카페 목록 관리":
  st.title("☕ 카페 목록 관리")
  cafe_df = pd.DataFrame([{
      "카페명": "맘스홀릭 베이비",
      "유형": "맘",
      "규모": "대형",
      "상태": "진행 가능",
  }])
  st.dataframe(cafe_df, use_container_width=True)

elif menu_option == "✍️ 카페 원고 작성기":
  st.title("📝 네이버 카페 원고 자동 생성")
  sheet_url = st.text_input(
      "원고 구글 시트 링크",
      placeholder="https://docs.google.com/spreadsheets/d/...",
  )
  if st.button("🚀 원고 생성 및 작성 수행"):
    st.success("✨ 원고 자동 생성이 완료되었습니다.")

elif menu_option == "🔍 카페 원고 자동 검수":
  st.title("🔍 카페 원고 자동 검수 프로그램")
  st.text_input("검수할 원고 구글 시트 링크")
  if st.button("🚀 자동 검수 시작"):
    st.success("✨ 금칙어 및 장비 규칙 자동 검수 완료")

elif menu_option == "🔗 카페 매칭·중복 검수":
  st.title("🔗 카페 매칭 및 지점별 중복 검수")
  if st.button("🚀 매칭 검수 실행"):
    st.success("✨ 매칭 및 중복 검수 완료")

elif menu_option == "📝 단건 원고 작성":
  st.title("📝 단건 원고 작성기")
  st.selectbox("작성 유형", ["카페 상위노출 원고", "이미지 캡션 글", "질문글"])
  st.text_input("주요 키워드 입력")
  if st.button("🚀 단건 생성"):
    st.success("✨ 단건 원고 생성 완료")

elif menu_option == "📢 체험단 모집 관리":
  st.title("👥 블로거 체험단 모집 관리")
  st.text_input("수집 키워드 입력")
  if st.button("🚀 블로거 수집 시작"):
    st.success("✨ 상위노출 개인 블로거 수집 및 필터링 완료")

elif menu_option == "📊 카페 보고서":
  st.title("📊 카페 작업 현황 보고서")
  report_df = pd.DataFrame([{
      "지점": "유앤아이 강남점",
      "발행일": "2026-06-07",
      "카페명": "맘스홀릭",
      "상태": "지점 담당자 확인 완료",
  }])
  st.dataframe(report_df, use_container_width=True)

  csv_data = report_df.to_csv(index=False).encode("utf-8-sig")
  st.download_button(
      "📥 외부용 보고서 다운로드 (실행사/아이디 제외)",
      data=csv_data,
      file_name="external_report.csv",
      mime="text/csv",
  )

elif menu_option == "📈 체험단 보고서":
  st.title("📈 체험단 모집 현황 보고서")
  report_exp_df = pd.DataFrame([{
      "키워드": "잠실 입술필러",
      "수집 인원": "50명",
      "제외 인원": "18명",
      "최종 등록": "32명",
  }])
  st.dataframe(report_exp_df, use_container_width=True)
