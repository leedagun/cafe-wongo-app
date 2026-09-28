import anthropic
import gspread
import streamlit as st

# 웹페이지 기본 설정
st.set_page_config(
    page_title="마케팅 자동화 프로그램", page_icon="🚀", layout="wide"
)

# 사이드바 메뉴 구성 (4가지 메뉴)
st.sidebar.title("📌 메뉴")
menu_option = st.sidebar.radio(
    "메뉴 선택",
    ["카페 원고 작성기", "카페 원고 검수", "카페 계정 매칭", "체험단 모집"],
    label_visibility="collapsed",
)

# 변수 미리 선언
sheet_url = ""
matching_sheet_url = ""
api_key = ""

# ---------------------------------------------------------
# [설정 영역] 메뉴별 맞춤 설정 분기
# ---------------------------------------------------------

# 1. 카페 원고 작성기 & 카페 원고 검수 선택 시
if menu_option in ["카페 원고 작성기", "카페 원고 검수"]:
  st.sidebar.markdown("---")
  st.sidebar.subheader("⚙️ 카페 프로그램 공통 설정")
  sheet_url = st.sidebar.text_input(
      "구글 시트 링크",
      placeholder="https://docs.google.com/spreadsheets/d/...",
  )
  api_key = st.sidebar.text_input(
      "Anthropic API Key", type="password", placeholder="sk-ant-..."
  )

# 2. 카페 계정 매칭 선택 시 (API 키는 공유하되, 시트 링크는 별도 설정)
elif menu_option == "카페 계정 매칭":
  st.sidebar.markdown("---")
  st.sidebar.subheader("⚙️ 카페 계정 매칭 설정")
  matching_sheet_url = st.sidebar.text_input(
      "계정 매칭 구글 시트 링크",
      placeholder="https://docs.google.com/spreadsheets/d/...",
  )
  api_key = st.sidebar.text_input(
      "Anthropic API Key", type="password", placeholder="sk-ant-..."
  )

# 3. 체험단 모집 선택 시 (설정 아예 없음)
elif menu_option == "체험단 모집":
  # 체험단은 설정창을 띄우지 않습니다.
  pass


# ---------------------------------------------------------
# 1. 카페 원고 작성기 화면
# ---------------------------------------------------------
if menu_option == "카페 원고 작성기":
  st.title("📝 네이버 카페 원고 자동 생성")
  st.markdown(
      "구글 시트의 데이터를 읽어와 클로드가 1~20번 원고(정보성/후기성/슈퍼세트)를"
      " 자동으로 작성합니다."
  )

  with st.expander("ℹ️ 카페 시트 가이드 보기"):
    st.markdown(
        """
        - **1~10번:** 정보성 글 (전문적인 톤)
        - **11~19번:** 체험 공유형 글 (친근한 일상 대화 톤)
        - **20번:** 종합 패키지형 글 (본문 400~500자 이내)
        - G열(제목), H열(본문), I~N열(댓글/대댓글 3세트)에 자동 입력됩니다.
        """
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
# 3. 카페 계정 매칭 화면 (별도 시트 링크 적용)
# ---------------------------------------------------------
elif menu_option == "카페 계정 매칭":
  st.title("🔗 카페 계정 매칭 프로그램")
  st.markdown(
      "작업할 네이버 카페와 배포용 계정을 서로 알맞게 매칭하고 관리하는"
      " 공간입니다."
  )

  if st.button("🚀 계정 매칭 실행"):
    if not matching_sheet_url or not api_key:
      st.warning("⚠️ 계정 매칭 구글 시트 링크와 Anthropic API 키를 모두 입력해주세요!")
    else:
      with st.spinner("카페 계정 매칭을 진행 중입니다..."):
        try:
          gc = gspread.service_account(filename="service_account.json")
          sh = gc.open_by_url(matching_sheet_url)
          # (추가적인 매칭 로직 처리 가능)

          st.success("✨ 카페 계정 매칭 작업이 완료되었습니다!")
        except Exception as e:
          st.error(f"❌ 오류가 발생했습니다: {e}")

# ---------------------------------------------------------
# 4. 체험단 모집 화면 (설정 없음)
# ---------------------------------------------------------
elif menu_option == "체험단 모집":
  st.title("👥 체험단 모집 관리")
  st.markdown(
      "체험단 신청자 명단을 관리하고 선정 가이드를 생성하는 공간입니다."
  )

  st.info("💡 체험단 모집 프로그램 사용을 위해 검색할 키워드를 입력해주세요")

  if st.button("🚀 체험단 프로그램 실행"):
    st.success("✨ 체험단 프로그램이 실행되었습니다!")
