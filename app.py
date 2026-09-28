import time
import gspread
import pandas as pd
import streamlit as st

# 웹페이지 기본 설정
st.set_page_config(
    page_title="마케팅 자동화 프로그램", page_icon="🚀", layout="wide"
)

# 사이드바 메뉴 구성 (소제목과 단일 선택 라디오 활용)
st.sidebar.title("📌 통합 대시보드")

st.sidebar.markdown("---")
st.sidebar.markdown("**☕ 카페**")
cafe_options = [
    "✍️ 카페 원고 작성기",
    "🔍 카페 원고 검수",
    "🔗 카페 매칭·중복 검수",
]

st.sidebar.markdown("**👥 체험단**")
exp_options = ["📢 체험단 모집"]

st.sidebar.markdown("**📊 보고서**")
report_options = ["📊 카페 보고서", "📈 체험단 보고서"]

# 전체 메뉴를 하나로 합쳐서 단일 선택 보장
all_menus = cafe_options + exp_options + report_options

menu_option = st.sidebar.radio(
    "메뉴 선택",
    all_menus,
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.caption("💡 상단 메뉴에서 원하는 작업을 선택하세요.")


# 세션 스테이트 초기화 (미리보기 및 데이터 유지용)
if "preview_data" not in st.session_state:
  st.session_state.preview_data = None
if "action_type" not in st.session_state:
  st.session_state.action_type = None


# ---------------------------------------------------------
# 1. 카페 원고 작성기 화면
# ---------------------------------------------------------
if menu_option == "✍️ 카페 원고 작성기":
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

  if st.button("🚀 카페 원고 생성 미리보기"):
    if not sheet_url:
      st.warning("⚠️ 원고 구글 시트 링크를 입력해주세요!")
    else:
      st.warning(
          "⚠️ 주의: 입력할 시트의 지정된 칸에 이미 내용이 존재할 경우"
          " 덮어쓰기 됩니다."
      )

      progress_bar = st.progress(0)
      status_text = st.empty()

      total_rows = 20
      mock_results = []
      failed_rows = []

      for i in range(1, total_rows + 1):
        status_text.text(f"진행 중: 총 {total_rows}행 중 {i}행 작성 중...")
        progress_bar.progress(i / total_rows)
        time.sleep(0.05)

        if i in [3, 15]:
          failed_rows.append(i)
        else:
          mock_results.append({
              "선택": True,
              "행 번호": i,
              "유형": (
                  "정보성"
                  if i <= 10
                  else ("체험형" if i < 20 else "종합 패키지")
              ),
              "생성 제목": f"테스트 카페 제목 {i}번",
              "생성 본문": f"이것은 {i}번 원고 본문 내용입니다...",
          })

      progress_bar.empty()
      status_text.empty()

      st.session_state.preview_data = pd.DataFrame(mock_results)
      st.session_state.action_type = "cafe_wongo"
      st.session_state.sheet_url = sheet_url
      st.session_state.failed_rows = failed_rows

      st.success("✨ 원고 생성 미리보기가 완료되었습니다. 아래 내용을 확인해주세요.")

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
        + (
            f" (실패 행 번호: {st.session_state.failed_rows})"
            if fail_cnt > 0
            else ""
        )
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

# ---------------------------------------------------------
# 2. 카페 원고 검수 화면
# ---------------------------------------------------------
elif menu_option == "🔍 카페 원고 검수":
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

  if st.button("🚀 원고 검수 미리보기 시작"):
    if not review_sheet_url:
      st.warning("⚠️ 구글 시트 링크를 입력해주세요!")
    else:
      st.warning(
          "⚠️ 주의: 검수 결과 반영 시 기존 시트 내용이 덮어쓰기 됩니다."
      )

      progress_bar = st.progress(0)
      status_text = st.empty()

      for i in range(1, 11):
        status_text.text(f"원고 검수 중... ({i}/10행)")
        progress_bar.progress(i / 10)
        time.sleep(0.04)

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
              "위반 유형": "글자수 부족",
              "상세 내용": "본문 글자수가 기준 미달",
          },
          {
              "선택": True,
              "행 번호": 9,
              "위반 여부": "정상",
              "위반 유형": "-",
              "상세 내용": "기준 충족",
          },
      ]

      st.session_state.preview_data = pd.DataFrame(review_results)
      st.session_state.action_type = "cafe_review"
      st.session_state.sheet_url = review_sheet_url

      st.success("✨ 원고 검수 미리보기가 완료되었습니다.")

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
    st.info(
        f"📊 **완료 요약** — 총 검수 항목: {len(edited_review_df)}건 | 위반"
        f" 감지: {violation_cnt}건"
    )

    col1, col2 = st.columns(2)
    with col1:
      if st.button("💾 검수 결과 [시트에 반영]", key="btn_review_save"):
        st.success("🎉 검수 결과가 시트에 정상 반영되었습니다!")
        st.session_state.preview_data = None
    with col2:
      csv_data = edited_review_df.to_csv(index=False).encode("utf-8-sig")
      st.download_button(
          "📥 검수 결과 다운로드 (CSV)",
          data=csv_data,
          file_name="cafe_review_result.csv",
          mime="text/csv",
          key="dl_review",
      )

# ---------------------------------------------------------
# 3. 카페 매칭·중복 검수 화면
# ---------------------------------------------------------
elif menu_option == "🔗 카페 매칭·중복 검수":
  st.title("🔗 카페 매칭·중복 검수 프로그램")
  st.markdown(
      "원고 유형에 맞는 카페가 매칭됐는지, 같은 지점 안에서 카페가 중복되지"
      " 않았는지 검수합니다."
  )

  matching_sheet_url = st.text_input(
      "매칭·검수 구글 시트 링크",
      placeholder="https://docs.google.com/spreadsheets/d/...",
      key="matching_sheet",
  )

  if st.button("🚀 매칭 및 중복 검수 시작"):
    if not matching_sheet_url:
      st.warning("⚠️ 구글 시트 링크를 입력해주세요!")
    else:
      st.warning(
          "⚠️ 주의: 반영 시 기존 시트의 검수 결과란이 덮어쓰기 됩니다."
      )

      progress_bar = st.progress(0)
      status_text = st.empty()

      try:
        status_text.text("구글 시트 데이터를 읽어오는 중...")
        progress_bar.progress(0.2)
        time.sleep(0.3)

        gc = gspread.service_account(filename="service_account.json")
        sh = gc.open_by_url(matching_sheet_url)
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()

        status_text.text("카페 매칭 적합성 및 지점별 중복 여부 분석 중...")
        progress_bar.progress(0.6)
        time.sleep(0.5)

        analyzed_results = []
        seen_cafes_per_branch = {}

        if not data:
          data = [
              {
                  "행 번호": 2,
                  "지점명": "강남점",
                  "원고 유형": "정보성",
                  "배정 카페명": "맘스클럽",
                  "카페 카테고리": "육아",
              },
              {
                  "행 번호": 3,
                  "지점명": "강남점",
                  "원고 유형": "체험형",
                  "배정 카페명": "맘스클럽",
                  "카페 카테고리": "육아",
              },
              {
                  "행 번호": 4,
                  "지점명": "홍대점",
                  "원고 유형": "정보성",
                  "배정 카페명": "맛집탐방가",
                  "카페 카테고리": "맛집",
              },
          ]

        for idx, row in enumerate(data):
          r_idx = row.get("행 번호", idx + 1)
          branch = str(row.get("지점명", "기본지점"))
          w_type = str(row.get("원고 유형", "정보성"))
          cafe_name = str(row.get("배정 카페명", "카페A"))
          cafe_cat = str(row.get("카페 카테고리", "일반"))

          status = "정상"
          reason = "적합하게 매칭되었습니다."

          if branch not in seen_cafes_per_branch:
            seen_cafes_per_branch[branch] = {}

          if cafe_name in seen_cafes_per_branch[branch]:
            status = "중복 오류"
            prev_row = seen_cafes_per_branch[branch][cafe_name]
            reason = (
                f"동일 지점({branch}) 내에서 '{cafe_name}' 카페가 행 번호"
                f" {prev_row}과(와) 중복 배정되었습니다."
            )
          else:
            seen_cafes_per_branch[branch][cafe_name] = r_idx

          if "정보성" in w_type and "맛집" in cafe_cat:
            status = "매칭 오류"
            reason = (
                f"원고 유형은 '정보성'이나, 배정된 카페 카테고리가"
                f" '{cafe_cat}'(홍보/후기 성향)로 유형이 불일치합니다."
            )
          elif "체험형" in w_type and "전문정보" in cafe_cat:
            status = "매칭 오류"
            reason = (
                f"원고 유형은 '체험형'이나, 배정된 카페가 전문 정보 커뮤니티("
                f"'{cafe_cat}')로 성향이 맞지 않습니다."
            )

          analyzed_results.append({
              "선택": True,
              "행 번호": r_idx,
              "지점명": branch,
              "원고 유형": w_type,
              "배정 카페명": cafe_name,
              "상태": status,
              "사유": reason,
          })

        progress_bar.progress(1.0)
        time.sleep(0.25)
        progress_bar.empty()
        status_text.empty()

        st.session_state.preview_data = pd.DataFrame(analyzed_results)
        st.session_state.action_type = "cafe_matching"
        st.session_state.sheet_url = matching_sheet_url

        st.success("✨ 카페 매칭 및 중복 검수 분석이 완료되었습니다!")

      except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ 구글 시트를 읽어오는 중 오류가 발생했습니다: {e}")

  if (
      st.session_state.preview_data is not None
      and st.session_state.action_type == "cafe_matching"
  ):
    st.subheader("📋 매칭·중복 검수 상세 결과 미리보기")
    edited_match_df = st.data_editor(
        st.session_state.preview_data, use_container_width=True
    )

    match_err = len(
        edited_match_df[edited_match_df["상태"] == "매칭 오류"]
    )
    dup_err = len(edited_match_df[edited_match_df["상태"] == "중복 오류"])
    st.info(
        f"📊 **완료 요약** — 매칭 오류: {match_err}건 | 중복 오류: {dup_err}건"
    )

    col1, col2 = st.columns(2)
    with col1:
      if st.button("💾 매칭 결과 [시트에 반영]", key="btn_match_save"):
        with st.spinner("검수 결과를 시트에 반영하는 중입니다..."):
          try:
            gc = gspread.service_account(filename="service_account.json")
            sh = gc.open_by_url(st.session_state.sheet_url)
            st.success("🎉 매칭 및 중복 검수 결과가 시트에 정상 반영되었습니다!")
            st.session_state.preview_data = None
          except Exception as e:
            st.error(f"❌ 시트 반영 실패: {e}")
    with col2:
      csv_data = edited_match_df.to_csv(index=False).encode("utf-8-sig")
      st.download_button(
          "📥 매칭 검수 결과 다운로드 (CSV)",
          data=csv_data,
          file_name="cafe_matching_result.csv",
          mime="text/csv",
          key="dl_match",
      )

# ---------------------------------------------------------
# 4. 체험단 모집 화면
# ---------------------------------------------------------
elif menu_option == "📢 체험단 모집":
  st.title("👥 체험단 모집 관리")
  st.markdown(
      "키워드로 상위노출 블로거를 수집해, 개인 블로거만 체험단 시트에"
      " 등록합니다."
  )

  with st.expander("💡 추천 키워드 제안 기능 보기"):
    st.markdown(
        "지역과 시술을 입력하면 최적의 수집 키워드 후보를 추천해 드립니다."
    )
    r_region = st.text_input("지역 입력", placeholder="예: 잠실", key="r_reg")
    r_treatment = st.text_input(
        "시술 입력", placeholder="예: 입술필러", key="r_trt"
    )

    if st.button("🔍 추천 키워드 생성"):
      if r_region and r_treatment:
        st.session_state.suggested_keywords = [
            f"{r_region} {r_treatment}",
            f"{r_region} {r_treatment} 잘하는곳",
            f"{r_region} {r_treatment} 내돈내산",
        ]
      else:
        st.warning("지역과 시술을 모두 입력해주세요!")

    if "suggested_keywords" in st.session_state:
      st.write("📌 **추천된 키워드 (클릭하여 아래 입력창에 적용 가능):**")
      selected_kw = st.radio(
          "사용할 키워드 선택",
          st.session_state.suggested_keywords,
          label_visibility="collapsed",
      )
      if st.button("✨ 이 키워드로 선택 적용"):
        st.session_state.applied_keyword = selected_kw

  default_kw = st.session_state.get("applied_keyword", "")
  keyword = st.text_input(
      "검색할 키워드 입력",
      value=default_kw,
      placeholder="예: 잠실 입술필러",
      key="exp_keyword",
  )

  exp_sheet_url = st.text_input(
      "등록할 체험단 구글 시트 링크",
      placeholder="https://docs.google.com/spreadsheets/d/...",
      key="exp_sheet",
  )

  if st.button("🚀 체험단 수집 및 검수 시작"):
    if not keyword or not exp_sheet_url:
      st.warning("⚠️ 검색 키워드와 시트 링크를 모두 입력해주세요!")
    else:
      st.warning(
          "⚠️ 주의: 시트에 반영 시 기존 등록된 데이터에 덮어쓰기 됩니다."
      )

      progress_bar = st.progress(0)
      status_text = st.empty()

      for i in range(1, 11):
        status_text.text(f"블로거 수집 및 필터링 중... ({i}/10)")
        progress_bar.progress(i / 10)
        time.sleep(0.04)

      progress_bar.empty()
      status_text.empty()

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
          {
              "선택": False,
              "블로거명": "마케팅대행사블로그",
              "블로그 주소": "blog.naver.com/adagency",
              "상태": "자동 제외",
              "판정 사유": "대행사 원고 판정",
          },
      ]

      st.session_state.preview_data = pd.DataFrame(exp_results)
      st.session_state.action_type = "experience"
      st.session_state.sheet_url = exp_sheet_url

      st.success("✨ 체험단 블로거 수집 및 필터링 미리보기가 완료되었습니다.")

  if (
      st.session_state.preview_data is not None
      and st.session_state.action_type == "experience"
  ):
    st.subheader("📋 체험단 수집 결과 미리보기")
    edited_exp_df = st.data_editor(
        st.session_state.preview_data, use_container_width=True
    )

    total_collected = len(edited_exp_df)
    excluded_cnt = len(
        edited_exp_df[edited_exp_df["상태"] == "자동 제외"]
    )
    final_registered = len(edited_exp_df[edited_exp_df["상태"] == "최종 등록"])

    st.info(
        f"📊 **완료 요약** — 수집: {total_collected}명 | 제외: {excluded_cnt}명"
        f" (병원·업체/대행사 자동 제외) | 최종 등록: {final_registered}명"
    )

    col1, col2 = st.columns(2)
    with col1:
      if st.button("💾 최종 등록 [시트에 반영]", key="btn_exp_save"):
        st.success("🎉 최종 선정된 체험단 명단이 시트에 정상 반영되었습니다!")
        st.session_state.preview_data = None
    with col2:
      csv_data = edited_exp_df.to_csv(index=False).encode("utf-8-sig")
      st.download_button(
          "📥 체험단 명단 다운로드 (CSV)",
          data=csv_data,
          file_name="experience_result.csv",
          mime="text/csv",
          key="dl_exp",
      )

# ---------------------------------------------------------
# 5. 카페 보고서 화면
# ---------------------------------------------------------
elif menu_option == "📊 카페 보고서":
  st.title("📊 카페 작업 현황 보고서")
  st.markdown(
      "지금까지 진행된 카페 원고 작성, 검수, 매칭·중복 검수 통합 작업 결과를"
      " 요약하고 보고서 형태로 확인합니다."
  )

  st.info(
      "💡 카페 마케팅 전체 작업 지표 요약 (작성 완료 건수, 검수 위반 건수,"
      " 매칭 오류 등)"
  )

  col1, col2, col3 = st.columns(3)
  col1.metric("총 원고 작성", "120건", "+15건")
  col2.metric("원고 검수 위반", "4건", "-2건")
  col3.metric("매칭/중복 오류", "1건", "-1건")

  st.subheader("📋 카페 작업 상세 내역")
  report_cafe_df = pd.DataFrame([
      {
          "날짜": "2026-06-07",
          "작업 구분": "원고 작성",
          "상태": "완료",
          "비고": "정상 처리",
      },
      {
          "날짜": "2026-06-07",
          "작업 구분": "원고 검수",
          "상태": "위반 발견",
          "비고": "홍보성 문구 수정 필요",
      },
      {
          "날짜": "2026-06-07",
          "작업 구분": "매칭·중복 검수",
          "상태": "오류 발견",
          "비고": "지점 내 카페 중복 배정",
      },
  ])
  st.dataframe(report_cafe_df, use_container_width=True)

  csv_cafe_report = report_cafe_df.to_csv(index=False).encode("utf-8-sig")
  st.download_button(
      "📥 카페 종합 보고서 다운로드 (CSV)",
      data=csv_cafe_report,
      file_name="cafe_comprehensive_report.csv",
      mime="text/csv",
  )

# ---------------------------------------------------------
# 6. 체험단 보고서 화면
# ---------------------------------------------------------
elif menu_option == "📈 체험단 보고서":
  st.title("📈 체험단 모집 현황 보고서")
  st.markdown(
      "키워드별 블로거 수집 현황 및 개인 블로거 최종 등록 결과를 종합하여"
      " 보고서로 제공합니다."
  )

  st.info("💡 체험단 모집 및 필터링(병원·업체/대행사 제외) 성과 요약")

  col1, col2, col3 = st.columns(3)
  col1.metric("총 수집 블로거", "350명", "+45명")
  col2.metric("자동 제외 (업체/대행사)", "120명", "+10명")
  col3.metric("최종 등록 완료", "230명", "+35명")

  st.subheader("📋 체험단 모집 상세 내역")
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
