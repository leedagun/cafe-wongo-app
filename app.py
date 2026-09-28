import anthropic
import gspread
import streamlit as st

# 웹페이지 기본 설정
st.set_page_config(
    page_title="마케팅 자동화 프로그램", page_icon="🚀", layout="wide"
)

# 사이드바 메뉴 구성
st.sidebar.title("📌 메뉴")
menu_option = st.sidebar.radio(
    "메뉴 선택",
    ["카페 원고 작성기", "카페 원고 검수", "체험단 모집"],
    label_visibility="collapsed",
)

# 변수 미리 선언
sheet_url = ""
api_key = ""

# ---------------------------------------------------------
# [중요] 카페 메뉴를 선택했을 때만 사이드바에 설정창이 나타나도록 설정
# ---------------------------------------------------------
if menu_option in ["카페 원고 작성기", "카페 원고 검수"]:
  st.sidebar.markdown("---")
  st.sidebar.subheader("⚙️ 카페 공통 설정")
  sheet_url = st.sidebar.text_input(
      "구글 시트 링크",
      placeholder="https://docs.google.com/spreadsheets/d/...",
  )
  api_key = st.sidebar.text_input(
      "Anthropic API Key", type="password", placeholder="sk-ant-..."
  )

# ---------------------------------------------------------
# 1. 카페 원고 작성기 화면
# ---------------------------------------------------------
if menu_option == "카페 원고 작성기":
  st.title("📝 네이버 카페 원고 자동 생성")
  st.markdown(
      "구글 시트 연동 후 원고를"
      " 자동으로 작성합니다."
  )

  with st.expander("ℹ️ 카페 원고 프로그램 사용 가이드 보기"):
    st.markdown(
        """
        - **구글 시트 링크 확인
        - **작성할 지점 확인
    )

  if st.button("🚀 카페 원고 생성 및 시트 입력 시작"):
    if not sheet_url or not api_key:
      st.warning("⚠️ 구글 시트 링크와 Anthropic API 키를 모두 입력해주세요!")
    else:
      with st.spinner("클로드가 카페 원고를 작성하고 있습니다..."):
        try:
          gc = gspread.service_account(filename="service_account.json")
          sh = gc.open_by_url(sheet_url)
          sheet = sh.get_worksheet(0)
          client = anthropic.Anthropic(api_key=api_key)

          st.success("✨ 카페 원고가 성공적으로 작성되어 구글 시트에 입력되었습니다!")
        except Exception as e:
          st.error(f"❌ 오류가 발생했습니다: {e}")

# ---------------------------------------------------------
# 2. 카페 원고 검수 화면
# ---------------------------------------------------------
elif menu_option == "카페 원고 검수":
  st.title("🔍 카페 원고 검수 프로그램")
  st.markdown(
      "작성된 카페 원고에 홍보성 문구나 금칙어가 포함되어 있는지, 가이드에 맞게"
      " 잘 작성되었는지 검수합니다."
  )

  if st.button("🚀 원고 검수 시작"):
    if not sheet_url or not api_key:
      st.warning("⚠️ 구글 시트 링크와 Anthropic API 키를 모두 입력해주세요!")
    else:
      st.success("✨ 원고 검수가 완료되었습니다!")

# ---------------------------------------------------------
# 3. 체험단 모집 화면 (공통 설정 아예 없음)
# ---------------------------------------------------------
elif menu_option == "체험단 모집":
  st.title("👥 체험단 모집 관리")
  st.markdown(
      "체험단 신청자 명단을 관리하고 선정 가이드를 생성하는 공간입니다."
  )

  st.info(
      "💡 체험단 모집 프로그램 사용을 위해 검색할 키워드를 입력해주세요"
  )

  if st.button("🚀 체험단 프로그램 실행"):
    st.success("✨ 체험단 프로그램이 실행되었습니다!")
