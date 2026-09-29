import time
import pandas as pd
import streamlit as st

# 웹페이지 기본 설정
st.set_page_config(
    page_title="마케팅 통합 관리 프로그램", page_icon="🚀", layout="wide"
)

# 세션 스테이트 초기화
if "menu_option" not in st.session_state:
  st.session_state.menu_option = "🏠 홈 (대시보드)"
if "current_month" not in st.session_state:
  st.session_state.current_month = "2026년 6월"
if "user_ role" not in st.session_state:
  st.session_state.user_role = "관리자"

role = "관리자"  # 1단계 관리자 중심 기본 구동

# =========================================================
# 사이드바 메뉴 구성 (2차 구성안 반영: 체험단 숨김, 원고보드/댓글침투 추가)
# =========================================================
st.sidebar.title("📌 통합 대시보드")
st.sidebar.markdown("---")

st.sidebar.markdown(f"📅 **운영 월 선택**: `{st.session_state.current_month}`")
if st.sidebar.button("🔄 [다음 달 시작] 이월 및 틀 생성", use_container_width=True):
  st.sidebar.success(
      "✨ 다음 달로 이월 및 지점별 20건 틀이 생성되었습니다[cite: 9]!"
  )

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
menu_btn("🏠 홈 (대시보드)", "🏠 홈 (대시보드)")
menu_btn("🏢 지점 및 장비 관리", "🏢 지점 및 장비 관리")
menu_btn("☕ 카페 목록 관리", "☕ 카페 목록 관리")
menu_btn("📋 원고 보드 (작성·검수·컨펌)", "📋 원고 보드")
menu_btn("💬 댓글 침투 관리", "💬 댓글 침투 관리")
menu_btn("📝 단건 원고 작성", "📝 단건 원고 작성")
op_role = st.sidebar.selectbox(
    "🔒 발행/운영 권한 선택", ["관리자/담당자", "실행사 전용 화면"]
)
if op_role == "실행사 전용 화면":
  menu_btn("🚀 실행사 발행 및 AS 관리", "🚀 실행사 발행 및 AS 관리")
else:
  menu_btn("📊 통합 작업 현황 보고서", "📊 통합 보고서")

st.sidebar.markdown("---")
st.sidebar.caption("🚀 마케팅 통합 관리 프로그램 v2.0 (시트 연동 제거 버전)")

menu_option = st.session_state.menu_option


# =========================================================
# 1. 홈 (대시보드) 화면
# =========================================================
if menu_option == "🏠 홈 (대시보드)":
  st.title("🏠 마케팅 통합 관리 홈 (대시보드)")
  st.markdown(
      f"현재 운영 월: **{st.session_state.current_month}** | 블루비뇨기과"
      " 스타일 전체 현황판[cite: 9]"
  )

  col1, col2, col3, col4 = st.columns(4)
  col1.metric("이번 달 목표 원고", "880건", "진행중")
  col2.metric("작성 완료", "640건", "+45건")
  col3.metric("검수 대기 / 위반", "12건", "-3건")
  col4.metric("절약된 시간", "142시간", "자동 집계")

  st.markdown("---")
  st.subheader("📌 지점별 진행상황 및 유형별 피드백 현황")

  status_board_df = pd.DataFrame([
      {
          "지점명": "유앤아이 강남점",
          "담당자": "김담당",
          "작가": "김작가",
          "진행상황": "20 / 20",
          "정보성(10)": "완료",
          "후기성(9)": "검수 대기",
          "슈퍼세트(1)": "작성 중",
      },
      {
          "지점명": "블루비뇨기과 신촌점",
          "담당자": "박담당",
          "작가": "이작가",
          "진행상황": "18 / 20",
          "정보성(10)": "완료",
          "후기성(9)": "피드백",
          "슈퍼세트(1)": "완료",
      },
  ])
  st.dataframe(status_board_df, use_container_width=True)


# =========================================================
# 2. 지점 및 장비 관리 화면
# =========================================================
elif menu_option == "🏢 지점 및 장비 관리":
  st.title("🏢 지점 및 보유 장비 관리")
  st.markdown(
      "병원 구분(유앤아이/블루비뇨기과/로컬), 원고 재료 칸(장비 비고 규칙,"
      " 금지 주제 등)을 관리합니다[cite: 9]."
  )

  branch_setting_df = pd.DataFrame([
      {
          "지점명": "유앤아이 강남점",
          "병원 구분": "유앤아이",
          "보유 장비 / 재료": "영국산 보톡스, 슈링크",
          "지점별 주의사항": "특정 수술 언급 금지",
      },
      {
          "지점명": "블루비뇨기과 신촌점",
          "병원 구분": "블루비뇨기과",
          "보유 장비 / 재료": "I-MOVE 쇄석기",
          "지점별 주의사항": "정관수술, 포경수술 등 수술은 진행하지 않음[cite: 9]",
      },
  ])
  st.data_editor(branch_setting_df, use_container_width=True)


# =========================================================
# 3. 카페 목록 관리 화면
# =========================================================
elif menu_option == "☕ 카페 목록 관리":
  st.title("☕ 카페 목록 및 지점·댓글침투용 연결 관리")
  st.markdown(
      "카페 유형(2030뷰티/맘/지역맘/남성), 단가, 상태(진행 가능/주의/위험) 및"
      " 댓글침투용 여부를 관리합니다[cite: 9]."
  )

  cafe_manage_df = pd.DataFrame([
      {
          "카페명": "맘스홀릭 베이비",
          "유형": "맘",
          "규모": "대형",
          "단가": "25,000원",
          "상태": "진행 가능",
          "댓글침투용": "O",
      },
      {
          "카페명": "여우야",
          "유형": "2030뷰티",
          "규모": "대형",
          "단가": "기본",
          "상태": "주의",
          "댓글침투용": "O",
      },
  ])
  st.data_editor(cafe_manage_df, use_container_width=True)


# =========================================================
# 4. 원고 보드 (작성·검수·컨펌 통합) 화면
# =========================================================
elif menu_option == "📋 원고 보드":
  st.title("📋 통합 원고 보드 (작성·자동 검수·컨펌)")
  st.markdown(
      "시트 없이 프로그램 안에서 월별·지점별 20건 틀을 관리하고, 저장 시"
      " 자동 검수(금칙어, 장비규칙, 지난 3개월 중복 검사)가 바로"
      " 실행됩니다[cite: 9]."
  )

  col_s1, col_s2 = st.columns(2)
  with col_s1:
    sel_branch = st.selectbox(
        "지점 선택", ["유앤아이 강남점", "블루비뇨기과 신촌점"]
    )
  with col_s2:
    sel_type = st.selectbox(
        "원고 유형 필터", ["전체 보기", "정보성", "후기성", "슈퍼세트"]
    )

  st.markdown("---")
  st.subheader(f"📌 [{sel_branch}] 월별 20건 원고 목록")

  wongo_board_df = pd.DataFrame([
      {
          "행": 1,
          "유형": "정보성",
          "제목": "환절기 피부 관리 꿀팁 총정리",
          "작성자": "김작가",
          "상태": "완료",
          "자동검수 결과": "이상 없음 (정상)",
          "중복 검사": "통과",
      },
      {
          "행": 2,
          "유형": "후기성",
          "제목": "내돈내산 솔직 후기 공유해요",
          "작성자": "김작가",
          "상태": "피드백",
          "자동검수 결과": "장비 규칙 위반 (미보유 장비 언급)",
          "중복 검사": "유사 문장 발견",
      },
      {
          "행": 20,
          "유형": "슈퍼세트",
          "제목": "종합 패키지 안내",
          "작성자": "김작가",
          "상태": "검수 대기",
          "자동검수 결과": "검수 대기 중",
          "중복 검사": "대기",
      },
  ])
  edited_board = st.data_editor(wongo_board_df, use_container_width=True)

  if st.button("🚀 선택 원고 저장 및 자동 검수 즉시 실행"):
    st.success(
        "✨ 원고가 저장되었으며, 자동 검수 및 지난 3개월 유사 문장 검사가"
        " 완료되었습니다[cite: 9]!"
    )


# =========================================================
# 5. 댓글 침투 관리 화면
# =========================================================
elif menu_option == "💬 댓글 침투 관리":
  st.title("💬 댓글 침투 대상 글 수집 및 관리")
  st.markdown(
      "자동 수집된 대상 글 또는 실행사가 직접 추가한 링크를 바탕으로 지점별"
      " 댓글 침투 작업을 관리합니다[cite: 9]."
  )

  tab1, tab2 = st.tabs(["📌 대상 글 목록", "➕ 직접 링크 추가"])

  with tab1:
    comment_target_df = pd.DataFrame([
        {
            "지점명": "블루비뇨기과 신촌점",
            "키워드": "남성수술",
            "카페명": "여우야",
            "게시글 제목": "여기 후기 좀 알려주세요",
            "댓글 가능 여부": "가능",
            "수집일시": "2026-06-07 14:00",
        }
    ])
    st.dataframe(comment_target_df, use_container_width=True)

  with tab2:
    st.text_input("지점 및 키워드 설정")
    direct_url = st.text_input(
        "카페 게시글 URL 입력 (붙여넣으면 카페명·ID 자동 채움)"
    )
    if st.button("➕ 댓글 침투 대상 추가"):
      if direct_url:
        st.success("✨ 정상적으로 등록되었습니다 (중복 URL 자동 차단)[cite: 9].")
      else:
        st.warning("URL을 입력해주세요.")


# =========================================================
# 6. 단건 원고 작성 화면
# =========================================================
elif menu_option == "📝 단건 원고 작성":
  st.title("📝 단건 원고 작성기")
  st.markdown(
      "시트 없이 필요할 때 바로 카페 상위노출 원고, 이미지 캡션 글, 질문글,"
      " 의료 후기 등을 생성합니다[cite: 9]."
  )

  single_type = st.selectbox(
      "작성 유형",
      ["카페 상위노출 원고", "이미지 캡션 글", "질문글", "의료 후기"],
  )
  keyword_box = st.text_input(
      "주요 키워드 입력", placeholder="예: 강남 인모드 리프팅"
  )

  if st.button("🚀 단건 원고 생성하기"):
    if keyword_box:
      st.success("✨ 단건 원고 초안이 생성되었습니다.")
      st.text_area(
          "생성 결과 복사",
          value=f"[{single_type}] '{keyword_box}' 관련 초안 내용입니다.",
          height=180,
      )
    else:
      st.warning("키워드를 입력해주세요.")


# =========================================================
# 7. 실행사 발행 및 AS 관리 화면 (계정 사용 체크 포함)
# =========================================================
elif menu_option == "🚀 실행사 발행 및 AS 관리":
  st.title("🚀 실행사 발행 및 AS / 계정 사용 관리")
  st.markdown(
      "카페 침투·댓글 침투 발행, 계정 사용 체크(10일/40개 제한), 그리고 발행 후"
      " AS(삭제·댓글 미완료·조회수 부족)를 관리합니다[cite: 9]."
  )

  tab_ex1, tab_ex2, tab_ex3 = st.tabs(
      ["☕ 카페/댓글 발행", "🔒 계정 사용 체크", "🛠️ 발행 후 AS 관리"]
  )

  with tab_ex1:
    st.subheader("📌 발행 완료 기입 (보고서 연동)")
    pub_df = pd.DataFrame([{
        "지점": "유앤아이 강남점",
        "카페명": "맘스홀릭",
        "사용 계정": "id_001",
        "제목": "환절기 관리",
        "침투 URL": "https://cafe.naver.com/...",
        "상태": "기입 완료",
    }])
    st.data_editor(pub_df, use_container_width=True)
    if st.button("📤 지점 단위 '기입 완료 확인 요청' 전송"):
      st.success("✨ 지점 담당자에게 확인 요청이 전달되었습니다[cite: 9]!")

  with tab_ex2:
    st.subheader("🔒 계정 사용 가능 여부 자동 체크")
    st.info(
        "💡 카페 침투: 동일 계정+동일 카페 10일 이내 발행 금지 | 댓글 침투:"
        " 한 계정 한 달 40개 제한[cite: 9]"
    )
    acc_check_df = pd.DataFrame([
        {
            "계정 아이디": "id_001",
            "대상 카페": "맘스홀릭",
            "규칙 확인": "사용 가능 (11일 경과)",
            "댓글 남은 개수": "잔여 12개 (주의)",
        }
    ])
    st.dataframe(acc_check_df, use_container_width=True)

  with tab_ex3:
    st.subheader("🛠️ 발행 후 AS 목록 (삭제·댓글 미완료·조회수 부족)")
    as_df = pd.DataFrame([
        {
            "링크": "https://cafe.naver.com/...",
            "상태 감지": "댓글 작업 미완료 (댓글 2개)",
            "조치 단계": "실행사 AS (재작업 필요)",
        }
    ])
    st.dataframe(as_df, use_container_width=True)


# =========================================================
# 8. 통합 보고서 화면
# =========================================================
elif menu_option == "📊 통합 보고서":
  st.title("📊 통합 작업 현황 보고서 및 컨펌 흐름")
  st.markdown(
      "실행사 기입 ➔ 관리자 1차 확인 ➔ 지점 담당자 확인(수정 요청 바로"
      " 전달) ➔ 관리자 최종본 확정 흐름을 관리합니다[cite: 9]."
  )

  report_main_df = pd.DataFrame([
      {
          "지점": "유앤아이 강남점",
          "발행일": "2026-06-07",
          "카페명": "맘스홀릭",
          "상태": "지점 담당자 확인 완료 (이상 없음)",
      },
      {
          "지점": "블루비뇨기과 신촌점",
          "발행일": "2026-06-07",
          "카페명": "세클맘",
          "상태": "수정 요청 진행 중 (실행사 반영 대기)",
      },
  ])
  st.dataframe(report_main_df, use_container_width=True)

  csv_export = report_main_df.to_csv(index=False).encode("utf-8-sig")
  st.download_button(
      "📥 외부용 최종 보고서 다운로드 (실행사·계정 아이디 자동 제외)",
      data=csv_export,
      file_name="external_final_report.csv",
      mime="text/csv",
  )
