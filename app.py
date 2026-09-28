import time
import gspread
import pandas as pd
import streamlit as st

# 웹페이지 기본 설정
st.set_page_config(
    page_title="마케팅 자동화 프로그램", page_icon="🚀", layout="wide"
)

# 세션 스테이트 초기화
if "menu_option" not in st.session_state:
  st.session_state.menu_option = "🏠 홈"
if "preview_data" not in st.session_state:
  st.session_state.preview_data = None
if "action_type" not in st.session_state:
  st.session_state.action_type = None
if "user_role" not in st.session_state:
  st.session_state.user_role = "관리자"

# =========================================================
# 사이드바 메뉴 및 권한(역할) 설정
# =========================================================
st.sidebar.title("📌 통합 대시보드")
st.sidebar.markdown("---")

# 6가지 권한 역할 지정 (이미지 표 기준)[cite: 5]
st.sidebar.markdown("🔒 **사용자 권한(역할)**")
st.session_state.user_role = st.sidebar.selectbox(
    "현재 접속자 역할",
    [
        "관리자",
        "지점 담당자 (유앤아이·블루비뇨기과)",
        "원고 작가",
        "게시판 담당",
        "실행사 (1곳)",
        "원장님 (로컬 지점)",
    ],
    index=0,
    key="role_select",
)

role = st.session_state.user_role

# 권한별 보는 범위 안내[cite: 5]
scope_dict = {
    "관리자": "전체 보기 (배정, 컨펌, 기준 정보 관리)",
    "지점 담당자 (유앤아이·블루비뇨기과)": "담당 지점만 (보유장비 수정, 키워드 입력)",
    "원고 작가": "배정된 원고만 (작성 및 피드백 반영)",
    "게시판 담당": "배정된 업로드 건 (업로드 완료 처리)",
    "실행사 (1곳)": "완료된 원고 및 자기가 기입한 보고서",
    "원장님 (로컬 지점)": "해당 지점 원고만 (확인 또는 수정 요청)",
}
st.sidebar.info(f"📌 **보는 범위**: {scope_dict[role]}")
st.sidebar.markdown("---")


# 메뉴 버튼 렌더링 함수
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

# 역할별 접근 가능 메뉴 제어 (원장님 역할은 홈 제외[cite: 5])
if role == "관리자":
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

elif role == "지점 담당자 (유앤아이·블루비뇨기과)":
  menu_btn("🏠 홈 (대시보드)", "🏠 홈")
  menu_btn("🏢 지점 및 장비 관리", "🏢 지점 및 장비 관리")
  menu_btn("✍️ 카페 원고 작성기", "✍️ 카페 원고 작성기")
  menu_btn("📊 카페 작업 현황 보고서", "📊 카페 보고서")

elif role == "원고 작가":
  menu_btn("🏠 홈 (대시보드)", "🏠 홈")
  menu_btn("✍️ 카페 원고 작성기", "✍️ 카페 원고 작성기")
  menu_btn("📝 단건 원고 작성", "📝 단건 원고 작성")

elif role == "게시판 담당":
  menu_btn("🏠 홈 (대시보드)", "🏠 홈")
  menu_btn("🔗 카페 매칭·중복 검수", "🔗 카페 매칭·중복 검수")

elif role == "실행사 (1곳)":
  menu_btn("🏠 홈 (대시보드)", "🏠 홈")
  menu_btn("📊 카페 작업 현황 보고서", "📊 카페 보고서")

elif role == "원장님 (로컬 지점)":
  # 원장님 역할은 홈(대시보드) 메뉴를 제외하고 보고서/확인 링크 화면만 제공[cite: 5]
  if st.session_state.menu_option == "🏠 홈":
    st.session_state.menu_option = "📊 카페 보고서"
  menu_btn("📊 카페 작업 현황 보고서", "📊 카페 보고서")

st.sidebar.markdown("---")
st.sidebar.caption("🚀 마케팅 통합 관리 프로그램 v1.0")

menu_option = st.session_state.menu_option


# =========================================================
# 화면 분기 및 렌더링 (권한별 제한 반영)
# =========================================================
if menu_option == "🏠 홈":
  st.title("🏠 마케팅 통합 관리 홈 (대시보드)")
  st.markdown(
      f"현재 접속 권한: **{role}** | 💡 모든 화면에 '내 담당만 보기' 필터가"
      f" 적용되어 있습니다[cite: 5]."
  )

  col1, col2, col3 = st.columns(3)
  col1.metric("이번 달 목표 원고", "880건", "진행중")
  col2.metric("작성 완료", "640건", "+45건")
  col3.metric("검수 대기 / 위반", "12건", "-3건")

  st.markdown("---")
  st.subheader("📌 내 할 일 (담당 범위 기준)")
  st.info(f"현재 '{role}' 역할이 처리해야 할 항목만 필터링되었습니다.")

  task_df = pd.DataFrame([{
      "지점": "유앤아이 강남점",
      "작업 구분": "원고 작성 및 확인",
      "상태": "진행 중",
  }])
  st.dataframe(task_df, use_container_width=True)

elif menu_option == "🏢 지점 및 장비 관리":
  st.title("🏢 지점 및 보유 장비 관리")
  if role == "지점 담당자 (유앤아이·블루비뇨기과)":
    st.success(
        "💡 지점 담당자 권한으로 접속하여 **보유장비 수정 및 월별 키워드 입력**이"
        " 가능합니다[cite: 5]."
    )
  branch_df = pd.DataFrame([{
      "지점명": "유앤아이 강남점",
      "구분": "유앤아이",
      "보유 장비": "영국산 보톡스, 슈링크",
  }])
  st.data_editor(branch_df, use_container_width=True)

elif menu_option == "☕ 카페 목록 관리":
  st.title("☕ 카페 목록 관리")
  st.warning(
      "🔒 **관리자 전용 메뉴**: 카페 단가 및 실행사 연동 정보는 관리자만"
      " 볼 수 있습니다[cite: 5]."
  )
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
    if role == "원고 작가":
      st.success("✨ 작가 권한으로 원고 작성 및 피드백 반영 완료[cite: 5]!")
    else:
      st.success("✨ 원고 자동 생성이 완료되었습니다.")

elif menu_option == "🔍 카페 원고 자동 검수":
  st.title("🔍 카페 원고 자동 검수 프로그램")
  st.text_input("검수할 원고 구글 시트 링크")
  if st.button("🚀 자동 검수 시작"):
    st.success("✨ 금칙어 및 장비 규칙 자동 검수 완료")

elif menu_option == "🔗 카페 매칭·중복 검수":
  st.title("🔗 카페 매칭 및 지점별 중복 검수")
  if role == "게시판 담당":
    st.info("💡 게시판 담당 권한: 배정된 업로드 건의 적합성을 검수합니다.")
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

  # 실행사 비공개 원칙 적용 (실행사 화면 및 외부 보고서에는 단가/아이디 등 숨김)[cite: 5]
  if role == "실행사 (1곳)":
    st.warning(
        "🔒 **실행사 보안 원칙 적용**: 발행 처리, 보고서 기입, 수정 요청 처리"
        " 기능만 노출됩니다 (내부 메모 및 병원 민감 정보 숨김)[cite: 5]."
    )
    report_df = pd.DataFrame([{
        "발행일": "2026-06-07",
        "카페명": "맘스홀릭",
        "상태": "보고서 기입 완료",
    }])
  elif role == "원장님 (로컬 지점)":
    st.info(
        "💡 **원장님 전용 확인 링크 화면**: 로그인 없이 해당 지점 원고에 대한"
        " 확인 또는 수정 요청만 가능합니다[cite: 5]."
    )
    report_df = pd.DataFrame(
        [{"지점": "로컬 지점", "상태": "원장님 컨펌 대기중"}]
    )
  else:
    report_df = pd.DataFrame([{
        "지점": "유앤아이 강남점",
        "발행일": "2026-06-07",
        "카페명": "맘스홀릭",
        "상태": "지점 담당자 확인 완료",
    }])

  st.dataframe(report_df, use_container_width=True)

  # 외부용 다운로드 (실행사/아이디 자동 제외 버전)[cite: 5]
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
