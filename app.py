import gspread
import streamlit as st

# 웹페이지 기본 설정
st.set_page_config(
    page_title="마케팅 자동화 프로그램", page_icon="🚀", layout="wide"
)

# 사이드바 메뉴 구성 (이모티콘 추가 버전)
st.sidebar.title("📌 메뉴")
menu_option = st.sidebar.radio(
    "메뉴 선택",
    [
        "✍️ 카페 원고 작성기",
        "🔍 카페 원고 검수",
        "🔗 카페 계정 매칭",
        "📢 체험단 모집",
    ],
    label_visibility="collapsed",
)

# ---------------------------------------------------------
# 1. 카페 원고 작성기 화면
# ---------------------------------------------------------
if menu_option == "카페 원고 작성기":
  st.title("📝 네이버 카페 원고 자동 생성")
  st.markdown("구글 시트의 데이터를 읽은 후 원고를 자동으로 작성합니다.")

  with st.expander("ℹ️ 카페 시트 가이드 보기"):
    st.markdown(
        """
        - **1~10번:** 정보성 글 (전문적인 톤)
        - **11~19번:** 체험 공유형 글 (친근한 일상 대화 톤)
        - **20번:** 종합 패키지형 글 (본문 400~500자 이내)
        - G열(제목), H열(본문), I~N열(댓글/대댓글 3세트)에 자동 입력됩니다.
        """
    )

  sheet_url = st.text_input(
      "원고 구글 시트 링크",
      placeholder="https://docs.google.com/spreadsheets/d/...",
      key="cafe_wongo_sheet",
  )

  if st.button("🚀 카페 원고 생성 및 시트 입력 시작"):
    if not sheet_url:
      st.warning("⚠️ 원고 구글 시트 링크를 입력해주세요!")
    else:
      with st.spinner("카페 원고를 처리하고 있습니다..."):
        try:
          gc = gspread.service_account(filename="service_account.json")
          sh = gc.open_by_url(sheet_url)
          sheet = sh.get_worksheet(0)

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

  review_sheet_url = st.text_input(
      "검수할 원고 구글 시트 링크",
      placeholder="https://docs.google.com/spreadsheets/d/...",
      key="cafe_review_sheet",
  )

  if st.button("🚀 원고 검수 시작"):
    if not review_sheet_url:
      st.warning("⚠️ 구글 시트 링크를 입력해주세요!")
    else:
      with st.spinner("원고를 검수 중입니다..."):
        try:
          gc = gspread.service_account(filename="service_account.json")
          sh = gc.open_by_url(review_sheet_url)

          st.success("✨ 원고 검수가 완료되었습니다!")
        except Exception as e:
          st.error(f"❌ 오류가 발생했습니다: {e}")

# ---------------------------------------------------------
# 3. 카페 계정 매칭 화면 (API 키 제거 버전)
# ---------------------------------------------------------
elif menu_option == "카페 계정 매칭":
  st.title("🔗 카페 계정 매칭 프로그램")
  st.markdown(
      "작업할 네이버 카페와 배포용 계정을 서로 알맞게 매칭하고 관리하는"
      " 공간입니다."
  )

  matching_sheet_url = st.text_input(
      "매칭 구글 시트 링크",
      placeholder="https://docs.google.com/spreadsheets/d/...",
      key="matching_sheet",
  )

  if st.button("🚀 계정 매칭 실행"):
    if not matching_sheet_url:
      st.warning("⚠️ 매칭 구글 시트 링크를 입력해주세요!")
    else:
      with st.spinner("카페 계정 매칭을 진행 중입니다..."):
        try:
          gc = gspread.service_account(filename="service_account.json")
          sh = gc.open_by_url(matching_sheet_url)

          st.success("✨ 카페 계정 매칭 작업이 완료되었습니다!")
        except Exception as e:
          st.error(f"❌ 오류가 발생했습니다: {e}")

# ---------------------------------------------------------
# 4. 체험단 모집 화면
# ---------------------------------------------------------
elif menu_option == "체험단 모집":
  st.title("👥 체험단 모집 관리")
  st.markdown(
      "체험단 신청자 명단을 관리하고 선정 가이드를 생성하는 공간입니다."
  )

  st.info("💡 체험단 모집 프로그램 사용을 위해 검색할 키워드를 입력해주세요")
  keyword = st.text_input("검색할 키워드 입력", placeholder="예: 맛집")

  if st.button("🚀 체험단 프로그램 실행"):
    if not keyword:
      st.warning("⚠️ 검색할 키워드를 입력해주세요!")
    else:
      st.success(
          f"✨ 체험단 프로그램이 실행되었습니다! (검색 키워드: {keyword})"
      )
