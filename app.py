import time
import gspread
import pandas as pd
import streamlit as st

# 웹페이지 기본 설정
st.set_page_config(
    page_title="마케팅 자동화 프로그램", page_icon="🚀", layout="wide"
)

# 세션 스테이트 초기화 (메뉴 및 데이터 유지용)
if "menu_option" not in st.session_state:
  st.session_state.menu_option = "🏠 홈"
if "preview_data" not in st.session_state:
  st.session_state.preview_data = None
if "action_type" not in st.session_state:
  st.session_state.action_type = None
if "user_role" not in st.session_state:
  # 권한 관리 시뮬레이션용 (관리자, 지점 담당자, 원고 작가 등)
  st.session_state.user_role = "관리자"


def set_menu(menu_name):
  st.session_state.menu_option = menu_name


# =========================================================
# 사이드바 메뉴 구성 (소제목 카테고리 형태 + 단일 선택)
# =========================================================
st.sidebar.title("📌 통합 대시보드")

# 권한 선택 필터 (구성안 2번 권한 역할 반영)
st.sidebar.markdown("---")
st.sidebar.session_state.user_role = st.sidebar.selectbox(
    "👤 내 권한(역할) 선택",
    ["관리자", "지점 담당자", "원고 작가", "게시판 담당", "실행사", "원장님"],
    index=0,
)
st.sidebar.caption("💡 모든 화면에 '내 담당만 보기' 필터가 적용됩니다.")
st.sidebar.markdown("---")

# 1. 홈 및 기준 정보
st.sidebar.markdown("🏠 **홈 / 기준 정보**")
if st.sidebar.button(
    "🏠 홈 (대시보드)",
    use_container_width=True,
    type=(
        "primary" if st.session_state.menu_option == "🏠 홈" else "secondary"
    ),
):
  set_menu("🏠 홈")
if st.sidebar.button(
    "🏢 지점 및 장비 관리",
    use_container_width=True,
    type=(
        "primary"
        if st.session_state.menu_option == "🏢 지점 및 장비 관리"
        else "secondary"
    ),
):
  set_menu("🏢 지점 및 장비 관리")
if st.sidebar.button(
    "☕ 카페 목록 관리",
    use_container_width=True,
    type=(
        "primary"
        if st.session_state.menu_option == "☕ 카페 목록 관리"
        else "secondary"
    ),
):
  set_menu("☕ 카페 목록 관리")

st.sidebar.markdown("---")

# 2. 카페 원고 제작 분야 (1단계 핵심)
st.sidebar.markdown("☕ **카페 원고 제작**")
if st.sidebar.button(
    "✍️ 카페 원고 작성기",
    use_container_width=True,
    type=(
        "primary"
        if st.session_state.menu_option == "✍️ 카페 원고 작성기"
        else "secondary"
    ),
):
  set_menu("✍️ 카페 원고 작성기")
if st.sidebar.button(
    "🔍 카페 원고 자동 검수",
    use_container_width=True,
    type=(
        "primary"
        if st.session_state.menu_option == "🔍 카페 원고 자동 검수"
        else "secondary"
    ),
):
  set_menu("🔍 카페 원고 자동 검수")
if st.sidebar.button(
    "🔗 카페 매칭·중복 검수",
    use_container_width=True,
    type=(
        "primary"
        if st.session_state.menu_option == "🔗 카페 매칭·중복 검수"
        else "secondary"
    ),
):
  set_menu("🔗 카페 매칭·중복 검수")
if st.sidebar.button(
    "📝 단건 원고 작성",
    use_container_width=True,
    type=(
        "primary"
        if st.session_state.menu_option == "📝 단건 원고 작성"
        else "secondary"
    ),
):
  set_menu("📝 단건 원고 작성")

st.sidebar.markdown("---")

# 3. 확장 분야 (체험단 및 보고서)
st.sidebar.markdown("📊 **운영 및 보고서**")
if st.sidebar.button(
    "📢 체험단 모집 관리",
    use_container_width=True,
    type=(
        "primary"
        if st.session_state.menu_option == "📢 체험단 모집 관리"
        else "secondary"
    ),
):
  set_menu("📢 체험단 모집 관리")
if st.sidebar.button(
    "📊 카페 작업 현황 보고서",
    use_container_width=True,
    type=(
        "primary"
        if st.session_state.menu_option == "📊 카페 보고서"
        else "secondary"
    ),
):
  set_menu("📊 카페 보고서")
if st.sidebar.button(
    "📈 체험단 모집 현황 보고서",
    use_container_width=True,
    type=(
        "primary"
        if st.session_state.menu_option == "📈 체험단 보고서"
        else "secondary"
    ),
):
  set_menu("📈 체험단 보고서")

st.sidebar.markdown("---")
st.sidebar.caption("🚀 마케팅 통합 관리 프로그램 v1.0")

menu_option = st.session_state.menu_option


# =========================================================
# 0. 홈 (대시보드) 화면
# =========================================================
if menu_option == "🏠 홈":
  st.title("🏠 마케팅 통합 관리 홈 (대시보드)")
  st.markdown(
      f"현재 접속 권한: **{st.session_state.user_role}** | 월 880건 원고"
      " 작성·검수 현황"
  )

  col1, col2, col3, col4 = st.columns(4)
  col1.metric("이번 달 목표 원고", "880건", "진행중")
  col2.metric("작성 완료", "640건", "+45건")
  col3.metric("검수 대기 / 위반", "12건", "-3건")
  col4.metric("절약된 시간", "142시간", "자동 집계")

  st.markdown("---")
  st.subheader("📌 내 할 일 및 마감 임박 항목")
  st.info(
      "💡 마감 임박 건, 피드백 대기 중인 원고, 지점 담당자 확인 요청 건이"
      " 이곳에 표시됩니다."
  )

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


# =========================================================
# 지점 및 장비 관리 화면
# =========================================================
elif menu_option == "🏢 지점 및 장비 관리":
  st.title("🏢 지점 및 보유 장비 관리")
  st.markdown(
      "지점별 병원 구분(유앤아이/블루비뇨기과/로컬) 및 표준 장비 사전과"
      " 연동된 보유 장비를 관리합니다."
  )

  with st.expander("ℹ️ 장비 규칙 자동 적용 가이드"):
    st.markdown(
        "- 표준 장비명 사전 연동 (예: 디스포트 명칭 언급 금지 → 영국산 보톡스"
        " 자동 치환 규칙 적용)"
    )

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


# =========================================================
# 카페 목록 관리 화면
# =========================================================
elif menu_option == "☕ 카페 목록 관리":
  st.title("☕ 카페 목록 및 지점 연결 관리")
  st.markdown(
      "구성안 7번 데이터 이전 기준에 맞춘 카페 데이터베이스 및 지점/지역 연결"
      " 관리 화면입니다."
  )

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


# =========================================================
# 1. 카페 원고 작성기 화면
# =========================================================
elif menu_option == "✍️ 카페 원고 작성기":
  st.title("📝 네이버 카페 원고 자동 생성")
  st.markdown(
      "구글 시트의 데이터를 읽은 후, 지점별 20건 틀(정보성 10 / 후기성 9 /"
      " 슈퍼세트 1)을 자동으로 생성합니다."
  )

  with st.expander("ℹ️ 카페 시트 가이드 보기"):
    st.markdown(
        """
        - **1~10번:** 정보성 글 (전문적인 톤)
        - **11~19번:** 체험 공유형 글 (친근한 일상 대화 톤)
        - **20번:** 종합 패키지형 글 (본문 400~500자 이내)
        - 보유장비는 기준 정보에서 자동으로 불러와 적용됩니다.
        """
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
      st.warning("⚠️ 주의: 지정된 칸에 이미 내용이 존재할 경우 덮어쓰기 됩니다.")

      progress_bar = st.progress(0)
      status_text = st.empty()

      total_rows = 20
      mock_results = []
      failed_rows = []

      for i in range(1, total_rows + 1):
        status_text.text(f"진행 중: 총 {total_rows}행 중 {i}행 작성 중...")
        progress_bar.progress(i / total_rows)
        time.sleep(0.03)

        if i in [3, 15]:
          failed_rows.append(i)
        else:
          mock_results.append({
              "선택": True,
              "행 번호": i,
              "유형": (
                  "정보성"
                  if i <= 10
                  else ("후기성" if i < 20 else "종합 패키지(슈퍼세트)")
              ),
              "생성 제목": f"지점 맞춤 카페 제목 테스트 {i}번",
              "생성 본문": f"이것은 보유 장비 규칙이 적용된 {i}번 원고 본문 내용입니다...",
          })

      progress_bar.empty()
      status_text.empty()

      st.session_state.preview_data = pd.DataFrame(mock_results)
      st.session_state.action_type = "cafe_wongo"
      st.session_state.sheet_url = sheet_url
      st.session_state.failed_rows = failed_rows

      st.success("✨ 원고 생성 미리보기가 완료되었습니다.")

  if (
      st.session_state.preview_data is not None
      and st.session_state.action_type == "cafe_wongo"
  ):
    st.subheader("📋 생성 결과 미리보기")
    edited_df = st.data_editor(
        st.session_state.preview_data, use_container_width=True
    )

    success_cnt = len(edited_df[edited_df["선택"] == True])
    fail_cnt = len(st.session_state.get("failed_rows", []))
    st.info(
        f"📊 **완료 요약** — 생성 성공: {success_cnt}건 | 실패: {fail_cnt}건"
    )

    col1, col2 = st.columns(2)
    with col1:
      if st.button("💾 [시트에 반영]"):
        with st.spinner("구글 시트에 반영 중입니다..."):
          try:
            gc = gspread.service_account(filename="service_account.json")
            sh = gc.open_by_url(st.session_state.sheet_url)
            st.success("🎉 성공적으로 시트에 반영되었습니다!")
            st.session_state.preview_data = None
          except Exception as e:
            st.error(f"❌ 반영 중 오류 발생: {e}")
    with col2:
      csv_data = edited_df.to_csv(index=False).encode("utf-8-sig")
      st.download_button(
          "📥 결과 파일 다운로드 (CSV)",
          data=csv_data,
          file_name="cafe_wongo_result.csv",
          mime="text/csv",
      )


# =========================================================
# 2. 카페 원고 자동 검수 화면
# =========================================================
elif menu_option == "🔍 카페 원고 자동 검수":
  st.title("🔍 카페 원고 자동 검수 프로그램")
  st.markdown(
      "금칙어, 계절어, 글자 수, 키워드 삽입 개수, 유사 문장 및 장비 규칙을"
      " 자동으로 검수합니다."
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
      progress_bar = st.progress(0)
      status_text = st.empty()

      for i in range(1, 11):
        status_text.text(f"규칙 및 금칙어 검수 중... ({i}/10행)")
        progress_bar.progress(i / 10)
        time.sleep(0.03)

      progress_bar.empty()
      status_text.empty()

      review_results = [
          {
              "선택": True,
              "행 번호": 2,
              "위반 여부": "위반",
              "위반 유형": "홍보성 과장 문구",
              "상세 내용": "최고, 1위 등의 금지 단어 포함",
          },
          {
              "선택": True,
              "행 번호": 7,
              "위반 여부": "위반",
              "위반 유형": "장비 규칙 위반",
              "상세 내용": "보유하지 않은 장비 명칭 언급",
          },
          {
              "선택": True,
              "행 번호": 9,
              "위반 여부": "정상",
              "위반 유형": "-",
              "상세 내용": "모든 가이드 충족",
          },
      ]

      st.session_state.preview_data = pd.DataFrame(review_results)
      st.session_state.action_type = "cafe_review"
      st.session_state.sheet_url = review_sheet_url

      st.success("✨ 자동 검수가 완료되었습니다.")

  if (
      st.session_state.preview_data is not None
      and st.session_state.action_type == "cafe_review"
  ):
    st.subheader("📋 검수 결과 미리보기")
    edited_review_df = st.data_editor(
        st.session_state.preview_data, use_container_width=True
    )
    violation_cnt = len(
        edited_review_df[edited_review_df["위반 여부"] == "위반"]
    )
    st.info(f"📊 **검수 요약** — 위반 감지: {violation_cnt}건")

    col1, col2 = st.columns(2)
    with col1:
      if st.button("💾 검수 결과 [시트에 반영]"):
        st.success("🎉 검수 결과가 시트에 정상 반영되었습니다!")
        st.session_state.preview_data = None
    with col2:
      csv_data = edited_review_df.to_csv(index=False).encode("utf-8-sig")
      st.download_button(
          "📥 검수 결과 다운로드 (CSV)",
          data=csv_data,
          file_name="cafe_review_result.csv",
          mime="text/csv",
      )


# =========================================================
# 3. 카페 매칭·중복 검수 화면
# =========================================================
elif menu_option == "🔗 카페 매칭·중복 검수":
  st.title("🔗 카페 매칭 및 지점별 중복 검수")
  st.markdown(
      "원고 유형에 맞는 카페가 적절히 매칭되었는지, 동일 지점 내 중복 배정은"
      " 없는지 검수합니다."
  )

  matching_sheet_url = st.text_input(
      "매칭·검수 구글 시트 링크",
      placeholder="https://docs.google.com/spreadsheets/d/...",
      key="matching_sheet",
  )

  if st.button("🚀 매칭 및 중복 검수 실행"):
    if not matching_sheet_url:
      st.warning("⚠️ 구글 시트 링크를 입력해주세요!")
    else:
      analyzed_results = [
          {
              "선택": True,
              "행 번호": 2,
              "지점명": "강남점",
              "원고 유형": "정보성",
              "배정 카페명": "맘스클럽",
              "상태": "정상",
              "사유": "적합하게 매칭되었습니다.",
          },
          {
              "선택": True,
              "행 번호": 3,
              "지점명": "강남점",
              "원고 유형": "정보성",
              "배정 카페명": "맘스클럽",
              "상태": "중복 오류",
              "사유": "동일 지점 내 카페 중복 배정",
          },
      ]
      st.session_state.preview_data = pd.DataFrame(analyzed_results)
      st.session_state.action_type = "cafe_matching"
      st.success("✨ 카페 매칭 및 중복 분석이 완료되었습니다!")

  if (
      st.session_state.preview_data is not None
      and st.session_state.action_type == "cafe_matching"
  ):
    st.subheader("📋 매칭·중복 검수 상세 결과")
    st.data_editor(st.session_state.preview_data, use_container_width=True)


# =========================================================
# 4. 단건 원고 작성 화면
# =========================================================
elif menu_option == "📝 단건 원고 작성":
  st.title("📝 단건 원고 작성기")
  st.markdown(
      "시트 없이 필요할 때 바로 상위노출 원고, 이미지 캡션, 질문글, 의료 후기"
      " 등을 생성하고 복사하여 사용할 수 있습니다."
  )

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
      with st.spinner("AI가 원고를 작성하고 있습니다..."):
        time.sleep(0.5)
        st.success("✨ 단건 원고가 생성되었습니다!")
        st.text_area(
            "생성된 원고 결과 (복사해서 사용하세요)",
            value=(
                f"[{content_type}] '{keyword_input}' 관련 작성된 초안"
                " 내용입니다...\n실제 서비스 연동 시 Claude API가 호출됩니다."
            ),
            height=200,
        )


# =========================================================
# 5. 체험단 모집 관리 화면
# =========================================================
elif menu_option == "📢 체험단 모집 관리":
  st.title("👥 블로거 체험단 모집 관리")
  st.markdown(
      "키워드로 상위노출 개인 블로거를 수집하고(병원·업체 및 대행사 원고 자동"
      " 제외), 섭외부터 노출 체크까지 보드 형태로 관리합니다."
  )

  exp_keyword = st.text_input("수집 키워드 입력", placeholder="예: 잠실 입술필러")
  if st.button("🚀 체험단 블로거 수집 시작"):
    if not exp_keyword:
      st.warning("⚠️ 검색할 키워드를 입력해주세요!")
    else:
      exp_results = [
          {
              "선택": True,
              "블로거명": "행복한일상",
              "블로그 주소": "blog.naver.com/happy",
              "상태": "최종 등록",
              "판정 사유": "개인 블로거 (정상)",
          },
          {
              "선택": False,
              "블로거명": "강남성모병원공식",
              "블로그 주소": "blog.naver.com/hospital",
              "상태": "자동 제외",
              "판정 사유": "병원·업체 계정",
          },
      ]
      st.dataframe(pd.DataFrame(exp_results), use_container_width=True)


# =========================================================
# 6. 카페 보고서 화면
# =========================================================
elif menu_option == "📊 카페 보고서":
  st.title("📊 카페 작업 현황 보고서")
  st.markdown(
      "실행사 기입 ➔ 관리자 1차 확인 ➔ 지점 담당자 확인(수정 요청 바로"
      " 전달) ➔ 최종본 확정 흐름을 관리합니다[cite: 5]."
  )

  col1, col2, col3 = st.columns(3)
  col1.metric("총 원고 발행", "120건", "+15건")
  col2.metric("지점 확인 완료", "30개 지점", "진행중")
  col3.metric("수정 요청 대기", "2건", "실행사 반영 대기")

  report_cafe_df = pd.DataFrame([
      {
          "지점": "유앤아이 강남점",
          "발행일": "2026-06-07",
          "카페명": "맘스홀릭",
          "상태": "지점 담당자 확인 완료",
      },
      {
          "지점": "블루비뇨기과 신촌점",
          "발행일": "2026-06-07",
          "카페명": "세클맘",
          "상태": "수정 요청 중",
      },
  ])
  st.dataframe(report_cafe_df, use_container_width=True)

  csv_cafe_report = report_cafe_df.to_csv(index=False).encode("utf-8-sig")
  st.download_button(
      "📥 외부용 보고서 다운로드 (실행사/아이디 제외)",
      data=csv_cafe_report,
      file_name="cafe_external_report.csv",
      mime="text/csv",
  )


# =========================================================
# 7. 체험단 보고서 화면
# =========================================================
elif menu_option == "📈 체험단 보고서":
  st.title("📈 체험단 모집 현황 보고서")
  st.markdown(
      "키워드별 블로거 수집 현황 및 개인 블로거 최종 등록 결과를 종합하여"
      " 보고서로 제공합니다."
  )

  col1, col2, col3 = st.columns(3)
  col1.metric("총 수집 블로거", "350명", "+45명")
  col2.metric("자동 제외", "120명", "병원·대행사")
  col3.metric("최종 등록", "230명", "진행률 65%")

  report_exp_df = pd.DataFrame([
      {
          "키워드": "잠실 입술필러",
          "수집 인원": "50명",
          "제외 인원": "18명",
          "최종 등록": "32명",
      },
      {
          "키워드": "강남 피부과",
          "수집 인원": "120명",
          "제외 인원": "45명",
          "최종 등록": "75명",
      },
  ])
  st.dataframe(report_exp_df, use_container_width=True)

  csv_exp_report = report_exp_df.to_csv(index=False).encode("utf-8-sig")
  st.download_button(
      "📥 체험단 종합 보고서 다운로드 (CSV)",
      data=csv_exp_report,
      file_name="experience_comprehensive_report.csv",
      mime="text/csv",
  )
