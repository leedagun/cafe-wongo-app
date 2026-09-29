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

# 역할별 메뉴 제한 설정 (실행사 메뉴에 카페 계정 관리 추가 반영)
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
st.sidebar.caption("🚀 마케팅 통합 관리 프로그램 v2.4")

menu_option = st.session_state.menu_option


# =========================================================
# 화면 분기 및 렌더링
# =========================================================
if menu_option == "🏠 홈 (대시보드)":
  st.title("🏠 마케팅 통합 관리 홈 (대시보드)")
  st.markdown(
      f"현재 운영 월: **{st.session_state.current_month}** | 접속 역할: **{role}**"
  )

  st.markdown("🚨 **[지금 확인할 것]**")
  col_chk1, col_chk2, col_chk3, col_chk4 = st.columns(4)
  col_chk1.metric("키워드 미입력 지점", "2곳", "확인 필요")
  col_chk2.metric("피드백 대기", "6건", "확인 필요")
  col_chk3.metric("마감 임박 건 (D-2)", "3건", "긴급")
  col_chk4.metric("지연 건 (배지 적용)", "1건", "확인 필요")

  st.markdown("---")
  st.subheader("📌 담당자별 카드 현황 (8명 기준)")
  c1, c2, c3, c4 = st.columns(4)
  with c1:
    st.info("**김담당 (사수)**\n\n- 담당 지점: 8곳\n- 진행률: 150/160 (93%)\n- 상태: 정상")
  with c2:
    st.warning(
        "**박담당 (부사수)**\n\n- 담당 지점: 6곳\n- 진행률: 95/120 (79%)\n- 상태:"
        " 주의 (지연 1일)"
    )
  with c3:
    st.info("**최담당**\n\n- 담당 지점: 5곳\n- 진행률: 100/100 (100%)\n- 상태: 완료")
  with c4:
    st.info("**이지점**\n\n- 담당 지점: 7곳\n- 진행률: 130/140 (92%)\n- 상태: 정상")


elif menu_option == "🏢 지점 및 장비 관리":
  st.title("🏢 지점 및 보유 장비 관리")
  st.markdown(
      "지점명을 2열로 나열하고 장비 분류별(리스트업된 표준 장비)로 묶어 관리합니다"
      "[cite: 13]."
  )

  col_b1, col_b2 = st.columns(2)
  with col_b1:
    st.markdown("### 🏥 유앤아이 강남점 (장비 12개)")
    st.info(
        "**[리프팅]** 울쎄라피 프라임 (수량: 2), 슈링크 유니버스\n\n**[주사"
        " 시술]** 리쥬란, 쥬베룩, 보톡스 (디스포트 명칭 언급x -> 영국산"
        " 보톡스)\n\n**[색소]** 피코플러스, CO2"
    )
  with col_b2:
    st.markdown("### 🏥 블루비뇨기과 신촌점 (장비 5개)")
    st.info(
        "**[기타/특수]** I-MOVE 쇄석기\n\n**[주의사항]** 정관수술, 포경수술 등 수술은"
        " 진행하지 않음[cite: 13]"
    )


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
  st.title("📋 통합 원고 보드 (지점 20세트 상세 화면)")
  st.markdown(
      "한 지점의 20건(정보성 1-10, 후기성 11-19, 슈퍼세트 20)이 한 화면에"
      " 보이고, 오른쪽에서 본문과 대화형 댓글 상세 패널을 확인합니다[cite: 13]."
  )

  view_mode = st.radio(
      "보기 전환", ["📊 표 보기 (20건 일괄 편집)", "☕ 카페 미리보기 (카드 뷰)"], horizontal=True
  )

  col_top1, col_top2 = st.columns([1, 2])
  with col_top1:
    sel_branch = st.selectbox(
        "지점 선택", ["건대점", "유앤아이 강남점", "블루비뇨기과 신촌점"]
    )
    st.markdown(
        "📌 **담당자:** 이선주 | **작가:** 장은하 | **진행상황:** 18 / 20"
        "[cite: 13]"
    )
  with col_top2:
    with st.expander("📝 원고 재료 패널 (접고 펼치기 가능)", expanded=True):
      st.markdown(
          "**발행 요청사항:** 자연스러운 볼륨감 강조 | **경쟁사 대비 장점:** 프라임"
          " 정품 장비 단독 사용[cite: 13]"
      )
      st.markdown(
          "**보유장비 목록:** 울쎄라피 프라임, 슈링크, 리쥬란[cite: 13]"
      )

  st.markdown("---")

  if view_mode == "📊 표 보기 (20건 일괄 편집)":
    col_table, col_detail = st.columns([3, 2])

    with col_table:
      st.subheader("📌 20세트 원고 목록 표")
      wongo_20_df = pd.DataFrame([
          {
              "번호": "1",
              "유형": "정보성",
              "상태": "완료",
              "키워드": "건대 인모드",
              "장비": "인모드",
              "제목": "환절기 건대 인모드 리프팅 총정리",
          },
          {
              "번호": "11",
              "유형": "후기성",
              "상태": "피드백",
              "키워드": "건대 보톡스",
              "장비": "영국산 보톡스",
              "제목": "내돈내산 솔직 후기 공유해요",
          },
          {
              "번호": "20",
              "유형": "슈퍼세트",
              "상태": "검수 대기",
              "키워드": "건대 패키지",
              "장비": "울쎄라",
              "제목": "종합 패키지 안내 (댓글 3쌍)",
          },
      ])
      st.data_editor(wongo_20_df, use_container_width=True)

    with col_detail:
      st.subheader("💬 선택 원고 상세 및 대화형 댓글 패널")
      st.info(
          "**[선택된 원고: 1번 - 정보성]**\n\n- **제목:** 환절기 건대 인모드"
          " 리프팅 총정리\n- **본문 미리보기:** 환절기 피부 탄력이 떨어질 때..."
          " (검수 위반 단어 형광펜 표시)\n\n**[대화형 댓글/대댓글]**\n- 댓글 1:"
          " 정보 감사합니다!\n- 대댓글: 도움이 되셨다니 다행입니다^^[cite: 13]"
      )
      st.markdown("🖼️ **이미지 배치 영역:** 울쎄라_01.png 매칭됨")

  else:
    st.subheader("☕ 카페 미리보기 카드 뷰")
    st.success(
        "실제 네이버 카페 게시글 형태로 렌더링된 카드 뷰 화면입니다. 본문과"
        " 대화형 댓글 구조를 한눈에 확인할 수 있습니다."
    )


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
  st.title("🎨 AI 이미지 보관함 및 썸네일 미리보기")
  st.markdown(
      "이미지 앱 1·2차 검수 후 넘어온 최종 컨펌본을 시술별 분류 및"
      " '시술명+번호' 자동 파일명으로 관리하며, 큰 썸네일 미리보기를"
      " 지원합니다[cite: 13]."
  )

  img_tab1, img_tab2 = st.tabs(["📦 AI 이미지 보관함", "🔗 원고별 이미지 배치"])

  with img_tab1:
    st.subheader("📌 최종 컨펌 이미지 보관함 (썸네일 미리보기 지원)")
    uploaded_files = st.file_uploader(
        "이미지 파일 업로드", type=["png", "jpg", "jpeg"], accept_multiple_files=True
    )
    if uploaded_files:
      st.success("이미지가 시술명 자동 분류 및 자동 파일명으로 등록되었습니다.")

    img_box_df = pd.DataFrame([
        {
            "자동 파일명": "울쎄라_01.png",
            "시술 분류": "리프팅 (울쎄라)",
            "지점": "건대점",
            "상태": "다운로드 대기 중",
        }
    ])
    st.dataframe(img_box_df, use_container_width=True)

  with img_tab2:
    st.subheader("📌 원고 항목별 이미지 매칭 및 실행사 일괄 다운로드")
    mapping_df = pd.DataFrame([
        {
            "지점": "건대점",
            "원고 제목": "환절기 건대 인모드",
            "배치된 이미지": "울쎄라_01.png",
            "상태": "실행사 다운로드 대기",
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
      "주요 키워드 입력", placeholder="예: 건대 인모드 리프팅"
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
  st.title("🚀 실행사 발행 및 AS / 카페 계정 관리")
  st.markdown(
      "실행사가 직접 등록·변경하는 카페 계정 목록 관리, 중복 체크(10일/40개"
      " 제한), 그리고 발행 후 AS를 관리합니다."
  )

  tab_ex1, tab_ex2, tab_ex3, tab_ex4 = st.tabs(
      ["☕ 카페/댓글 발행", "🔒 계정 사용 체크", "👤 카페 계정 목록", "🛠️ 발행 후 AS 관리"]
  )

  with tab_ex1:
    st.subheader(
        "📌 오늘 발행할 지점 목록 (하루 3지점 자동 배정 및 실행사 뷰)"
        "[cite: 13]"
    )
    pub_df = pd.DataFrame([{
        "발행 예정일": "오늘 (D-0)",
        "지점": "건대점",
        "카페명": "맘스홀릭",
        "사용 계정": "id_001",
        "상태": "발행 대기",
    }])
    st.data_editor(pub_df, use_container_width=True)
    if st.button("📤 지점 단위 '기입 완료 확인 요청' 전송"):
      st.success("지점 담당자에게 확인 요청이 전달되었습니다.")

  with tab_ex2:
    st.subheader("🔒 계정 사용 가능 여부 자동 체크")
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
    st.subheader("👤 카페 계정 목록 관리 (실행사 직접 등록 및 변경)")
    st.markdown(
        "실행사가 직접 아이디, 닉네임, 용도, 상태(사용 중/교체됨/제재·정지)를"
        " 관리하며, 동일 아이디 중복 등록을 자동으로 확인합니다."
    )
    account_manage_df = pd.DataFrame([
        {
            "카페 아이디": "id_001",
            "닉네임": "뷰티러버",
            "용도": "카페 침투",
            "상태": "사용 중",
            "메모": "메인 계정",
        },
        {
            "카페 아이디": "id_002",
            "닉네임": "헬스맨",
            "용도": "댓글 침투",
            "상태": "제재·정지",
            "메모": "사용 금지",
        },
    ])
    st.data_editor(account_manage_df, use_container_width=True)
    if st.button("➕ 새 계정 등록 및 중복 체크 실행"):
      st.success("계정이 정상적으로 등록되었으며 중복 검사가 완료되었습니다.")

  with tab_ex4:
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
      "보고일에 '한눈에 보기' 요약 탭이 포함된 병원별(유앤아이, 블루비뇨기과,"
      " 로컬) 구글 시트 보고서를 생성합니다[cite: 13]."
  )

  if st.button("📊 [보고서 만들기] 구글 시트 보고서 생성 및 갱신"):
    st.success(
        "이번 달 데이터 및 '한눈에 보기' 요약 탭이 포함된 병원별 구글 시트"
        " 보고서가 성공적으로 생성되었습니다[cite: 13]."
    )

  report_main_df = pd.DataFrame([
      {
          "지점": "건대점",
          "발행일": "2026-10-01",
          "카페명": "맘스홀릭",
          "상태": "지점 담당자 확인 완료 (이상 없음)",
      }
  ])
  st.dataframe(report_main_df, use_container_width=True)

  csv_export = report_main_df.to_csv(index=False).encode("utf-8-sig")
  st.download_button(
      "📥 외부용 최종 보고서 다운로드 (실행사·계정 아이디 자동 제외)",
      data=csv_export,
      file_name="external_final_report.csv",
      mime="text/csv",
  )
