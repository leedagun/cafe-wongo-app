import time
import pandas as pd
import streamlit as st

# 웹페이지 기본 설정
st.set_page_config(
    page_title="마케팅 자동화 프로그램", page_icon="🚀", layout="wide"
)

# 세션 스테이트 초기화
if "menu_option" not in st.session_state:
  st.session_state.menu_option = "🏠 홈 (대시보드)"
if "current_month" not in st.session_state:
  st.session_state.current_month = "2026년 10월"
if "user_role" not in st.session_state:
  st.session_state.user_role = "관리자"

# =========================================================
# 사이드바 메뉴 및 권한(역할) 설정
# =========================================================
st.sidebar.title("📌 통합 대시보드")
st.sidebar.markdown("---")

st.sidebar.markdown(f"📅 **운영 월 선택**: `{st.session_state.current_month}`")
if st.sidebar.button("🔄 [다음 달 시작] 이월 및 틀 생성", use_container_width=True):
  st.sidebar.success("다음 달로 이월 및 지점별 20건 틀이 생성되었습니다.")

if st.sidebar.button("📥 배정 시트에서 지점 담당자 자동 동기화", use_container_width=True):
  st.sidebar.success("배정 시트 연동 완료: 변경 8건 반영")

st.sidebar.markdown("---")

# 사용자 권한(역할) 선택 영역
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

# 역할별 메뉴 제한 설정
if role == "관리자":
  menu_btn("🏠 홈 (대시보드)", "🏠 홈 (대시보드)")
  menu_btn("🏢 지점 및 장비 관리", "🏢 지점 및 장비 관리")
  menu_btn("☕ 카페 목록 관리", "☕ 카페 목록 관리")
  menu_btn("📋 원고 보드 (작성·검수·컨펌)", "📋 원고 보드")
  menu_btn("💬 댓글 침투 관리", "💬 댓글 침투 관리")
  menu_btn("🎨 AI 이미지 보관함", "🎨 AI 이미지 보관함")
  menu_btn("📝 단건 원고 작성", "📝 단건 원고 작성")
  menu_btn("🚀 실행사 발행 및 AS 관리", "🚀 실행사 발행 및 AS 관리")
  menu_btn("📊 통합 작업 현황 보고서", "📊 통합 보고서")

elif role == "지점 담당자 (유앤아이·블루비뇨기과)":
  menu_btn("🏠 홈 (대시보드)", "🏠 홈 (대시보드)")
  menu_btn("🏢 지점 및 장비 관리", "🏢 지점 및 장비 관리")
  menu_btn("📊 통합 작업 현황 보고서", "📊 통합 보고서")

elif role == "원고 작가":
  if st.session_state.menu_option not in [
      "📋 원고 보드",
      "🎨 AI 이미지 보관함",
      "📝 단건 원고 작성",
  ]:
    st.session_state.menu_option = "📋 원고 보드"
  menu_btn("📋 원고 보드 (작성·검수·컨펌)", "📋 원고 보드")
  menu_btn("🎨 AI 이미지 보관함", "🎨 AI 이미지 보관함")
  menu_btn("📝 단건 원고 작성", "📝 단건 원고 작성")

elif role == "게시판 담당":
  if st.session_state.menu_option not in ["🏠 홈 (대시보드)", "📋 원고 보드"]:
    st.session_state.menu_option = "🏠 홈 (대시보드)"
  menu_btn("🏠 홈 (대시보드)", "🏠 홈 (대시보드)")
  menu_btn("📋 원고 보드 (작성·검수·컨펌)", "📋 원고 보드")

elif role == "실행사 (1곳)":
  if st.session_state.menu_option not in [
      "🏠 홈 (대시보드)",
      "💬 댓글 침투 관리",
      "🎨 AI 이미지 보관함",
      "🚀 실행사 발행 및 AS 관리",
      "📊 통합 보고서",
  ]:
    st.session_state.menu_option = "🚀 실행사 발행 및 AS 관리"
  menu_btn("🏠 홈 (대시보드)", "🏠 홈 (대시보드)")
  menu_btn("💬 댓글 침투 관리", "💬 댓글 침투 관리")
  menu_btn("🎨 AI 이미지 보관함", "🎨 AI 이미지 보관함")
  menu_btn("🚀 실행사 발행 및 AS 관리", "🚀 실행사 발행 및 AS 관리")
  menu_btn("📊 통합 작업 현황 보고서", "📊 통합 보고서")

elif role == "원장님 (로컬 지점)":
  if st.session_state.menu_option != "📊 통합 보고서":
    st.session_state.menu_option = "📊 통합 보고서"
  menu_btn("📊 통합 작업 현황 보고서", "📊 통합 보고서")

st.sidebar.markdown("---")
st.sidebar.caption("🚀 마케팅 통합 관리 프로그램 v2.2")

menu_option = st.session_state.menu_option


# =========================================================
# 화면 분기 및 렌더링
# =========================================================
if menu_option == "🏠 홈 (대시보드)":
  st.title("🏠 마케팅 통합 관리 홈 (대시보드)")
  st.markdown(
      f"현재 운영 월: **{st.session_state.current_month}** | 접속 역할: **{role}**"
  )

  # 상단 긴급 확인 줄 (구성안 반영)
  st.markdown("🚨 **[지금 확인할 것]**")
  col_chk1, col_chk2, col_chk3, col_chk4 = st.columns(4)
  col_chk1.metric("키워드 미입력 지점", "2곳", "확인 필요")
  col_chk2.metric("피드백 대기", "6건", "확인 필요")
  col_chk3.metric("마감 임박 건", "3건", "긴급")
  col_chk4.metric("AS 대기 건", "1건", "확인 필요")

  st.markdown("---")
  st.subheader("📌 담당자별 진행 현황")
  st.markdown(
      "지점 50개를 담당자 8명 기준으로 묶어 카드 형태로 진행률을 보여줍니다."
  )

  # 담당자 카드 그리드 뷰 시뮬레이션
  c1, c2, c3, c4 = st.columns(4)
  with c1:
    st.info("**박윤지**\n\n- 담당 지점: 8곳\n- 진행률: 150/160 (93%)\n- 상태: 정상")
  with c2:
    st.warning(
        "**김민지**\n\n- 담당 지점: 6곳\n- 진행률: 95/120 (79%)\n- 상태:"
        " 주의"
    )
  with c3:
    st.info("**이유진**\n\n- 담당 지점: 5곳\n- 진행률: 100/100 (100%)\n- 상태: 완료")
  with c4:
    st.info("**신지명**\n\n- 담당 지점: 7곳\n- 진행률: 130/140 (92%)\n- 상태: 정상")
  st.markdown("---")
  st.subheader("📌 상세 전체 현황 탭 뷰")
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


elif menu_option == "🏢 지점 및 장비 관리":
  st.title("🏢 지점 및 보유 장비 관리")
  st.markdown(
      "보유 장비 사전 관리 및 원고 재료 칸(발행 요청사항, 경쟁사 대비 장점,"
      " 지점별 주의사항)을 관리합니다."
  )

  branch_setting_df = pd.DataFrame([
      {
          "지점명": "유앤아이 강남점",
          "보유 장비": "영국산 보톡스, 슈링크",
          "발행 요청사항": "자연스러운 볼륨감 강조",
          "주의사항": "과장 광고 문구 금지",
      },
      {
          "지점명": "블루비뇨기과 신촌점",
          "보유 장비": "I-MOVE 쇄석기",
          "발행 요청사항": "전문적인 비뇨기 진료 강조",
          "주의사항": "정관수술, 포경수술 등 수술은 진행하지 않음",
      },
  ])
  st.data_editor(branch_setting_df, use_container_width=True)


elif menu_option == "☕ 카페 목록 관리":
  st.title("☕ 카페 목록 및 지점·댓글침투용 연결 관리")
  st.markdown(
      "카페 유형(2030뷰티/맘/지역맘/남성), 단가, 상태(진행 가능/주의/위험) 및"
      " 댓글침투용 여부를 관리합니다."
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
          "상태": "주의 (삭제율 높음)",
          "댓글침투용": "O",
      },
  ])
  st.data_editor(cafe_manage_df, use_container_width=True)


elif menu_option == "📋 원고 보드":
  st.title("📋 통합 원고 보드 (작성·자동 검수·컨펌)")
  st.markdown(
      "원고 작성 전 지점 담당자가 키워드, 보유장비, 특이사항 등 원고 재료를"
      " 먼저 입력한 뒤 작가가 작성하며, 저장 시 자동 검수 및 지난 3개월 유사"
      " 문장 검사가 실행됩니다."
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
  st.subheader(f"📌 [{sel_branch}] 원고 재료 입력 및 20건 원고 보드")

  with st.expander("📝 지점 담당자 원고 재료 입력 칸 펼치기"):
    st.text_input("이번 달 키워드 취합 입력")
    st.selectbox("지점 보유 장비 선택", ["영국산 보톡스", "슈링크", "I-MOVE 쇄석기"])
    st.text_area("특이사항 및 발행 요청사항 입력")
    st.button("💾 원고 재료 저장 (작가에게 전달)")

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
          "자동검수 결과": "장비 규칙 위반",
          "중복 검사": "지난 3개월 원고와 유사 문장 발견",
      },
  ])
  st.data_editor(wongo_board_df, use_container_width=True)

  if st.button("🚀 선택 원고 저장 및 자동 검수 즉시 실행"):
    st.success("원고가 저장되었으며, 자동 검수 및 중복 검사가 완료되었습니다.")


elif menu_option == "💬 댓글 침투 관리":
  st.title("💬 댓글 침투 대상 글 수집 및 관리")
  st.markdown(
      "자동 수집된 대상 글 또는 실행사가 직접 추가한 링크를 바탕으로 지점별"
      " 댓글 침투 작업을 관리합니다."
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
            "수집일시": "2026-10-01 14:00",
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
        st.success("정상적으로 등록되었습니다 (중복 URL 자동 차단).")
      else:
        st.warning("URL을 입력해주세요.")


elif menu_option == "🎨 AI 이미지 보관함":
  st.title("🎨 AI 이미지 보관함 및 원고 배치 관리")
  st.markdown(
      "이미지 앱 1·2차 검수를 거친 뒤 프로그램 보관함으로 들어온 최종"
      " 컨펌본을 관리하고, 시술별 분류 및 자동 파일명(시술명+번호) 부여를"
      " 지원합니다."
  )

  img_tab1, img_tab2 = st.tabs(["📦 AI 이미지 보관함", "🔗 원고별 이미지 배치"])

  with img_tab1:
    st.subheader("📌 최종 컨펌 이미지 보관함 (시술별 분류 및 자동 명칭)")
    uploaded_files = st.file_uploader(
        "이미지 파일 업로드 (또는 이미지 앱 연동 연동 대기)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    if uploaded_files:
      st.success(
          f"총 {len(uploaded_files)}개의 이미지가 시술명 자동 분류 및"
          " '시술명+번호' 형태로 보관함에 등록되었습니다."
      )

    img_box_df = pd.DataFrame([
        {
            "자동 파일명": "울쎄라_01.png",
            "시술 분류": "울쎄라",
            "지점": "유앤아이 강남점",
            "상태": "다운로드 대기 중",
        },
        {
            "자동 파일명": "인모드_01.png",
            "시술 분류": "인모드",
            "지점": "블루비뇨기과 신촌점",
            "상태": "다운로드 대기 중",
        },
    ])
    st.dataframe(img_box_df, use_container_width=True)

  with img_tab2:
    st.subheader("📌 원고 항목별 이미지 매칭 및 실행사 일괄 다운로드")
    st.markdown(
        "스마트브랜딩(관리자)이 원고 보드에서 미리보기를 보고 배치하며, 실행사는"
        " 원고 단위로 묶여진 이미지를 한 번에 다운로드합니다. (다운로드 완료 시"
        " 보관함에서 자동 처리)"
    )
    mapping_df = pd.DataFrame([
        {
            "지점": "유앤아이 강남점",
            "원고 제목": "환절기 피부 관리",
            "배치된 이미지": "울쎄라_01.png",
            "다운로드 상태": "실행사 다운로드 대기",
        }
    ])
    st.dataframe(mapping_df, use_container_width=True)


elif menu_option == "📝 단건 원고 작성":
  st.title("📝 단건 원고 작성기")
  st.markdown(
      "시트 없이 필요할 때 바로 카페 상위노출 원고, 이미지 캡션 글, 질문글,"
      " 의료 후기 등을 생성합니다."
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
      st.success("단건 원고 초안이 생성되었습니다.")
      st.text_area(
          "생성 결과 복사",
          value=f"[{single_type}] '{keyword_box}' 관련 초안 내용입니다.",
          height=180,
      )
    else:
      st.warning("키워드를 입력해주세요.")


elif menu_option == "🚀 실행사 발행 및 AS 관리":
  st.title("🚀 실행사 발행 및 AS / 계정 사용 관리")
  st.markdown(
      "카페 침투·댓글 침투 발행, 계정 사용 체크(10일/40개 제한), 그리고 발행 후"
      " AS(삭제·댓글 미완료·조회수 부족)를 관리합니다."
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
      st.success("지점 담당자에게 확인 요청이 전달되었습니다.")

  with tab_ex2:
    st.subheader("🔒 계정 사용 가능 여부 자동 체크")
    st.info(
        "카페 침투: 동일 계정+동일 카페 10일 이내 발행 금지 | 댓글 침투: 한 계정"
        " 한 달 40개 제한"
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


elif menu_option == "📊 통합 보고서":
  st.title("📊 통합 작업 현황 보고서 및 컨펌 흐름")
  st.markdown(
      "보고일에 버튼 하나로 병원별(유앤아이, 블루비뇨기과, 로컬) 구글 시트"
      " 보고서 생성 및 갱신을 수행합니다."
  )

  if st.button("📊 [보고서 만들기] 구글 시트 보고서 생성 및 갱신"):
    st.success(
        "이번 달 데이터로 병원별 구글 시트 보고서가 성공적으로 생성 및"
        " 갱신되었습니다."
    )

  report_main_df = pd.DataFrame([
      {
          "지점": "유앤아이 강남점",
          "발행일": "2026-10-01",
          "카페명": "맘스홀릭",
          "상태": "지점 담당자 확인 완료 (이상 없음)",
      },
      {
          "지점": "블루비뇨기과 신촌점",
          "발행일": "2026-10-01",
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
