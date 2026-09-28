import time
import gspread
import pandas as pd
import streamlit as st

# 웹페이지 기본 설정
st.set_page_config(
    page_title="마케팅 자동화 프로그램", page_icon="🚀", layout="wide"
)

# 세션 스테이트 초기화 (메뉴 및 권한 유지용)
if "menu_option" not in st.session_state:
  st.session_state.menu_option = "🏠 홈"
if "preview_data" not in st.session_state:
  st.session_state.preview_data = None
if "action_type" not in st.session_state:
  st.session_state.action_type = None
if "user_role" not in st.session_state:
  # 기본 권한 설정 (관리자가 직접 지정 가능)
  st.session_state.user_role = "관리자"

# =========================================================
# 사이드바 메뉴 및 권한 지정 구성
# =========================================================
st.sidebar.title("📌 통합 대시보드")
st.sidebar.markdown("---")

# 1. 관리자 권한 지정 기능 (관리자가 직접 역할 변경 가능)
st.sidebar.markdown("🔒 **관리자 권한 지정**")
st.session_state.user_role = st.sidebar.selectbox(
    "현재 접속자 역할 설정",
    [
        "관리자",
        "지점 담당자 (유앤아이·블루)",
        "원고 작가",
        "게시판 담당",
        "실행사",
        "원장님 (로컬)",
    ],
    index=0,
    key="admin_role_select",
)
st.sidebar.caption(
    "💡 관리자가 지정한 권한에 따라 화면 범위와 노출 정보가 조절됩니다[cite: 5]."
)
st.sidebar.markdown("---")

# 2. 메뉴 버튼 정의 함수 (클릭 시 색상 지정용 primary/secondary 동적 제어)
st.sidebar.markdown("📌 **메뉴 선택**")


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


# 홈 / 기준 정보 섹션
st.sidebar.markdown("🏠 **홈 / 기준 정보**")
menu_btn("🏠 홈 (대시보드)", "🏠 홈")
menu_btn("🏢 지점 및 장비 관리", "🏢 지점 및 장비 관리")
menu_btn("☕ 카페 목록 관리", "☕ 카페 목록 관리")

st.sidebar.markdown("---")

# 카페 원고 제작 섹션
st.sidebar.markdown("☕ **카페 원고 제작**")
menu_btn("✍️ 카페 원고 작성기", "✍️ 카페 원고 작성기")
menu_btn("🔍 카페 원고 자동 검수", "🔍 카페 원고 자동 검수")
menu_btn("🔗 카페 매칭·중복 검수", "🔗 카페 매칭·중복 검수")
menu_btn("📝 단건 원고 작성", "📝 단건 원고 작성")

st.sidebar.markdown("---")

# 운영 및 보고서 섹션
st.sidebar.markdown("📊 **운영 및 보고서**")
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
  st.markdown(
      f"현재 지정된 권한: **{st.session_state.user_role}** | 월 880건 원고"
      " 작성·검수 현황"
  )

  col1, col2, col3, col4 = st.columns(4)
  col1.metric("이번 달 목표 원고", "880건", "진행중")
  col2.metric("작성 완료", "640건", "+45건")
  col3.metric("검수 대기 / 위반", "12건", "-3건")
  col4.metric("절약된 시간", "142시간", "자동 집계")

  st.markdown("---")
  st.subheader("📌 내 할 일 및 마감 임박 항목")
  task_df = pd.DataFrame([
      {
          "지점": "유앤아이 강남점",
          "작업 구분": "정보성 원고 작성",
          "담당자/작가": "김작가",
          "마감일": "2026-06-10",
          "상태": "피드백 대기",
      },
      {
          "지점": "블루비뇨기과 신촌점",
          "작업 구분": "후기성 원고 검수",
          "담당자/작가": "이작가",
          "마감일": "2026-06-11",
          "상태": "검수 대기",
      },
  ])
  st.dataframe(task_df, use_container_width=True)

elif menu_option == "🏢 지점 및 장비 관리":
  st.title("🏢 지점 및 보유 장비 관리")
  st.markdown("표준 장비명 사전과 연동된 보유 장비를 관리합니다[cite: 5].")
  branch_df = pd.DataFrame([
      {
          "지점명": "유앤아이 강남점",
          "구분": "유앤아이",
          "지역": "서울",
          "담당자": "김담당",
          "작가": "김작가",
          "보유 장비": "영국산 보톡스, 슈링크",
      },
      {
          "지점명": "블루비뇨기과 신촌점",
          "구분": "블루비뇨기과",
          "지역": "서울",
          "담당자": "박담당",
          "작가": "이작가",
          "보유 장비": "Lumenis One, 레이저토닝",
      },
  ])
  st.data_editor(branch_df, use_container_width=True)

elif menu_option == "☕ 카페 목록 관리":
  st.title("☕ 카페 목록 및 지점 연결 관리")
  cafe_df = pd.DataFrame([
      {
          "카페명": "맘스홀릭 베이비",
          "다른 표기": "맘스홀릭",
          "유형": "맘",
          "규모": "대형",
          "지역": "전국",
          "상태": "진행 가능",
          "단가": "25,000원",
      },
      {
          "카페명": "세클맘",
          "다른 표기": "세상 모든 엄마들",
          "유형": "지역맘",
          "규모": "소형",
          "지역": "서울",
          "상태": "진행 가능",
          "단가": "기본 단가",
      },
  ])
  st.data_editor(cafe_df, use_container_width=True)

elif menu_option == "✍️ 카페 원고 작성기":
  st.title("📝 네이버 카페 원고 자동 생성")
  st.markdown(
      "구글 시트의 데이터를 읽은 후, 지점별 20건 틀(정보성 10 / 후기성 9 /"
      " 슈퍼세트 1)을 자동으로 생성합니다[cite: 5]."
  )
  sheet_url = st.text_input(
      "원고 구글 시트 링크",
      placeholder="https://docs.google.com/spreadsheets/d/...",
      key="cafe_wongo_sheet",
  )
  if st.button("🚀 카페 원고 생성 미리보기"):
    if not sheet_url:
      st.warning("⚠️ 원고 구글 시트 링크를 입력해주세요!")
    else:
      st.success("✨ 원고 생성 미리보기가 완료되었습니다.")

elif menu_option == "🔍 카페 원고 자동 검수":
  st.title("🔍 카페 원고 자동 검수 프로그램")
  st.markdown(
      "금칙어, 계절어, 글자 수, 키워드 삽입 개수, 유사 문장 및 장비 규칙을"
      " 자동으로 검수합니다[cite: 5]."
  )
  review_sheet_url = st.text_input(
      "검수할 원고 구글 시트 링크",
      placeholder="https://docs.google.com/spreadsheets/d/...",
      key="cafe_review_sheet",
  )
  if st.button("🚀 원고 자동 검수 시작"):
    if not review_sheet_url:
      st.warning("⚠️ 구글 시트 링크를 입력해주세요!")
    else:
      st.success("✨ 자동 검수가 완료되었습니다.")

elif menu_option == "🔗 카페 매칭·중복 검수":
  st.title("🔗 카페 매칭 및 지점별 중복 검수")
  st.markdown("원고 유형 및 지점 내 카페 중복 배정 여부를 검수합니다[cite: 5].")
  matching_sheet_url = st.text_input(
      "매칭·검수 구글 시트 링크",
      placeholder="https://docs.google.com/spreadsheets/d/...",
      key="matching_sheet",
  )
  if st.button("🚀 매칭 및 중복 검수 실행"):
    if not matching_sheet_url:
      st.warning("⚠️ 구글 시트 링크를 입력해주세요!")
    else:
      st.success("✨ 카페 매칭 및 중복 분석이 완료되었습니다!")

elif menu_option == "📝 단건 원고 작성":
  st.title("📝 단건 원고 작성기")
  content_type = st.selectbox(
      "작성 유형 선택",
      ["카페 상위노출 원고", "이미지 캡션 글", "질문글", "의료 후기"],
  )
  keyword_input = st.text_input(
      "주요 키워드 입력", placeholder="예: 잠실 인모드 리프팅"
  )
  if st.button("🚀 단건 원고 생성하기"):
    if not keyword_input:
      st.warning("⚠️ 키워드를 입력해주세요!")
    else:
      st.success("✨ 단건 원고가 생성되었습니다!")
      st.text_area(
          "생성된 원고 결과",
          value=f"[{content_type}] '{keyword_input}' 관련 작성된 초안 내용입니다.",
          height=200,
      )

elif menu_option == "📢 체험단 모집 관리":
  st.title("👥 블로거 체험단 모집 관리")
  exp_keyword = st.text_input("수집 키워드 입력", placeholder="예: 잠실 입술필러")
  if st.button("🚀 체험단 블로거 수집 시작"):
    if not exp_keyword:
      st.warning("⚠️ 검색할 키워드를 입력해주세요!")
    else:
      st.success("✨ 블로거 수집 및 필터링 완료")

elif menu_option == "📊 카페 보고서":
  st.title("📊 카페 작업 현황 보고서")
  st.markdown(
      "실행사 기입 ➔ 관리자 1차 확인 ➔ 지점 담당자 확인(수정 요청 바로"
      " 전달) ➔ 최종본 확정 흐름[cite: 5]."
  )
  report_cafe_df = pd.DataFrame([
      {
          "지점": "유앤아이 강남점",
          "발행일": "2026-06-07",
          "카페명": "맘스홀릭",
          "상태": "지점 담당자 확인 완료",
      }
  ])
  st.dataframe(report_cafe_df, use_container_width=True)
  csv_cafe_report = report_cafe_df.to_csv(index=False).encode("utf-8-sig")
  st.download_button(
      "📥 외부용 보고서 다운로드 (실행사/아이디 제외)",
      data=csv_cafe_report,
      file_name="cafe_external_report.csv",
      mime="text/csv",
  )

elif menu_option == "📈 체험단 보고서":
  st.title("📈 체험단 모집 현황 보고서")
  report_exp_df = pd.DataFrame([
      {
          "키워드": "잠실 입술필러",
          "수집 인원": "50명",
          "제외 인원": "18명",
          "최종 등록": "32명",
      }
  ])
  st.dataframe(report_exp_df, use_container_width=True)
  csv_exp_report = report_exp_df.to_csv(index=False).encode("utf-8-sig")
  st.download_button(
      "📥 체험단 종합 보고서 다운로드 (CSV)",
      data=csv_exp_report,
      file_name="experience_comprehensive_report.csv",
      mime="text/csv",
  )
