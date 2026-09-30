# -*- coding: utf-8 -*-
"""카페·체험단 마케팅 통합 관리 프로그램 — 한 파일 버전 (구성안 1·2단계)

■ 이 파일 하나만 붙여넣고 실행하면 됩니다:   streamlit run app.py
■ 필요한 패키지:  pip install streamlit pandas openpyxl requests anthropic
■ 테스트 모드:    로그인 없이 사이드바 맨 위에서 역할(사람)을 골라 접속합니다.
■ 데이터는 이 파일 옆 data/app.db 에 저장됩니다.
■ AI 초안·단건 작성을 쓰려면: .streamlit/secrets.toml 에 ANTHROPIC_API_KEY = "..." 를 넣고,
  이 파일 옆 skills/<스킬이름>/SKILL.md 에 스킬 파일을 두세요(없으면 스킬 없이 작성).

구조: 아래 MODULES 안에 모듈별 코드가 들어 있고(core = 데이터·규칙, views = 화면, rules.verify = uandi-wongo 검수기),
맨 아래가 실제 화면 시작점입니다. 수정할 때는 해당 모듈 문자열 안의 코드를 고치면 됩니다.
"""
import os
import sys
import types

_BASE = os.path.dirname(os.path.abspath(__file__))
MODULES = {}

# ============================================================================
# core.db
# ============================================================================
MODULES['core.db'] = r'''"""데이터 저장소 (SQLite).

구성안 8장 기술 메모: 저장소는 외부 DB(예: Supabase)를 쓰고, 구글 시트는 보고서 출력용.
지금은 설치 없이 바로 돌도록 SQLite 파일(data/app.db)을 쓰고, 모든 SQL을 이 파일의
q / ex 두 함수로만 통과시켜서 나중에 Postgres(Supabase)로 옮길 때 여기만 바꾸면 되게 했다.
"""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))
DB_PATH = os.environ.get("DB_PATH", os.path.join(DATA_DIR, "app.db"))
IMG_DIR = os.path.join(DATA_DIR, "images")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today():
    return datetime.now().strftime("%Y-%m-%d")


@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    try:
        yield c
        c.commit()
    finally:
        c.close()


def q(sql, params=()):
    """SELECT → dict 리스트"""
    with conn() as c:
        return [dict(r) for r in c.execute(sql, params).fetchall()]


def q1(sql, params=()):
    r = q(sql, params)
    return r[0] if r else None


def qv(sql, params=(), default=None):
    r = q1(sql, params)
    if not r:
        return default
    v = list(r.values())[0]
    return default if v is None else v


def qdf(sql, params=()):
    return pd.DataFrame(q(sql, params))


def ex(sql, params=()):
    with conn() as c:
        cur = c.execute(sql, params)
        return cur.lastrowid


def exmany(sql, rows):
    with conn() as c:
        c.executemany(sql, rows)


SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  pw TEXT NOT NULL,
  name TEXT NOT NULL,
  role TEXT NOT NULL,
  active INTEGER DEFAULT 1,
  created_at TEXT
);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE IF NOT EXISTS branches(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  hospital TEXT NOT NULL,             -- 유앤아이 / 블루비뇨기과 / 로컬
  region TEXT,                        -- 서울·경기·인천·충청·전라·경상
  location TEXT,
  region_tokens TEXT,                 -- 원고에 쓰는 지역 표기(쉼표) = 시트 H3
  report_link TEXT, photo_link TEXT,
  banned_topics TEXT,                 -- 지점 금지 주제(쉼표). 예: 정관수술,포경수술
  guideline TEXT,                     -- 로컬 지점 원장님 가이드라인
  active INTEGER DEFAULT 1,
  created_at TEXT
);
CREATE TABLE IF NOT EXISTS branch_aliases(alias TEXT PRIMARY KEY, branch_id INTEGER);

CREATE TABLE IF NOT EXISTS months(month TEXT PRIMARY KEY, created_at TEXT, created_by TEXT);

CREATE TABLE IF NOT EXISTS branch_month(
  month TEXT, branch_id INTEGER,
  manager_id INTEGER, writer_id INTEGER,
  req_notes TEXT, competitor TEXT, must_include TEXT, special TEXT,
  material_done INTEGER DEFAULT 0,
  dl_setting TEXT, dl_writing TEXT, dl_publish TEXT,
  planned_publish TEXT,
  report_stage TEXT DEFAULT '작성 중',
  report_locked INTEGER DEFAULT 0,
  report_requested_at TEXT, report_confirmed_at TEXT, report_final_at TEXT,
  cm_report_stage TEXT DEFAULT '작성 중',
  PRIMARY KEY(month, branch_id)
);

CREATE TABLE IF NOT EXISTS equip_std(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  category TEXT,
  aliases TEXT,          -- 다른 표기(쉼표)
  banned_names TEXT,     -- 원고에 쓰면 안 되는 명칭(쉼표). 예: 디스포트
  replacement TEXT       -- 대신 쓸 말. 예: 영국산 보톡스
);
CREATE TABLE IF NOT EXISTS branch_equipment(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  branch_id INTEGER, std_id INTEGER,
  qty INTEGER DEFAULT 1, in_date TEXT, note TEXT,
  active INTEGER DEFAULT 1, updated_at TEXT, updated_by TEXT
);

CREATE TABLE IF NOT EXISTS cafes(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL, alt_names TEXT, url TEXT UNIQUE, base_id TEXT,
  members INTEGER, note TEXT,
  ctype TEXT,            -- 2030뷰티 / 맘 / 지역맘 / 남성
  size TEXT,             -- 대형 / 소형
  region TEXT,           -- 지역맘만
  status TEXT DEFAULT '준비 중',   -- 준비 중 / 진행 가능 / 주의 / 위험
  flag_large INTEGER DEFAULT 0, flag_smart INTEGER DEFAULT 0,
  comment_use INTEGER DEFAULT 0,
  price INTEGER DEFAULT 0,
  archived INTEGER DEFAULT 0, archive_reason TEXT, archived_at TEXT,
  created_at TEXT
);
CREATE TABLE IF NOT EXISTS cafe_links(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cafe_id INTEGER, link_type TEXT,   -- 지점 / 지역
  branch_id INTEGER, region TEXT
);
CREATE TABLE IF NOT EXISTS cafe_log(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cafe_id INTEGER, at TEXT, user TEXT, old TEXT, new TEXT, reason TEXT
);

CREATE TABLE IF NOT EXISTS manuscripts(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  month TEXT, branch_id INTEGER, no INTEGER, mtype TEXT,
  status TEXT DEFAULT '작성 전',
  keyword TEXT, equipment TEXT, special TEXT, no_equip_mention INTEGER DEFAULT 0,
  title TEXT, body TEXT,
  c1 TEXT, r1 TEXT, c2 TEXT, r2 TEXT, c3 TEXT, r3 TEXT,
  feedback TEXT, confirmed_by TEXT, confirmed_at TEXT,
  check_json TEXT, check_fail INTEGER DEFAULT 0,
  updated_at TEXT, updated_by TEXT,
  UNIQUE(month, branch_id, no)
);
CREATE TABLE IF NOT EXISTS ms_history(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ms_id INTEGER, at TEXT, user TEXT, action TEXT, detail TEXT
);

CREATE TABLE IF NOT EXISTS accounts(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  acc_id TEXT UNIQUE NOT NULL, nickname TEXT,
  purpose TEXT,          -- 카페 침투 / 댓글 침투 / 둘 다
  status TEXT DEFAULT '사용 중',   -- 사용 중 / 교체됨 / 제재·정지
  memo TEXT, replaced_from INTEGER, created_at TEXT, created_by TEXT
);
CREATE TABLE IF NOT EXISTS account_log(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id INTEGER, at TEXT, user TEXT, action TEXT, detail TEXT
);

CREATE TABLE IF NOT EXISTS publications(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ms_id INTEGER UNIQUE, month TEXT, branch_id INTEGER,
  cafe_id INTEGER, account_id INTEGER,
  url TEXT, pub_date TEXT,
  views INTEGER, comments INTEGER, last_checked TEXT,
  check_state TEXT DEFAULT '정상',  -- 정상 / 삭제됨 / 댓글 작업 미완료 / 조회수 부족
  as_state TEXT DEFAULT '',         -- '' / AS 대기 / 처리 완료
  as_opened_at TEXT, as_done_at TEXT,
  created_at TEXT, created_by TEXT
);
CREATE TABLE IF NOT EXISTS report_issues(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pub_id INTEGER, month TEXT, branch_id INTEGER,
  kind TEXT DEFAULT '카페',        -- 카페 / 댓글
  source TEXT,                      -- 관리자 1차 / 지점 확인
  reason TEXT, status TEXT DEFAULT '접수됨',  -- 접수됨 / 처리 중 / 반영 완료 / 확인 완료
  created_at TEXT, created_by TEXT, resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS comment_targets(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  month TEXT, branch_id INTEGER, keyword TEXT,
  source TEXT,              -- 자동 수집 / 직접 추가
  search_type TEXT, block TEXT, rank INTEGER,
  title TEXT, cafe_name TEXT, cafe_base TEXT, article_id TEXT,
  url TEXT UNIQUE, commentable TEXT DEFAULT '가능', collected_at TEXT,
  status TEXT DEFAULT '대기',     -- 대기 / 완료
  account_id INTEGER, done_date TEXT, comment_text TEXT,
  created_by TEXT
);

CREATE TABLE IF NOT EXISTS board_tasks(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  month TEXT, branch_id INTEGER, cafe_id INTEGER, board TEXT, due TEXT, note TEXT,
  assignee_id INTEGER,
  status TEXT DEFAULT '요청', done_by TEXT, done_at TEXT, created_at TEXT, created_by TEXT
);

CREATE TABLE IF NOT EXISTS issues(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  month TEXT, branch_id INTEGER, pub_id INTEGER, account_id INTEGER,
  kind TEXT, description TEXT, action TEXT, rework INTEGER DEFAULT 0,
  status TEXT DEFAULT '접수', created_at TEXT, created_by TEXT
);

CREATE TABLE IF NOT EXISTS images(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT, procedure TEXT, path TEXT,
  status TEXT DEFAULT '보관',   -- 보관 / 배치 / 사용 완료
  ms_id INTEGER, slot INTEGER,
  uploaded_at TEXT, uploaded_by TEXT, used_at TEXT, deleted INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS notifications(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER, kind TEXT, message TEXT, created_at TEXT,
  read INTEGER DEFAULT 0, dedup TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS audit(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT, user TEXT, action TEXT, detail TEXT
);
CREATE TABLE IF NOT EXISTS client_requests(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hospital TEXT, branch_id INTEGER, content TEXT, received TEXT, due TEXT,
  assignee_id INTEGER, status TEXT DEFAULT '접수', note TEXT, created_at TEXT, created_by TEXT
);
CREATE TABLE IF NOT EXISTS reports_generated(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  month TEXT, hospital TEXT, version TEXT, link TEXT, created_at TEXT, created_by TEXT
);
CREATE INDEX IF NOT EXISTS ix_ms_mb ON manuscripts(month, branch_id);
CREATE INDEX IF NOT EXISTS ix_pub_acc ON publications(account_id, cafe_id);
"""


def init_db():
    with conn() as c:
        c.executescript(SCHEMA)
'''

# ============================================================================
# core.common
# ============================================================================
MODULES['core.common'] = r'''"""역할·권한, 설정값, 알림, 변경 이력, 월/마감 계산 등 공통 기능."""
import hashlib
import io
import json
import os
import re
from datetime import date, datetime, timedelta

import pandas as pd

from core.db import ex, now, q, q1, qv, today

# ── 역할 ─────────────────────────────────────────────────────────────────────
ADMIN = "관리자"
MANAGER = "지점 담당자"
WRITER = "원고 작가"
BOARD = "게시판 담당"
EXEC = "실행사"
ROLES = [ADMIN, MANAGER, WRITER, BOARD, EXEC]

HOSPITALS = ["유앤아이", "블루비뇨기과", "로컬"]
REGIONS = ["서울", "경기", "인천", "충청", "전라", "경상", "강원", "제주"]
CAFE_TYPES = ["2030뷰티", "맘", "지역맘", "남성"]
CAFE_STATUS = ["준비 중", "진행 가능", "주의", "위험"]
MS_STATUS = ["작성 전", "작성 중", "검수 대기", "피드백", "완료", "사용 완료"]
ACC_STATUS = ["사용 중", "교체됨", "제재·정지"]
ACC_PURPOSE = ["카페 침투", "댓글 침투", "둘 다"]


def mtype_of(no: int) -> str:
    return "정보성" if no <= 10 else ("후기성" if no <= 19 else "슈퍼세트")


def can_see_exec(role) -> bool:
    """실행사 비공개 원칙: 실행사 이름·카페 아이디·계정 현황은 관리자와 실행사만."""
    return role in (ADMIN, EXEC)


# ── 비밀번호 ─────────────────────────────────────────────────────────────────
def hash_pw(pw: str) -> str:
    salt = os.urandom(8).hex()
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 120_000).hex()
    return f"{salt}${h}"


def check_pw(pw: str, stored: str) -> bool:
    try:
        salt, h = stored.split("$", 1)
    except ValueError:
        return False
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 120_000).hex() == h


# ── 설정 (관리자가 설정 화면에서 바꾸는 숫자들) ──────────────────────────────
DEFAULT_SETTINGS = {
    # 계정 사용 체크
    "cafe_repost_days": 10,          # 같은 계정+같은 카페 N일 이내 발행 금지 (N+1일째부터 가능)
    "comment_month_limit": 40,       # 한 계정 한 달 댓글 한도
    "comment_warn_at": 35,           # 이 개수부터 주의
    "comment_month_target": 1000,    # 월 댓글 목표 (필요 계정 수 계산)
    # 마감
    "deadline_warn_days": 2,         # 마감 N일 전부터 초록 표시
    "alert_hours": [9, 13, 17],      # 마감 당일 알림 시각
    "as_days": 3,                    # AS 처리 기한(일)
    "report_fix_hours": 24,          # 보고서 수정 요청 처리 기한(시간)
    "publish_per_day": 3,            # 실행사 하루 발행 지점 수
    "default_dl_setting_day": 3,     # [다음 달 시작] 기본 마감: 해당 월 N일
    "default_dl_writing_day": 10,
    "default_dl_publish_day": 25,
    # 발행 후 관리
    "as_comment_min": 4,             # 댓글 N개 이하 → 댓글 작업 미완료
    "as_view_min": 10,               # 조회수 N 이하 → 조회수 부족
    "as_view_after_days": 3,         # 발행 후 N일 지난 뒤에만 조회수 판단
    "cafe_delete_rate_warn": 30,     # 카페 삭제율(%) 넘으면 상태 '주의'
    # 검수
    "comment_max_chars": 35,         # 댓글 공백 제외 최대 글자
    "dup_compare_months": 3,         # 같은 지점 지난 N개월 원고와 중복 비교
    "dup_threshold": 0.6,            # 문장 유사도 기준(8글자 조각 겹침 비율)
    "extra_banned_words": ["최고", "100%", "부작용 없", "완치"],
    "keyword_min": {"정보성": 1, "후기성": 1, "슈퍼세트": 2},
    "high_price": 30000,             # 이 단가 이상이면 고단가 카페
    "local_mom_min": 2,              # 지역맘 카페가 이 수보다 적으면 부족 지점
    # 이미지
    "image_slots": 2,
    "image_keep_days": 30,
    # 매칭 규칙 (병원별)
    "match_rules": {
        "유앤아이": {"정보성": ["맘", "지역맘"], "후기성": ["2030뷰티"], "슈퍼세트": ["2030뷰티"]},
        "블루비뇨기과": {"정보성": ["맘", "지역맘", "남성"], "후기성": ["2030뷰티", "남성"], "슈퍼세트": ["2030뷰티", "남성"]},
        "로컬": {"정보성": ["맘", "지역맘"], "후기성": ["2030뷰티"], "슈퍼세트": ["2030뷰티"]},
    },
    "equip_categories": ["리프팅", "제모", "색소", "주사", "비만·바디", "여드름 치료", "여드름 흉터", "기타"],
    "feature_experience": False,     # 체험단 메뉴 (3단계) — 1단계에서는 숨김
    "feature_requests": True,        # 요청 접수 메뉴
}


def get_setting(key):
    v = qv("SELECT value FROM settings WHERE key=?", (key,))
    if v is None:
        return DEFAULT_SETTINGS.get(key)
    try:
        return json.loads(v)
    except Exception:
        return v


def set_setting(key, value, user="system"):
    old = get_setting(key)
    ex("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
       (key, json.dumps(value, ensure_ascii=False)))
    if old != value:
        audit(user, "설정 변경", f"{key}: {old} → {value}")


# ── 이력 / 알림 ──────────────────────────────────────────────────────────────
def audit(user, action, detail=""):
    ex("INSERT INTO audit(at,user,action,detail) VALUES(?,?,?,?)", (now(), user, action, str(detail)[:2000]))


def notify(user_ids, kind, message, dedup=None):
    """알림 문구에는 실행사·작업팀·업체명을 쓰지 않는다 (비공개 원칙)."""
    if isinstance(user_ids, int):
        user_ids = [user_ids]
    for uid in {u for u in user_ids if u}:
        key = f"{dedup}:{uid}" if dedup else None
        try:
            ex("INSERT INTO notifications(user_id,kind,message,created_at,dedup) VALUES(?,?,?,?,?)",
               (uid, kind, message, now(), key))
        except Exception:
            pass  # dedup 중복 → 이미 보냄


def users_by_role(role):
    return [r["id"] for r in q("SELECT id FROM users WHERE role=? AND active=1", (role,))]


def notify_role(role, kind, message, dedup=None):
    notify(users_by_role(role), kind, message, dedup)


def user_name(uid):
    return qv("SELECT name FROM users WHERE id=?", (uid,), "") if uid else ""


def user_options(role=None):
    if role:
        rows = q("SELECT id,name FROM users WHERE active=1 AND role=? ORDER BY name", (role,))
    else:
        rows = q("SELECT id,name FROM users WHERE active=1 ORDER BY name")
    return {r["name"]: r["id"] for r in rows}


# ── 월 ───────────────────────────────────────────────────────────────────────
def month_label(m):
    y, mo = m.split("-")
    return f"{y}년 {int(mo)}월"


def next_month(m):
    y, mo = map(int, m.split("-"))
    mo += 1
    if mo == 13:
        y, mo = y + 1, 1
    return f"{y:04d}-{mo:02d}"


def prev_months(m, n):
    y, mo = map(int, m.split("-"))
    out = []
    for _ in range(n):
        mo -= 1
        if mo == 0:
            y, mo = y - 1, 12
        out.append(f"{y:04d}-{mo:02d}")
    return out


def all_months():
    return [r["month"] for r in q("SELECT month FROM months ORDER BY month DESC")]


# ── 마감 표시 ────────────────────────────────────────────────────────────────
def to_date(s):
    if not s:
        return None
    if isinstance(s, date):
        return s
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def deadline_badge(due, done=False, ref=None):
    """색만으로 구분하지 않도록 글자도 같이: '', '🟢 D-2', '🔴 오늘 마감', '⚫ 지연 1일'"""
    d = to_date(due)
    if not d or done:
        return ""
    ref = ref or date.today()
    diff = (d - ref).days
    warn = int(get_setting("deadline_warn_days"))
    if diff < 0:
        return f"⚫ 지연 {-diff}일"
    if diff == 0:
        return "🔴 오늘 마감"
    if diff <= warn:
        return f"🟢 D-{diff}"
    return ""


def is_overdue(due, done=False):
    d = to_date(due)
    return bool(d and not done and d < date.today())


# ── 지점 ─────────────────────────────────────────────────────────────────────
def branches(hospital=None, active=True):
    sql = "SELECT * FROM branches WHERE 1=1"
    p = []
    if active:
        sql += " AND active=1"
    if hospital and hospital != "전체":
        sql += " AND hospital=?"
        p.append(hospital)
    sql += " ORDER BY name"
    return q(sql, p)


def branch_name(bid):
    return qv("SELECT name FROM branches WHERE id=?", (bid,), "")


def norm_name(s):
    return re.sub(r"\s+", "", str(s or ""))


def my_branch_ids(user, month):
    """'내 담당만 보기' — 역할별 담당 지점"""
    role = user["role"]
    if role == MANAGER:
        rows = q("SELECT branch_id FROM branch_month WHERE month=? AND manager_id=?", (month, user["id"]))
    elif role == WRITER:
        rows = q("SELECT branch_id FROM branch_month WHERE month=? AND writer_id=?", (month, user["id"]))
    elif role == EXEC:
        # 실행사는 로컬 지점 원고 작성 + 완료 원고 발행
        rows = q("SELECT id AS branch_id FROM branches WHERE active=1")
    else:
        rows = q("SELECT id AS branch_id FROM branches WHERE active=1")
    return [r["branch_id"] for r in rows]


def branch_equipment_names(bid):
    return [r["name"] for r in q(
        """SELECT s.name FROM branch_equipment be JOIN equip_std s ON s.id=be.std_id
           WHERE be.branch_id=? AND be.active=1 ORDER BY s.category, s.name""", (bid,))]


def branch_equipment_grouped(bid):
    """원고 화면 드롭다운도 같은 분류로 묶어서 — '분류 · 장비명' 형식"""
    cats = get_setting("equip_categories")
    rows = q("""SELECT s.name, s.category FROM branch_equipment be JOIN equip_std s ON s.id=be.std_id
                WHERE be.branch_id=? AND be.active=1""", (bid,))
    rows.sort(key=lambda r: (cats.index(r["category"]) if r["category"] in cats else 99, r["name"]))
    return [r["name"] for r in rows]


# ── 엑셀 ─────────────────────────────────────────────────────────────────────
def to_excel(sheets: dict) -> bytes:
    """{'탭 이름': DataFrame} → xlsx 바이트"""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        for name, df in sheets.items():
            safe = re.sub(r"[\[\]\*\?/\\:]", "_", str(name))[:31] or "Sheet"
            (df if len(df.columns) else pd.DataFrame({"(비어 있음)": []})).to_excel(w, sheet_name=safe, index=False)
            ws = w.sheets[safe]
            for col in ws.columns:
                width = max((len(str(c.value)) if c.value is not None else 0) for c in col[:200])
                ws.column_dimensions[col[0].column_letter].width = min(max(8, width * 1.6), 60)
    return buf.getvalue()


def cafe_base(url: str):
    """https://cafe.naver.com/<카페ID>/<글번호> → (카페ID, 글번호)"""
    if not url:
        return None, None
    u = url.strip()
    m = re.search(r"cafe\.naver\.com/(?:ca-fe/cafes/(\d+)/articles/(\d+)|([A-Za-z0-9_\-]+)(?:/(\d+))?)", u)
    if not m:
        return None, None
    if m.group(1):
        return m.group(1), m.group(2)
    art = m.group(4)
    m2 = re.search(r"articleid=(\d+)", u, re.I)
    if not art and m2:
        art = m2.group(1)
    return m.group(3), art
'''

# ============================================================================
# core.ops
# ============================================================================
MODULES['core.ops'] = r'''"""업무 규칙 (화면과 분리된 로직). 화면은 이 함수들만 부른다."""
import json
import math
import os
from datetime import date, datetime, timedelta

from core.common import (ADMIN, BOARD, EXEC, MANAGER, WRITER, audit, branch_name, cafe_base,
                         deadline_badge, get_setting, mtype_of, next_month, norm_name, notify,
                         notify_role, to_date, user_name)
from core.db import IMG_DIR, ex, exmany, now, q, q1, qv, today

TEXT_FIELDS = ["title", "body", "c1", "r1", "c2", "r2", "c3", "r3"]
INPUT_FIELDS = ["keyword", "equipment", "special", "no_equip_mention"]


# ═════════════════════════════════════════════════════════════════════════════
# 월 단위 운영
# ═════════════════════════════════════════════════════════════════════════════
def ensure_month_frame(month, branch_id):
    """지점별 20건 틀 (정보성 10 / 후기성 9 / 슈퍼세트 1)"""
    exmany("INSERT OR IGNORE INTO manuscripts(month,branch_id,no,mtype,status) VALUES(?,?,?,?, '작성 전')",
           [(month, branch_id, n, mtype_of(n)) for n in range(1, 21)])


def start_month(month, user, deadlines=None, carry_from=None):
    """[다음 달 시작]: 지점·담당자·작가·원고 재료 이월, 20건 틀 생성, 마감일 일괄 지정.
    보유장비는 지점에 붙어 있으므로 자동으로 이어진다."""
    ex("INSERT OR IGNORE INTO months(month,created_at,created_by) VALUES(?,?,?)", (month, now(), user))
    y, m = map(int, month.split("-"))
    dl = deadlines or {}

    def d(day):
        day = min(int(day), 28)
        return f"{y:04d}-{m:02d}-{day:02d}"

    dls = dl.get("setting") or d(get_setting("default_dl_setting_day"))
    dlw = dl.get("writing") or d(get_setting("default_dl_writing_day"))
    dlp = dl.get("publish") or d(get_setting("default_dl_publish_day"))
    n = 0
    for b in q("SELECT id FROM branches WHERE active=1"):
        prev = q1("SELECT * FROM branch_month WHERE month=? AND branch_id=?", (carry_from, b["id"])) if carry_from else None
        ex("""INSERT OR IGNORE INTO branch_month(month,branch_id,manager_id,writer_id,req_notes,competitor,
              must_include,special,dl_setting,dl_writing,dl_publish) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
           (month, b["id"], prev and prev["manager_id"], prev and prev["writer_id"],
            prev and prev["req_notes"], prev and prev["competitor"], prev and prev["must_include"],
            prev and prev["special"], dls, dlw, dlp))
        ensure_month_frame(month, b["id"])
        n += 1
    audit(user, "다음 달 시작", f"{month}: 지점 {n}곳 이월, 20건 틀 생성 (마감 {dls}/{dlw}/{dlp})")
    return n


# ═════════════════════════════════════════════════════════════════════════════
# 원고
# ═════════════════════════════════════════════════════════════════════════════
def ms_rows(month, branch_id):
    return q("SELECT * FROM manuscripts WHERE month=? AND branch_id=? ORDER BY no", (month, branch_id))


def _is_written(r):
    return bool((r.get("title") or "").strip() or (r.get("body") or "").strip())


def save_manuscripts(month, branch_id, edited_rows, user):
    """표에서 고친 행을 저장. 상태 규칙:
    - 글을 새로 쓰거나 고치면 → 검수 대기 (작성 중이던 것도 저장 시 검수 대기)
    - '완료' 뒤에 글을 고치면 → 자동으로 '검수 대기'로 돌아감
    - 원고 재료(키워드·장비·특이사항)만 바뀐 경우 상태 유지
    저장 후 자동 검수를 돌린다."""
    old = {r["no"]: r for r in ms_rows(month, branch_id)}
    changed_text = 0
    for r in edited_rows:
        no = int(r["no"])
        o = old.get(no)
        if not o:
            continue
        diffs = {}
        for f in TEXT_FIELDS + INPUT_FIELDS:
            nv = r.get(f)
            if f == "no_equip_mention":
                nv = 1 if nv in (True, 1, "1", "True") else 0
            else:
                nv = "" if nv is None or (isinstance(nv, float) and math.isnan(nv)) else str(nv)
            ov = o.get(f)
            ov = (ov or 0) if f == "no_equip_mention" else (ov or "")
            if nv != ov:
                diffs[f] = (ov, nv)
        if not diffs:
            continue
        status = o["status"]
        text_changed = any(f in TEXT_FIELDS for f in diffs)
        if text_changed:
            changed_text += 1
            if status == "완료":
                status = "검수 대기"
            elif status in ("작성 전", "작성 중", "피드백"):
                status = "검수 대기" if _is_written({**o, **{k: v[1] for k, v in diffs.items()}}) else "작성 전"
        # 특이사항에 '장비언급X' 같은 규칙이 있으면 자동으로 장비명 언급 금지 체크
        sp = diffs.get("special", (None, o.get("special") or ""))[1]
        if sp and any(k in sp.replace(" ", "") for k in ["장비언급X", "장비언급x", "장비명언급금지", "장비언급금지"]):
            diffs["no_equip_mention"] = (o.get("no_equip_mention"), 1)
        sets = ", ".join(f"{f}=?" for f in diffs) + ", status=?, updated_at=?, updated_by=?"
        ex(f"UPDATE manuscripts SET {sets} WHERE id=?",
           [v[1] for v in diffs.values()] + [status, now(), user["name"], o["id"]])
        detail = "; ".join(f"{k}: {str(v[0])[:30]} → {str(v[1])[:30]}" for k, v in diffs.items())
        ex("INSERT INTO ms_history(ms_id,at,user,action,detail) VALUES(?,?,?,?,?)",
           (o["id"], now(), user["name"], "수정" + (f" (상태 {o['status']}→{status})" if status != o["status"] else ""), detail))
    from core.checks import check_branch
    res = check_branch(month, branch_id)
    if changed_text:
        audit(user["name"], "원고 저장", f"{month} {branch_name(branch_id)} {changed_text}건")
    return res


def set_status(ms_ids, status, user, feedback=None):
    """피드백 / 완료 (관리자 컨펌). 묶음 단위 변경도 이 함수."""
    for mid in ms_ids:
        o = q1("SELECT * FROM manuscripts WHERE id=?", (mid,))
        if not o or not _is_written(o):
            continue
        if status == "완료":
            ex("UPDATE manuscripts SET status='완료', confirmed_by=?, confirmed_at=? WHERE id=?", (user["name"], now(), mid))
        elif status == "피드백":
            ex("UPDATE manuscripts SET status='피드백', feedback=? WHERE id=?", (feedback or o.get("feedback"), mid))
        else:
            ex("UPDATE manuscripts SET status=? WHERE id=?", (status, mid))
        ex("INSERT INTO ms_history(ms_id,at,user,action,detail) VALUES(?,?,?,?,?)",
           (mid, now(), user["name"], f"상태 → {status}", feedback or ""))
    if not ms_ids:
        return
    o = q1("SELECT month, branch_id FROM manuscripts WHERE id=?", (ms_ids[0],))
    bm = q1("SELECT * FROM branch_month WHERE month=? AND branch_id=?", (o["month"], o["branch_id"]))
    bname = branch_name(o["branch_id"])
    if status == "피드백" and bm:
        notify(bm["writer_id"], "피드백", f"[{bname}] 원고 {len(ms_ids)}건에 피드백이 있습니다: {feedback or ''}")
    if status == "완료":
        done = qv("SELECT COUNT(*) FROM manuscripts WHERE month=? AND branch_id=? AND status IN ('완료','사용 완료')",
                  (o["month"], o["branch_id"]), 0)
        if done == 20:
            notify_role(EXEC, "발행 가능", f"[{bname}] 원고 20건이 발행 가능 목록에 올라왔습니다.",
                        dedup=f"pubready:{o['month']}:{o['branch_id']}")
            plan_publish_dates(o["month"])


def material_done(month, branch_id, user):
    ex("UPDATE branch_month SET material_done=1 WHERE month=? AND branch_id=?", (month, branch_id))
    bm = q1("SELECT writer_id FROM branch_month WHERE month=? AND branch_id=?", (month, branch_id))
    notify(bm and bm["writer_id"], "할 일", f"[{branch_name(branch_id)}] 원고 재료 입력이 끝났습니다. 작성을 시작해 주세요.")
    audit(user["name"], "원고 재료 입력 완료", branch_name(branch_id))


def progress(month, branch_id):
    rows = q("SELECT mtype,status,keyword FROM manuscripts WHERE month=? AND branch_id=?", (month, branch_id))
    total = len(rows)
    done = sum(r["status"] in ("완료", "사용 완료") for r in rows)
    written = sum(r["status"] not in ("작성 전", "작성 중") for r in rows)
    fb = sum(r["status"] == "피드백" for r in rows)
    kw_missing = sum(not (r["keyword"] or "").strip() for r in rows)
    by = {}
    for t in ["정보성", "후기성", "슈퍼세트"]:
        rr = [r for r in rows if r["mtype"] == t]
        st = {r["status"] for r in rr}
        if not rr:
            by[t] = "-"
        elif "피드백" in st:
            by[t] = "피드백"
        elif st <= {"완료", "사용 완료"}:
            by[t] = "완료"
        elif st <= {"작성 전"}:
            by[t] = "작성 전"
        else:
            by[t] = "진행 중"
    return {"total": total, "done": done, "written": written, "feedback": fb, "kw_missing": kw_missing, "by": by}


def stage_of(month, branch_id):
    """키워드 입력 → 작성 → 검수 → 완료 → 발행 → 보고서"""
    p = progress(month, branch_id)
    bm = q1("SELECT * FROM branch_month WHERE month=? AND branch_id=?", (month, branch_id)) or {}
    pub = qv("SELECT COUNT(*) FROM publications WHERE month=? AND branch_id=? AND url<>''", (month, branch_id), 0)
    if bm.get("report_stage") == "최종 확정":
        return "보고서 완료"
    if pub >= 20:
        return "보고서"
    if pub > 0:
        return "발행"
    if p["total"] and p["done"] == p["total"]:
        return "완료"
    if p["written"] > 0:
        return "검수"
    if p["kw_missing"] > 0 and not bm.get("material_done"):
        return "키워드 입력"
    return "작성"


# ═════════════════════════════════════════════════════════════════════════════
# 계정 사용 체크 (카페 침투·댓글 침투 공통)
# ═════════════════════════════════════════════════════════════════════════════
def account_cafe_check(account_id, cafe_id, on_date=None, exclude_pub=None):
    """같은 계정 + 같은 카페 N일 이내 발행 금지 (N+1일째부터 가능).
    return (ok, 메시지, 다시 쓸 수 있는 날)"""
    days = int(get_setting("cafe_repost_days"))
    on = to_date(on_date) or date.today()
    rows = q("""SELECT pub_date FROM publications WHERE account_id=? AND cafe_id=? AND pub_date IS NOT NULL
                AND pub_date<>'' AND id<>? ORDER BY pub_date DESC""", (account_id, cafe_id, exclude_pub or -1))
    for r in rows:
        last = to_date(r["pub_date"])
        if last and abs((on - last).days) < days:
            avail = last + timedelta(days=days)
            return False, f"{last.isoformat()} 사용 — {avail.isoformat()}부터 가능", avail
    return True, "사용 가능", None


def account_comment_count(account_id, month):
    return qv("SELECT COUNT(*) FROM comment_targets WHERE account_id=? AND status='완료' AND substr(done_date,1,7)=?",
              (account_id, month), 0)


def account_comment_check(account_id, month):
    lim, warn = int(get_setting("comment_month_limit")), int(get_setting("comment_warn_at"))
    n = account_comment_count(account_id, month)
    if n >= lim:
        return False, f"이번 달 {n}/{lim} — 입력 차단", n
    if n >= warn:
        return True, f"이번 달 {n}/{lim} — 주의 (잔여 {lim - n})", n
    return True, f"이번 달 {n}/{lim} (잔여 {lim - n})", n


def usable_accounts(purpose):
    """제재·정지, 교체됨 계정은 발행·댓글 입력에서 고를 수 없다."""
    ok = ["둘 다", purpose]
    return q(f"SELECT * FROM accounts WHERE status='사용 중' AND purpose IN ({','.join('?' * len(ok))}) ORDER BY acc_id", ok)


def accounts_for_cafe(cafe_id, on_date=None):
    out = []
    for a in usable_accounts("카페 침투"):
        ok, msg, avail = account_cafe_check(a["id"], cafe_id, on_date)
        out.append({"id": a["id"], "계정": a["acc_id"], "닉네임": a["nickname"], "가능": ok, "상태": msg})
    return out


# ═════════════════════════════════════════════════════════════════════════════
# 카페 선택 사전 체크 (cafe-match-check 규칙)
# ═════════════════════════════════════════════════════════════════════════════
def cafe_linked_to_branch(cafe, branch):
    if cafe["ctype"] != "지역맘":
        return True
    links = q("SELECT * FROM cafe_links WHERE cafe_id=?", (cafe["id"],))
    for l in links:
        if l["link_type"] == "지점" and l["branch_id"] == branch["id"]:
            return True
        if l["link_type"] == "지역" and l["region"] and l["region"] == branch["region"]:
            return True
    return False


def cafe_precheck(ms, cafe_id, exclude_pub=None):
    """return (막힘 여부, [경고 문구])"""
    cafe = q1("SELECT * FROM cafes WHERE id=?", (cafe_id,))
    branch = q1("SELECT * FROM branches WHERE id=?", (ms["branch_id"],))
    msgs, block = [], False
    rules = get_setting("match_rules").get(branch["hospital"], {})
    allowed = rules.get(ms["mtype"], [])
    if allowed and cafe["ctype"] not in allowed:
        msgs.append(f"❌ 유형 불일치: {ms['mtype']}은 {'/'.join(allowed)} 카페 (선택: {cafe['ctype']})")
        block = True
    if not cafe_linked_to_branch(cafe, branch):
        msgs.append(f"❌ 지역맘 지점 불일치: 이 카페는 {branch['name']}에 연결되어 있지 않음")
        block = True
    dup = q("""SELECT m.no FROM publications p JOIN manuscripts m ON m.id=p.ms_id
               WHERE p.month=? AND p.branch_id=? AND p.cafe_id=? AND p.id<>?""",
            (ms["month"], ms["branch_id"], cafe_id, exclude_pub or -1))
    if dup:
        msgs.append(f"❌ 같은 지점 카페 중복: {', '.join(str(d['no']) + '번' for d in dup)}에서 이미 사용")
        block = True
    if cafe["status"] in ("주의", "위험"):
        msgs.append(f"⚠️ 카페 상태: {cafe['status']}")
    if cafe["status"] == "준비 중":
        msgs.append("⚠️ 준비 중인 카페 (진행 가능 전환 전)")
    if (cafe["price"] or 0) >= int(get_setting("high_price")):
        msgs.append(f"💰 고단가 카페 ({cafe['price']:,}원)")
    return block, msgs


def eligible_cafes(ms):
    """이 원고에 쓸 수 있는 카페 후보 + 이번 달 남은 사용 가능 횟수(=지금 쓸 수 있는 계정 수)"""
    out = []
    for c in q("SELECT * FROM cafes WHERE archived=0 AND status IN ('진행 가능','주의','위험') ORDER BY name"):
        block, msgs = cafe_precheck(ms, c["id"])
        avail = sum(a["가능"] for a in accounts_for_cafe(c["id"]))
        out.append({"id": c["id"], "카페": c["name"], "유형": c["ctype"], "상태": c["status"],
                    "적합": not block, "사용 가능 계정": avail, "체크": " / ".join(msgs) or "✅ 통과"})
    return out


# ═════════════════════════════════════════════════════════════════════════════
# 발행
# ═════════════════════════════════════════════════════════════════════════════
def ready_branches(month):
    """20건 모두 완료(또는 사용 완료)인 지점 — 실행사 발행 가능 목록"""
    rows = q("""SELECT branch_id, SUM(status IN ('완료','사용 완료')) AS done, COUNT(*) AS n
                FROM manuscripts WHERE month=? GROUP BY branch_id""", (month,))
    return [r["branch_id"] for r in rows if r["n"] and r["done"] == r["n"]]


def plan_publish_dates(month):
    """완료된 지점을 하루 N지점씩 나눠 발행 예정일을 자동으로 잡는다 (이미 잡힌 곳은 유지)."""
    per = max(1, int(get_setting("publish_per_day")))
    ready = ready_branches(month)
    rows = q("SELECT branch_id, planned_publish FROM branch_month WHERE month=?", (month,))
    planned = {r["branch_id"]: r["planned_publish"] for r in rows}
    counts = {}
    for d in planned.values():
        if d:
            counts[d] = counts.get(d, 0) + 1
    day = date.today()
    for bid in ready:
        if planned.get(bid):
            continue
        while counts.get(day.isoformat(), 0) >= per:
            day += timedelta(days=1)
        ex("UPDATE branch_month SET planned_publish=? WHERE month=? AND branch_id=?", (day.isoformat(), month, bid))
        counts[day.isoformat()] = counts.get(day.isoformat(), 0) + 1


def publish_backlog(month):
    """밀림 경고: 예정일이 지난 지점 / 남은 지점을 하루 N곳으로 마감까지 못 끝내는 경우"""
    per = max(1, int(get_setting("publish_per_day")))
    warns = []
    late = []
    for r in q("SELECT * FROM branch_month WHERE month=? AND planned_publish IS NOT NULL", (month,)):
        pubs = qv("SELECT COUNT(*) FROM publications WHERE month=? AND branch_id=? AND url<>''", (month, r["branch_id"]), 0)
        if pubs < 20 and to_date(r["planned_publish"]) and to_date(r["planned_publish"]) < date.today():
            late.append(branch_name(r["branch_id"]))
    if late:
        warns.append(f"발행 예정일이 지난 지점: {', '.join(late)}")
    remaining = [b for b in q("SELECT branch_id, dl_publish FROM branch_month WHERE month=?", (month,))
                 if qv("SELECT COUNT(*) FROM publications WHERE month=? AND branch_id=? AND url<>''",
                       (month, b["branch_id"]), 0) < 20]
    dls = [to_date(b["dl_publish"]) for b in remaining if b["dl_publish"]]
    if remaining and dls:
        last = max(dls)
        days_left = (last - date.today()).days + 1
        need = math.ceil(len(remaining) / per)
        if days_left < need:
            warns.append(f"남은 {len(remaining)}지점을 하루 {per}곳씩 하면 {need}일 필요 — 마감까지 {max(days_left, 0)}일")
    return warns


def save_publication(ms_id, cafe_id, account_id, url, pub_date, user, force=False):
    ms = q1("SELECT * FROM manuscripts WHERE id=?", (ms_id,))
    old = q1("SELECT * FROM publications WHERE ms_id=?", (ms_id,))
    block, msgs = cafe_precheck(ms, cafe_id, exclude_pub=old and old["id"])
    ok, amsg, _ = account_cafe_check(account_id, cafe_id, pub_date, exclude_pub=old and old["id"])
    acc = q1("SELECT * FROM accounts WHERE id=?", (account_id,))
    if acc and acc["status"] != "사용 중":
        return False, [f"❌ {acc['status']} 계정은 고를 수 없습니다"]
    if not ok:
        return False, [f"❌ 계정 10일 규칙: {amsg}"]
    if block and not force:
        return False, msgs
    if url:
        dup = q1("SELECT id FROM publications WHERE url=? AND ms_id<>?", (url.strip(), ms_id))
        if dup:
            return False, ["❌ 이미 등록된 URL입니다"]
    if old:
        ex("""UPDATE publications SET cafe_id=?, account_id=?, url=?, pub_date=? WHERE id=?""",
           (cafe_id, account_id, url.strip(), pub_date, old["id"]))
    else:
        ex("""INSERT INTO publications(ms_id,month,branch_id,cafe_id,account_id,url,pub_date,created_at,created_by)
              VALUES(?,?,?,?,?,?,?,?,?)""",
           (ms_id, ms["month"], ms["branch_id"], cafe_id, account_id, url.strip(), pub_date, now(), user["name"]))
    if url:
        ex("UPDATE manuscripts SET status='사용 완료' WHERE id=?", (ms_id,))
        ex("INSERT INTO ms_history(ms_id,at,user,action,detail) VALUES(?,?,?,?,?)",
           (ms_id, now(), user["name"], "상태 → 사용 완료", url))
        # 배치된 이미지 사용 완료
    audit(user["name"], "발행 입력", f"{branch_name(ms['branch_id'])} {ms['no']}번")
    return True, msgs


# ═════════════════════════════════════════════════════════════════════════════
# 발행 후 관리 (삭제·조회수·댓글) → AS
# ═════════════════════════════════════════════════════════════════════════════
def evaluate_publication(pub, deleted=None):
    cmin = int(get_setting("as_comment_min"))
    vmin = int(get_setting("as_view_min"))
    after = int(get_setting("as_view_after_days"))
    state = "정상"
    if deleted:
        state = "삭제됨"
    elif pub.get("comments") is not None and pub["comments"] != "" and int(pub["comments"]) <= cmin:
        state = "댓글 작업 미완료"
    else:
        d = to_date(pub.get("pub_date"))
        if d and (date.today() - d).days >= after and pub.get("views") is not None and pub["views"] != "" \
                and int(pub["views"]) <= vmin:
            state = "조회수 부족"
    return state


def update_check(pub_id, views, comments, deleted, user):
    p = q1("SELECT * FROM publications WHERE id=?", (pub_id,))
    p.update({"views": views, "comments": comments})
    state = evaluate_publication(p, deleted)
    as_state = p["as_state"] or ""
    opened = p["as_opened_at"]
    if state != "정상" and as_state != "AS 대기":
        as_state, opened = "AS 대기", now()
        notify_role(EXEC, "AS", f"[{branch_name(p['branch_id'])}] 발행 글 확인 필요: {state}",
                    dedup=f"as:{pub_id}:{state}")
    ex("""UPDATE publications SET views=?, comments=?, last_checked=?, check_state=?, as_state=?, as_opened_at=?
          WHERE id=?""", (views, comments, now(), state, as_state, opened, pub_id))
    update_cafe_delete_rates(user)
    return state


def resolve_as(pub_id, new_url, user):
    p = q1("SELECT * FROM publications WHERE id=?", (pub_id,))
    if new_url and new_url.strip() != p["url"]:
        ex("UPDATE publications SET url=?, pub_date=? WHERE id=?", (new_url.strip(), today(), pub_id))
    ex("UPDATE publications SET as_state='처리 완료', as_done_at=?, check_state='정상' WHERE id=?", (now(), pub_id))
    audit(user["name"], "AS 처리 완료", f"pub {pub_id} {new_url or ''}")


def try_fetch_link(url):
    """링크가 열리는지만 확인 (네이버 카페 본문·조회수는 로그인·스크립트가 필요해 여기서 못 읽음 →
    조회수·댓글 수는 수집 프로그램 결과를 CSV로 올리거나 직접 입력)"""
    try:
        import requests
        r = requests.get(url, timeout=8, allow_redirects=True)
        return r.status_code < 400, r.status_code
    except Exception as e:  # noqa
        return None, str(e)[:60]


def update_cafe_delete_rates(user=None):
    th = float(get_setting("cafe_delete_rate_warn"))
    for c in q("""SELECT cafe_id, COUNT(*) n, SUM(check_state='삭제됨') d FROM publications
                  WHERE cafe_id IS NOT NULL GROUP BY cafe_id"""):
        if c["n"] >= 3 and c["d"] * 100.0 / c["n"] > th:
            cafe = q1("SELECT * FROM cafes WHERE id=?", (c["cafe_id"],))
            if cafe and cafe["status"] == "진행 가능":
                ex("UPDATE cafes SET status='주의' WHERE id=?", (cafe["id"],))
                ex("INSERT INTO cafe_log(cafe_id,at,user,old,new,reason) VALUES(?,?,?,?,?,?)",
                   (cafe["id"], now(), "자동", "진행 가능", "주의", f"삭제율 {c['d']}/{c['n']}"))


# ═════════════════════════════════════════════════════════════════════════════
# 보고서 흐름: 실행사 기입 → 관리자 1차 확인 → 지점 담당자 확인 → 관리자 최종본
# ═════════════════════════════════════════════════════════════════════════════
REPORT_STAGES = ["작성 중", "관리자 확인", "지점 확인", "수정 중", "최종 대기", "최종 확정"]


def report_rows(month, branch_id):
    return q("""SELECT m.id ms_id, m.no, m.mtype, m.title, m.keyword, p.id pub_id, p.pub_date, p.url,
                       p.views, p.comments, p.check_state, p.as_state,
                       c.name cafe_name, c.url cafe_url, c.ctype, a.acc_id
                FROM manuscripts m
                LEFT JOIN publications p ON p.ms_id=m.id
                LEFT JOIN cafes c ON c.id=p.cafe_id
                LEFT JOIN accounts a ON a.id=p.account_id
                WHERE m.month=? AND m.branch_id=? ORDER BY m.no""", (month, branch_id))


def report_auto_check(month, branch_id):
    """관리자 1차 확인 자동 체크: 빈칸, 형식, 유형 매칭, 중복, 발행 건수"""
    rows = report_rows(month, branch_id)
    problems = []
    seen = {}
    for r in rows:
        if not r["pub_id"]:
            problems.append((r, "발행 정보 없음"))
            continue
        miss = [k for k, v in [("발행일", r["pub_date"]), ("카페", r["cafe_name"]), ("카페 아이디", r["acc_id"]),
                               ("URL", r["url"])] if not v]
        if miss:
            problems.append((r, "빈칸: " + ", ".join(miss)))
        if r["url"] and not cafe_base(r["url"])[0]:
            problems.append((r, "URL 형식 오류 (cafe.naver.com 아님)"))
        if r["pub_date"] and not to_date(r["pub_date"]):
            problems.append((r, "발행일 형식 오류"))
        if r["cafe_name"]:
            ms = q1("SELECT * FROM manuscripts WHERE id=?", (r["ms_id"],))
            cid = qv("SELECT cafe_id FROM publications WHERE id=?", (r["pub_id"],))
            block, msgs = cafe_precheck(ms, cid, exclude_pub=r["pub_id"])
            for m in msgs:
                if m.startswith("❌") and "중복" not in m:
                    problems.append((r, m[2:]))
            key = r["cafe_url"]
            if key in seen:
                problems.append((r, f"카페 중복 ({seen[key]}번과 같은 카페)"))
            seen.setdefault(key, r["no"])
    n_pub = sum(1 for r in rows if r["url"])
    return problems, n_pub


def report_request_confirm(month, branch_id, user):
    """실행사: 지점 단위 '기입 완료 · 확인 요청'"""
    ex("UPDATE branch_month SET report_stage='관리자 확인', report_requested_at=? WHERE month=? AND branch_id=?",
       (now(), month, branch_id))
    notify_role(ADMIN, "확인 요청", f"[{branch_name(branch_id)}] 보고서 확인 요청이 접수되었습니다.")
    audit(user["name"], "보고서 기입 완료", branch_name(branch_id))


def report_admin_pass(month, branch_id, user, returns=None):
    """관리자 1차: 문제 행은 사유를 붙여 되돌림 / 통과 시 지점 담당자 확인으로 (로컬은 바로 최종 대기)"""
    returns = returns or []
    if returns:
        for pub_id, reason in returns:
            ex("""INSERT INTO report_issues(pub_id,month,branch_id,source,reason,created_at,created_by)
                  VALUES(?,?,?,?,?,?,?)""", (pub_id, month, branch_id, "관리자 1차", reason, now(), user["name"]))
        ex("UPDATE branch_month SET report_stage='작성 중' WHERE month=? AND branch_id=?", (month, branch_id))
        notify_role(EXEC, "수정 요청", f"[{branch_name(branch_id)}] 보고서 {len(returns)}행 수정 요청이 있습니다.")
        return "작성 중"
    hosp = qv("SELECT hospital FROM branches WHERE id=?", (branch_id,))
    nxt = "최종 대기" if hosp == "로컬" else "지점 확인"
    ex("UPDATE branch_month SET report_stage=? WHERE month=? AND branch_id=?", (nxt, month, branch_id))
    if nxt == "지점 확인":
        mid = qv("SELECT manager_id FROM branch_month WHERE month=? AND branch_id=?", (month, branch_id))
        notify(mid, "확인 요청", f"[{branch_name(branch_id)}] 보고서 확인을 부탁드립니다.")
    audit(user["name"], "보고서 1차 확인 통과", branch_name(branch_id))
    return nxt


def report_manager_ok(month, branch_id, user):
    open_n = qv("""SELECT COUNT(*) FROM report_issues WHERE month=? AND branch_id=? AND source='지점 확인'
                   AND status IN ('접수됨','처리 중')""", (month, branch_id), 0)
    if open_n:
        return False
    ex("UPDATE branch_month SET report_stage='최종 대기', report_confirmed_at=? WHERE month=? AND branch_id=?",
       (now(), month, branch_id))
    ex("""UPDATE report_issues SET status='확인 완료' WHERE month=? AND branch_id=? AND status='반영 완료'""",
       (month, branch_id))
    notify_role(ADMIN, "확인 완료", f"[{branch_name(branch_id)}] 지점 확인이 끝났습니다 (이상 없음).")
    audit(user["name"], "보고서 지점 확인", branch_name(branch_id))
    return True


def report_manager_request(month, branch_id, pub_id, reason, user):
    """지점 담당자 수정 요청은 관리자를 거치지 않고 바로 처리 쪽으로 간다 (관리자는 참조)."""
    ex("""INSERT INTO report_issues(pub_id,month,branch_id,source,reason,created_at,created_by)
          VALUES(?,?,?,?,?,?,?)""", (pub_id, month, branch_id, "지점 확인", reason, now(), user["name"]))
    ex("UPDATE branch_month SET report_stage='수정 중' WHERE month=? AND branch_id=?", (month, branch_id))
    notify_role(EXEC, "수정 요청", f"[{branch_name(branch_id)}] 지점 확인 요청: {reason}")
    notify_role(ADMIN, "수정 요청(참조)", f"[{branch_name(branch_id)}] 보고서 수정 요청: {reason}")


def report_issue_update(issue_id, status, user):
    ex("UPDATE report_issues SET status=?, resolved_at=? WHERE id=?",
       (status, now() if status == "반영 완료" else None, issue_id))
    it = q1("SELECT * FROM report_issues WHERE id=?", (issue_id,))
    if status == "반영 완료":
        if it["source"] == "지점 확인":
            mid = qv("SELECT manager_id FROM branch_month WHERE month=? AND branch_id=?", (it["month"], it["branch_id"]))
            notify(mid, "수정 완료", f"[{branch_name(it['branch_id'])}] 수정이 반영되었습니다. 다시 확인해 주세요.")
            left = qv("""SELECT COUNT(*) FROM report_issues WHERE month=? AND branch_id=? AND source='지점 확인'
                         AND status IN ('접수됨','처리 중')""", (it["month"], it["branch_id"]), 0)
            if not left:
                ex("UPDATE branch_month SET report_stage='지점 확인' WHERE month=? AND branch_id=?",
                   (it["month"], it["branch_id"]))


def report_finalize(month, branch_id, user):
    ex("UPDATE branch_month SET report_stage='최종 확정', report_locked=1, report_final_at=? WHERE month=? AND branch_id=?",
       (now(), month, branch_id))
    audit(user["name"], "보고서 최종 확정", f"{month} {branch_name(branch_id)}")


# ═════════════════════════════════════════════════════════════════════════════
# 마감·지연 알림 (접속할 때마다 한 번씩 훑는다)
# ═════════════════════════════════════════════════════════════════════════════
def deadline_sweep(month):
    """마감 당일: 설정 시각(9·13·17시)마다 담당자에게 알림.
    마감 지남: 매일 한 번 담당자와 관리자에게. 초록(D-2, D-1)은 표시만."""
    hour = datetime.now().hour
    slots = [h for h in get_setting("alert_hours") if h <= hour]
    slot = slots[-1] if slots else None
    td = today()
    for bm in q("SELECT * FROM branch_month WHERE month=?", (month,)):
        bname = branch_name(bm["branch_id"])
        p = progress(month, bm["branch_id"])
        stages = [
            ("키워드·장비·특이사항 세팅", bm["dl_setting"], bm["manager_id"], bm["material_done"] or p["kw_missing"] == 0),
            ("원고 작성", bm["dl_writing"], bm["writer_id"], p["written"] >= p["total"] > 0),
        ]
        for name, due, uid, done in stages:
            d = to_date(due)
            if not d or done:
                continue
            if d.isoformat() == td and slot is not None:
                notify(uid, "마감 임박", f"[{bname}] {name} 오늘 마감입니다.", dedup=f"dl:{month}:{bm['branch_id']}:{name}:{td}:{slot}")
            elif d < date.today():
                late = (date.today() - d).days
                msg = f"[{bname}] {name} 지연 {late}일"
                notify(uid, "지연", msg, dedup=f"late:{month}:{bm['branch_id']}:{name}:{td}")
                notify_role(ADMIN, "지연", msg, dedup=f"late:{month}:{bm['branch_id']}:{name}:{td}")
    # 보고서 수정 요청 처리 기한
    hrs = int(get_setting("report_fix_hours"))
    for it in q("SELECT * FROM report_issues WHERE status IN ('접수됨','처리 중')"):
        try:
            age = (datetime.now() - datetime.strptime(it["created_at"], "%Y-%m-%d %H:%M:%S")).total_seconds() / 3600
        except Exception:
            continue
        if age > hrs:
            notify_role(ADMIN, "지연", f"[{branch_name(it['branch_id'])}] 보고서 수정 요청이 {int(age)}시간째 처리되지 않았습니다.",
                        dedup=f"fixlate:{it['id']}:{td}")
    # 밀림 경고
    for w in publish_backlog(month):
        notify_role(ADMIN, "발행 밀림", w, dedup=f"backlog:{month}:{td}:{hash(w)}")
    # 이미지 보관 기간 지난 사용 완료 파일 삭제
    keep = int(get_setting("image_keep_days"))
    cutoff = (datetime.now() - timedelta(days=keep)).strftime("%Y-%m-%d %H:%M:%S")
    for im in q("SELECT * FROM images WHERE status='사용 완료' AND deleted=0 AND used_at < ?", (cutoff,)):
        try:
            os.remove(im["path"])
        except OSError:
            pass
        ex("UPDATE images SET deleted=1 WHERE id=?", (im["id"],))


# ═════════════════════════════════════════════════════════════════════════════
# 이미지
# ═════════════════════════════════════════════════════════════════════════════
def next_image_name(procedure, ext):
    n = qv("SELECT COUNT(*) FROM images WHERE procedure=?", (procedure,), 0) + 1
    while q1("SELECT id FROM images WHERE filename=?", (f"{procedure}{n}{ext}",)):
        n += 1
    return f"{procedure}{n}{ext}"


def save_image(uploaded, procedure, user):
    ext = os.path.splitext(uploaded.name)[1].lower() or ".png"
    fname = next_image_name(procedure, ext)
    path = os.path.join(IMG_DIR, f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext}")
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    ex("INSERT INTO images(filename,procedure,path,uploaded_at,uploaded_by) VALUES(?,?,?,?,?)",
       (fname, procedure, path, now(), user["name"]))
    return fname


def place_image(image_id, ms_id, slot, user):
    """한 이미지는 한 원고에만 배치 (중복 사용 막음)"""
    ex("UPDATE images SET status='보관', ms_id=NULL, slot=NULL WHERE ms_id=? AND slot=? AND status='배치'", (ms_id, slot))
    ex("UPDATE images SET status='배치', ms_id=?, slot=? WHERE id=? AND status='보관'", (ms_id, slot, image_id))
    audit(user["name"], "이미지 배치", f"img {image_id} → ms {ms_id} 칸 {slot}")


def ms_images(ms_id):
    return q("SELECT * FROM images WHERE ms_id=? AND deleted=0 ORDER BY slot", (ms_id,))


def mark_images_used(ms_id):
    ex("UPDATE images SET status='사용 완료', used_at=? WHERE ms_id=? AND status='배치'", (now(), ms_id))


# ═════════════════════════════════════════════════════════════════════════════
# 지점 담당자 자동 배정 (배정 시트)
# ═════════════════════════════════════════════════════════════════════════════
def resolve_branch(raw):
    """배정 시트 지점명 → 프로그램 지점. 대응표(branch_aliases) → 정확 일치 → 부분 일치"""
    key = norm_name(raw)
    if not key:
        return None
    r = q1("SELECT branch_id FROM branch_aliases WHERE alias=?", (key,))
    if r:
        return r["branch_id"]
    stripped = key.replace("유앤아이", "").replace("블루비뇨기과", "")
    for b in q("SELECT id,name FROM branches"):
        n = norm_name(b["name"])
        if n in (key, stripped, stripped + "점") or n.rstrip("점") == stripped:
            return b["id"]
    return None


def assignment_diff(month, parsed):
    """parsed: [{'raw':지점명, 'person':담당자명}] → 변경점 미리보기"""
    out = []
    users = {r["name"]: r["id"] for r in q("SELECT id,name FROM users WHERE active=1")}
    for p in parsed:
        bid = resolve_branch(p["raw"]) or resolve_branch(p.get("branch_raw"))
        cur = q1("SELECT manager_id FROM branch_month WHERE month=? AND branch_id=?", (month, bid)) if bid else None
        cur_name = user_name(cur["manager_id"]) if cur else ""
        person = (p["person"] or "").strip()
        out.append({
            "배정 시트 지점명": p["raw"], "프로그램 지점": branch_name(bid) if bid else "❓ 대응 없음",
            "branch_id": bid, "현재 담당": cur_name, "새 담당": person,
            "user_id": users.get(person), "변경": bool(bid and person and person != cur_name),
            "계정 없음": bool(person and person not in users),
        })
    return out


def apply_assignment(month, diffs, user):
    n = 0
    for d in diffs:
        if not d["변경"] or not d["branch_id"]:
            continue
        if not d["user_id"]:
            notify_role(ADMIN, "계정 필요", f"배정 시트의 '{d['새 담당']}' 계정이 없습니다. 계정을 만들어 주세요.",
                        dedup=f"needacc:{d['새 담당']}")
            continue
        old = q1("SELECT manager_id FROM branch_month WHERE month=? AND branch_id=?", (month, d["branch_id"]))
        ex("UPDATE branch_month SET manager_id=? WHERE month=? AND branch_id=?", (d["user_id"], month, d["branch_id"]))
        notify(d["user_id"], "배정", f"[{d['프로그램 지점']}] 담당 지점으로 배정되었습니다. 남은 할 일을 확인해 주세요.")
        audit(user["name"], "담당자 배정 변경", f"{d['프로그램 지점']}: {d['현재 담당']} → {d['새 담당']} (이전 {old and old['manager_id']})")
        n += 1
    return n
'''

# ============================================================================
# core.checks
# ============================================================================
MODULES['core.checks'] = r'''"""자동 검수.

- 스킬(uandi-wongo)에 들어 있는 기계 검수기 rules/verify.py 를 그대로 돌린다
  (글자수, 금지어·계절어, 병원명 위치, 부호 비율, 댓글 35자, 키워드, 지역 혼입, D열 밖 장비 등).
- 여기에 프로그램 쪽 규칙을 더한다:
  · 장비 규칙: 보유하지 않은 장비, 금지 명칭(예: 디스포트 → 영국산 보톡스), 장비명 언급 금지 행
  · 지점 금지 주제 (예: 블루비뇨기과 '정관수술')
  · 관리자 추가 금지어, 키워드 삽입 개수, 댓글 글자수
  · 지점 간 중복·유사 문장 (같은 달) / 같은 지점 지난 N개월 원고와 겹침
결과는 manuscripts.check_json 에 저장되고 원고 옆에 표시된다.
"""
import importlib.util
import json
import os
import re
from collections import defaultdict

from core.common import get_setting, prev_months
from core.db import ex, q, q1

_VERIFY = None


def _verify_mod():
    global _VERIFY
    import sys
    if _VERIFY is None and "rules.verify" in sys.modules:   # 한 파일 버전
        _VERIFY = sys.modules["rules.verify"]
    if _VERIFY is None:
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rules", "verify.py")
        spec = importlib.util.spec_from_file_location("verify_rules", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _VERIFY = mod
    return _VERIFY


HOSPITAL_TOKEN = {"유앤아이": "유앤아이", "블루비뇨기과": "블루비뇨기과"}


def split_list(s):
    return [x.strip() for x in re.split(r"[,\n/]", s or "") if x.strip()]


def comments_of(r):
    cells = [r.get(k) or "" for k in ("c1", "r1", "c2", "r2")]
    if r["mtype"] == "슈퍼세트":
        cells += [r.get("c3") or "", r.get("r3") or ""]
    return cells


def full_text(r):
    return " ".join([r.get("title") or "", r.get("body") or ""] + comments_of(r))


def _sentences(text):
    t = re.sub(r"[ㅠㅜㅎㅋ^~]+", " ", text or "")
    parts = re.split(r"[.!?\n]+|(?<=[가-힣])(?:요|죠)\s", t)
    return [p.strip() for p in parts if p and len(re.sub(r"\s", "", p)) >= 12]


def _grams(s, n=8):
    t = re.sub(r"\s+", "", s)
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))}


class DupIndex:
    """8글자 조각 역색인으로 비슷한 문장 빠르게 찾기"""

    def __init__(self):
        self.idx = defaultdict(set)
        self.sents = []

    def add(self, sent, label):
        g = _grams(sent)
        if not g:
            return
        i = len(self.sents)
        self.sents.append((sent, label, g))
        for x in g:
            self.idx[x].add(i)

    def find(self, sent, th):
        g = _grams(sent)
        if not g:
            return None
        cnt = defaultdict(int)
        for x in g:
            for i in self.idx.get(x, ()):
                cnt[i] += 1
        best = None
        for i, c in cnt.items():
            ratio = c / min(len(g), len(self.sents[i][2]))
            if ratio >= th and (not best or ratio > best[0]):
                best = (ratio, self.sents[i][0], self.sents[i][1])
        return best


def _equip_dict():
    """표준 장비명 사전: 이름·다른 표기 → 표준명, 금지 명칭 → 대체어"""
    names, banned = {}, {}
    for s in q("SELECT * FROM equip_std"):
        names[s["name"]] = s["name"]
        for a in split_list(s["aliases"]):
            names[a] = s["name"]
        for b in split_list(s["banned_names"]):
            banned[b] = s["replacement"] or s["name"]
    return names, banned


RULE_NOTE = re.compile(r"(.+?)\s*(?:명칭)?\s*언급\s*(?:x|X|금지|×)\s*(?:->|→|=>)\s*(.+)")


def check_branch(month, branch_id, save=True):
    branch = q1("SELECT * FROM branches WHERE id=?", (branch_id,))
    rows = q("SELECT * FROM manuscripts WHERE month=? AND branch_id=? ORDER BY no", (month, branch_id))
    written = [r for r in rows if (r["title"] or "").strip() or (r["body"] or "").strip()]
    per = {r["no"]: [] for r in rows}
    batch = []
    hl = {r["no"]: set() for r in rows}

    names, banned = _equip_dict()
    have = {r["name"] for r in q("""SELECT s.name FROM branch_equipment be JOIN equip_std s ON s.id=be.std_id
                                     WHERE be.branch_id=? AND be.active=1""", (branch_id,))}
    # 지점 장비 비고의 규칙 (예: "디스포트 명칭 언급 x → 영국산 보톡스")
    for be in q("SELECT note FROM branch_equipment WHERE branch_id=? AND active=1", (branch_id,)):
        m = RULE_NOTE.search(be["note"] or "")
        if m:
            banned[m.group(1).strip().strip('"“”')] = m.group(2).strip().strip('"“”')

    # ── 1) 스킬 검수기 (verify.py) ────────────────────────────────────────────
    if written:
        try:
            v = _verify_mod()
            v.HOSPITAL = HOSPITAL_TOKEN.get(branch["hospital"], re.sub(r"점$", "", branch["name"]))
            others = q("SELECT region_tokens FROM branches WHERE id<>? AND hospital=? AND active=1",
                       (branch_id, branch["hospital"]))
            foreign = sorted({t for o in others for t in split_list(o["region_tokens"])} - set(split_list(branch["region_tokens"])))
            bm = q1("SELECT special FROM branch_month WHERE month=? AND branch_id=?", (month, branch_id)) or {}
            ops_words = ["야간진료", "공휴일진료", "주말진료", "점심시간", "일요일진료"]
            data = {
                "branch": branch["name"],
                "region_tokens": split_list(branch["region_tokens"]),
                "foreign_regions": foreign,
                "allowed_equipment": sorted({(r["equipment"] or "").strip() for r in rows if r["equipment"]} | have),
                "known_equipment": sorted(names.keys()),
                "ops_evidence": [w for w in ops_words if w in (bm.get("special") or "").replace(" ", "")],
                "rows": [{"n": r["no"], "type": r["mtype"], "keyword": (r["keyword"] or None),
                          "equipment": r["equipment"] or "", "title": r["title"] or "", "body": r["body"] or "",
                          "comments": comments_of(r)} for r in written],
            }
            prev = _prev_text(month, branch_id)
            rep = v.run(data, prev)
            for code, label, ok, detail in rep.items:
                if ok:
                    continue
                lines = [l.strip() for l in str(detail or "").split("\n") if l.strip()]
                hit_any = False
                for line in lines:
                    nums = {int(n) for n in re.findall(r"(\d+)번", line) if int(n) in per}
                    for n in nums:
                        per[n].append({"code": code, "label": label, "detail": line, "src": "스킬"})
                        hit_any = True
                        for w in re.findall(r"[「'‘\"]([^」'’\"]{1,20})[」'’\"]", line):
                            hl[n].add(w)
                if not hit_any:
                    batch.append({"code": code, "label": label, "detail": " / ".join(lines)[:500]})
        except Exception as e:  # 검수기 오류가 저장을 막지 않게
            batch.append({"code": "!", "label": "스킬 검수기 실행 오류", "detail": str(e)[:300]})

    # ── 2) 프로그램 규칙 ─────────────────────────────────────────────────────
    cmax = int(get_setting("comment_max_chars"))
    kmin = get_setting("keyword_min") or {}
    extra = get_setting("extra_banned_words") or []
    topics = split_list(branch["banned_topics"])
    th = float(get_setting("dup_threshold"))

    other_idx, prev_idx = DupIndex(), DupIndex()
    for o in q("""SELECT m.*, b.name bname FROM manuscripts m JOIN branches b ON b.id=m.branch_id
                  WHERE m.month=? AND m.branch_id<>? AND (m.body<>'' OR m.title<>'')""", (month, branch_id)):
        for s in _sentences(full_text(o)):
            other_idx.add(s, f"{o['bname']} {o['no']}번")
    pm = prev_months(month, int(get_setting("dup_compare_months")))
    if pm:
        for o in q(f"""SELECT * FROM manuscripts WHERE branch_id=? AND month IN ({','.join('?' * len(pm))})
                       AND (body<>'' OR title<>'')""", [branch_id] + pm):
            for s in _sentences(full_text(o)):
                prev_idx.add(s, f"{o['month']} {o['no']}번")
    titles_other = {(o["title"] or "").strip(): f"{o['bname']} {o['no']}번" for o in q(
        """SELECT m.title, m.no, b.name bname FROM manuscripts m JOIN branches b ON b.id=m.branch_id
           WHERE m.month=? AND m.branch_id<>? AND m.title<>''""", (month, branch_id))}

    for r in written:
        n = r["no"]
        text = full_text(r)
        body = r["body"] or ""
        add = lambda code, label, detail: per[n].append({"code": code, "label": label, "detail": detail, "src": "프로그램"})
        # 금지어 (관리자 추가분)
        for w in extra:
            if w and w in text:
                add("P1", "금지어", f"'{w}' 사용"); hl[n].add(w)
        # 지점 금지 주제
        for t in topics:
            if t in text:
                add("P2", "지점 금지 주제", f"'{t}' — 이 지점은 다루지 않음"); hl[n].add(t)
        # 장비 금지 명칭
        for b, rep_ in banned.items():
            if b and b in text:
                add("P3", "장비 금지 명칭", f"'{b}' → '{rep_}'로"); hl[n].add(b)
        # 보유하지 않은 장비 (짧은 이름이 보유 장비명에 포함되면 제외)
        for nm, std in names.items():
            if len(nm) >= 2 and nm in text and std not in have and not any(nm in h for h in have) \
                    and nm != (r["equipment"] or ""):
                add("P4", "보유하지 않은 장비", f"'{nm}' — {branch['name']} 보유장비에 없음"); hl[n].add(nm)
        # 장비명 언급 금지 행
        if r["no_equip_mention"]:
            for nm in list(have) + [r["equipment"] or ""]:
                if nm and nm in body:
                    add("P5", "장비명 언급 금지 행", f"본문에 '{nm}'"); hl[n].add(nm)
        # 키워드 삽입 개수
        kw = (r["keyword"] or "").strip()
        need = int(kmin.get(r["mtype"], 1))
        if kw:
            c = text.count(kw)
            if c < need:
                add("P6", "키워드 삽입 개수", f"'{kw}' {c}회 (최소 {need}회)")
        # 댓글 글자수 (공백 제외)
        for i, cell in enumerate(comments_of(r)):
            L = len(re.sub(r"\s", "", cell))
            if L > cmax:
                add("P7", f"댓글 {cmax}자 초과", f"{i + 1}번째 칸 {L}자")
            if r["mtype"] != "슈퍼세트" and i < 4 and not cell.strip():
                add("P8", "댓글 빈칸", f"{i + 1}번째 칸 비어 있음")
        if r["mtype"] == "슈퍼세트" and not all(c.strip() for c in comments_of(r)):
            add("P8", "댓글 빈칸", "슈퍼세트는 댓글 3쌍(6칸)")
        # 지점 간 중복
        t = (r["title"] or "").strip()
        if t and t in titles_other:
            add("D1", "지점 간 제목 중복", f"{titles_other[t]}와 같은 제목")
        for s in _sentences(text):
            hit = other_idx.find(s, th)
            if hit:
                add("D2", "지점 간 유사 문장", f"'{s[:30]}…' ≈ {hit[2]}"); hl[n].add(s[:25])
            hit = prev_idx.find(s, th)
            if hit:
                add("D3", "지난 원고와 겹침", f"'{s[:30]}…' ≈ {hit[2]}"); hl[n].add(s[:25])
        # 같은 배치 안 중복 제목
        for o in written:
            if o["no"] < n and (o["title"] or "").strip() and o["title"].strip() == t:
                add("D4", "지점 내 제목 중복", f"{o['no']}번과 같음")

    result = {}
    for r in rows:
        n = r["no"]
        items = per[n]
        stats = {
            "본문(공백포함)": len(r["body"] or ""),
            "본문(공백제외)": len(re.sub(r"\s", "", r["body"] or "")),
            "키워드 횟수": full_text(r).count((r["keyword"] or "").strip()) if (r["keyword"] or "").strip() else 0,
        }
        result[n] = {"fails": items, "hl": sorted(hl[n], key=len, reverse=True), "stats": stats}
        if save:
            ex("UPDATE manuscripts SET check_json=?, check_fail=? WHERE id=?",
               (json.dumps(result[n], ensure_ascii=False), len(items), r["id"]))
    result["_batch"] = batch
    if save:
        ex("""INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
           (f"batchcheck:{month}:{branch_id}", json.dumps(batch, ensure_ascii=False)))
    return result


def batch_result(month, branch_id):
    r = q1("SELECT value FROM settings WHERE key=?", (f"batchcheck:{month}:{branch_id}",))
    return json.loads(r["value"]) if r else []


def _prev_text(month, branch_id):
    pm = prev_months(month, int(get_setting("dup_compare_months")))
    if not pm:
        return ""
    rows = q(f"""SELECT * FROM manuscripts WHERE branch_id=? AND month IN ({','.join('?' * len(pm))})""",
             [branch_id] + pm)
    return "\n".join(full_text(r) for r in rows)


def highlight(text, words):
    """검수에 걸린 단어를 형광펜(<mark>)으로"""
    import html
    t = html.escape(text or "")
    for w in sorted({w for w in words if w}, key=len, reverse=True):
        t = t.replace(html.escape(w), f"<mark>{html.escape(w)}</mark>")
    return t.replace("\n", "<br>")
'''

# ============================================================================
# core.ai
# ============================================================================
MODULES['core.ai'] = r'''"""Claude API 연결 — 스킬(SKILL.md)을 시스템 프롬프트로 넣어 호출한다.

API 키: 환경변수 ANTHROPIC_API_KEY 또는 .streamlit/secrets.toml 의 ANTHROPIC_API_KEY
모델:   환경변수 CLAUDE_MODEL (기본 claude-sonnet-5-5)
스킬 파일: skills/<스킬이름>/SKILL.md (+ references/*.md). 스킬을 고치면 이 폴더 파일만 바꾸면 된다.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(BASE, "skills")


def _key():
    k = os.environ.get("ANTHROPIC_API_KEY")
    if k:
        return k
    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        return None


def available():
    try:
        import anthropic  # noqa
    except ImportError:
        return False
    return bool(_key())


def model():
    return os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")


def load_skill(name, with_refs=True):
    d = os.path.join(SKILL_DIR, name)
    parts = []
    p = os.path.join(d, "SKILL.md")
    if os.path.exists(p):
        parts.append(open(p, encoding="utf-8").read())
    rd = os.path.join(d, "references")
    if with_refs and os.path.isdir(rd):
        for f in sorted(os.listdir(rd)):
            if f.endswith(".md"):
                parts.append(f"\n\n# references/{f}\n\n" + open(os.path.join(rd, f), encoding="utf-8").read())
    return "\n".join(parts)


def call(system, user, max_tokens=8000):
    import anthropic
    client = anthropic.Anthropic(api_key=_key())
    with client.messages.stream(model=model(), max_tokens=max_tokens, system=system,
                                messages=[{"role": "user", "content": user}]) as s:
        msg = s.get_final_message()
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def _json_from(text):
    m = re.search(r"```json\s*(.+?)```", text, re.S)
    raw = m.group(1) if m else text[text.find("{"): text.rfind("}") + 1]
    return json.loads(raw)


def draft_branch(materials: dict):
    """uandi-wongo 스킬로 20세트 초안. materials 는 schema.md 형식 + 원고 재료.
    return rows: [{n,title,body,comments:[...]}]"""
    system = load_skill("uandi-wongo") + """

# 프로그램 연동 규칙
- 이 대화는 원고 관리 프로그램에서 자동으로 호출된다. 시트·파일·스크립트 실행은 없다.
- 결과는 반드시 ```json 코드블록 하나로만 낸다. 형식: {"rows":[{"n":1,"title":"","body":"","comments":["","","",""]}, ...]}
- 정보성·후기성 comments 는 4칸, 슈퍼세트(20번)는 6칸. 요청받은 번호만 쓴다.
"""
    user = "아래 지점 재료로 원고를 작성해 주세요.\n\n" + json.dumps(materials, ensure_ascii=False, indent=1)
    out = call(system, user, max_tokens=24000)
    return _json_from(out).get("rows", [])


def review_branch(rows_text: str):
    """wongo-gumsu 스킬로 사람 판단이 필요한 부분만 코멘트"""
    system = load_skill("wongo-gumsu") + "\n\n# 프로그램 연동: 시트 반영은 하지 않는다. 위반 항목과 수정 제안만 번호별로 짧게 정리한다."
    return call(system, rows_text, max_tokens=6000)


SINGLE_SKILLS = {
    "카페 상위노출 원고": "uandi-wongo",
    "이미지 캡션 글": "cafe-image-caption",
    "질문글": "naver-cafe-question",
    "의료 후기": "naver-cafe-medical-review",
}


def single(kind, prompt):
    system = load_skill(SINGLE_SKILLS[kind])
    if kind == "카페 상위노출 원고":
        system += "\n\n# 단건 모드: 20세트가 아니라 요청한 1건(제목·본문·댓글)만 순수 텍스트로 쓴다."
    return call(system, prompt, max_tokens=4000)
'''

# ============================================================================
# core.sheets
# ============================================================================
MODULES['core.sheets'] = r'''"""보고서 출력(엑셀·구글 시트)과 기존 시트 불러오기.

시트는 '프로그램 → 시트' 한 방향으로만 만든다. 시트에서 고친 내용은 프로그램으로 돌아오지 않는다.
구글 시트로 바로 만들려면 .streamlit/secrets.toml 에 [gcp_service_account] 를 넣고
`pip install gspread` 하면 [보고서 만들기]가 구글 시트를 만들어 링크를 저장한다. 없으면 엑셀로 내려받는다.
"""
import io
import re

import pandas as pd

from core.common import branch_name, cafe_base, mtype_of, norm_name
from core.db import q, q1, qv

EXEC_COLS = ["카페 아이디", "실행사"]


def cafe_report_df(month, hospital, external):
    rows = q("""SELECT b.name 지점명, m.no NO, m.mtype 유형, p.pub_date 발행일, c.name 카페명, c.url 카페링크,
                       a.acc_id "카페 아이디", m.title 제목, p.url "카페침투 URL", p.views 조회수, p.check_state 확인,
                       p.as_state AS "AS"
                FROM manuscripts m JOIN branches b ON b.id=m.branch_id
                LEFT JOIN publications p ON p.ms_id=m.id
                LEFT JOIN cafes c ON c.id=p.cafe_id
                LEFT JOIN accounts a ON a.id=p.account_id
                WHERE m.month=? AND (?='전체' OR b.hospital=?)
                ORDER BY b.name, m.no""", (month, hospital, hospital))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    if external:
        # 외부용: 실행사·계정 칸 제외, AS 중인 링크 제외(AS가 끝난 최종 링크만)
        df.loc[df["AS"] == "AS 대기", "카페침투 URL"] = ""
        df = df.drop(columns=[c for c in EXEC_COLS + ["확인", "AS"] if c in df.columns])
    return df


def comment_report_df(month, hospital, external):
    rows = q("""SELECT b.name 지점명, t.keyword 키워드, t.cafe_name 카페명, t.title "게시글 제목", t.url URL,
                       t.done_date 작성일, t.comment_text "댓글 내용", a.acc_id "카페 아이디", t.status 상태
                FROM comment_targets t JOIN branches b ON b.id=t.branch_id
                LEFT JOIN accounts a ON a.id=t.account_id
                WHERE t.month=? AND (?='전체' OR b.hospital=?) AND t.status='완료'
                ORDER BY b.name, t.done_date""", (month, hospital, hospital))
    df = pd.DataFrame(rows)
    if not df.empty and external:
        df = df.drop(columns=[c for c in EXEC_COLS if c in df.columns])
    return df


def summary_df(month, hospital):
    """'한눈에 보기': 지점별 발행 건수(20/20), 댓글 침투 건수, 조회수 합계, AS 처리 건수"""
    rows = q("""SELECT b.id, b.name 지점명, b.hospital 병원,
                  (SELECT COUNT(*) FROM publications p WHERE p.month=? AND p.branch_id=b.id AND p.url<>'') pub,
                  (SELECT COUNT(*) FROM manuscripts m WHERE m.month=? AND m.branch_id=b.id) tot,
                  (SELECT COUNT(*) FROM comment_targets t WHERE t.month=? AND t.branch_id=b.id AND t.status='완료') cm,
                  (SELECT COALESCE(SUM(views),0) FROM publications p WHERE p.month=? AND p.branch_id=b.id) views,
                  (SELECT COUNT(*) FROM publications p WHERE p.month=? AND p.branch_id=b.id AND p.as_state='처리 완료') asd
                FROM branches b WHERE b.active=1 AND (?='전체' OR b.hospital=?) ORDER BY b.name""",
             (month, month, month, month, month, hospital, hospital))
    return pd.DataFrame([{"지점명": r["지점명"], "병원": r["병원"], "발행 건수": f"{r['pub']}/{r['tot'] or 20}",
                          "댓글 침투 건수": r["cm"], "조회수 합계": r["views"], "AS 처리 건수": r["asd"]} for r in rows])


def build_report_sheets(month, hospital, external):
    cafe = cafe_report_df(month, hospital, external)
    cm = comment_report_df(month, hospital, external)
    summ = summary_df(month, hospital)
    sheets = {"한눈에 보기": summ, f"{hospital} 카페 침투 보고서": cafe, f"{hospital} 댓글 침투 보고서": cm}
    if not cafe.empty:
        for b, g in cafe.groupby("지점명"):
            sheets[str(b)] = g.drop(columns=["지점명"])
    return sheets


def gsheets_available():
    try:
        import gspread  # noqa
        import streamlit as st
        return "gcp_service_account" in st.secrets
    except Exception:
        return False


def push_gsheet(title, sheets: dict, share_with=None):
    import gspread
    import streamlit as st
    gc = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
    sh = gc.create(title)
    first = True
    for name, df in sheets.items():
        safe = str(name)[:90]
        if first:
            ws = sh.sheet1
            ws.update_title(safe)
            first = False
        else:
            ws = sh.add_worksheet(safe, rows=max(len(df) + 5, 20), cols=max(len(df.columns) + 2, 5))
        values = [list(map(str, df.columns))] + df.fillna("").astype(str).values.tolist()
        ws.update(values)
    for email in share_with or []:
        sh.share(email, perm_type="user", role="writer")
    return sh.url


# ── 기존 원고 시트 불러오기 ──────────────────────────────────────────────────
def col_idx(letter):
    n = 0
    for ch in letter.upper():
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def parse_manuscript_workbook(file, mapping):
    """지점 탭(1~3행 헤더, A열 원고재료, 5~24행 원고) → {탭이름: [행...]}
    mapping: {'first_row':5, 'keyword':'B','special':'C','equipment':'D','status':'E','title':'G','body':'H',
              'comments':['I','J','K','L','M','N'], 'material':'A'}"""
    xl = pd.ExcelFile(file)
    out = {}
    for sh in xl.sheet_names:
        df = xl.parse(sh, header=None, dtype=str).fillna("")
        fr = int(mapping["first_row"]) - 1
        if len(df) < fr + 1:
            continue
        rows = []
        for i in range(20):
            ri = fr + i
            if ri >= len(df):
                break
            row = df.iloc[ri]

            def g(letter):
                j = col_idx(letter)
                return str(row.iloc[j]).strip() if j < len(row) else ""

            cm = [g(c) for c in mapping["comments"]]
            rows.append({"no": i + 1, "keyword": g(mapping["keyword"]), "special": g(mapping["special"]),
                         "equipment": g(mapping["equipment"]), "status_raw": g(mapping["status"]) if mapping.get("status") else "",
                         "title": g(mapping["title"]), "body": g(mapping["body"]),
                         "c1": cm[0], "r1": cm[1], "c2": cm[2], "r2": cm[3],
                         "c3": cm[4] if len(cm) > 4 else "", "r3": cm[5] if len(cm) > 5 else ""})
        material = ""
        if mapping.get("material"):
            j = col_idx(mapping["material"])
            material = "\n".join(str(v) for v in df.iloc[:, j].tolist() if str(v).strip()) if j < df.shape[1] else ""
        if any(r["title"] or r["keyword"] for r in rows):
            out[sh] = {"rows": rows, "material": material}
    return out


def status_from_raw(s, has_text):
    s = (s or "").strip()
    if "완료" in s:
        return "완료"
    if "피드백" in s:
        return "피드백"
    return "검수 대기" if has_text else "작성 전"


def parse_assignment_sheet(file, sheet_name):
    """배정 시트: 칸 이름으로 읽는다(탭마다 칸 구성이 다름).
    과목/병원명 칸에 유앤아이·블루가 있는 행만. 담당 칸은 '블로그 포스팅' → '사수' 순으로 찾는다."""
    raw = pd.read_excel(file, sheet_name=sheet_name, header=None, dtype=str).fillna("")
    hdr_row = None
    for i in range(min(15, len(raw))):
        vals = [norm_name(v) for v in raw.iloc[i].tolist()]
        if any("지점명" in v for v in vals):
            hdr_row = i
            break
    if hdr_row is None:
        raise ValueError("'지점명' 칸을 찾지 못했습니다.")
    df = raw.iloc[hdr_row + 1:].copy()
    df.columns = [norm_name(c) for c in raw.iloc[hdr_row].tolist()]

    def find(*keys):
        for k in keys:
            for c in df.columns:
                if k in c:
                    return c
        return None

    c_hosp = find("과목", "병원명", "병원")
    c_branch = find("지점명")
    c_person = find("블로그포스팅", "SEO", "사수", "담당")
    if not c_person:
        raise ValueError("담당자 칸(블로그 포스팅 / 사수)을 찾지 못했습니다.")
    out = []
    for _, r in df.iterrows():
        hosp = str(r.get(c_hosp, "")) if c_hosp else ""
        br = str(r.get(c_branch, ""))
        if not br.strip():
            continue
        if c_hosp and not any(k in hosp for k in ("유앤아이", "블루")):
            continue
        person = re.split(r"[,/\n]", str(r.get(c_person, "")))[0].strip()
        out.append({"raw": (hosp + " " + br).strip() if c_hosp else br, "branch_raw": br, "person": person})
    return out, {"병원 칸": c_hosp, "지점 칸": c_branch, "담당 칸": c_person}
'''

# ============================================================================
# core.seed
# ============================================================================
MODULES['core.seed'] = r'''"""처음 실행할 때 넣는 데모 데이터. 실제 운영 전에는 설정 > 데이터 초기화로 비우거나
환경변수 SEED_DEMO=0 으로 실행하면 관리자 계정만 만든다."""
import os
from datetime import date, timedelta

from core.common import ADMIN, BOARD, EXEC, MANAGER, WRITER, hash_pw
from core.db import ex, exmany, now, q, qv
from core.ops import ensure_month_frame, start_month


def seed():
    if qv("SELECT COUNT(*) FROM users", default=0):
        return
    ex("INSERT INTO users(username,pw,name,role,created_at) VALUES(?,?,?,?,?)",
       ("admin", hash_pw("admin1234"), "관리자", ADMIN, now()))
    if os.environ.get("SEED_DEMO", "1") == "0":
        return

    users = [("kim", "김담당", MANAGER), ("park", "박담당", MANAGER), ("lee", "이선주", MANAGER),
             ("writer1", "장은하", WRITER), ("writer2", "오작가", WRITER),
             ("board", "게시판담당", BOARD), ("exec", "실행사", EXEC)]
    for u, n, r in users:
        ex("INSERT INTO users(username,pw,name,role,created_at) VALUES(?,?,?,?,?)", (u, hash_pw("1234"), n, r, now()))
    uid = {r["name"]: r["id"] for r in q("SELECT id,name FROM users")}

    branches = [
        ("건대점", "유앤아이", "서울", "건대입구역 2번 출구", "건대,건대입구,화양동", ""),
        ("강남점", "유앤아이", "서울", "강남역 11번 출구", "강남,강남역,역삼", ""),
        ("경기광주점", "유앤아이", "경기", "경기광주역", "경기광주,광주,오포", ""),
        ("광교점", "유앤아이", "경기", "광교중앙역", "광교,광교중앙,이의동", ""),
        ("광명점", "유앤아이", "경기", "광명사거리역", "광명,철산", ""),
        ("대전점", "유앤아이", "충청", "둔산동", "대전,둔산동,탄방동", ""),
        ("배곧점", "유앤아이", "경기", "배곧신도시", "배곧,시흥", ""),
        ("하남미사점", "유앤아이", "경기", "미사역", "하남미사,미사", ""),
        ("블루 강남점", "블루비뇨기과", "서울", "강남역", "강남,신논현", "정관수술,포경수술"),
        ("블루 잠실점", "블루비뇨기과", "서울", "잠실역", "잠실,송파", "정관수술,포경수술"),
        ("목포점", "로컬", "전라", "목포 하당", "목포,하당", ""),
    ]
    for name, h, reg, loc, tok, ban in branches:
        ex("""INSERT INTO branches(name,hospital,region,location,region_tokens,banned_topics,created_at)
              VALUES(?,?,?,?,?,?,?)""", (name, h, reg, loc, tok, ban, now()))
    bid = {r["name"]: r["id"] for r in q("SELECT id,name FROM branches")}
    exmany("INSERT INTO branch_aliases(alias,branch_id) VALUES(?,?)",
           [("유앤아이건대", bid["건대점"]), ("유앤아이대전(1)·대전(2)", bid["대전점"]),
            ("블루비뇨기과강남", bid["블루 강남점"]), ("유앤아이경기광주", bid["경기광주점"])])

    std = [("울쎄라피 프라임", "리프팅", "울쎄라피,울쎄라", "", ""),
           ("슈링크 유니버스", "리프팅", "슈링크", "", ""),
           ("인모드", "리프팅", "", "", ""),
           ("써마지FLX", "리프팅", "써마지", "", ""),
           ("아포지", "제모", "", "", ""),
           ("피코플러스", "색소", "", "", ""),
           ("리쥬란", "주사", "리쥬란힐러", "", ""),
           ("쥬베룩", "주사", "", "", ""),
           ("영국산 보톡스", "주사", "보톡스", "디스포트", "영국산 보톡스"),
           ("노블쉐이프", "비만·바디", "", "", ""),
           ("네오빔", "여드름 치료", "", "", ""),
           ("프락셀", "여드름 흉터", "", "", ""),
           ("I-MOVE 쇄석기", "기타", "쇄석기", "", "")]
    for s in std:
        ex("INSERT INTO equip_std(name,category,aliases,banned_names,replacement) VALUES(?,?,?,?,?)", s)
    sid = {r["name"]: r["id"] for r in q("SELECT id,name FROM equip_std")}
    have = {
        "건대점": ["울쎄라피 프라임", "인모드", "리쥬란", "영국산 보톡스", "피코플러스"],
        "강남점": ["울쎄라피 프라임", "슈링크 유니버스", "써마지FLX", "쥬베룩"],
        "경기광주점": ["슈링크 유니버스", "리쥬란", "아포지", "노블쉐이프"],
        "광교점": ["울쎄라피 프라임", "인모드", "네오빔", "프락셀"],
        "광명점": ["슈링크 유니버스", "리쥬란"], "대전점": ["울쎄라피 프라임", "슈링크 유니버스", "쥬베룩"],
        "배곧점": ["인모드", "아포지"], "하남미사점": ["슈링크 유니버스", "피코플러스"],
        "블루 강남점": ["I-MOVE 쇄석기"], "블루 잠실점": ["I-MOVE 쇄석기"], "목포점": ["울쎄라피 프라임"],
    }
    for b, lst in have.items():
        for i, e in enumerate(lst):
            note = "디스포트 명칭 언급 x → 영국산 보톡스" if e == "영국산 보톡스" else ""
            ex("""INSERT INTO branch_equipment(branch_id,std_id,qty,in_date,note,updated_at,updated_by)
                  VALUES(?,?,?,?,?,?,?)""", (bid[b], sid[e], 1 + i % 2, f"2026-0{1 + i}-15", note, now(), "관리자"))

    cafes = [("맘스홀릭 베이비", "https://cafe.naver.com/imsanbu", "맘", "대형", None, "진행 가능", 25000, 1),
             ("여우야", "https://cafe.naver.com/foxyu", "2030뷰티", "대형", None, "주의", 0, 1),
             ("파우더룸", "https://cafe.naver.com/cosmania", "2030뷰티", "대형", None, "진행 가능", 0, 0),
             ("뷰티톡", "https://cafe.naver.com/beautytalk", "2030뷰티", "소형", None, "진행 가능", 0, 0),
             ("레몬테라스", "https://cafe.naver.com/remonterrace", "맘", "대형", None, "진행 가능", 35000, 0),
             ("광진맘", "https://cafe.naver.com/gwangjinmom", "지역맘", None, "서울", "진행 가능", 0, 0),
             ("세클맘", "https://cafe.naver.com/seclmom", "지역맘", None, "서울", "진행 가능", 0, 0),
             ("용광맘 모여라", "https://cafe.naver.com/yonggwangmom", "지역맘", None, "경기", "진행 가능", 0, 0),
             ("대전맘", "https://cafe.naver.com/daejeonmom", "지역맘", None, "충청", "진행 가능", 0, 0),
             ("남자들의 공간", "https://cafe.naver.com/mensroom", "남성", "대형", None, "주의", 0, 0)]
    for n, u, t, s, r, st, p, cu in cafes:
        ex("""INSERT INTO cafes(name,url,base_id,ctype,size,region,status,price,comment_use,created_at)
              VALUES(?,?,?,?,?,?,?,?,?,?)""", (n, u, u.rsplit("/", 1)[1], t, s, r, st, p, cu, now()))
    cid = {r["name"]: r["id"] for r in q("SELECT id,name FROM cafes")}
    ex("INSERT INTO cafe_links(cafe_id,link_type,branch_id) VALUES(?,?,?)", (cid["광진맘"], "지점", bid["건대점"]))
    ex("INSERT INTO cafe_links(cafe_id,link_type,region) VALUES(?,?,?)", (cid["세클맘"], "지역", "서울"))
    for b in ["광교점", "경기광주점", "배곧점"]:
        ex("INSERT INTO cafe_links(cafe_id,link_type,branch_id) VALUES(?,?,?)", (cid["용광맘 모여라"], "지점", bid[b]))
    ex("INSERT INTO cafe_links(cafe_id,link_type,branch_id) VALUES(?,?,?)", (cid["대전맘"], "지점", bid["대전점"]))

    for a, nick, pur, st in [("id_001", "뷰티스타", "둘 다", "사용 중"), ("id_002", "헬스토커", "카페 침투", "제재·정지"),
                             ("id_003", "봄날", "카페 침투", "사용 중"), ("id_004", "하늘색", "댓글 침투", "사용 중"),
                             ("id_005", "라떼", "둘 다", "사용 중")]:
        ex("INSERT INTO accounts(acc_id,nickname,purpose,status,created_at,created_by) VALUES(?,?,?,?,?,?)",
           (a, nick, pur, st, now(), "실행사"))

    # 이번 달 + 틀
    today = date.today()
    month = f"{today.year:04d}-{today.month:02d}"
    start_month(month, "관리자", deadlines={
        "setting": (today + timedelta(days=1)).isoformat(),
        "writing": (today + timedelta(days=6)).isoformat(),
        "publish": (today + timedelta(days=20)).isoformat()})
    mgr = {"건대점": "이선주", "강남점": "김담당", "경기광주점": "김담당", "광교점": "김담당", "광명점": "박담당",
           "대전점": "박담당", "배곧점": "이선주", "하남미사점": "박담당", "블루 강남점": "이선주", "블루 잠실점": "이선주"}
    for b, m in mgr.items():
        ex("UPDATE branch_month SET manager_id=?, writer_id=? WHERE month=? AND branch_id=?",
           (uid[m], uid["장은하" if b in ("건대점", "강남점", "광교점", "블루 강남점") else "오작가"], month, bid[b]))
    ex("""UPDATE branch_month SET req_notes=?, competitor=?, must_include=?, special=?, material_done=1
          WHERE month=? AND branch_id=?""",
       ("자연스러운 볼륨감 강조", "프라임 정품 장비 사용", "상담 때 얼굴 상태부터 확인", "장비언급X -> 피코토닝으로 (7번)",
        month, bid["건대점"]))

    kw = ["건대 울쎄라", "건대 인모드", "건대 리쥬란", "건대 보톡스", "건대 피코토닝", "건대 피부과", "건대 울쎄라",
          "건대 리프팅", "건대 인모드", "건대 리쥬란"] + ["건대 보톡스", "건대 울쎄라", "건대 리쥬란", "건대 인모드",
                                                  "건대 피코토닝", "건대 리프팅", "건대 울쎄라", "건대 리쥬란", "건대 피부과", "건대 울쎄라"]
    eq = ["울쎄라피 프라임", "인모드", "리쥬란", "영국산 보톡스", "피코플러스", "인모드", "울쎄라피 프라임",
          "울쎄라피 프라임", "인모드", "리쥬란"] * 2
    samples = {
        1: ("건대 울쎄라 몇 번은 해야 하나요?", "고개 숙여서 폰 볼 때마다 턱선이 겹쳐 보여서요ㅠㅠ 건대 울쎄라 보통 몇 번은 해야 하는지 궁금해요",
            ["건대 울쎄라면 유앤아이요 샷수 얼굴 보고 잡아줘요", "아 거기 저장해둘게요", "저는 한 번 하고 좀 지나서 알겠더라구요", "저도 폰 볼 때 그게 제일 신경 쓰여요ㅠㅠ"]),
        2: ("건대 인모드 받아보신 분 계세요", "요즘 볼 아래가 물렁하게 내려앉는 느낌이라 건대 인모드 알아보고 있어요~ 아픈 편인지 궁금합니다",
            ["건대 인모드는 유앤아이에서 했는데 세기 조절해줘서 괜찮았어요", "오 세기 조절 되는 거 좋네요", "저는 따끈한 정도였어요!", "따끈한 정도면 해볼만하겠어요ㅎㅎ"]),
        4: ("건대 보톡스 디스포트 괜찮나요", "사각턱 보톡스 맞아보려는데 건대 보톡스 디스포트로 하는 곳이 좋다고 들어서요 최고인 곳 있을까요",
            ["건대 보톡스 유앤아이 괜찮았어요", "감사해요!", "저도 거기 다녀요", "후기 감사합니다"]),
        11: ("건대 보톡스 맞고 왔어요", "사각턱 때문에 고민하다가 건대 보톡스 맞고 왔어요! 상담 때 근육 상태부터 만져보시고 양 정해주셔서 좋았어요ㅎㅎ 2주 지나니까 확실히 턱선이 정리된 느낌이에요~ 다음엔 써마지도 해볼까 해요",
             ["건대 보톡스 어디서 하셨어요?", "유앤아이 건대점이요 근육부터 만져보고 정해줘요", "저도 가봐야겠어요ㅎㅎ", "꼭 상담 받아보세요!"]),
    }
    for n in range(1, 21):
        ex("UPDATE manuscripts SET keyword=?, equipment=? WHERE month=? AND branch_id=? AND no=?",
           (kw[n - 1], eq[n - 1], month, bid["건대점"], n))
    for n, (t, b, cm) in samples.items():
        ex("""UPDATE manuscripts SET title=?, body=?, c1=?, r1=?, c2=?, r2=?, status=?, updated_at=?, updated_by=?
              WHERE month=? AND branch_id=? AND no=?""",
           (t, b, *cm, "완료" if n == 1 else ("피드백" if n == 4 else "검수 대기"), now(), "장은하", month, bid["건대점"], n))
    ex("UPDATE manuscripts SET feedback='디스포트 명칭 빼고, 최고 표현 삭제' WHERE month=? AND branch_id=? AND no=4",
       (month, bid["건대점"]))
    # 강남점은 20건 모두 완료 → 실행사 발행 목록 데모
    for n in range(1, 21):
        ex("""UPDATE manuscripts SET keyword=?, equipment=?, title=?, body=?, c1=?, r1=?, c2=?, r2=?, c3=?, r3=?,
              status='완료', confirmed_by='관리자', confirmed_at=? WHERE month=? AND branch_id=? AND no=?""",
           ("강남 울쎄라", "울쎄라피 프라임", f"강남 울쎄라 {n}번째 이야기", f"강남 울쎄라 샘플 본문 {n}입니다 상담부터 꼼꼼하게 해주셨어요",
            "강남 울쎄라 어디서 하셨어요", "유앤아이 강남점이요", "저장해요", "네 좋았어요", "c3" if n == 20 else "", "r3" if n == 20 else "",
            now(), month, bid["강남점"], n))
    from core.ops import plan_publish_dates
    plan_publish_dates(month)
    from core.checks import check_branch
    check_branch(month, bid["건대점"])

    ex("""INSERT INTO comment_targets(month,branch_id,keyword,source,title,cafe_name,cafe_base,article_id,url,commentable,collected_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
       (month, bid["블루 강남점"], "남성수술", "자동 수집", "여기 후기 좀 알려주세요", "여우야", "foxyu", "123456",
        "https://cafe.naver.com/foxyu/123456", "가능", now()))
'''

# ============================================================================
# rules.verify
# ============================================================================
MODULES['rules.verify'] = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유앤아이 카페 바이럴 원고 기계 검수기.

사람이 눈으로 세면 반드시 틀리는 것들(글자수, 어휘 출현, 부호 비율, 위치, 분포)만
기계가 본다. 문장이 사람 말 같은지는 여기서 판정하지 않는다 — 그건 SKILL.md 6장이 한다.

사용법:
    python verify.py 원고.json
    python verify.py 원고.json --prev 이전원고들.txt

입력 JSON 스키마는 references/schema.md 참고.
"""

import json
import re
import sys
import argparse
import statistics
from collections import Counter

HOSPITAL = "유앤아이"

# ── 어휘 사전 ────────────────────────────────────────────────────────────────

SEASON = ["봄", "여름", "가을", "겨울", "환절기", "장마", "무더위", "더위", "추위",
          "한파", "폭염", "에어컨", "냉방", "난방", "히터", "온풍기", "자외선",
          "선크림", "휴가", "바캉스", "물놀이", "수영장", "머리 묶", "반팔",
          "목폴라", "이맘때", "이 시기", "드레스", "가봉", "초여름", "한여름",
          "늦여름", "초겨울", "한겨울", "건조한 계절", "습해서"]

THIRD = ["엄마", "아빠", "어머니", "아버지", "부모", "남편", "남자친구", "여자친구",
         "와이프", "언니", "오빠", "누나", "동생", "조카", "시어머니", "딸", "아들",
         "아이가", "아이를", "아이도", "애기", "애가", "애를", "친구", "지인", "동료",
         "옆자리", "후배", "선배", "상사", "사촌", "주변에서", "남들이", "다들",
         "사람들이", "지나가다 들었"]
THIRD_ALLOW = ["원장", "실장", "선생님", "직원",
               # 동사 어간 안에 호칭이 묻히는 오탐 — 「잦아들다」의 '아들', 「스며들다」의 '며들'.
               # 멀쩡한 문장을 반려시키고, 피하려다 어휘가 이상해진다.
               "잦아들", "받아들", "빨아들", "숨어들", "접어들", "스며들", "파고들",
               "빠져들", "잠들", "만들", "흔들", "아들아들"]

BANNED_WORDS = ["거울", "사진", "셀카", "찍", "마스크", "살이고", "대인데", "대 중반",
                "대 초반", "대 후반", "살인데", "안녕하세요", "반갑습니다",
                # N1 축(안 해도 될 걸 빼줌)을 옮기다 보면 제일 먼저 나오는 말인데,
                # 문장에 넣으면 어색하다. 실제로 카페에 쓰는 사람은 이 말을 안 쓴다.
                # 대체어는 「빼주다」가 기본 — materials.md 9장.
                "덜어내", "덜어 내", "덜어냄", "덜어낸", "덜어낼", "덜어냈",
                "덜어주", "덜어줘", "덜어줌", "덜어 주"]

DECOR = ["인테리어", "분위기", "1인실", "프라이빗", "대기실", "시설", "깨끗",
         "응대", "친절", "직원분"]

EXCLUSIVE = ["정품", "정량", "최초", "유일", "여기만", "다른 데는 안", "다른데는 안"]

AI_PHRASES = ["고민이 많았", "고민이 깊었", "확실히 달라진 게 느껴", "만족스러운 경험",
              "강력 추천", "결과적으로", "무엇보다", "특히나", "게다가",
              "저에게 딱 맞", "저와 잘 맞", "세심한 케어", "전문적인 상담",
              "시간이 지날수록", "도움이 되셨으면", "참고하시면 좋을",
              "인상적이었", "어느새", "어느 순간", "새삼", "용기가 났", "용기 내서"]

MARKETING = ["유수분 밸런스", "피부 장벽", "콜라겐 리모델링", "턴오버", "진피층까지"]

CLICHE = ["만족", "추천", "꼼꼼", "세심", "효과", "자연스럽"]

CONJ_HEAD = ["그래서", "하지만", "그리고", "그런데", "또한", "게다가", "무엇보다",
             "결과적으로", "따라서", "특히"]

AD_TONE = ["곳이에요", "곳입니다", "곳이예요", "해주는 곳", "드립니다",
           "추천드립니다", "인 곳", "하는 곳이"]

# 변화 = 「어디가 어떻게 달라졌는지」. 병원 칸의 주인공이다.
# 병원을 찾는 사람이 알고 싶은 건 방식이 아니라 결과라서, 이게 빠지면 칸이 설명문으로 굳는다.
CHANGE_MARKERS = ["뚜렷", "선명", "섰어", "섰고", "잡혔", "잡히", "살았", "살아났",
                  "옅어", "흐려", "덜해", "덜 띄", "덜 나", "덜 올라", "덜 접", "덜 당",
                  "덜 벌게", "덜 달아", "덜 비쳐", "덜 도드라", "덜 끼", "덜 번들",
                  "덜 보여", "덜 보이", "덜 잡혀", "덜 남아", "덜 뭉", "덜 무거",
                  "매끈", "부드러", "탄탄", "차올", "찼어", "폈어", "펴졌", "펴져",
                  "줄었", "줄어", "가벼워", "달라졌", "좋아졌", "나아졌", "옅어졌",
                  "스며들", "안 뭉", "안 겉돌", "안 일어나", "덮여", "환해", "맑아",
                  "정리됐", "깔끔해", "티가 나", "티 나"]

# 부위가 잡혀야 배너 카피와 갈린다. "확실히 좋아졌어요"는 변화가 아니다.
BODY_PARTS = ["턱선", "턱 밑", "턱 아래", "턱", "볼", "광대", "눈가", "눈 밑", "코 옆",
              "콧볼", "이마", "목", "입가", "입꼬리", "모공", "자국", "결", "안색",
              "피부", "얼굴", "잔주름", "주름", "그늘", "각질", "관자놀이", "앞볼",
              "옆모습", "라인", "팔", "허벅지", "아랫배", "옆구리", "잔털"]

# 병원 후기 = 「사람이 어떻게 봐주는지」와 「운영 방식」
# 「~아/어 주다」는 주/줘/줌/줍 으로 갈리므로 어간까지만 본다.
# 맨 「해주/해줘」는 넣지 않는다 — 자연스러운 변화 문장 아무데나 붙어서,
# 이게 마커면 의도 없이 사람·방식으로 분류되고 상한을 피하려다 문장을 비틀게 된다.
CARE_MARKERS = ["봐주", "봐줘", "잡아주", "잡아줘", "권유", "권하", "멈춰주", "멈춰줘",
                "알려주", "알려줘", "맞춰주", "맞춰줘", "놔주", "놔줘", "놓아주", "놓아줘",
                "말해주", "말해줘", "물어봐주", "물어봐줘", "쏴주", "쏴줘", "빼주", "빼줘",
                "정해주", "정해줘", "하자고", "디자인", "부풀리", "보고 정", "천천히",
                "세기", "강도", "깊이", "단계", "순서", "상담", "안 권", "과하지",
                "필요한 만큼", "나눠서", "미리 알", "관리법"]

OPS_INFO = ["야간진료", "공휴일진료", "주말진료", "점심시간", "늦은 타임", "늦게까지",
            "첫방문 이벤트", "이벤트", "동선"]

# 「가도 오늘 다 못 받는다」는 장점이 아니라 가기 싫어질 이유다.
# 이 글을 읽는 사람은 병원을 고르는 중이라, 미룬다는 말은 그대로 이탈 사유가 된다.
DEFER = ["여기까지만", "다음에 보자", "다음에 하자", "다음에 오", "다음에 와",
         "다음에 다시", "나머지는 두고", "두고 보자", "오늘 할 데만", "오늘 할 데를",
         "다음 번에", "나중에 보자", "담에 보자", "남은 건 다음", "나머지는 다음",
         "담에 하자", "다음번에 보자", "또 오라", "반만 하고", "반만 받고",
         "두고 본", "두고 봤", "남겨 두자", "미뤄 두자"]

# 시술과 무관한 잡담. 사람 냄새를 내려고 넣기 쉬운데, 읽는 사람은 시술 얘기를 찾다가 나간다.
# 예전 스킬이 「끝나고 뭐 했는지」·「순수 잡담」을 요구해서 국수·카페 문장이 들어갔다.
CHITCHAT = ["국수", "빵 ", "빵을", "빵 사", "커피", "카페", "라떼", "아메리카노", "점심 뭐",
            "점심은", "밥 먹", "밥은", "저녁 먹", "맛집", "디저트", "케이크", "치킨",
            "산책", "한 바퀴 돌", "쇼핑", "옷 사", "드라마", "넷플", "날씨", "비 와",
            # 맨 「버스」는 장비명 「슈링크 유니버스」에 묻혀 20행마다 오탐을 낸다.
            # D열 표기는 바꿀 수 없으니 여기서 갈라 본다.
            # ⛔ 맨 「버스」에 조사만 붙인 형태(「버스를」「버스로 」)는 넣지 않는다.
            #    「슈링크 유니버스를」「슈링크 유니버스로」에 그대로 걸린다.
            "주차가", "주차를", "차 대", "버스 타", "버스 정류", "버스에서", "버스 기다",
            "지하철 타", "막히", "출근길", "퇴근길에 들",
            "회식", "야근"]

# 몸짓으로 고민을 발견하는 연출. 본문 첫 문장에서 0건이다.
# 「턱을 괴고 있다가 볼이 물컹한 걸 느꼈어요」류가 원고를 제일 어색하게 만들었다.
# 고민은 몸짓이 아니라 피부 상태(탄력·잔주름·결·안색)로 말한다 — SKILL.md 4-1장.
GESTURE = ["턱을 괴", "턱 괴", "괴고 있", "괴다가", "받치면", "받치고", "받쳤",
           "눌렀다", "눌러보", "누르면", "누르니", "눌리는", "눌린 자국",
           "꼬집", "집으면", "집었", "집어 보", "쓸어올리", "쓸어 올리", "쓸어내리",
           "쓸어 내리", "쓸어보", "만지면", "만져보", "만졌", "문지르", "문질러",
           "고개를", "고개 숙", "고개 돌", "고개 젖", "고개만", "하품",
           "입을 벌리", "입 벌릴", "입을 크게", "혀로", "머리를 넘기", "머리 넘기",
           "손끝에 걸", "손등에", "손바닥에", "손으로", "손가락으로",
           "당기면", "당겨보", "당겨서 보", "잡아당기"]

# 회차 서사. 흉터·여드름·색소·제모처럼 여러 회가 기본인 시술에만 쓴다.
# 리프팅·스킨부스터·필러는 회차 대신 경과 시점으로 쓴다 — SKILL.md 4-5장.
REPEAT_RE = re.compile(r"(첫|두|세|네|다섯|여섯)\s*번째|[0-9０-９]\s*회차|[0-9０-９]\s*번째"
                       r"|(두|세|네|다섯)\s*번\s*(받|채우|하고|째)")
# 회차를 써도 되는 시술 — D열 표기에 이 조각이 들어가면 허용으로 본다.
REPEAT_OK_DEVICES = ["프락셀", "프락셔널", "포텐자", "시크릿", "아그네스", "더마펜",
                     "스칼렛", "피코", "클라리티", "엑셀브이", "브이빔", "젠틀맥스",
                     "아포지", "토닝", "제모", "실펌", "라셈드", "모자이크", "아쿠아필",
                     "버츄", "인피니", "라라필", "실키필", "크리스탈필", "블랙필", "필링",
                     "ldm", "관리", "이산화탄소", "co2", "레이저", "흉터", "여드름",
                     "트리플로", "듀오"]
# ⛔ 「필」 한 글자는 넣지 않는다 — 「필러」에 걸린다.
# ⛔ 바디 리프팅(바디인모드·바디온다리프팅)은 실제로 회차제지만, 이름이 리프팅이라
#    여기 넣지 않는다. 회차를 쓰려면 그 행에 repeat_ok: true 를 직접 찍는다.
# 회차를 「묻는」 문장은 후기 서사가 아니라 질문이라 통과시킨다(P4 패턴).
REPEAT_ASK = ["몇", "하나요", "해야", "할까요", "인가요", "되나요", "보통", "궁금"]

PLACE_ASK = ["어디", "어느", "병원 정보", "병원 이름", "이름 여쭤", "검색", "알려주실",
             "같은 데", "그 데", "어딘지", "다니시는지", "정보 좀", "정보 궁금",
             "가보고 싶", "알려주세요", "여쭤봐도"]

# 정보성 본문이 「병원을 찾는 글」인지 보는 표지.
# 「얼굴 보고 잡아주는 데로 갈까요」처럼 조건만 걸고 묻는 글도 병원을 찾는 글이다.
# 여기가 좁으면 멀쩡한 문장에 "피부과"를 억지로 끼워 넣게 된다 — 검사기 통과용 문장이 그렇게 생긴다.
CLINIC_SEEK = ["피부과", "병원", "의원", "잘하는", "잘 보는", "잘 봐주", "괜찮은 데",
               "괜찮은 곳", "추천", "다니시", "다니는 데", "어디로", "어디에", "어느 쪽",
               "어디가", "정보 좀", "아시는 분", "받아보신 분", "가보신 분", "해보신 분",
               "알아보는 중", "알아보고 있", "알아만 보", "잡아주는", "봐주는", "정해주는",
               "빼주는", "맞춰주는", "권하지 않", "안 권하는", "가볼 만한", "갈 만한",
               "가면 될까", "가야 할까", "어느 데", "그런 데", "그런 곳"]

# 정보성 제목이 「병원을 찾는 사람」의 제목인지. 본문은 병원을 찾는데 제목이 시술 질문이면
# 둘이 따로 논다 — 카페 목록에서는 제목만 보이므로 여기서 갈린다.
TITLE_SEEK = ["피부과", "병원", "의원", "추천", "잘하는", "잘 보는", "잘 봐주", "괜찮은",
              "알아보", "어디", "어느", "다니세", "다니시", "받아보신", "가보신",
              "해보신", "계실까요", "계신가요", "정보 좀", "알려주"]

# 같은 요청 어구를 열 번 쓰면 패턴을 나눈 의미가 없다. 어구별 상한 2회.
ASK_PHRASES = ["잘하는 피부과", "잘하는 곳", "잘하는 데", "잘 보는 곳", "잘 보는 데",
               "괜찮은 데", "괜찮은 곳", "추천 좀", "추천해주세요", "정보 좀",
               "아시는 분 계실까요", "어디로들 다니시는지", "어디로 다니시는지",
               "받아보신 분 계실까요", "알려주세요"]

EMOJI = re.compile(r"[\U0001F300-\U0001FAFF☀-➿❤♥♡️♡♥]")

TARGET = {
    "정보성_본문": {"ㅠ": 40, "!": 30, "..": 19, "~": 15, "ㅎㅎ": 8, "ㅋㅋ": 6, "^^": 4},
    "후기성_본문": {"ㅠ": 23, "!": 51, "..": 10, "~": 21, "ㅎㅎ": 34, "ㅋㅋ": 30, "^^": 12},
    "댓글": {"ㅠ": 9, "!": 32, "..": 7, "~": 18, "ㅎㅎ": 12, "ㅋㅋ": 9, "^^": 6},
}
TOLERANCE = 15  # ±15%p


# ── 유틸 ────────────────────────────────────────────────────────────────────

def strip_marks(s):
    return re.sub(r"[ㅠㅜㅎㅋ^~!?.,\s]+", " ", s).strip()


def sentences(body):
    """문장 경계를 찾는다.

    종결어미 뒤에는 ~ ! ㅎㅎ ㅠㅠ 가 얼마든지 붙는다("잡히나요~ 저는"). 부호를 먼저
    통째로 지운 뒤에 「요|죠」 + 공백으로 자르지 않으면 3문장짜리가 2문장으로 세어져
    ⑮·⑰이 엉뚱하게 실패한다.
    '다 ' 뒤는 "하다 ", "보다 " 오탐이 많아 경계로 쓰지 않는다.

    「요」는 앞 글자에 붙어 있을 때만 종결어미다. 1-1이 권하는 시점 표현 「요 며칠」의
    '요'는 혼자 선 어절이라 경계가 아니다 — 여기서 자르면 1문장이 2문장으로 세어져
    ⑮가 엉뚱하게 뒤집힌다. 그래서 앞에 한글이 붙어 있는지를 본다.
    """
    t = re.sub(r"[ㅠㅜㅎㅋ^~]+", "", body)
    t = re.sub(r"[!?]+", ".", t)
    t = re.sub(r"\.{2,}", ".", t)
    t = re.sub(r"(?<=[가-힣])(요|죠)\s*\.?\s", r"\1.", t)
    return [p.strip() for p in t.split(".") if p.strip()]


def ops_evidence_required(ops_ok):
    """시트에 운영 정보 근거가 실제로 적혀 있는가."""
    return [e for e in (ops_ok or []) if e and e.strip()]


def count_region_tokens(text, regions):
    """한 칸에 든 지역 토큰을 돌려준다.

    지점 표기는 서로 품는다 — 「동탄」과 「동탄역」이 둘 다 등록되면 "동탄역" 한 마디가
    토큰 2개로 세어져 멀쩡한 댓글이 반려된다. 긴 표기부터 찾아 그 자리를 지우고 센다.
    """
    hits, rest = [], text
    for g in sorted(regions, key=len, reverse=True):
        if g and g in rest:
            hits.append(g)
            rest = rest.replace(g, " ")
    return hits


def eojeol(s):
    return [w for w in s.split() if w]


def hospital_index(cells):
    for i, c in enumerate(cells):
        if HOSPITAL in c:
            return i
    return None


def ngrams(text, n=8):
    t = re.sub(r"\s+", "", text)
    return {t[i:i + n] for i in range(len(t) - n + 1)}


class Report:
    def __init__(self):
        self.items = []

    def add(self, code, label, ok, detail=""):
        self.items.append((code, label, bool(ok), detail))

    def dump(self):
        fails = [i for i in self.items if not i[2]]
        print("=" * 72)
        for code, label, ok, detail in self.items:
            print(f"[{'PASS' if ok else 'FAIL'}] {code} {label}")
            if detail:
                for line in str(detail).strip().split("\n"):
                    if line.strip():
                        print(f"        {line}")
        print("=" * 72)
        print(f"통과 {len(self.items) - len(fails)} / {len(self.items)}   위반 {len(fails)}건")
        if fails:
            print("\n고쳐야 하는 항목:")
            for code, label, _, _ in fails:
                print(f"  - {code} {label}")
        return len(fails)


# ── 검사 ────────────────────────────────────────────────────────────────────

def run(data, prev_text=""):
    r = Report()
    rows = data["rows"]
    regions = data.get("region_tokens", [])
    foreign = data.get("foreign_regions", [])
    allowed = data.get("allowed_equipment", [])
    ops_ok = data.get("ops_evidence", [])
    known_equipment = data.get("known_equipment", [])

    info = [x for x in rows if x["type"] == "정보성"]
    rev = [x for x in rows if x["type"] == "후기성"]
    supers = [x for x in rows if x["type"] == "슈퍼세트"]
    all_cells = [(x["n"], c) for x in rows for c in x["comments"]]
    whole = " ".join(x["title"] + x["body"] + " ".join(x["comments"]) for x in rows)

    # ① 글자수
    bad = []
    for x in rows:
        kw = x.get("keyword")
        cap = min(len(kw) + 16, 30) if kw else 24
        if len(x["title"]) > cap:
            bad.append(f"{x['n']}번 제목 {len(x['title'])}자 (상한 {cap})")
        b = len(x["body"])
        lo, hi = {"정보성": (50, 100), "후기성": (100, 170), "슈퍼세트": (300, 400)}[x["type"]]
        if not (lo <= b <= hi):
            bad.append(f"{x['n']}번 본문 {b}자 (범위 {lo}~{hi})")
    r.add("①", "글자수 — 제목·본문", not bad, "\n".join(bad))

    # ② 댓글 길이
    over = [f"{n}번 {len(c)}자: {c}" for n, c in all_cells if len(c) > 35]
    lens = [len(c) for _, c in all_cells]
    med = statistics.median(lens) if lens else 0
    short = sum(1 for l in lens if l <= 15)
    if over:
        detail = "\n".join(over)
    else:
        # 아래 둘은 참고치다(FAIL 아님). 35자 상한 때문에 실측 중앙 32자보다 낮게 나오는 게 정상이고,
        # 짧은 칸 6~10개를 지키면 중앙값은 더 내려간다. 26 아래로 떨어지면 전보체를 의심한다.
        detail = f"전 {len(lens)}칸 35자 이내 / 중앙 {med}자 / 15자 이하 {short}칸"
        if not (26 <= med <= 32):
            detail += "   ← 참고: 중앙 26~32 권장"
        if not (6 <= short <= 10):
            detail += "   ← 참고: 짧은 칸 6~10개 권장"
    r.add("②", "댓글 35자 상한", not over, detail)

    # ③ 키워드 / 지역명
    bad = []
    for x in rows:
        kw = x.get("keyword")
        cz = " ".join(x["comments"])
        if kw:
            if not x["title"].startswith(kw):
                bad.append(f"{x['n']}번 제목이 키워드로 시작하지 않음")
            for place, txt in (("제목", x["title"]), ("본문", x["body"]), ("댓글영역", cz)):
                if txt.count(kw) < 1:
                    bad.append(f"{x['n']}번 {place}에 키워드 '{kw}' 없음")
        else:
            if not any(g in x["body"] for g in regions):
                bad.append(f"{x['n']}번 키워드 없는 행인데 본문에 지역명 없음")

    # 시트 H3에 적힌 지역을 20개에 흩는다. 한 표기만 열네 번 쓰면
    # 나머지 표기로 검색해 들어오는 사람이 이 배치에서 아무것도 못 만난다.
    used = Counter()
    for x in rows:
        hit = count_region_tokens(x["body"], regions)
        if hit:
            used[max(hit, key=len)] += 1
    if regions and rows:
        floor = max(1, round(len(rows) / len(regions) / 2))
        cap = round(len(rows) * 0.55)
        for g in regions:
            if used[g] < floor:
                bad.append(f"지역 '{g}' {used[g]}회 ({floor} 이상) — H3의 표기는 전부 쓴다")
        for g, k in used.items():
            if k > cap:
                bad.append(f"지역 '{g}' {k}회 ({cap} 이하) — 한 표기로 쏠렸다")
    r.add("③", "키워드 3곳 / 무키워드 행 본문 지역명 / H3 지역 고르게", not bad,
          "\n".join(bad) if bad else "지역 배분 " + " · ".join(f"{g} {used[g]}" for g in regions))

    # ④ D열 행별 일치 + D열 밖 장비명
    bad = []
    for x in rows:
        eq = x.get("equipment", "")
        if not eq:
            continue
        # 본문에 D열 표기 그대로 1회가 원칙이다. 「키워드가 시술명을 품으면 충족」은
        # 키워드가 D열 표기를 통째로 품을 때만이다 — 「동탄써마지」는 「써마지FLX」를 품지 않고,
        # 「동탄모공」에는 시술명이 아예 없다. 본문·댓글 통합으로만 보면 본문에서 빠져도 안 잡힌다.
        kw = x.get("keyword") or ""
        if eq not in x["body"] and eq not in kw:
            where = "댓글에만 있음" if eq in " ".join(x["comments"]) else "어디에도 없음"
            bad.append(f"{x['n']}번 본문에 D열 표기 '{eq}' 없음 ({where})")
    # 「울쎄라」가 사전에 있고 D열이 「울쎄라피 프라임」이면 부분 문자열이라 늘 걸린다.
    # 허용 장비명에 포함되는 이름은 D열 밖으로 보지 않는다.
    outside = {e for e in known_equipment
               if e not in allowed and not any(e in a for a in allowed)}
    hits = sorted({e for e in outside if e in whole})
    if hits:
        bad.append("D열 밖 장비명 등장: " + ", ".join(hits))
    r.add("④", "D열 행별 일치 / D열 밖 장비명 0건", not bad, "\n".join(bad))

    # ⑤⑥⑦ 어휘 금지
    def scan(words, allow=None):
        out = []
        for x in rows:
            txt = x["title"] + " " + x["body"] + " " + " ".join(x["comments"])
            for w in words:
                idx = txt.find(w)
                while idx >= 0:
                    ctx = txt[max(0, idx - 6):idx + len(w) + 6]
                    if not (allow and any(a in ctx for a in allow)):
                        out.append(f"{x['n']}번 '{w}' … {ctx.strip()}")
                        break
                    idx = txt.find(w, idx + 1)
        return out

    b5, b6 = scan(BANNED_WORDS) + scan(DEFER) + scan(CHITCHAT), scan(SEASON)
    b7 = scan(THIRD, allow=THIRD_ALLOW)
    r.add("⑤", "금지어(거울·사진·찍·마스크·나이·인사말·「다음에 보자」·「덜어내다」)", not b5, "\n".join(b5))
    r.add("⑥", "계절어 0건", not b6, "\n".join(b6))
    r.add("⑦", "제3자 호칭 0건", not b7, "\n".join(b7))

    # ⑧ 병원명 1회 / 정보성 본문 금지 / 지역 혼입
    bad = []
    for x in rows:
        row_txt = x["title"] + x["body"] + " ".join(x["comments"])
        c = row_txt.count(HOSPITAL)
        if c != 1:
            bad.append(f"{x['n']}번 '{HOSPITAL}' {c}회 (정확히 1회)")
        if x["type"] == "정보성" and HOSPITAL in x["body"]:
            bad.append(f"{x['n']}번 정보성 본문에 병원명")
        for f in foreign:
            if f in row_txt:
                bad.append(f"{x['n']}번 타 지점 지역명 '{f}'")
        for cell in x["comments"]:
            stripped = cell.replace(x.get("keyword") or "\0", "")
            toks = count_region_tokens(stripped, regions)
            if len(toks) >= 2:
                bad.append(f"{x['n']}번 한 댓글에 지역 토큰 {toks}: {cell}")
    r.add("⑧", "병원명 1회 / 정보성 본문 금지 / 지역 혼입", not bad, "\n".join(bad))

    # ⑨ 병원명 문두
    bad = []
    hcells = []
    for x in rows:
        hi = hospital_index(x["comments"])
        if hi is None:
            continue
        cell = x["comments"][hi]
        hcells.append((x["n"], cell))
        toks = eojeol(cell)
        pos = next((i for i, t in enumerate(toks) if HOSPITAL in t), 99)
        kw = x.get("keyword") or ""
        limit = 3 if (kw and kw in cell and any(g in kw for g in regions)) else 2
        # 「동탄역 앞 유앤아이」처럼 앞 어절이 전부 지역·위치 표기면 3어절을 허용한다.
        # 이걸 막으면 materials 3장이 권하는 표기 순환(역·출구·건너편)의 절반이 봉쇄된다.
        LOC = ("앞", "근처", "쪽", "옆", "건너", "건너편", "사거리", "출구", "번출구",
               "역", "점", "지나", "위", "아래")
        if pos == 2 and limit == 2 and all(
                any(g in t for g in regions) or t.endswith(LOC) or t in LOC
                for t in toks[:2]):
            limit = 3
        if pos >= limit:
            bad.append(f"{x['n']}번 {pos + 1}번째 어절 (상한 {limit}): {cell}")
    r.add("⑨", "병원명이 문장 앞 2어절 안", not bad, "\n".join(bad))

    # ⑩ 병원 칸 내용
    care = [n for n, c in hcells if any(m in c for m in CARE_MARKERS)]
    eqin = [n for n, c in hcells if any(e in c for e in allowed)]
    decor = [f"{n}번 인테리어·분위기 '{w}': {c}" for n, c in hcells for w in DECOR if w in c]
    ops = [n for n, c in hcells if any(o in c for o in OPS_INFO)]
    ops_bad = [f"{n}번 운영정보인데 특이사항 근거 없음: {c}" for n, c in hcells
               if any(o in c for o in OPS_INFO) and not any(e in c for e in ops_ok)]
    ad = [f"{n}번 홍보문투 '{w}': {c}" for n, c in hcells for w in AD_TONE if w in c]
    dup = [f"병원 칸 중복: {t}" for t, k in Counter(c for _, c in hcells).items() if k > 1]
    # 임계값은 실제 병원 칸 수에 비례시킨다. 20행 기준 절대수로 박아 두면
    # "1~10번만 먼저 뽑아줘" 같은 부분 작업이 구조적으로 못 넘어 FAIL이 무의미해진다.
    n_h = len(hcells)
    change = [n for n, c in hcells if any(m in c for m in CHANGE_MARKERS)]
    vague = [f"{n}번 변화에 부위가 없다 (「확실히 좋아졌어요」류): {c}" for n, c in hcells
             if any(m in c for m in CHANGE_MARKERS) and not any(p in c for p in BODY_PARTS)]
    need_change, need_eq = round(n_h * 0.65), round(n_h * 0.5)
    care_lo, care_hi = round(n_h * 0.2), round(n_h * 0.5)
    cap_ops = max(2, round(n_h * 0.2))

    # 특이사항·발행요청에 근거가 있으면 최소 1칸은 나가야 한다. 상한만 두면
    # 다른 걸 고치다가 클라이언트 요청이 통째로 사라져도 전 항목이 통과해버린다.
    ops_missing = bool(ops_evidence_required(ops_ok)) and not ops
    if ops_missing:
        ops_bad.append(f"운영 정보 0칸 — 시트에 근거({', '.join(ops_ok)})가 있는데 한 칸도 안 나갔다")

    # 정보성 병원 칸(댓글러가 말한다)과 후기성 답 칸(작성자가 말한다)은 역할이 다르다.
    # 정보성은 새 정보라 변화가 값이지만, 후기성 답 칸은 본문에서 이미 말한 걸
    # 되풀이하면 값이 0이다. 그래서 유형을 갈라 본다.
    info_h = [(n, c) for n, c in hcells if n in {x["n"] for x in info}]
    rev_h = [(n, c) for n, c in hcells if n not in {x["n"] for x in info}]
    body_of = {x["n"]: x["body"] for x in rows}

    echo = []
    for n, c in rev_h:
        b = body_of.get(n, "")
        same_change = [m for m in CHANGE_MARKERS if m in c and m in b]
        same_part = [p for p in BODY_PARTS if p in c and p in b]
        if same_change and same_part:
            echo.append(f"{n}번 답 칸이 본문을 되풀이한다 "
                        f"(같은 부위 '{max(same_part, key=len)}' + 같은 변화 '{same_change[0]}'): {c}")
    rev_care = [n for n, c in rev_h if any(m in c for m in CARE_MARKERS)]
    need_rev_care = round(len(rev_h) * 0.6)
    info_change = [n for n, c in info_h if any(m in c for m in CHANGE_MARKERS)]
    need_info_change = round(len(info_h) * 0.8)

    # 5-2장의 「시술+변화 13칸 이상」을 실제로 막는다.
    # 이게 없으면 후기성 답 칸을 전부 방식으로 써도 통과해 전체 변화가 10칸으로 떨어진다.
    need_change_all = round(n_h * 0.65)
    ok = (len(eqin) >= need_eq and not vague and not decor and not echo
          and len(info_change) >= need_info_change
          and len(change) >= need_change_all
          and len(rev_care) >= need_rev_care
          and len(ops) <= cap_ops and not ops_bad and not ad and not dup)
    notes = [f"병원 칸 {n_h}개 (정보성 {len(info_h)} / 후기성·슈퍼 {len(rev_h)})",
             f"정보성 — 시술+변화 {len(info_change)}칸 ({need_info_change} 이상)",
             f"후기성 답 칸 — 사람·방식 {len(rev_care)}칸 ({need_rev_care} 이상)",
             f"후기성 답 칸 — 본문 되풀이 {len(echo)}건 (0건)",
             f"시술명 포함 {len(eqin)}칸 ({need_eq} 이상)",
             f"전체 시술+변화 {len(change)}칸 ({need_change_all} 이상) · 전체 사람·방식 {len(care)}칸 (참고)",
             f"운영 정보 {len(ops)}칸 ({cap_ops} 이하)"] + echo + vague + decor + ops_bad + ad + dup
    r.add("⑩", "병원 칸 — 정보성은 변화 / 후기성 답 칸은 방식·본문 되풀이 금지", ok, "\n".join(notes))

    # ⑪ 정보성 비병원 칸 분류
    # 댓글은 35자를 넘지 않으니 거리 제한을 두지 않는다. 제한을 두면
    # "저는 그날 살짝 붉고 다음 날엔 멀쩡했어요" 같은 멀쩡한 시술 후기가 설명형으로 샌다.
    exp_re = re.compile(
        r"(저는|제가|저도|저희도|전)\s.*"
        r"(받았|받고|받아|받은|해봤|해보|갔|했|하고|맞았|맞고|채우|채웠|다녀|뒀|봤|겪|견뎠|견딜)")
    emp_re = re.compile(r"(저도|저만|똑같|미루|헤맸|부럽|공감|같은 고민|저랑)")
    # 「아직 안 해봤다」는 과거형 동사를 써도 공감이다.
    # "저도 계속 미루기만 했어요"를 시술 후기로 세면 배분이 무너지고,
    # 그걸 피하려고 공감 칸에서 과거형을 전부 빼면 말투가 한쪽으로 쏠린다.
    not_yet_re = re.compile(r"(미루|못 가|못 갔|안 가봤|안 해봤|못 해봤|망설|헤맸|엄두|겁이|부럽)")
    buckets = Counter()
    misc = []
    for x in info:
        hi = hospital_index(x["comments"])
        if hi is None:
            misc.append(f"{x['n']}번 병원 칸 없음")
            continue
        skip = {hi, hi + 1}
        for i, c in enumerate(x["comments"]):
            if i in skip:
                continue
            if not_yet_re.search(c):
                buckets["공감"] += 1
            elif exp_re.search(c):
                buckets["시술후기"] += 1
            elif emp_re.search(c):
                buckets["공감"] += 1
            else:
                buckets["설명형"] += 1
                misc.append(f"{x['n']}번 설명형: {c}")
            if HOSPITAL in c:
                misc.append(f"{x['n']}번 비병원 칸에 병원명: {c}")
    ok = buckets["시술후기"] >= 6 and buckets["공감"] >= 6 and buckets["설명형"] <= 8
    detail = (f"시술후기 {buckets['시술후기']} (6 이상) / 공감 {buckets['공감']} (6 이상) / "
              f"설명형 {buckets['설명형']} (8 이하)\n" + "\n".join(misc))
    r.add("⑪", "정보성 비병원 칸 — 시술후기 6 / 공감 6 / 설명형 8 이하", ok, detail)

    # ⑪-2 대댓글이 앞 댓글에 답하고 있는가 / 정보성 글쓴이가 시술 경험을 주장하지 않는가
    # 대댓글은 글쓴이 자리다. 정보성 글쓴이는 아직 안 받은 사람이라 시술 경험을 말할 수 없고,
    # 앞 댓글을 받지 않으면 두 사람이 각자 떠드는 꼴이 된다.
    own_exp = re.compile(r"(저는|제가|전|저도)\s?.{0,12}"
                         r"(받았|받고서|받고 |맞았|맞고|해봤|채웠|채우고|다녀왔)")
    STOP = {"그거", "저도", "저는", "제가", "거기", "그게", "그건", "이거", "저기",
            "정말", "진짜", "너무", "한번", "이번", "다음", "그럼", "근데", "아직"}

    def content_words(s):
        """조사가 붙어도 같은 말로 본다.

        어절을 통째로 비교하면 「아래턱」과 「아래턱만」이 다른 토큰이 되어,
        앞 칸의 명사를 조사까지 똑같이 되풀이해야 통과한다 — 그러면 복창 검사에 걸린다.
        규칙의 취지는 「명사는 받고 서술은 바꾼다」이므로 앞 2자를 어간으로 본다.
        """
        out = set()
        for w in re.findall(r"[가-힣]{2,}", s):
            if w in STOP:
                continue
            out.add(w[:2])
        return out

    bad, recv_cliche, thanks = [], [], []
    for x in rows:
        cells = x["comments"]
        hi = hospital_index(cells)
        for i in range(1, len(cells), 2):          # 대댓글 자리
            a = cells[i]
            q = cells[i - 1]
            if x["type"] == "정보성" and own_exp.search(a):
                bad.append(f"{x['n']}번 대댓글{i//2+1} — 글쓴이가 시술 경험을 말한다 "
                           f"(정보성 본문은 아직 안 받은 사람): {a}")
            # 앞 댓글의 말이 한 조각은 남아야 한다. 수신 칸(병원 칸 다음)은 예외 —
            # 거기는 「받았다는 신호」라 어휘가 안 겹치는 게 정상이다.
            if hi is not None and i == hi + 1:
                # 병원명이 나온 댓글에 대한 대댓글은 「정보 알려줘서 고맙다」가 기본형이다.
                # 누가 병원을 알려줬는데 딴 반응을 하면 그 댓글이 공중에 뜬다.
                thanks.append(bool(re.search(r"(감사|고마|고맙)", a)))
                if re.search(r"(건물|지나다|지나가|지나는|몰랐)", a):
                    recv_cliche.append(f"{x['n']}번: {a}")
                continue
            if not (content_words(q) & content_words(a)):
                bad.append(f"{x['n']}번 대댓글{i//2+1} — 앞 댓글을 받지 않는다\n"
                           f"        Q: {q}\n        A: {a}")
            # 받는다고 앞 댓글을 그대로 복창하면 그게 더 AI 티다. 받되 자기 말로 바꾼다.
            qs = re.sub(r"\s+", "", strip_marks(q))
            as_ = re.sub(r"\s+", "", strip_marks(a))
            # 5자가 경계다. 4자로 낮추면 「톤업크림」·「아랫입술」처럼 앞 칸의 명사를
            # 제대로 받는 칸까지 걸린다 — 명사를 받는 건 오히려 규칙이 요구하는 것이다.
            # 대신 「두 번이면 충분한가요」→「두 번이면 되는 건가요」 같은 4자 거울 문장은
            # 기계가 못 잡으니 6-3장 세로 읽기에서 사람이 본다.
            echo = next((qs[k:k + 5] for k in range(len(qs) - 4) if qs[k:k + 5] in as_), None)
            if echo:
                bad.append(f"{x['n']}번 대댓글{i//2+1} — 앞 댓글을 그대로 복창한다 "
                           f"'{echo}': {a}")
    cap_recv = max(3, round(len(rows) * 0.15))
    if len(recv_cliche) > cap_recv:
        bad.append(f"수신 칸이 「건물·지나다니다·몰랐다」 한 틀로 굳었다 "
                   f"{len(recv_cliche)}개 ({cap_recv} 이하)\n        "
                   + "\n        ".join(recv_cliche))
    # 병원 칸 다음 대댓글은 고맙다는 말이 기본형. 인지로만 받는 건 2~3개까지.
    if thanks:
        need_thanks = round(len(thanks) * 0.7)
        if sum(thanks) < need_thanks:
            bad.append(f"병원명이 나온 댓글에 「정보 고맙다」로 답한 칸 {sum(thanks)}개 "
                       f"({need_thanks} 이상) — 누가 병원을 알려줬는데 딴 반응을 하면 "
                       f"그 댓글이 공중에 뜬다")
    r.add("⑪-2", "대댓글이 앞 댓글에 답하는가 / 글쓴이가 시술 경험을 주장하지 않는가",
          not bad, "\n".join(bad) if bad else
          f"전 대댓글이 앞 칸을 받는다 · 수신 칸 상투구 {len(recv_cliche)}개")

    # ⑪-3 후기성 댓글 역할 — 칸마다 할 일이 정해져 있다(5-8장)
    #   댓글1 = 시술 궁금증(통증·붓기·회차·다운타임) 또는 부러움
    #   댓글2 = 같은 고민인데 어디 다녀왔는지 (장소 질문)
    #   댓글3 = 슈퍼세트에만, 본문 내용에 대한 질문·공감·부러움 (⛔ 잡담 금지)
    CURIOUS = ["아프", "아팠", "따갑", "붓", "부었", "부어", "멍", "다음날", "다음 날",
               "회차", "몇 번", "몇 회", "몇 샷", "언제부터", "얼마나", "며칠", "출근",
               "다운타임", "붉은", "따끔", "참을", "마취", "통증", "간격", "유지"]
    ENVY = ["부럽", "좋겠", "솔깃", "대단", "성공", "잘 되셨", "잘되셨", "효과 보", "나도 그랬으면"]
    bad = []
    for x in rev + supers:
        c = x["comments"]
        if len(c) < 4:
            continue
        if not (any(w in c[0] for w in CURIOUS) or any(w in c[0] for w in ENVY)
                or "?" in c[0]):
            bad.append(f"{x['n']}번 댓글1이 시술 궁금증도 부러움도 아니다: {c[0]}")
        if not any(w in c[2] for w in PLACE_ASK):
            bad.append(f"{x['n']}번 댓글2가 「어디 다녀왔는지」를 묻지 않는다: {c[2]}")
        if len(c) >= 6:
            body_words = {w[:2] for w in re.findall(r"[가-힣]{2,}", x["body"])}
            c3 = {w[:2] for w in re.findall(r"[가-힣]{2,}", c[4])}
            if not (body_words & c3):
                bad.append(f"{x['n']}번 댓글3이 본문과 무관하다 (잡담 금지): {c[4]}")
    r.add("⑪-3", "후기성 댓글1 궁금증·부러움 / 댓글2 장소 질문 / 댓글3 본문 관련", not bad,
          "\n".join(bad) if bad else f"후기성·슈퍼 {len(rev) + len(supers)}개 역할 배치 정상")

    # ⑫ 장소 질문
    bad, asks = [], []
    for x in rev + supers:
        hi = hospital_index(x["comments"])
        if hi is None:
            bad.append(f"{x['n']}번 병원 칸 없음")
            continue
        if hi == 0:
            bad.append(f"{x['n']}번 병원 칸이 댓글1 — 아무도 묻지 않았다")
            continue
        prev_cell = x["comments"][hi - 1]
        asks.append((x["n"], prev_cell))
        if not any(p in prev_cell for p in PLACE_ASK):
            bad.append(f"{x['n']}번 병원 칸 직전이 장소 질문이 아님: {prev_cell}")
        kw = x.get("keyword")
        ans = x["comments"][hi]
        if kw and kw in ans:
            bad.append(f"{x['n']}번 답 칸에 키워드 재등장: {ans}")
        # 답 칸은 정보성 병원 칸과 같은 형태다 — [지역] 유앤아이 [시술] + [변화].
        # 지역이나 시술명이 빠지면 「어디서 뭘 받았는지」가 안 남는다.
        if not kw and regions and not count_region_tokens(ans, regions):
            bad.append(f"{x['n']}번 답 칸에 지역 표기 없음: {ans}")
        eq = x.get("equipment", "")
        if eq and eq not in ans and not any(e in ans for e in allowed):
            bad.append(f"{x['n']}번 답 칸에 시술명 없음: {ans}")
    where = sum(1 for _, a in asks if ("어디" in a or "어느" in a))
    dupa = [t for t, k in Counter(a for _, a in asks).items() if k > 1]
    if where > 6:
        bad.append(f"「어디·어느」 {where}개 (6 이하)")
    if dupa:
        bad.append("장소 질문 중복: " + " / ".join(dupa))
    r.add("⑫", "장소 질문이 병원 칸 앞에 / 「어디·어느」 6 이하 / 전부 다름", not bad,
          "\n".join(bad) if bad else
          (f"장소 질문 {len(asks)}개 · 「어디·어느」 {where}개" if asks
           else "⚠ 후기성·슈퍼세트가 없어 검사되지 않았다 — PASS를 근거로 삼지 말 것"))

    # ⑬ 부호 비율
    notes, ok = [], True
    groups = {"정보성_본문": [x["body"] for x in info],
              "후기성_본문": [x["body"] for x in rev + supers],
              "댓글": [c for _, c in all_cells]}
    for gname, texts in groups.items():
        if not texts:
            continue
        for mark, target in TARGET[gname].items():
            hit = sum(1 for t in texts if mark in t)
            pct = round(hit * 100 / len(texts))
            if abs(pct - target) > TOLERANCE:
                ok = False
                notes.append(f"{gname} '{mark}' {pct}% (목표 {target}%, ±{TOLERANCE}%p)")
    emo = [f"{n}번 이모지/♡: {c}" for n, c in all_cells if EMOJI.search(c)]
    emo += [f"{x['n']}번 본문 이모지/♡" for x in rows if EMOJI.search(x["body"])]
    if emo:
        ok = False
        notes += emo
    r.add("⑬", "부호 비율 ±15%p / 그래픽 이모지·♡ 0건", ok,
          "\n".join(notes) if notes else "전 구간 목표 범위 안")

    # ⑭ AI 문장 · 마케팅 용어 · 상투구 · 접속부사 · 배타적 주장
    bad = []
    for x in rows:
        txt = x["title"] + " " + x["body"] + " " + " ".join(x["comments"])
        for w in AI_PHRASES + MARKETING:
            if w in txt:
                bad.append(f"{x['n']}번 AI 문장 '{w}'")
    counts = {w: whole.count(w) for w in CLICHE}
    for w, k in counts.items():
        if k > 8:
            bad.append(f"상투구 '{w}' {k}회 (8 이하)")
    if whole.count("추천드려") > 2:
        bad.append(f"'추천드려' {whole.count('추천드려')}회 (2 이하)")
    conj = sum(1 for x in rows if any(x["body"].startswith(c) for c in CONJ_HEAD))
    if conj > 3:
        bad.append(f"접속부사로 여는 본문 {conj}개 (3 이하)")
    exc = sum(whole.count(w) for w in EXCLUSIVE)
    if exc > 1:
        bad.append(f"배타적 주장 합계 {exc}회 (1 이하) — 오탐인지 문맥 확인")
    r.add("⑭", "AI 문장 / 마케팅 용어 / 상투구 / 접속부사 / 배타적 주장", not bad,
          "\n".join(bad) if bad else "상투구 " + " · ".join(f"{w} {k}" for w, k in counts.items()))

    # ⑮ 정보성 문장 수 · 종결
    s1 = sum(1 for x in info if len(sentences(x["body"])) == 1)
    s3 = sum(1 for x in info if len(sentences(x["body"])) >= 3)
    # 요청 종결 개수는 여기서 막지 않는다. ⑮-2가 「9개는 병원 추천 요청으로 닫는다」를
    # 요구하므로 상한 8을 두면 두 검사가 정면으로 부딪히고, 사전에 없는 어미를 찾아
    # 우회하는 짓을 하게 된다. 종결의 다양성은 ⑮-2의 「종결 2어절 2회까지」가 본다.
    ask_end = sum(1 for x in info if re.search(
        r"(까요|나요|주세요|궁금해요|부탁드려요|되나요|드려요|여쭤봐요|좋겠어요)\W*$",
        strip_marks(x["body"])))
    bad = []
    # 한 호흡으로 잇는 게 기본이다. 3문장을 강제하면 본문을 토막 내게 되고
    # 그게 대행 원고 티의 원인이었다 — 그래서 1문장 쪽에 하한을 둔다.
    if s1 < 4:
        bad.append(f"1문장 원고 {s1}개 (4 이상) — 끊지 말고 ~해서·~는데로 이어라")
    if s3 > 2:
        bad.append(f"3문장 이상 원고 {s3}개 (2 이하) — 세 토막으로 끊긴 본문이 많다")
    r.add("⑮", "정보성 문장 수 — 1문장 4개 이상 · 3문장 2개 이하", not bad,
          "\n".join(bad) if bad else f"1문장 {s1} · 3문장+ {s3} · 요청종결 {ask_end}(참고)")

    # ⑮-2 정보성 본문 — 병원 찾는 글인가 / 묻는 방식이 반복되지 않는가
    bad = []
    # 병원 추천 요청으로 닫혔는가 — 마지막 문장에 병원 찾는 말 + 요청·질문 종결이 같이 있어야 한다.
    ask_end_re = re.compile(r"(까요|나요|주세요|부탁드려요|좋겠어요|궁금해요|계실까요|없을까요|어때요)")
    closes = []
    for x in info:
        ss = sentences(x["body"])
        last = ss[-1] if ss else ""
        if any(w in last for w in CLINIC_SEEK) and ask_end_re.search(last):
            closes.append(x["n"])
    if info:
        lo, hi = round(len(info) * 0.8), len(info)
        if not (lo <= len(closes) <= hi):
            bad.append(f"병원 추천 요청으로 닫는 원고 {len(closes)}개 ({lo}~{hi}) — "
                       f"목표는 10개 중 9개. 이게 적으면 댓글1의 병원 추천이 뜬금없어진다")

    seek = [x["n"] for x in info if any(w in x["body"] for w in CLINIC_SEEK)]
    if info and len(seek) < round(len(info) * 0.8):
        bad.append(f"병원을 찾는 글 {len(seek)}개 ({round(len(info) * 0.8)} 이상)")

    # 종결 2어절이 겹치면 같은 사람이 열 번 쓴 글로 읽힌다.
    tails = Counter()
    for x in info:
        toks = eojeol(strip_marks(x["body"]))
        if toks:
            tails[" ".join(toks[-2:])] += 1
    bad += [f"종결 '{t}' {k}회 (2회까지)" for t, k in tails.items() if k > 2]

    # 요청 어구는 긴 것부터 세고 그 자리를 지워 「잘하는 피부과」가 「잘하는 데」로 겹세지 않게 한다.
    info_bodies = [x["body"] for x in info]
    for ph in sorted(ASK_PHRASES, key=len, reverse=True):
        k = 0
        for i, b in enumerate(info_bodies):
            if ph in b:
                k += b.count(ph)
                info_bodies[i] = b.replace(ph, " ")
        if k > 2:
            bad.append(f"요청 어구 '{ph}' {k}회 (2회까지)")

    r.add("⑮-2", "정보성 — 9개는 병원 추천 요청으로 닫기 / 종결·요청 어구 반복 2회까지", not bad,
          "\n".join(bad) if bad else
          f"추천 요청으로 닫음 {len(closes)}개 · 병원 찾는 글 {len(seek)}개 · "
          f"종결 {len(tails)}종 · 요청 어구 반복 없음")

    # ⑯ 지역명 + 시술명 인접 (키워드 없는 행)
    adj = []
    for x in rows:
        if x.get("keyword"):
            continue
        toks = eojeol(x["body"])
        for i in range(len(toks) - 1):
            if any(g in toks[i] for g in regions) and any(e in toks[i + 1] for e in allowed):
                adj.append(f"{x['n']}번: {toks[i]} {toks[i + 1]}")
    # 키워드가 전 행 없는 배치는 20행 전부 본문에 지역명을 넣어야 해서
    # 인접을 피하려다 「[지역] 쪽에서」 한 형태로 쏠린다. 그래서 형태별로도 센다.
    forms = Counter()
    for x in rows:
        toks = eojeol(x["body"])
        for i, t in enumerate(toks):
            if any(g in t for g in regions):
                nxt = toks[i + 1] if i + 1 < len(toks) else ""
                stem = re.sub(r"^.*?(" + "|".join(re.escape(g) for g in regions) + r")", "", t)
                forms[(stem + " " + nxt).strip()] += 1
    over = [f"지역 표현 '{f}' {k}회 (4 이하)" for f, k in forms.items() if k > 4]
    r.add("⑯", "지역명·시술명 인접 5개 이하 / 지역 표현 형태 4회 이하",
          len(adj) <= 5 and not over,
          "\n".join(adj + over) if (adj or over) else f"인접 0개 · 지역 표현 {len(forms)}종")

    # ⑰ 후기 문장 길이 편차 / 제목 물음표
    bad = []
    for x in rev:
        ss = [len(s) for s in sentences(x["body"])]
        if len(ss) >= 2:
            sd = statistics.pstdev(ss)
            if sd < 8:
                bad.append(f"{x['n']}번 문장 길이 편차 {sd:.1f} (8 이상) — 짧은 문장 하나 끼울 것")
    # 후기성 제목 — 짧고, 시술명이 들어가고, 고민 설명이 아니어야 한다.
    for x in rev:
        t, eq = x["title"], x.get("equipment", "")
        if len(t) > 18:
            bad.append(f"{x['n']}번 후기 제목 {len(t)}자 (18자 이하) — 고민은 본문에서: {t}")
        if eq and eq not in t and not any(e in t for e in allowed):
            bad.append(f"{x['n']}번 후기 제목에 시술명 없음 — 뭘 받았는지 안 보인다: {t}")
    hugi = sum(1 for x in rev if re.search(r"후기\W*$", x["title"]))
    if hugi > 4:
        bad.append(f"'…후기'로 끝나는 제목 {hugi}개 (4개 이하)")
    q_rev = sum(1 for x in rev if "?" in x["title"])
    q_info = sum(1 for x in info if "?" in x["title"])
    if q_rev:
        bad.append(f"후기성 제목 물음표 {q_rev}개 (0이어야 함)")
    if info and not (0.35 <= q_info / len(info) <= 0.75):
        bad.append(f"정보성 제목 물음표 {q_info}/{len(info)} (절반 안팎 권장)")
    # 정보성 제목 — 병원 찾는 프레임 7할, 같은 요청 어구 2회까지
    if info:
        t_seek = [x["n"] for x in info if any(w in x["title"] for w in TITLE_SEEK)]
        need = round(len(info) * 0.7)
        if len(t_seek) < need:
            bad.append(f"정보성 제목 중 병원 찾는 프레임 {len(t_seek)}개 ({need} 이상) — "
                       f"제목이 시술 질문이면 본문과 따로 논다")
        titles = [x["title"] for x in info]
        for ph in sorted(ASK_PHRASES + ["알아보고 있는데", "알아보는 중", "추천해주세요"],
                         key=len, reverse=True):
            k = 0
            for i, t in enumerate(titles):
                if ph in t:
                    k += 1
                    titles[i] = t.replace(ph, " ")
            if k > 2:
                bad.append(f"제목 요청 어구 '{ph}' {k}회 (2회까지)")
    r.add("⑰", "후기 문장 길이 편차 / 제목 물음표 / 정보성 제목 프레임", not bad,
          "\n".join(bad) if bad else
          (f"정보성 제목 ? {q_info}개 · 후기성 0개" if rev
           else "⚠ 후기성이 없어 문장 길이 편차는 검사되지 않았다"))

    # ⑱ 댓글 수치 ⊆ 본문 수치
    numword = re.compile(r"(한|두|세|네|다섯|여섯|일곱|여덟|아홉|열|\d+)\s?(번|회차|회|주|달|개월|샷|cc)")
    # 붙여 쓴 "한번"은 수치가 아니라 「한번 가보세요」의 부사다. 띄어 쓴 "한 번"만 수치로 본다.
    NOT_COUNT = {"한번"}
    bad = []
    for x in rev + supers:
        b = {m.group(0).replace(" ", "") for m in numword.finditer(x["body"])}
        for c in x["comments"]:
            for m in numword.finditer(c):
                if m.group(0) in NOT_COUNT:
                    continue
                v = m.group(0).replace(" ", "")
                if v not in b:
                    bad.append(f"{x['n']}번 댓글 '{v}' — 본문에 없는 수치: {c}")
    r.add("⑱", "댓글 수치가 본문 수치 안에 있는가", not bad, "\n".join(bad))

    # ⑲ 댓글·제목 중복
    bad = [f"댓글 중복: {t}" for t, k in Counter(c for _, c in all_cells).items() if k > 1]
    heads = Counter()
    for x in rows:
        t = x["title"]
        if x.get("keyword"):
            t = t[len(x["keyword"]):].strip()
        if t:
            heads[t[:6]] += 1
    bad += [f"제목 앞 6자 중복 '{h}' {k}회" for h, k in heads.items() if k > 1]
    r.add("⑲", "댓글 문구 / 제목 앞 6자 중복", not bad, "\n".join(bad))

    # ⑳ 마크다운 기호
    md = [f"{x['n']}번" for x in rows
          if re.search(r"(^|\s)[#*>]|\s-\s", x["body"] + " " + " ".join(x["comments"]))]
    r.add("⑳", "마크다운 기호 0건", not md, ", ".join(md))

    # ㉑ 이전 원고 교차 대조
    if prev_text:
        # 화이트리스트에는 병원명도 넣는다 — 지점이 달라도 「유앤아이 + 시술명」은 같은 글자가 나온다.
        white = {w.replace(" ", "") for w in
                 set(allowed) | set(regions) | {HOSPITAL}
                 | {x.get("keyword") or "" for x in rows} if w}
        # 5-3장이 「[지역] 유앤아이 [시술명]」 어순을 요구하므로, 이 셋이 붙어 만드는
        # 조각(「앤아이젠틀맥스프」)은 문장을 어떻게 바꿔도 이전 배치와 같아진다.
        # 낱말만 화이트리스트에 넣으면 9자 넘는 장비명에서 양방향 포함이 둘 다 실패한다.
        # 규칙이 강제하는 조합은 겹침으로 세지 않는다.
        eqs = {e.replace(" ", "") for e in allowed if e}
        regs = {r.replace(" ", "") for r in regions if r}
        white |= {HOSPITAL + e for e in eqs}
        white |= {r + HOSPITAL for r in regs}
        white |= {r + HOSPITAL + e for r in regs for e in eqs}
        prev_n = ngrams(prev_text)
        overlaps = set()
        for x in rows:
            # 칸마다 따로 센다. 본문과 댓글을 이어 붙인 뒤 공백을 지우면
            # 「댓글1 끝 + 대댓글1 앞」이 붙어 실제로 없는 문구가 겹침으로 잡힌다.
            cell_grams = set()
            for cell in [x["body"]] + list(x["comments"]):
                cell_grams |= ngrams(cell)
            for g in cell_grams:
                # 「젠틀맥스프로플러스」처럼 9자가 넘는 이름은 8자 조각이 이름을 통째로 담지 못한다.
                # w in g 만 보면 그 이름의 내부 조각이 전부 겹침으로 잡힌다 — 양방향으로 본다.
                if g in prev_n and not any(w in g or g in w for w in white):
                    overlaps.add(f"{x['n']}번: {g}")
        uniq = sorted(overlaps)
        tail = f"\n... 총 {len(uniq)}건" if len(uniq) > 25 else ""
        r.add("㉑", "이전 원고와 8자 연속 겹침 5건 이하", len(uniq) <= 5,
              "\n".join(uniq[:25]) + tail if uniq else "겹침 0건")
    else:
        r.add("㉑", "이전 원고 교차 대조", True,
              "--prev 미지정 — 이전 배치·타 지점 원고를 모아 반드시 따로 한 번 더 돌릴 것")

    # ㉒ 본문 첫 문장 — 몸짓 연출 금지
    # 고민은 몸짓이 아니라 피부 상태로 연다. 첫 문장만 본다: 뒤쪽 시술 설명에서
    # 「손으로 놔주셔서」처럼 정당하게 쓰이는 자리를 잡으면 안 되기 때문이다.
    gest = []
    for x in rows:
        ss = sentences(x["body"])
        head = ss[0] if ss else x["body"]
        hit = [w for w in GESTURE if w in head]
        if hit:
            gest.append(f"{x['n']}번: {', '.join(hit)}  ← {head[:40]}")
    r.add("㉒", "본문 첫 문장 몸짓 연출 0건", not gest, "\n".join(gest) or "0건")

    # ㉓ 회차 서사는 여러 회 받는 시술에만
    rep = []
    for x in rows:
        eq = (x.get("equipment") or "").lower().replace(" ", "")
        ok = x.get("repeat_ok")
        if ok is None:
            ok = any(w in eq for w in REPEAT_OK_DEVICES)
        if ok:
            continue
        for label, text in (("제목", x["title"]), ("본문", x["body"])):
            for s in (sentences(text) or [text]):
                if REPEAT_RE.search(s) and not any(w in s for w in REPEAT_ASK):
                    rep.append(f"{x['n']}번 {label}({x.get('equipment')}): {s[:40]}")
    r.add("㉓", "회차 서사는 흉터·여드름·색소·제모 행에만", not rep,
          "\n".join(rep) or "0건 — 리프팅·스킨부스터는 경과 시점으로 씀")

    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_file")
    ap.add_argument("--prev", help="이전 지점·이전 배치 원고 텍스트 파일")
    a = ap.parse_args()

    with open(a.json_file, encoding="utf-8") as f:
        data = json.load(f)
    prev = ""
    if a.prev:
        with open(a.prev, encoding="utf-8") as f:
            prev = f.read()

    sys.exit(1 if run(data, prev).dump() else 0)


if __name__ == "__main__":
    main()
'''

# ============================================================================
# views.assign
# ============================================================================
MODULES['views.assign'] = r'''"""작가 배정·마감 기한 (관리자)"""
from datetime import date

import pandas as pd
import streamlit as st

from core.common import (MANAGER, WRITER, audit, deadline_badge, notify, to_date, user_name, user_options)
from core.db import ex, q
from core.ops import plan_publish_dates, progress


def render(ctx):
    user, month = ctx["user"], ctx["month"]
    st.title("🗓️ 작가 배정·마감 기한")
    st.caption("지점별 담당자·작가와 단계별 마감일을 정합니다. 앞 단계가 늦어지면 뒤 단계 여유가 줄어드는 것도 함께 보여줍니다.")

    mgrs, wrs = user_options(MANAGER), user_options(WRITER)
    rows = q("""SELECT bm.*, b.name, b.hospital FROM branch_month bm JOIN branches b ON b.id=bm.branch_id
                WHERE bm.month=? AND b.active=1 ORDER BY b.hospital, b.name""", (month,))
    data = []
    for r in rows:
        p = progress(month, r["branch_id"])
        set_done = bool(r["material_done"]) or p["kw_missing"] == 0
        ds, dw = to_date(r["dl_setting"]), to_date(r["dl_writing"])
        start = max(date.today(), ds) if ds and not set_done else (ds or date.today())
        slack = (dw - start).days if dw else None
        data.append({"branch_id": r["branch_id"], "지점": r["name"], "병원": r["hospital"],
                     "담당자": user_name(r["manager_id"]), "작가": user_name(r["writer_id"]),
                     "세팅 기한": ds, "작성 기한": dw, "발행 기한": to_date(r["dl_publish"]),
                     "발행 예정일": to_date(r["planned_publish"]),
                     "상태": " ".join(x for x in [deadline_badge(r["dl_setting"], set_done),
                                                  deadline_badge(r["dl_writing"], p["written"] >= p["total"])] if x),
                     "작가 작성 여유(일)": slack})
    df = pd.DataFrame(data)
    if df.empty:
        st.info("이 달의 지점이 없습니다.")
        return
    with st.expander("⏱️ 전체 지점 마감일 한 번에 바꾸기"):
        c = st.columns(4)
        a = c[0].date_input("세팅 기한", value=None, key="bulk_s")
        b = c[1].date_input("작성 기한", value=None, key="bulk_w")
        d = c[2].date_input("발행 기한", value=None, key="bulk_p")
        if c[3].button("모든 지점에 적용"):
            for col, v in [("dl_setting", a), ("dl_writing", b), ("dl_publish", d)]:
                if v:
                    ex(f"UPDATE branch_month SET {col}=? WHERE month=?", (v.isoformat(), month))
            audit(user["name"], "마감 일괄 변경", f"{month} {a} {b} {d}")
            st.rerun()

    ed = st.data_editor(
        df, hide_index=True, width="stretch", key=f"assign_{month}",
        disabled=["branch_id", "지점", "병원", "상태", "작가 작성 여유(일)"],
        column_config={
            "branch_id": None,
            "담당자": st.column_config.SelectboxColumn("담당자", options=[""] + list(mgrs)),
            "작가": st.column_config.SelectboxColumn("작가", options=[""] + list(wrs)),
            "세팅 기한": st.column_config.DateColumn("세팅 기한"),
            "작성 기한": st.column_config.DateColumn("작성 기한"),
            "발행 기한": st.column_config.DateColumn("발행 기한"),
            "발행 예정일": st.column_config.DateColumn("발행 예정일", help="비우면 완료 순서대로 하루 N곳씩 자동 배정"),
        })
    c1, c2 = st.columns(2)
    if c1.button("💾 저장", type="primary", width="stretch"):
        old = {r["branch_id"]: r for r in data}
        for r in ed.to_dict("records"):
            o = old[r["branch_id"]]
            mid, wid = mgrs.get(r["담당자"]), wrs.get(r["작가"])
            ds = lambda v: v.isoformat() if hasattr(v, "isoformat") and not pd.isna(v) else None
            ex("""UPDATE branch_month SET manager_id=?, writer_id=?, dl_setting=?, dl_writing=?, dl_publish=?,
                  planned_publish=? WHERE month=? AND branch_id=?""",
               (mid, wid, ds(r["세팅 기한"]), ds(r["작성 기한"]), ds(r["발행 기한"]), ds(r["발행 예정일"]),
                month, r["branch_id"]))
            if r["작가"] != o["작가"] and wid:
                notify(wid, "할 일", f"[{r['지점']}] 원고 작성이 배정되었습니다. 작성 기한 {ds(r['작성 기한']) or '-'}")
            if r["담당자"] != o["담당자"] and mid:
                notify(mid, "배정", f"[{r['지점']}] 담당 지점으로 배정되었습니다.")
            if (r["담당자"], r["작가"]) != (o["담당자"], o["작가"]):
                audit(user["name"], "배정 변경", f"{r['지점']}: {o['담당자']}/{o['작가']} → {r['담당자']}/{r['작가']}")
        st.success("저장했습니다.")
        st.rerun()
    if c2.button("📅 발행 예정일 자동 배정 (빈 곳만)", width="stretch"):
        plan_publish_dates(month)
        st.rerun()
'''

# ============================================================================
# views.audit
# ============================================================================
MODULES['views.audit'] = r'''"""변경 이력: 누가, 언제, 무엇을 바꿨는지"""
import pandas as pd
import streamlit as st

from core.common import to_excel
from core.db import q


def render(ctx):
    st.title("🧾 변경 이력")
    s = st.text_input("검색 (사람·내용)")
    rows = q("SELECT at 언제, user 누가, action 무엇, detail 내용 FROM audit ORDER BY id DESC LIMIT 3000")
    if s:
        rows = [r for r in rows if s in (r["누가"] or "") + (r["무엇"] or "") + (r["내용"] or "")]
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, width="stretch", height=600)
    if not df.empty:
        st.download_button("📥 엑셀로 받기", to_excel({"변경 이력": df}), file_name="변경이력.xlsx")
'''

# ============================================================================
# views.board
# ============================================================================
MODULES['views.board'] = r'''"""원고 보드 (중심 화면): 월 → 병원 → 지점 → 원고 20건 한 화면.
왼쪽 원고 재료 / 가운데 20건 표 / 오른쪽 선택 원고 상세."""
import json

import pandas as pd
import streamlit as st

from core import ai
from core.checks import batch_result, check_branch, highlight
from core.common import (ADMIN, EXEC, HOSPITALS, MANAGER, WRITER, audit, branch_equipment_grouped,
                         deadline_badge, get_setting, my_branch_ids, user_name)
from core.db import ex, now, q, q1, qv
from core.ops import (TEXT_FIELDS, material_done, ms_images, ms_rows, place_image, progress, save_manuscripts,
                      set_status)

STATUS_ICON = {"작성 전": "⚪ 작성 전", "작성 중": "✏️ 작성 중", "검수 대기": "🔘 검수 대기", "피드백": "🟡 피드백",
               "완료": "🟢 완료", "사용 완료": "🔵 사용 완료"}
COLS = {"no": "번호", "mtype": "유형", "status": "상태", "check": "검수", "keyword": "키워드", "equipment": "장비",
        "special": "특이사항", "no_equip_mention": "장비명 언급 금지", "photo": "사진", "title": "제목", "body": "본문",
        "c1": "댓글1", "r1": "대댓글1", "c2": "댓글2", "r2": "대댓글2", "c3": "댓글3(슈퍼)", "r3": "대댓글3(슈퍼)"}


def _visible_branches(ctx):
    user, role, month = ctx["user"], ctx["role"], ctx["month"]
    bs = q("SELECT * FROM branches WHERE active=1 ORDER BY name")
    if role in (MANAGER, WRITER):
        mine = set(my_branch_ids(user, month))
        bs = [b for b in bs if b["id"] in mine]
    elif role == EXEC:
        bs = [b for b in bs if b["hospital"] == "로컬"]   # 실행사: 로컬 지점 원고 작성
    elif ctx["mine"] and role == ADMIN:
        pass
    return bs


def _can(role, bm, user, branch):
    """(재료 입력 가능, 본문 작성 가능, 컨펌 가능)"""
    if role == ADMIN:
        return True, True, True
    if role == MANAGER:
        return bm and bm["manager_id"] == user["id"], False, False
    if role == WRITER:
        return False, bm and bm["writer_id"] == user["id"], False
    if role == EXEC:
        return False, branch["hospital"] == "로컬", False
    return False, False, False


def render(ctx):
    user, role, month = ctx["user"], ctx["role"], ctx["month"]
    st.title("📋 원고 보드")
    bs = _visible_branches(ctx)
    if not bs:
        st.info("볼 수 있는 지점이 없습니다. (담당 배정을 확인해 주세요)")
        return
    c1, c2, c3 = st.columns([1.2, 2, 1.3])
    hosps = ["전체"] + [h for h in HOSPITALS if any(b["hospital"] == h for b in bs)]
    hosp = c1.selectbox("병원", hosps, key="bd_hosp")
    cand = [b for b in bs if hosp == "전체" or b["hospital"] == hosp]
    if not cand:
        st.info("지점이 없습니다.")
        return
    names = [b["name"] for b in cand]
    if st.session_state.get("bd_branch") not in names:
        st.session_state.bd_branch = names[0]
    bname = c2.selectbox("지점", names, key="bd_branch")
    branch = next(b for b in cand if b["name"] == bname)
    bid = branch["id"]
    view = c3.radio("보기", ["표 보기", "카페 미리보기"], horizontal=True, key="bd_view")

    bm = q1("SELECT * FROM branch_month WHERE month=? AND branch_id=?", (month, bid))
    if not bm:
        st.warning("이 달의 틀이 없습니다. 사이드바 운영 월을 확인하거나 설정 > [다음 달 시작]을 실행하세요.")
        return
    can_input, can_write, can_confirm = _can(role, bm, user, branch)
    rows = ms_rows(month, bid)
    p = progress(month, bid)

    # ── 위쪽 줄 ───────────────────────────────────────────────────────────────
    def cnt(t):
        rr = [r for r in rows if r["mtype"] == t]
        return f"{sum(r['status'] in ('완료', '사용 완료') for r in rr)}/{len(rr)}"
    people = "" if role == EXEC else f" · 담당 {user_name(bm['manager_id']) or '-'} · 작가 {user_name(bm['writer_id']) or '-'}"
    set_done = bool(bm["material_done"]) or p["kw_missing"] == 0
    badges = " ".join(x for x in [
        ("세팅 " + deadline_badge(bm["dl_setting"], set_done)) if deadline_badge(bm["dl_setting"], set_done) else "",
        ("작성 " + deadline_badge(bm["dl_writing"], p["written"] >= p["total"])) if deadline_badge(bm["dl_writing"], p["written"] >= p["total"]) else ""] if x)
    with st.container(border=True):
        st.markdown(f"**{bname}**{people} · 진행상황 **{p['done']}/{p['total']}** {badges}  \n"
                    f"<span class='small'>정보성 {cnt('정보성')} · 후기성 {cnt('후기성')} · 슈퍼세트 {cnt('슈퍼세트')}"
                    f" · 마감 세팅 {bm['dl_setting'] or '-'} / 작성 {bm['dl_writing'] or '-'} / 발행 {bm['dl_publish'] or '-'}"
                    f"{' · 위치 ' + branch['location'] if branch['location'] else ''}</span>", unsafe_allow_html=True)
        links = [f"[보고서]({branch['report_link']})" if branch["report_link"] else "",
                 f"[사진]({branch['photo_link']})" if branch["photo_link"] else ""]
        if any(links):
            st.markdown(" · ".join(l for l in links if l))

    left, mid, right = st.columns([1.1, 3.2, 1.9])

    # ── 왼쪽: 원고 재료 ───────────────────────────────────────────────────────
    with left:
        with st.expander("📝 원고 재료", expanded=True):
            if branch["hospital"] == "로컬":
                st.markdown("**원장님 가이드라인**")
                st.write(branch["guideline"] or "(설정 안 됨 — 지점 화면에서 입력)")
            dis = not (can_input or role == ADMIN)
            req = st.text_area("발행 요청사항", bm["req_notes"] or "", disabled=dis, key=f"req_{bid}")
            comp = st.text_area("경쟁사 대비 장점", bm["competitor"] or "", disabled=dis, key=f"comp_{bid}")
            must = st.text_area("넣었으면 하는 내용", bm["must_include"] or "", disabled=dis, key=f"must_{bid}")
            spc = st.text_area("특이사항", bm["special"] or "", disabled=dis, key=f"spc_{bid}",
                               help="예: 수술은 진행하지 않음 / 장비언급X -> 피코토닝으로")
            if not dis and st.button("재료 저장", key=f"savemat_{bid}", width="stretch"):
                ex("""UPDATE branch_month SET req_notes=?, competitor=?, must_include=?, special=?
                      WHERE month=? AND branch_id=?""", (req, comp, must, spc, month, bid))
                audit(user["name"], "원고 재료 저장", bname)
                st.success("저장했습니다.")
            eq = branch_equipment_grouped(bid)
            st.markdown("**보유장비**  \n" + (", ".join(eq) if eq else "(없음)"))
            if branch["banned_topics"]:
                st.markdown(f"**금지 주제**: {branch['banned_topics']}")
            if can_input and not bm["material_done"]:
                if st.button("✅ 재료 입력 완료 → 작가에게", key=f"matdone_{bid}", width="stretch", type="primary"):
                    material_done(month, bid, user)
                    st.rerun()
            elif bm["material_done"]:
                st.caption("재료 입력 완료됨")

    # ── 가운데: 20건 ──────────────────────────────────────────────────────────
    with mid:
        batch = batch_result(month, bid)
        if batch:
            with st.expander(f"⚠️ 지점 전체(20건 묶음) 검수 {len(batch)}건", expanded=False):
                for b in batch:
                    st.markdown(f"- **{b['code']} {b['label']}** — {b['detail']}")
        tools = st.columns(3)
        if (can_write or role == ADMIN) and tools[0].button("🤖 빈 원고 AI 초안", width="stretch",
                                                             help="uandi-wongo 스킬로 비어 있는 원고만 채웁니다"):
            _ai_draft(month, branch, bm, rows, user)
        if tools[1].button("🔍 다시 검수", width="stretch"):
            check_branch(month, bid)
            st.rerun()
        if role == ADMIN and ai.available() and tools[2].button("🧠 AI 검수 의견", width="stretch"):
            txt = "\n\n".join(f"{r['no']}번({r['mtype']}) 키워드:{r['keyword']} 장비:{r['equipment']}\n제목:{r['title']}\n본문:{r['body']}\n"
                              f"댓글:{r['c1']} / {r['r1']} / {r['c2']} / {r['r2']} / {r['c3'] or ''} / {r['r3'] or ''}"
                              for r in rows if r["title"] or r["body"])
            with st.spinner("wongo-gumsu 스킬로 검토 중…"):
                st.session_state[f"aireview_{bid}"] = ai.review_branch(txt)
        if st.session_state.get(f"aireview_{bid}"):
            with st.expander("🧠 AI 검수 의견", expanded=True):
                st.markdown(st.session_state[f"aireview_{bid}"])

        if view == "표 보기":
            _table_view(month, bid, branch, rows, role, can_input, can_write, can_confirm, user)
        else:
            _card_view(rows)

    # ── 오른쪽: 선택 원고 ─────────────────────────────────────────────────────
    with right:
        _detail(month, bid, rows, role, can_write, can_confirm, user)


def _table_view(month, bid, branch, rows, role, can_input, can_write, can_confirm, user):
    eq_opts = [""] + branch_equipment_grouped(bid)
    data = []
    for r in rows:
        chk = json.loads(r["check_json"] or "{}")
        nf = len(chk.get("fails", []))
        written = bool(r["title"] or r["body"])
        data.append({
            "no": r["no"], "mtype": r["mtype"], "status": STATUS_ICON.get(r["status"], r["status"]),
            "check": ("❌ " + str(nf)) if nf else ("✅" if written else ""),
            "keyword": r["keyword"] or "", "equipment": r["equipment"] or "", "special": r["special"] or "",
            "no_equip_mention": bool(r["no_equip_mention"]),
            "photo": "🖼️" * len(ms_images(r["id"])),
            **{f: r[f] or "" for f in TEXT_FIELDS},
        })
    df = pd.DataFrame(data)
    input_cols = ["keyword", "equipment", "special", "no_equip_mention"]
    editable = set()
    if can_input:
        editable |= set(input_cols)
    if can_write:
        editable |= set(TEXT_FIELDS)
    disabled = [c for c in df.columns if c not in editable]
    cfg = {k: st.column_config.Column(v) for k, v in COLS.items()}
    cfg["no"] = st.column_config.NumberColumn("번호", width="small")
    cfg["equipment"] = st.column_config.SelectboxColumn("장비", options=eq_opts, width="medium",
                                                        help="이 지점 보유장비만 나옵니다")
    cfg["no_equip_mention"] = st.column_config.CheckboxColumn("장비명 언급 금지")
    cfg["body"] = st.column_config.TextColumn("본문", width="large")
    cfg["title"] = st.column_config.TextColumn("제목", width="medium")
    st.caption("정보성 1–10 · 후기성 11–19 · 슈퍼세트 20 — 엑셀·시트에서 여러 칸을 복사해 표에 그대로 붙여넣을 수 있습니다 "
               "(댓글3·대댓글3은 슈퍼세트만 사용).")
    key = f"ed_{month}_{bid}_{st.session_state.get('ed_ver', 0)}"
    edited = st.data_editor(df, key=key, disabled=disabled, column_config=cfg, hide_index=True,
                            width="stretch", height=735, num_rows="fixed")
    if editable:
        if st.button("💾 저장 (저장하면 자동 검수가 바로 돌아요)", type="primary", width="stretch"):
            recs = edited.to_dict("records")
            for r in recs:
                if r["no"] != 20:
                    r["c3"] = r["r3"] = ""
            save_manuscripts(month, bid, recs, user)
            st.session_state.ed_ver = st.session_state.get("ed_ver", 0) + 1
            st.toast("저장했습니다. 자동 검수 결과가 표시됩니다.")
            st.rerun()
    drafts = [r["id"] for r in rows if r["status"] == "작성 중" and (r["title"] or r["body"])]
    if can_write and drafts:
        if st.button(f"📤 작성 중인 원고 {len(drafts)}건 검수 요청", width="stretch"):
            set_status(drafts, "검수 대기", user)
            st.rerun()

    if can_confirm:
        st.markdown("**묶음 단위 처리**")
        gcols = st.columns(3)
        for gc, (t, rng) in zip(gcols, [("정보성", range(1, 11)), ("후기성", range(11, 20)), ("슈퍼세트", [20])]):
            with gc.container(border=True):
                st.markdown(f"**{t}**")
                ids = [r["id"] for r in rows if r["no"] in rng and r["status"] in ("검수 대기", "피드백", "완료")]
                fb = st.text_input("피드백 내용", key=f"gfb_{bid}_{t}", label_visibility="collapsed", placeholder="피드백 내용")
                b1, b2 = st.columns(2)
                if b1.button("피드백", key=f"gf_{bid}_{t}", width="stretch", disabled=not ids):
                    set_status(ids, "피드백", user, fb)
                    st.rerun()
                if b2.button("완료", key=f"gd_{bid}_{t}", width="stretch", type="primary", disabled=not ids):
                    set_status(ids, "완료", user)
                    st.rerun()


def _conversation_html(r, hl):
    cells = [("c1", "r1"), ("c2", "r2")] + ([("c3", "r3")] if r["mtype"] == "슈퍼세트" else [])
    out = ""
    for c, rp in cells:
        if r.get(c):
            out += f"<div class='cmt'>💬 {highlight(r[c], hl)}</div>"
        if r.get(rp):
            out += f"<div class='rpl'>↳ ✍️ 작성자 {highlight(r[rp], hl)}</div>"
    return out


def _card_view(rows):
    for t, rng in [("정보성 1–10", range(1, 11)), ("후기성 11–19", range(11, 20)), ("슈퍼세트 20", [20])]:
        st.markdown(f"##### {t}")
        for r in [x for x in rows if x["no"] in rng]:
            if not (r["title"] or r["body"]):
                st.caption(f"{r['no']}번 — 작성 전")
                continue
            chk = json.loads(r["check_json"] or "{}")
            hl = chk.get("hl", [])
            st.markdown(f"<div class='cafe-post'><div class='small'>{r['no']}번 · {STATUS_ICON.get(r['status'])} · "
                        f"키워드 {r['keyword'] or '-'}</div><h4>{highlight(r['title'], hl)}</h4>"
                        f"<div>{highlight(r['body'], hl)}</div><hr style='margin:10px 0'>{_conversation_html(r, hl)}</div>",
                        unsafe_allow_html=True)
            imgs = ms_images(r["id"])
            if imgs:
                st.image([i["path"] for i in imgs], width=160, caption=[i["filename"] for i in imgs])
            st.write("")


def _detail(month, bid, rows, role, can_write, can_confirm, user):
    st.markdown("#### 선택한 원고")
    opts = [f"{r['no']}번 · {r['mtype']} · {r['status']}" for r in rows]
    sel = st.selectbox("원고", opts, key=f"sel_{bid}", label_visibility="collapsed")
    r = rows[opts.index(sel)]
    chk = json.loads(r["check_json"] or "{}")
    hl = chk.get("hl", [])
    fails = chk.get("fails", [])
    stats = chk.get("stats", {})
    st.markdown(f"**{STATUS_ICON.get(r['status'])}** · 키워드 `{r['keyword'] or '-'}` · 장비 `{r['equipment'] or '-'}`")
    if stats:
        st.caption(" · ".join(f"{k} {v}" for k, v in stats.items()))
    if r["confirmed_by"]:
        st.caption(f"컨펌 {r['confirmed_by']} {r['confirmed_at']}")
    if r["feedback"] and r["status"] == "피드백":
        st.warning(f"피드백: {r['feedback']}")

    if fails:
        with st.container(border=True):
            st.markdown(f"**검수 위반 {len(fails)}건**")
            for f in fails:
                st.markdown(f"- `{f['code']}` **{f['label']}** — {f['detail']}")
    elif r["title"] or r["body"]:
        st.success("검수 통과")

    if r["title"] or r["body"]:
        st.markdown(f"<div class='cafe-post'><h4>{highlight(r['title'], hl)}</h4>{highlight(r['body'], hl)}"
                    f"<hr style='margin:10px 0'>{_conversation_html(r, hl)}</div>", unsafe_allow_html=True)

    if can_write:
        with st.expander("✏️ 이 원고 크게 고치기"):
            t = st.text_input("제목", r["title"] or "", key=f"dt_{r['id']}")
            b = st.text_area("본문", r["body"] or "", height=200, key=f"db_{r['id']}")
            cm = {}
            pairs = ["c1", "r1", "c2", "r2"] + (["c3", "r3"] if r["mtype"] == "슈퍼세트" else [])
            for f in pairs:
                cm[f] = st.text_input(COLS[f], r[f] or "", key=f"d{f}_{r['id']}")
            if st.button("저장", key=f"dsave_{r['id']}", type="primary"):
                rec = {**r, "title": t, "body": b, **cm}
                save_manuscripts(month, bid, [rec], user)
                st.session_state.ed_ver = st.session_state.get("ed_ver", 0) + 1
                st.rerun()

    # 이미지
    slots = int(get_setting("image_slots"))
    imgs = {i["slot"]: i for i in ms_images(r["id"])}
    st.markdown("**🖼️ 이미지**")
    if imgs:
        st.image([i["path"] for i in imgs.values()], width=130, caption=[i["filename"] for i in imgs.values()])
    if role == ADMIN:
        free = q("SELECT * FROM images WHERE status='보관' AND deleted=0 ORDER BY procedure, filename")
        with st.expander("이미지 배치"):
            for s in range(1, slots + 1):
                cur = imgs.get(s)
                opts2 = ["(비움)"] + [f"{i['id']}|{i['filename']}" for i in free]
                label = f"칸 {s}" + (f" — 현재 {cur['filename']}" if cur else "")
                pick = st.selectbox(label, opts2, key=f"img_{r['id']}_{s}")
                if pick != "(비움)":
                    iid = int(pick.split("|")[0])
                    st.image(next(i["path"] for i in free if i["id"] == iid), width=220)
                    if st.button(f"칸 {s}에 배치", key=f"imgset_{r['id']}_{s}"):
                        place_image(iid, r["id"], s, user)
                        st.rerun()

    if can_confirm and (r["title"] or r["body"]):
        fb = st.text_area("피드백 메모", r["feedback"] or "", key=f"fb_{r['id']}", height=80)
        c1, c2 = st.columns(2)
        if c1.button("🟡 피드백", key=f"f_{r['id']}", width="stretch"):
            set_status([r["id"]], "피드백", user, fb)
            st.rerun()
        if c2.button("🟢 완료", key=f"d_{r['id']}", width="stretch", type="primary"):
            set_status([r["id"]], "완료", user)
            st.rerun()
    with st.expander("수정 이력"):
        h = q("SELECT at 시각, user 누가, action 무엇, detail 내용 FROM ms_history WHERE ms_id=? ORDER BY id DESC LIMIT 50", (r["id"],))
        st.dataframe(pd.DataFrame(h), hide_index=True, width="stretch") if h else st.caption("이력 없음")


def _ai_draft(month, branch, bm, rows, user):
    if not ai.available():
        st.error("Claude API 키가 없습니다. README의 'AI 연결'대로 ANTHROPIC_API_KEY를 넣어 주세요.")
        return
    todo = [r for r in rows if not (r["title"] or r["body"])]
    if not todo:
        st.info("빈 원고가 없습니다.")
        return
    from core.checks import split_list
    others = q("SELECT region_tokens FROM branches WHERE id<>? AND hospital=?", (branch["id"], branch["hospital"]))
    materials = {
        "branch": branch["name"], "hospital": branch["hospital"],
        "region_tokens": split_list(branch["region_tokens"]),
        "foreign_regions": sorted({t for o in others for t in split_list(o["region_tokens"])}),
        "allowed_equipment": branch_equipment_grouped(branch["id"]),
        "발행 요청사항": bm["req_notes"], "경쟁사 대비 장점": bm["competitor"],
        "넣었으면 하는 내용": bm["must_include"], "특이사항": bm["special"],
        "지점 금지 주제": branch["banned_topics"], "원장님 가이드라인": branch["guideline"],
        "rows": [{"n": r["no"], "type": r["mtype"], "keyword": r["keyword"] or None, "equipment": r["equipment"],
                  "특이사항": r["special"], "장비명 언급 금지": bool(r["no_equip_mention"])} for r in todo],
    }
    with st.spinner(f"{len(todo)}건 초안 작성 중… (1–3분)"):
        try:
            out = ai.draft_branch(materials)
        except Exception as e:
            st.error(f"AI 호출 실패: {e}")
            return
    by = {int(x["n"]): x for x in out if "n" in x}
    for r in todo:
        x = by.get(r["no"])
        if not x:
            continue
        cm = (x.get("comments") or []) + [""] * 6
        ex("""UPDATE manuscripts SET title=?, body=?, c1=?, r1=?, c2=?, r2=?, c3=?, r3=?, status='작성 중',
              updated_at=?, updated_by=? WHERE id=?""",
           (x.get("title", ""), x.get("body", ""), cm[0], cm[1], cm[2], cm[3],
            cm[4] if r["no"] == 20 else "", cm[5] if r["no"] == 20 else "", now(), "AI 초안", r["id"]))
        ex("INSERT INTO ms_history(ms_id,at,user,action,detail) VALUES(?,?,?,?,?)",
           (r["id"], now(), user["name"], "AI 초안", ""))
    check_branch(month, branch["id"])
    st.session_state.ed_ver = st.session_state.get("ed_ver", 0) + 1
    st.success(f"{len(by)}건 초안을 넣었습니다. 다듬은 뒤 저장하면 '검수 대기'가 됩니다.")
    st.rerun()
'''

# ============================================================================
# views.boardtask
# ============================================================================
MODULES['views.boardtask'] = r'''"""게시판 담당: 배정된 업로드 건만 보고 '업로드 완료' 처리"""
import pandas as pd
import streamlit as st

from core.common import ADMIN, audit, notify_role
from core.db import ex, now, q


def render(ctx):
    user, role, month = ctx["user"], ctx["role"], ctx["month"]
    st.title("📌 게시판 업로드")
    where = "" if role == ADMIN else "AND (t.assignee_id IS NULL OR t.assignee_id=?)"
    params = (month,) if role == ADMIN else (month, user["id"])
    rows = q(f"""SELECT t.*, b.name bname, c.name cname, c.url curl FROM board_tasks t
                 LEFT JOIN branches b ON b.id=t.branch_id LEFT JOIN cafes c ON c.id=t.cafe_id
                 WHERE t.month=? {where} ORDER BY t.status DESC, t.due""", params)
    todo = [r for r in rows if r["status"] == "요청"]
    st.metric("처리할 업로드", len(todo))
    for r in todo:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{r['due']}** · {r['bname']} · [{r['cname']}]({r['curl']}) · 게시판 **{r['board']}**  \n{r['note'] or ''}")
            if c2.button("업로드 완료", key=f"bt_{r['id']}", type="primary"):
                ex("UPDATE board_tasks SET status='완료', done_by=?, done_at=? WHERE id=?", (user["name"], now(), r["id"]))
                audit(user["name"], "게시판 업로드 완료", f"{r['bname']} {r['cname']} {r['board']}")
                notify_role(ADMIN, "완료", f"[{r['bname']}] 게시판 업로드가 완료되었습니다.")
                st.rerun()
    done = [r for r in rows if r["status"] == "완료"]
    if done:
        st.markdown("##### 완료")
        st.dataframe(pd.DataFrame([{"일정": r["due"], "지점": r["bname"], "카페": r["cname"], "게시판": r["board"],
                                    "처리": r["done_by"], "처리일": r["done_at"]} for r in done]),
                     hide_index=True, width="stretch")
'''

# ============================================================================
# views.branch
# ============================================================================
MODULES['views.branch'] = r'''"""지점 및 보유장비 — 첫 화면은 지점명 버튼만, 누르면 장비 화면. 장비 수정은 관리자만."""
from datetime import date

import pandas as pd
import streamlit as st

from core.common import (ADMIN, HOSPITALS, REGIONS, audit, get_setting, norm_name, notify, to_date)
from core.db import ex, now, q, q1, qv


def _notify_equipment_change(month, bid, msg):
    bm = q1("SELECT manager_id FROM branch_month WHERE month=? AND branch_id=?", (month, bid))
    notify(bm and bm["manager_id"], "장비 변경", msg)


def render(ctx):
    user, role, month = ctx["user"], ctx["role"], ctx["month"]
    if st.session_state.get("eq_branch"):
        return _detail(ctx, st.session_state.eq_branch)
    st.title("🏢 지점·보유장비")
    if role == ADMIN:
        tabs = st.tabs(["🏥 지점 목록", "➕ 여러 지점에 장비 추가", "📖 표준 장비명 사전", "🆕 지점 추가"])
    else:
        tabs = [st.container()]
    with tabs[0]:
        hosp = st.radio("병원", HOSPITALS, horizontal=True, key="br_h")
        s = st.text_input("🔍 지점명 검색 (두세 글자만 입력해도 바로 걸러져요)", key="br_s")
        bs = q("SELECT id,name FROM branches WHERE active=1 AND hospital=? ORDER BY name", (hosp,))
        if s:
            bs = [b for b in bs if norm_name(s) in norm_name(b["name"])]
        cols = st.columns(4)
        for i, b in enumerate(bs):
            if cols[i % 4].button(b["name"], key=f"brb_{b['id']}", width="stretch"):
                st.session_state.eq_branch = b["id"]
                st.rerun()
        if not bs:
            st.caption("해당하는 지점이 없습니다.")
    if role != ADMIN:
        return

    with tabs[1]:
        st.caption("전체 공지로 여러 지점에 같은 장비가 들어올 때 한 번에 추가합니다. 장비 이름은 표준 장비명에서만 고릅니다.")
        stds = {s["name"]: s["id"] for s in q("SELECT id,name FROM equip_std ORDER BY category,name")}
        allb = {b["name"]: b["id"] for b in q("SELECT id,name FROM branches WHERE active=1 ORDER BY name")}
        with st.form("multi_eq"):
            e = st.selectbox("장비 (표준명)", list(stds))
            targets = st.multiselect("지점", list(allb))
            c = st.columns(3)
            qty = c[0].number_input("수량", 1, 99, 1)
            indate = c[1].date_input("입고일", value=date.today())
            note = c[2].text_input("비고", placeholder="예: 울쎄라피 프라임으로 교체")
            if st.form_submit_button("추가", type="primary") and targets:
                for t in targets:
                    ex("""INSERT INTO branch_equipment(branch_id,std_id,qty,in_date,note,updated_at,updated_by)
                          VALUES(?,?,?,?,?,?,?)""", (allb[t], stds[e], qty, indate.isoformat(), note, now(), user["name"]))
                    _notify_equipment_change(month, allb[t], f"[{t}] 보유장비에 '{e}'가 추가되었습니다.")
                audit(user["name"], "장비 일괄 추가", f"{e} → {', '.join(targets)}")
                st.success(f"{len(targets)}개 지점에 추가했습니다.")

    with tabs[2]:
        st.caption("같은 장비가 다른 이름으로 들어가지 않게 표준명을 관리합니다. '금지 명칭'을 넣으면 자동 검수에서 걸리고 '대체어'를 안내합니다. "
                   "(예: 영국산 보톡스 — 금지 명칭 '디스포트')")
        cats = get_setting("equip_categories")
        df = pd.DataFrame(q("SELECT id,name,category,aliases,banned_names,replacement FROM equip_std ORDER BY category,name"))
        if df.empty:
            df = pd.DataFrame(columns=["id", "name", "category", "aliases", "banned_names", "replacement"])
        ed = st.data_editor(df, num_rows="dynamic", hide_index=True, width="stretch", key="std_ed",
                            disabled=["id"], column_config={
                                "id": None, "name": "표준 장비명",
                                "category": st.column_config.SelectboxColumn("분류", options=cats),
                                "aliases": "다른 표기(쉼표)", "banned_names": "금지 명칭(쉼표)", "replacement": "대체어"})
        if st.button("사전 저장"):
            for r in ed.to_dict("records"):
                if not str(r.get("name") or "").strip():
                    continue
                if r.get("id") and not pd.isna(r["id"]):
                    ex("UPDATE equip_std SET name=?,category=?,aliases=?,banned_names=?,replacement=? WHERE id=?",
                       (r["name"], r["category"], r["aliases"], r["banned_names"], r["replacement"], int(r["id"])))
                else:
                    if q1("SELECT id FROM equip_std WHERE name=?", (r["name"].strip(),)):
                        st.error(f"'{r['name']}' 은 이미 있습니다.")
                        continue
                    ex("INSERT INTO equip_std(name,category,aliases,banned_names,replacement) VALUES(?,?,?,?,?)",
                       (r["name"].strip(), r["category"], r["aliases"], r["banned_names"], r["replacement"]))
            audit(user["name"], "표준 장비명 사전 저장", "")
            st.rerun()

    with tabs[3]:
        with st.form("new_branch"):
            c = st.columns(3)
            name = c[0].text_input("지점명 (예: 경기광주점)")
            hosp = c[1].selectbox("병원", HOSPITALS)
            reg = c[2].selectbox("지역", REGIONS)
            loc = st.text_input("위치")
            tok = st.text_input("원고 지역 표기 (쉼표, 시트 H3)")
            if st.form_submit_button("지점 추가") and name.strip():
                if q1("SELECT id FROM branches WHERE name=?", (name.strip(),)):
                    st.error("이미 있는 지점명입니다.")
                else:
                    bid = ex("INSERT INTO branches(name,hospital,region,location,region_tokens,created_at) VALUES(?,?,?,?,?,?)",
                             (name.strip(), hosp, reg, loc, tok, now()))
                    from core.ops import ensure_month_frame
                    ex("INSERT OR IGNORE INTO branch_month(month,branch_id) VALUES(?,?)", (month, bid))
                    ensure_month_frame(month, bid)
                    audit(user["name"], "지점 추가", name)
                    st.success("추가했습니다. 이번 달 20건 틀도 만들었습니다.")


def _detail(ctx, bid):
    user, role, month = ctx["user"], ctx["role"], ctx["month"]
    b = q1("SELECT * FROM branches WHERE id=?", (bid,))
    if st.button("⬅️ 목록으로"):
        st.session_state.eq_branch = None
        st.rerun()
    st.title(f"🏥 {b['name']}")
    st.caption(f"{b['hospital']} · {b['region'] or ''} · {b['location'] or ''}")
    cats = get_setting("equip_categories")
    rows = q("""SELECT be.id, s.category 분류, s.name 장비명, be.qty 수량, be.in_date 입고일, be.note 비고
                FROM branch_equipment be JOIN equip_std s ON s.id=be.std_id WHERE be.branch_id=? AND be.active=1""", (bid,))
    rows.sort(key=lambda r: (cats.index(r["분류"]) if r["분류"] in cats else 99, r["장비명"]))
    if role != ADMIN:
        for cat in cats + ["(기타)"]:
            rr = [r for r in rows if (r["분류"] if r["분류"] in cats else "(기타)") == cat]
            if rr:
                st.markdown(f"#### {cat}")
                st.dataframe(pd.DataFrame(rr).drop(columns=["id", "분류"]), hide_index=True, width="stretch")
        if not rows:
            st.info("등록된 장비가 없습니다.")
        return

    tabs = st.tabs(["🧰 보유장비", "ℹ️ 지점 정보"])
    with tabs[0]:
        stds = {s["name"]: s["id"] for s in q("SELECT id,name FROM equip_std ORDER BY category,name")}
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["id", "분류", "장비명", "수량", "입고일", "비고"])
        df["입고일"] = df["입고일"].map(to_date)
        ed = st.data_editor(df, num_rows="dynamic", hide_index=True, width="stretch", key=f"beq_{bid}",
                            disabled=["id", "분류"], column_config={
                                "id": None, "장비명": st.column_config.SelectboxColumn("장비명", options=list(stds), required=True),
                                "입고일": st.column_config.DateColumn("입고일"),
                                "비고": st.column_config.TextColumn("비고", help="예: 디스포트 명칭 언급 x → 영국산 보톡스 (자동 검수에 반영)")})
        if st.button("💾 장비 저장", type="primary"):
            old = {r["id"]: r for r in rows}
            keep = set()
            changed = []
            for r in ed.to_dict("records"):
                if not r.get("장비명"):
                    continue
                d = r["입고일"].isoformat() if hasattr(r["입고일"], "isoformat") and not pd.isna(r["입고일"]) else None
                rid = r.get("id")
                if rid and not pd.isna(rid) and int(rid) in old:
                    rid = int(rid)
                    keep.add(rid)
                    o = old[rid]
                    if (o["장비명"], o["수량"], o["입고일"], o["비고"] or "") != (r["장비명"], r["수량"], d, r["비고"] or ""):
                        ex("UPDATE branch_equipment SET std_id=?, qty=?, in_date=?, note=?, updated_at=?, updated_by=? WHERE id=?",
                           (stds[r["장비명"]], int(r["수량"] or 1), d, r["비고"], now(), user["name"], rid))
                        changed.append(f"{o['장비명']} → {r['장비명']}" if o["장비명"] != r["장비명"] else f"{r['장비명']} 수정")
                else:
                    ex("""INSERT INTO branch_equipment(branch_id,std_id,qty,in_date,note,updated_at,updated_by)
                          VALUES(?,?,?,?,?,?,?)""", (bid, stds[r["장비명"]], int(r["수량"] or 1) if not pd.isna(r["수량"]) else 1,
                                                    d, r["비고"], now(), user["name"]))
                    changed.append(f"{r['장비명']} 추가")
            for rid, o in old.items():
                if rid not in keep:
                    ex("UPDATE branch_equipment SET active=0, updated_at=?, updated_by=? WHERE id=?", (now(), user["name"], rid))
                    changed.append(f"{o['장비명']} 삭제")
            if changed:
                used = q("SELECT DISTINCT equipment FROM manuscripts WHERE month=? AND branch_id=? AND equipment<>''", (month, bid))
                touched = [u["equipment"] for u in used if any(u["equipment"] in c for c in changed)]
                msg = f"[{b['name']}] 보유장비 변경: {', '.join(changed)}"
                if touched:
                    msg += f" — 이번 달 원고에 이미 들어간 장비: {', '.join(touched)}"
                    st.warning("이번 달 원고에 이미 들어간 장비가 바뀌었습니다: " + ", ".join(touched))
                _notify_equipment_change(month, bid, msg)
                audit(user["name"], "보유장비 변경", msg)
            st.success("저장했습니다. 원고 드롭다운과 자동 검수에 바로 반영됩니다.")
            st.rerun()

    with tabs[1]:
        with st.form(f"binfo_{bid}"):
            c = st.columns(3)
            name = c[0].text_input("지점명", b["name"])
            hosp = c[1].selectbox("병원", HOSPITALS, index=HOSPITALS.index(b["hospital"]))
            reg = c[2].selectbox("지역", REGIONS, index=REGIONS.index(b["region"]) if b["region"] in REGIONS else 0)
            loc = st.text_input("위치", b["location"] or "")
            tok = st.text_input("원고 지역 표기 (쉼표) — 자동 검수 지역 규칙에 사용", b["region_tokens"] or "")
            c2 = st.columns(2)
            rl = c2[0].text_input("보고서 링크", b["report_link"] or "")
            pl = c2[1].text_input("사진 링크", b["photo_link"] or "")
            ban = st.text_input("금지 주제 (쉼표) — 자동 검수에서 걸림", b["banned_topics"] or "")
            gl = st.text_area("원장님 가이드라인 (로컬 지점)", b["guideline"] or "")
            aliases = ", ".join(r["alias"] for r in q("SELECT alias FROM branch_aliases WHERE branch_id=?", (bid,)))
            al = st.text_input("배정 시트 지점명 대응 (쉼표) 예: 유앤아이 대전(1)·대전(2)", aliases)
            active = st.checkbox("사용 중", value=bool(b["active"]))
            if st.form_submit_button("저장", type="primary"):
                ex("""UPDATE branches SET name=?,hospital=?,region=?,location=?,region_tokens=?,report_link=?,photo_link=?,
                      banned_topics=?,guideline=?,active=? WHERE id=?""",
                   (name, hosp, reg, loc, tok, rl, pl, ban, gl, int(active), bid))
                ex("DELETE FROM branch_aliases WHERE branch_id=?", (bid,))
                for a in [x.strip() for x in al.split(",") if x.strip()]:
                    ex("INSERT OR REPLACE INTO branch_aliases(alias,branch_id) VALUES(?,?)", (norm_name(a), bid))
                audit(user["name"], "지점 정보 수정", name)
                st.success("저장했습니다.")
'''

# ============================================================================
# views.cafe
# ============================================================================
MODULES['views.cafe'] = r'''"""카페 목록 (관리자·실행사): 카페 표 + 지점-카페 연결 표"""
import pandas as pd
import streamlit as st

from core.common import CAFE_STATUS, CAFE_TYPES, REGIONS, audit, cafe_base, get_setting
from core.db import ex, now, q, q1, qv


def _log(cafe_id, user, old, new, reason):
    ex("INSERT INTO cafe_log(cafe_id,at,user,old,new,reason) VALUES(?,?,?,?,?,?)", (cafe_id, now(), user, old, new, reason))


def render(ctx):
    user, month = ctx["user"], ctx["month"]
    st.title("☕ 카페 목록")
    tabs = st.tabs(["📋 카페 표", "🔗 지점-카페 연결", "➕ 카페 추가", "🗄️ 보관함 (진행 불가)", "📈 사용 현황", "🧾 상태 변경 이력"])

    with tabs[0]:
        c = st.columns(3)
        ft = c[0].multiselect("유형", CAFE_TYPES, key="cf_t")
        fs = c[1].multiselect("상태", CAFE_STATUS, key="cf_s")
        s = c[2].text_input("검색", key="cf_q")
        rows = q("SELECT * FROM cafes WHERE archived=0 ORDER BY ctype, name")
        rows = [r for r in rows if (not ft or r["ctype"] in ft) and (not fs or r["status"] in fs)
                and (not s or s in (r["name"] or "") + (r["alt_names"] or "") + (r["url"] or ""))]
        df = pd.DataFrame([{"id": r["id"], "카페명": r["name"], "다른 표기": r["alt_names"], "URL": r["url"], "회원수": r["members"],
                            "유형": r["ctype"], "규모": r["size"], "지역": r["region"], "상태": r["status"],
                            "대형카페": bool(r["flag_large"]), "스마트브랜딩 추가": bool(r["flag_smart"]),
                            "댓글침투용": bool(r["comment_use"]), "단가": r["price"], "비고": r["note"]} for r in rows])
        if df.empty:
            st.info("카페가 없습니다.")
        else:
            ed = st.data_editor(df, hide_index=True, width="stretch", key="cafe_ed", disabled=["id", "URL"],
                                column_config={"id": None, "URL": st.column_config.LinkColumn("URL"),
                                               "유형": st.column_config.SelectboxColumn("유형", options=CAFE_TYPES),
                                               "규모": st.column_config.SelectboxColumn("규모", options=["", "대형", "소형"]),
                                               "지역": st.column_config.SelectboxColumn("지역", options=[""] + REGIONS),
                                               "상태": st.column_config.SelectboxColumn("상태", options=CAFE_STATUS)})
            reason = st.text_input("상태를 바꿨다면 사유", key="cf_reason")
            if st.button("💾 카페 표 저장", type="primary"):
                old = {r["id"]: r for r in rows}
                for r in ed.to_dict("records"):
                    o = old[r["id"]]
                    if o["status"] != r["상태"]:
                        _log(r["id"], user["name"], o["status"], r["상태"], reason)
                    ex("""UPDATE cafes SET name=?, alt_names=?, members=?, ctype=?, size=?, region=?, status=?, flag_large=?,
                          flag_smart=?, comment_use=?, price=?, note=? WHERE id=?""",
                       (r["카페명"], r["다른 표기"], None if pd.isna(r["회원수"]) else int(r["회원수"]), r["유형"], r["규모"], r["지역"],
                        r["상태"], int(r["대형카페"]), int(r["스마트브랜딩 추가"]), int(r["댓글침투용"]),
                        0 if pd.isna(r["단가"]) else int(r["단가"]), r["비고"], r["id"]))
                audit(user["name"], "카페 표 저장", "")
                st.rerun()

    with tabs[1]:
        st.caption("지점 연결 = 연결된 지점만 / 지역 연결 = 그 지역 모든 지점(새 지점도 자동 포함). 지역맘 카페에 씁니다.")
        cafes = {c_["name"]: c_["id"] for c_ in q("SELECT id,name FROM cafes WHERE archived=0 ORDER BY name")}
        if cafes:
            cn = st.selectbox("카페", list(cafes), key="lk_c")
            cid = cafes[cn]
            links = q("""SELECT l.*, b.name bname FROM cafe_links l LEFT JOIN branches b ON b.id=l.branch_id WHERE l.cafe_id=?""", (cid,))
            for l in links:
                c1, c2 = st.columns([5, 1])
                c1.write(f"{l['link_type']} 연결 → {l['bname'] if l['link_type'] == '지점' else l['region'] + ' 전체'}")
                if c2.button("삭제", key=f"lkdel_{l['id']}"):
                    ex("DELETE FROM cafe_links WHERE id=?", (l["id"],))
                    st.rerun()
            c1, c2 = st.columns(2)
            with c1.form("lk_b"):
                bs = {b["name"]: b["id"] for b in q("SELECT id,name FROM branches WHERE active=1 ORDER BY name")}
                sel = st.multiselect("지점 연결 추가", list(bs))
                if st.form_submit_button("추가"):
                    for s_ in sel:
                        ex("INSERT INTO cafe_links(cafe_id,link_type,branch_id) VALUES(?,?,?)", (cid, "지점", bs[s_]))
                    st.rerun()
            with c2.form("lk_r"):
                reg = st.selectbox("지역 연결 추가", REGIONS)
                if st.form_submit_button("추가"):
                    ex("INSERT INTO cafe_links(cafe_id,link_type,region) VALUES(?,?,?)", (cid, "지역", reg))
                    st.rerun()
        all_links = q("""SELECT c.name 카페, l.link_type 방식, COALESCE(b.name, l.region || ' 전체') 대상
                         FROM cafe_links l JOIN cafes c ON c.id=l.cafe_id LEFT JOIN branches b ON b.id=l.branch_id ORDER BY c.name""")
        st.dataframe(pd.DataFrame(all_links), hide_index=True, width="stretch")

    with tabs[2]:
        st.caption("URL 중복을 자동으로 확인합니다. '준비 중'으로 시작해 실행사 쪽 준비가 끝나면 '진행 가능'으로 바꿉니다.")
        with st.form("cafe_new"):
            url = st.text_input("카페 URL")
            c = st.columns(4)
            name = c[0].text_input("카페명")
            t = c[1].selectbox("유형", CAFE_TYPES)
            size = c[2].selectbox("규모 (2030뷰티·맘)", ["", "대형", "소형"])
            reg = c[3].selectbox("지역 (지역맘)", [""] + REGIONS)
            price = st.number_input("단가", 0, 1_000_000, 0, step=1000)
            bs = {b["name"]: b["id"] for b in q("SELECT id,name FROM branches WHERE active=1 ORDER BY name")}
            links = st.multiselect("연결 지점", list(bs))
            region_link = st.checkbox("지역 전체로 연결 (위 지역)")
            cm = st.checkbox("댓글침투용")
            if st.form_submit_button("추가", type="primary"):
                base, _ = cafe_base(url)
                if not base:
                    st.error("네이버 카페 URL을 넣어 주세요.")
                else:
                    ex_ = q1("SELECT * FROM cafes WHERE base_id=? OR url=?", (base, url.strip()))
                    if ex_ and ex_["archived"]:
                        st.error(f"⚠️ 진행 불가로 보관된 카페입니다 ({ex_['archive_reason']}, {ex_['archived_at']}). 보관함에서 복구하세요.")
                    elif ex_:
                        st.error(f"이미 등록된 카페입니다: {ex_['name']}")
                    else:
                        cid = ex("""INSERT INTO cafes(name,url,base_id,ctype,size,region,status,price,comment_use,created_at)
                                    VALUES(?,?,?,?,?,?,?,?,?,?)""", (name or base, f"https://cafe.naver.com/{base}", base, t, size,
                                                                   reg, "준비 중", price, int(cm), now()))
                        for l in links:
                            ex("INSERT INTO cafe_links(cafe_id,link_type,branch_id) VALUES(?,?,?)", (cid, "지점", bs[l]))
                        if region_link and reg:
                            ex("INSERT INTO cafe_links(cafe_id,link_type,region) VALUES(?,?,?)", (cid, "지역", reg))
                        _log(cid, user["name"], "", "준비 중", "신규 등록")
                        st.success("추가했습니다 (준비 중).")

    with tabs[3]:
        cafes = {c_["name"]: c_["id"] for c_ in q("SELECT id,name FROM cafes WHERE archived=0 ORDER BY name")}
        c1, c2, c3 = st.columns([2, 3, 1])
        cn = c1.selectbox("진행 불가 처리할 카페", ["(선택)"] + list(cafes), key="ar_c")
        why = c2.text_input("사유", key="ar_w")
        if c3.button("보관함으로") and cn != "(선택)":
            ex("UPDATE cafes SET archived=1, archive_reason=?, archived_at=? WHERE id=?", (why, now(), cafes[cn]))
            _log(cafes[cn], user["name"], "", "진행 불가", why)
            st.rerun()
        arch = q("SELECT * FROM cafes WHERE archived=1 ORDER BY archived_at DESC")
        for a in arch:
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"**{a['name']}** · {a['url']} · {a['archive_reason'] or ''} · {a['archived_at']}")
            if c2.button("복구", key=f"rest_{a['id']}"):
                ex("UPDATE cafes SET archived=0 WHERE id=?", (a["id"],))
                _log(a["id"], user["name"], "진행 불가", a["status"], "복구")
                st.rerun()

    with tabs[4]:
        hp = int(get_setting("high_price"))
        rows = q("""SELECT c.name 카페, c.ctype 유형, c.price 단가, COUNT(p.id) "사용 횟수", MAX(p.pub_date) "최근 사용일",
                           COUNT(DISTINCT p.branch_id) "사용 지점 수"
                    FROM cafes c LEFT JOIN publications p ON p.cafe_id=c.id AND p.url<>'' WHERE c.archived=0
                    GROUP BY c.id ORDER BY "사용 횟수" DESC""")
        d = pd.DataFrame(rows)
        if not d.empty:
            d["고단가"] = d["단가"].fillna(0) >= hp
            d["비용"] = d["단가"].fillna(0) * d["사용 횟수"]
            hi = d[d["고단가"]]
            st.metric("고단가 카페 사용", f"{int(hi['사용 횟수'].sum())}건 · {int(hi['비용'].sum()):,}원")
            st.dataframe(d, hide_index=True, width="stretch")
        st.markdown("##### 지점별 사용")
        st.dataframe(pd.DataFrame(q("""SELECT b.name 지점, c.name 카페, COUNT(*) 횟수, MAX(p.pub_date) 최근
                                       FROM publications p JOIN cafes c ON c.id=p.cafe_id JOIN branches b ON b.id=p.branch_id
                                       WHERE p.url<>'' GROUP BY b.id, c.id ORDER BY b.name""")), hide_index=True, width="stretch")

    with tabs[5]:
        st.dataframe(pd.DataFrame(q("""SELECT l.at 언제, l.user 누가, c.name 카페, l.old 이전, l.new 이후, l.reason 사유
                                       FROM cafe_log l JOIN cafes c ON c.id=l.cafe_id ORDER BY l.id DESC LIMIT 300""")),
                     hide_index=True, width="stretch")
'''

# ============================================================================
# views.comments
# ============================================================================
MODULES['views.comments'] = r'''"""댓글 침투: 대상 글 모으기(자동 수집 결과 올리기 / 직접 추가) → 지점별 선정 → 실행사 작업 입력 → 보고서"""
from datetime import date

import pandas as pd
import streamlit as st

from core.common import audit, cafe_base
from core.db import ex, now, q, q1, qv
from core.ops import account_comment_check, usable_accounts


def render(ctx):
    user, role, month = ctx["user"], ctx["role"], ctx["month"]
    st.title("💬 댓글 침투")
    tabs = st.tabs(["📌 대상 글 · 작업", "➕ 직접 추가", "📥 자동 수집 결과 올리기", "☕ 댓글침투용 카페"])
    bs = {b["name"]: b["id"] for b in q("SELECT id,name FROM branches WHERE active=1 ORDER BY name")}

    with tabs[0]:
        c1, c2 = st.columns(2)
        bf = c1.selectbox("지점", ["전체"] + list(bs), key="cm_b")
        only = c2.radio("보기", ["댓글 가능 · 대기", "완료", "전체"], horizontal=True, key="cm_view")
        sql = """SELECT t.*, b.name bname, a.acc_id FROM comment_targets t LEFT JOIN branches b ON b.id=t.branch_id
                 LEFT JOIN accounts a ON a.id=t.account_id WHERE t.month=?"""
        p = [month]
        if bf != "전체":
            sql += " AND t.branch_id=?"
            p.append(bs[bf])
        if only == "댓글 가능 · 대기":
            sql += " AND t.status='대기' AND t.commentable='가능'"
        elif only == "완료":
            sql += " AND t.status='완료'"
        rows = q(sql + " ORDER BY b.name, t.collected_at DESC", p)
        st.caption(f"{len(rows)}건")
        if rows:
            st.dataframe(pd.DataFrame([{"지점": r["bname"], "키워드": r["keyword"], "카페": r["cafe_name"], "제목": r["title"],
                                        "URL": r["url"], "댓글 가능": r["commentable"], "수집": r["source"],
                                        "상태": r["status"], "계정": r["acc_id"], "작성일": r["done_date"]} for r in rows]),
                         hide_index=True, width="stretch", column_config={"URL": st.column_config.LinkColumn()})
        todo = [r for r in rows if r["status"] == "대기"]
        if todo:
            st.markdown("##### 댓글 발행 입력")
            sel = st.selectbox("대상 글", todo, format_func=lambda r: f"{r['bname']} · {r['cafe_name']} · {r['title']}", key="cm_sel")
            accs = usable_accounts("댓글 침투")
            opts = {}
            for a in accs:
                ok, msg, _ = account_comment_check(a["id"], month)
                opts[f"{'✅' if ok else '⛔'} {a['acc_id']} — {msg}"] = (a, ok)
            if not opts:
                st.warning("댓글 침투용 계정이 없습니다.")
            else:
                ak = st.selectbox("카페 아이디", list(opts), key="cm_acc")
                acc, ok = opts[ak]
                d = st.date_input("작성 날짜", value=date.today(), key="cm_date")
                txt = st.text_area("댓글 내용", key="cm_txt")
                if st.button("✅ 완료 처리", type="primary", disabled=not ok):
                    ex("UPDATE comment_targets SET status='완료', account_id=?, done_date=?, comment_text=? WHERE id=?",
                       (acc["id"], d.isoformat(), txt, sel["id"]))
                    audit(user["name"], "댓글 침투 완료", sel["url"])
                    st.rerun()

    with tabs[1]:
        st.caption("지점과 키워드를 고르고 URL을 붙여넣으면 카페명·게시글 ID를 URL에서 채웁니다. 이미 등록된 글이면 막습니다.")
        with st.form("cm_add"):
            c = st.columns(2)
            br = c[0].selectbox("지점", list(bs))
            kw = c[1].text_input("키워드")
            url = st.text_input("카페 게시글 URL")
            title = st.text_input("게시글 제목 (선택)")
            if st.form_submit_button("추가"):
                base, art = cafe_base(url)
                if not base:
                    st.error("네이버 카페 URL이 아닙니다.")
                elif q1("SELECT id FROM comment_targets WHERE url=?", (url.strip(),)) or \
                        (art and q1("SELECT id FROM comment_targets WHERE cafe_base=? AND article_id=?", (base, art))):
                    st.error("이미 등록된 글입니다.")
                else:
                    cafe = q1("SELECT name FROM cafes WHERE base_id=?", (base,))
                    ex("""INSERT INTO comment_targets(month,branch_id,keyword,source,title,cafe_name,cafe_base,article_id,url,
                          collected_at,created_by) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                       (month, bs[br], kw, "직접 추가", title, cafe["name"] if cafe else base, base, art, url.strip(), now(), user["name"]))
                    st.success(f"등록했습니다 (카페 {cafe['name'] if cafe else base}, 글 {art or '-'})")

    with tabs[2]:
        st.caption("이사님 프로그램 결과(키워드, 구좌종류, 블록순서·제목, 순위, 글 제목, 카페 URL, 댓글 가능 여부, 수집일시)를 "
                   "CSV/엑셀로 올리면 중복을 빼고 들어옵니다. 지점명 칸이 없으면 아래에서 지점을 고릅니다.")
        up = st.file_uploader("수집 결과 파일", type=["csv", "xlsx"], key="cm_up")
        br = st.selectbox("지점 (파일에 지점명 칸이 없을 때)", list(bs), key="cm_up_b")
        if up is not None:
            d = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up)
            st.dataframe(d.head(20), width="stretch")

            def col(*keys):
                return next((c for c in d.columns if any(k in str(c) for k in keys)), None)
            cu, ct, ck, cc, cr, cb, cs, cd, cn = (col("URL", "url", "링크"), col("제목"), col("키워드"), col("댓글"),
                                                  col("순위"), col("블록"), col("구좌"), col("수집"), col("지점"))
            st.caption(f"읽을 칸 → URL:{cu} 제목:{ct} 키워드:{ck} 댓글 가능:{cc} 지점:{cn}")
            if st.button("가져오기 (미리보기 확인 후)", type="primary", disabled=not cu):
                n = dup = 0
                for _, x in d.iterrows():
                    url = str(x[cu]).strip()
                    base, art = cafe_base(url)
                    if not base or q1("SELECT id FROM comment_targets WHERE url=?", (url,)):
                        dup += 1
                        continue
                    bid = bs.get(str(x[cn]).strip()) if cn else bs[br]
                    cafe = q1("SELECT name FROM cafes WHERE base_id=?", (base,))
                    ok = str(x[cc]) if cc else "가능"
                    ex("""INSERT INTO comment_targets(month,branch_id,keyword,source,search_type,block,rank,title,cafe_name,
                          cafe_base,article_id,url,commentable,collected_at,created_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                       (month, bid or bs[br], str(x[ck]) if ck else "", "자동 수집", str(x[cs]) if cs else "",
                        str(x[cb]) if cb else "", int(x[cr]) if cr and str(x[cr]).isdigit() else None,
                        str(x[ct]) if ct else "", cafe["name"] if cafe else base, base, art, url,
                        "가능" if ok in ("가능", "O", "o", "True", "1", "Y") else "불가", str(x[cd]) if cd else now(), user["name"]))
                    n += 1
                st.success(f"{n}건 추가, {dup}건 중복·형식 오류로 제외")

    with tabs[3]:
        st.caption("카페 목록에서 '댓글침투용'으로 표시된 카페입니다 (통합 보고서 '지점명 설정' 탭 대체).")
        st.dataframe(pd.DataFrame(q("""SELECT name 카페, ctype 유형, status 상태, url URL FROM cafes
                                       WHERE comment_use=1 AND archived=0 ORDER BY name""")), hide_index=True, width="stretch")
'''

# ============================================================================
# views.experience
# ============================================================================
MODULES['views.experience'] = r'''"""체험단 (3단계) — 설정에서 켜야 보인다. 지금은 보드 틀만."""
import streamlit as st

STEPS = ["키워드 제안", "블로거 수집", "섭외 연락", "수락", "일정", "포스팅", "검수", "노출 체크", "댓글 대응 확인"]


def render(ctx):
    st.title("🧪 체험단 (3단계 예정)")
    st.info("구성안 6장에 따라 체험단은 3단계에서 만듭니다. 수집은 naver-chehumdan-listup 스킬로 연결할 예정입니다.")
    st.markdown(" → ".join(STEPS))
'''

# ============================================================================
# views.home
# ============================================================================
MODULES['views.home'] = r'''import pandas as pd
import streamlit as st

from core.common import (ADMIN, BOARD, EXEC, HOSPITALS, MANAGER, WRITER, deadline_badge, get_setting,
                         is_overdue, month_label, my_branch_ids, user_name)
from core.db import q, q1, qv
from core.ops import progress, publish_backlog, stage_of


def branch_status(month, hospital="전체", branch_ids=None, hide_people=False):
    rows = q("""SELECT b.id, b.name, b.hospital, bm.manager_id, bm.writer_id, bm.dl_setting, bm.dl_writing,
                       bm.dl_publish, bm.material_done, bm.planned_publish, bm.report_stage
                FROM branches b LEFT JOIN branch_month bm ON bm.branch_id=b.id AND bm.month=?
                WHERE b.active=1 ORDER BY b.name""", (month,))
    out = []
    for r in rows:
        if hospital != "전체" and r["hospital"] != hospital:
            continue
        if branch_ids is not None and r["id"] not in branch_ids:
            continue
        p = progress(month, r["id"])
        as_n = qv("SELECT COUNT(*) FROM publications WHERE month=? AND branch_id=? AND as_state='AS 대기'", (month, r["id"]), 0)
        set_done = bool(r["material_done"]) or p["kw_missing"] == 0
        write_done = p["written"] >= p["total"] > 0
        badges = [b for b in [
            ("세팅 " + deadline_badge(r["dl_setting"], set_done)) if deadline_badge(r["dl_setting"], set_done) else "",
            ("작성 " + deadline_badge(r["dl_writing"], write_done)) if deadline_badge(r["dl_writing"], write_done) else "",
        ] if b]
        row = {"id": r["id"], "지점": r["name"], "병원": r["hospital"],
               "담당자": user_name(r["manager_id"]), "작가": user_name(r["writer_id"]),
               "진행상황": f"{p['done']}/{p['total']}", "정보성": p["by"]["정보성"], "후기성": p["by"]["후기성"],
               "슈퍼세트": p["by"]["슈퍼세트"], "단계": stage_of(month, r["id"]),
               "키워드 미입력": p["kw_missing"], "피드백": p["feedback"], "AS 대기": as_n,
               "마감": " · ".join(badges), "manager_id": r["manager_id"],
               "_done": p["done"], "_total": p["total"],
               "_late": any("지연" in b for b in badges), "_soon": any(("D-" in b) or ("오늘" in b) for b in badges)}
        if hide_people:
            row.pop("담당자"); row.pop("작가")
        out.append(row)
    return out


def _table(rows, key):
    if not rows:
        st.info("해당하는 지점이 없습니다.")
        return
    df = pd.DataFrame(rows)
    show = [c for c in df.columns if not c.startswith("_") and c not in ("id", "manager_id")]
    st.dataframe(df[show], width="stretch", hide_index=True, key=key)


def render(ctx):
    user, role, month = ctx["user"], ctx["role"], ctx["month"]
    st.title("🏠 홈")
    st.caption(f"운영 월 {month_label(month)} · {user['name']} ({role})")

    # ── 내 할 일 ─────────────────────────────────────────────────────────────
    todo = []
    if role == WRITER:
        for bm in q("SELECT * FROM branch_month WHERE month=? AND writer_id=?", (month, user["id"])):
            p = progress(month, bm["branch_id"])
            left = p["total"] - p["written"]
            b = q1("SELECT name FROM branches WHERE id=?", (bm["branch_id"],))["name"]
            if left or p["feedback"]:
                todo.append(f"**{b}** — 작성 남음 {left}건 · 피드백 {p['feedback']}건 {deadline_badge(bm['dl_writing'], left == 0)}"
                            + ("" if bm["material_done"] else " · (원고 재료 입력 전)"))
    if role == MANAGER:
        for bm in q("SELECT * FROM branch_month WHERE month=? AND manager_id=?", (month, user["id"])):
            p = progress(month, bm["branch_id"])
            b = q1("SELECT name FROM branches WHERE id=?", (bm["branch_id"],))["name"]
            if p["kw_missing"] and not bm["material_done"]:
                todo.append(f"**{b}** — 키워드 미입력 {p['kw_missing']}건 {deadline_badge(bm['dl_setting'])}")
            if bm["report_stage"] == "지점 확인":
                todo.append(f"**{b}** — 보고서 확인 요청")
    if role == BOARD:
        n = qv("SELECT COUNT(*) FROM board_tasks WHERE status='요청' AND (assignee_id IS NULL OR assignee_id=?)", (user["id"],), 0)
        if n:
            todo.append(f"게시판 업로드 요청 **{n}건**")
    if role == EXEC:
        today = pd.Timestamp.today().strftime("%Y-%m-%d")
        tb = q("SELECT branch_id FROM branch_month WHERE month=? AND planned_publish<=?", (month, today))
        left = [r for r in tb if qv("SELECT COUNT(*) FROM publications WHERE month=? AND branch_id=? AND url<>''",
                                     (month, r["branch_id"]), 0) < 20]
        if left:
            todo.append(f"오늘 발행할 지점 **{len(left)}곳**")
        n = qv("SELECT COUNT(*) FROM publications WHERE as_state='AS 대기'", default=0)
        if n:
            todo.append(f"AS 대기 **{n}건**")
        n = qv("SELECT COUNT(*) FROM report_issues WHERE status IN ('접수됨','처리 중')", default=0)
        if n:
            todo.append(f"보고서 지점 확인 요청 **{n}건**")
        n = qv("SELECT COUNT(*) FROM comment_targets WHERE month=? AND status='대기' AND commentable='가능'", (month,), 0)
        if n:
            todo.append(f"댓글 침투 대기 **{n}건**")
    unread = q("SELECT * FROM notifications WHERE user_id=? AND read=0 ORDER BY id DESC LIMIT 5", (user["id"],))
    with st.container(border=True):
        st.markdown("**✅ 내 할 일**")
        if not todo and not unread:
            st.write("지금 처리할 일이 없습니다.")
        for t in todo:
            st.markdown(f"- {t}")
        for n in unread:
            st.markdown(f"- 🔔 {n['message']} <span class='small'>{n['created_at'][5:16]}</span>", unsafe_allow_html=True)

    if role in (BOARD,):
        return

    hide_people = role == EXEC   # 실행사 화면에는 담당자 이름을 보이지 않는다
    c1, c2 = st.columns([2, 1])
    hospital = c1.radio("병원", ["전체"] + HOSPITALS, horizontal=True, key="home_hosp")
    view = c2.radio("보기", ["담당자 카드", "지점 전체 보기"], horizontal=True, key="home_view",
                    index=1 if hide_people else 0, disabled=hide_people)
    ids = my_branch_ids(user, month) if ctx["mine"] and role in (MANAGER, WRITER) else None
    rows = branch_status(month, hospital, ids, hide_people)

    # ── 지금 확인할 것 ───────────────────────────────────────────────────────
    st.markdown("#### 🚨 지금 확인할 것")
    groups = {
        "키워드 미입력": [r for r in rows if r["키워드 미입력"] and r["단계"] == "키워드 입력"],
        "피드백 대기": [r for r in rows if r["피드백"]],
        "마감 임박": [r for r in rows if r["_soon"]],
        "지연": [r for r in rows if r["_late"]],
        "AS 대기": [r for r in rows if r["AS 대기"]],
    }
    cols = st.columns(len(groups))
    for c, (k, v) in zip(cols, groups.items()):
        n = sum(x["피드백"] for x in v) if k == "피드백 대기" else (sum(x["AS 대기"] for x in v) if k == "AS 대기" else len(v))
        unit = "건" if k in ("피드백 대기", "AS 대기") else "곳"
        if c.button(f"{k}\n\n**{n}{unit}**", key=f"chk_{k}", width="stretch",
                    type="primary" if st.session_state.get("home_filter") == k else "secondary"):
            st.session_state.home_filter = None if st.session_state.get("home_filter") == k else k
            st.rerun()
    f = st.session_state.get("home_filter")
    if f:
        st.markdown(f"**{f}** 지점")
        _table(groups[f], "tbl_filter")

    if role == ADMIN:
        few = []
        need = int(get_setting("local_mom_min"))
        for b in q("SELECT * FROM branches WHERE active=1 AND hospital<>'로컬'"):
            n = qv("""SELECT COUNT(DISTINCT c.id) FROM cafes c JOIN cafe_links l ON l.cafe_id=c.id
                      WHERE c.ctype='지역맘' AND c.archived=0 AND c.status<>'준비 중'
                      AND ((l.link_type='지점' AND l.branch_id=?) OR (l.link_type='지역' AND l.region=?))""",
                   (b["id"], b["region"]), 0)
            if n < need:
                few.append(f"{b['name']}({n})")
        if few:
            st.warning(f"지역맘 카페 부족 지점 (기준 {need}개): " + ", ".join(few))
        for w in publish_backlog(month):
            st.error("발행 밀림: " + w)

    # ── 처리 건수 ───────────────────────────────────────────────────────────
    ids_all = [r["id"] for r in rows]
    if ids_all:
        cnt = {r["status"]: r["n"] for r in q(
            f"SELECT status, COUNT(*) n FROM manuscripts WHERE month=? AND branch_id IN ({','.join('?' * len(ids_all))}) GROUP BY status",
            [month] + ids_all)}
        pub = qv(f"SELECT COUNT(*) FROM publications WHERE month=? AND url<>'' AND branch_id IN ({','.join('?' * len(ids_all))})",
                 [month] + ids_all, 0)
        mc = st.columns(6)
        for c, k in zip(mc, ["작성 전", "검수 대기", "피드백", "완료", "사용 완료"]):
            c.metric(k, cnt.get(k, 0) + (cnt.get("작성 중", 0) if k == "작성 전" else 0))
        mc[5].metric("발행", pub)

    st.markdown("---")
    if view == "지점 전체 보기" or hide_people:
        st.markdown("#### 📋 전체현황")
        _table(rows, "tbl_all")
        return

    # ── 담당자 카드 ─────────────────────────────────────────────────────────
    st.markdown("#### 👥 담당자별 현황")
    by_mgr = {}
    for r in rows:
        by_mgr.setdefault(r["manager_id"], []).append(r)
    if role == MANAGER:
        st.session_state.home_card = user["id"]
    mgr_ids = sorted(by_mgr, key=lambda m: user_name(m) or "~")
    cols = st.columns(4)
    for i, mid in enumerate(mgr_ids):
        rs = by_mgr[mid]
        done, tot = sum(r["_done"] for r in rs), sum(r["_total"] for r in rs)
        pct = round(done * 100 / tot) if tot else 0
        fb, asn = sum(r["피드백"] for r in rs), sum(r["AS 대기"] for r in rs)
        late = sum(r["_late"] for r in rs)
        soon = sum(r["_soon"] for r in rs)
        icon = "⚫" if late else ("🔴" if fb or asn else ("🟢" if soon else "⚪"))
        state = f"지연 {late}곳" if late else ("확인 필요" if fb or asn else ("마감 임박" if soon else "정상"))
        with cols[i % 4].container(border=True):
            st.markdown(f"{icon} **{user_name(mid) or '(미배정)'}**  \n"
                        f"담당 지점 {len(rs)}곳 · 진행 {done}/{tot} (**{pct}%**)  \n"
                        f"피드백 {fb} · AS 대기 {asn} · {state}")
            st.progress(pct / 100)
            if st.button("지점 목록 펼치기", key=f"card_{mid}", width="stretch"):
                st.session_state.home_card = None if st.session_state.get("home_card") == mid else mid
                st.rerun()
    sel = st.session_state.get("home_card")
    if sel in by_mgr or (sel is None and False):
        st.markdown(f"#### {user_name(sel)} 담당 지점")
        _table(by_mgr[sel], "tbl_card")
'''

# ============================================================================
# views.images
# ============================================================================
MODULES['views.images'] = r'''"""AI 이미지 보관함: 1·2차 검수 끝난 최종본을 시술별로 보관 → 원고에 배치 → 실행사가 원고 단위로 내려받으면 '사용 완료'"""
import os
import shutil

import pandas as pd
import streamlit as st

from core.common import audit, get_setting
from core.db import DATA_DIR, IMG_DIR, ex, now, q, q1
from core.ops import next_image_name, save_image

INBOX = os.path.join(DATA_DIR, "inbox")
os.makedirs(INBOX, exist_ok=True)


def render(ctx):
    user = ctx["user"]
    st.title("🎨 AI 이미지 보관함")
    procs = [r["name"] for r in q("SELECT name FROM equip_std ORDER BY category, name")]
    tabs = st.tabs(["📦 보관함", "⬆️ 올리기", "🔗 배치 현황", "♻️ 사용 완료 · 되돌리기"])

    with tabs[1]:
        st.caption("파일 이름은 '시술명+번호'(울쎄라1, 울쎄라2 …)로 자동으로 붙습니다.")
        c1, c2 = st.columns(2)
        pick = c1.selectbox("시술", procs + ["(직접 입력)"])
        custom = c2.text_input("시술명 직접 입력") if pick == "(직접 입력)" else ""
        proc = (custom or pick).strip()
        files = st.file_uploader("이미지", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
        if files and proc and st.button("보관함에 넣기", type="primary"):
            names = [save_image(f, proc, user) for f in files]
            audit(user["name"], "이미지 등록", ", ".join(names))
            st.success("등록: " + ", ".join(names))
        st.markdown("---")
        st.caption(f"드라이브 폴더 연동 1단계: 이미지 앱이 올리는 폴더를 이 경로에 동기화하면 새 파일을 가져옵니다 → `{INBOX}` "
                   "(하위 폴더 이름 = 시술명)")
        if st.button("📂 폴더의 새 파일 가져오기"):
            n = 0
            for root, _, fs in os.walk(INBOX):
                proc2 = os.path.basename(root) if root != INBOX else "기타"
                for f in fs:
                    src = os.path.join(root, f)
                    ext = os.path.splitext(f)[1].lower()
                    if ext not in (".png", ".jpg", ".jpeg", ".webp"):
                        continue
                    fname = next_image_name(proc2, ext)
                    dst = os.path.join(IMG_DIR, f"inbox_{n}_{os.path.getmtime(src):.0f}{ext}")
                    shutil.move(src, dst)
                    ex("INSERT INTO images(filename,procedure,path,uploaded_at,uploaded_by) VALUES(?,?,?,?,?)",
                       (fname, proc2, dst, now(), "폴더 가져오기"))
                    n += 1
            st.success(f"{n}개 가져옴")

    with tabs[0]:
        rows = q("SELECT * FROM images WHERE status='보관' AND deleted=0 ORDER BY procedure, filename")
        if not rows:
            st.info("보관 중인 이미지가 없습니다.")
        groups = {}
        for r in rows:
            groups.setdefault(r["procedure"], []).append(r)
        for proc, imgs in groups.items():
            st.markdown(f"#### {proc} ({len(imgs)})")
            cols = st.columns(5)
            for i, im in enumerate(imgs):
                with cols[i % 5]:
                    st.image(im["path"], width="stretch")
                    with st.popover(im["filename"], width="stretch"):
                        st.image(im["path"])  # 원본 크기로 크게 보기
                        new = st.text_input("파일 이름", im["filename"], key=f"rn_{im['id']}")
                        if st.button("이름 바꾸기", key=f"rnb_{im['id']}"):
                            if q1("SELECT id FROM images WHERE filename=? AND id<>?", (new, im["id"])):
                                st.error("같은 이름이 있습니다.")
                            else:
                                ex("UPDATE images SET filename=? WHERE id=?", (new, im["id"]))
                                st.rerun()
                        if st.button("삭제", key=f"del_{im['id']}"):
                            ex("UPDATE images SET deleted=1 WHERE id=?", (im["id"],))
                            st.rerun()

    with tabs[2]:
        rows = q("""SELECT i.*, m.no, m.title, b.name bname, m.month FROM images i JOIN manuscripts m ON m.id=i.ms_id
                    JOIN branches b ON b.id=m.branch_id WHERE i.status='배치' AND i.deleted=0 ORDER BY b.name, m.no, i.slot""")
        st.caption("배치는 원고 보드 오른쪽 상세 패널에서 합니다. 한 이미지는 한 원고에만 배치됩니다.")
        if rows:
            st.dataframe(pd.DataFrame([{"월": r["month"], "지점": r["bname"], "원고": f"{r['no']}번", "제목": r["title"],
                                        "칸": r["slot"], "이미지": r["filename"], "상태": "실행사 다운로드 대기"} for r in rows]),
                         hide_index=True, width="stretch")
        else:
            st.info("배치된 이미지가 없습니다.")

    with tabs[3]:
        keep = get_setting("image_keep_days")
        st.caption(f"실행사가 내려받은 이미지는 보관함에서 사라지고, AS 재발행을 위해 {keep}일간 해당 원고에만 남습니다. "
                   "실수나 다운로드 실패 때는 여기서 되돌립니다.")
        rows = q("""SELECT i.*, m.no, b.name bname FROM images i LEFT JOIN manuscripts m ON m.id=i.ms_id
                    LEFT JOIN branches b ON b.id=m.branch_id WHERE i.status='사용 완료' AND i.deleted=0 ORDER BY i.used_at DESC""")
        for r in rows:
            c1, c2, c3 = st.columns([1, 4, 1])
            c1.image(r["path"], width=70)
            c2.markdown(f"**{r['filename']}** · {r['bname']} {r['no']}번 · 사용 {r['used_at']}")
            if c3.button("배치로 되돌리기", key=f"rs_{r['id']}"):
                ex("UPDATE images SET status='배치', used_at=NULL WHERE id=?", (r["id"],))
                audit(user["name"], "이미지 되돌리기", r["filename"])
                st.rerun()
'''

# ============================================================================
# views.importer
# ============================================================================
MODULES['views.importer'] = r'''"""기존 시트 불러오기 — 진행 중인 달의 원고 시트·카페 목록·보유장비를 프로그램으로. (미리보기 → 승인, 덮어쓰기 경고)"""
import pandas as pd
import streamlit as st

from core.checks import check_branch
from core.common import CAFE_TYPES, audit, cafe_base, month_label, norm_name
from core.db import ex, now, q, q1
from core.ops import ensure_month_frame, resolve_branch
from core.sheets import parse_manuscript_workbook, status_from_raw


def render(ctx):
    user, month = ctx["user"], ctx["month"]
    st.title("📥 기존 시트 불러오기")
    tabs = st.tabs(["📝 원고 시트", "☕ 카페 목록", "🧰 보유장비"])
    with tabs[0]:
        _manuscripts(user, month)
    with tabs[1]:
        _cafes(user)
    with tabs[2]:
        _equipment(user)


def _manuscripts(user, month):
    st.caption("원고 전달용 시트를 엑셀로 내려받아 올립니다. 탭 하나 = 지점 하나. 기본 배치는 5–24행(20건), B 키워드 · C 특이사항 · D 보유장비 · "
               "G 제목 · H 본문 · I–N 댓글/대댓글 3쌍, A열 = 원고 재료. 시트와 다르면 아래에서 칸을 바꿔 주세요.")
    up = st.file_uploader("원고 시트 (.xlsx)", type=["xlsx"], key="imp_ms")
    with st.expander("칸 배치"):
        c = st.columns(6)
        mp = {"first_row": c[0].number_input("첫 행", 1, 50, 5), "keyword": c[1].text_input("키워드", "B"),
              "special": c[2].text_input("특이사항", "C"), "equipment": c[3].text_input("장비", "D"),
              "status": c[4].text_input("상태(피드백/완료)", "E"), "title": c[5].text_input("제목", "G")}
        c = st.columns(3)
        mp["body"] = c[0].text_input("본문", "H")
        mp["comments"] = [x.strip() for x in c[1].text_input("댓글·대댓글 칸", "I,J,K,L,M,N").split(",")]
        mp["material"] = c[2].text_input("원고 재료 칸", "A")
    if not up:
        return
    parsed = parse_manuscript_workbook(up, mp)
    if not parsed:
        st.warning("읽을 수 있는 탭이 없습니다.")
        return
    rows = []
    for tab, d in parsed.items():
        bid = resolve_branch(tab) or resolve_branch(tab + "점")
        exist = q1("""SELECT COUNT(*) n FROM manuscripts WHERE month=? AND branch_id=? AND (title<>'' OR body<>'')""",
                   (month, bid)) if bid else {"n": 0}
        rows.append({"탭": tab, "지점": q1("SELECT name FROM branches WHERE id=?", (bid,))["name"] if bid else "❓ 대응 없음",
                     "branch_id": bid, "제목 있는 행": sum(bool(r["title"]) for r in d["rows"]),
                     "키워드 있는 행": sum(bool(r["keyword"]) for r in d["rows"]), "⚠️ 덮어쓸 기존 원고": exist["n"]})
    df = pd.DataFrame(rows)
    st.dataframe(df.drop(columns=["branch_id"]), hide_index=True, width="stretch")
    pick = st.selectbox("미리보기", list(parsed))
    st.dataframe(pd.DataFrame(parsed[pick]["rows"]), hide_index=True, width="stretch")
    if df["⚠️ 덮어쓸 기존 원고"].sum():
        st.warning("이미 원고가 있는 지점이 있습니다. 가져오면 같은 번호의 원고를 덮어씁니다.")
    if df["branch_id"].isna().any():
        st.info("대응 없는 탭은 건너뜁니다. 지점 정보의 '배정 시트 지점명 대응'에 탭 이름을 넣으면 이어집니다.")
    ok = st.checkbox(f"{month_label(month)}로 가져오기를 승인합니다")
    if ok and st.button("가져오기", type="primary"):
        n = 0
        for r in rows:
            bid = r["branch_id"]
            if not bid:
                continue
            ex("INSERT OR IGNORE INTO branch_month(month,branch_id) VALUES(?,?)", (month, bid))
            ensure_month_frame(month, bid)
            d = parsed[r["탭"]]
            if d["material"]:
                ex("UPDATE branch_month SET req_notes=COALESCE(NULLIF(req_notes,''), ?) WHERE month=? AND branch_id=?",
                   (d["material"][:2000], month, bid))
            for x in d["rows"]:
                has = bool(x["title"] or x["body"])
                ex("""UPDATE manuscripts SET keyword=?, special=?, equipment=?, title=?, body=?, c1=?, r1=?, c2=?, r2=?, c3=?, r3=?,
                      status=?, updated_at=?, updated_by=? WHERE month=? AND branch_id=? AND no=?""",
                   (x["keyword"], x["special"], x["equipment"], x["title"], x["body"], x["c1"], x["r1"], x["c2"], x["r2"],
                    x["c3"] if x["no"] == 20 else "", x["r3"] if x["no"] == 20 else "",
                    status_from_raw(x["status_raw"], has), now(), "시트 불러오기", month, bid, x["no"]))
            check_branch(month, bid)
            n += 1
        audit(user["name"], "원고 시트 불러오기", f"{month} {n}개 지점")
        st.success(f"{n}개 지점을 가져왔습니다.")


def _cafes(user):
    st.caption("통합 보고서 '작업 진행 카페' 탭을 엑셀로 올립니다. 칸: 카테고리 · 지역 구분 · 카페명 · URL (+ 회원수·비고). "
               "카테고리 '대형 2030' → 2030뷰티/대형, '서울 지역맘' → 지역맘/서울 처럼 바꾸고, 같은 URL은 하나로 합쳐 다른 이름은 '다른 표기'로 둡니다.")
    up = st.file_uploader("카페 목록 (.xlsx/.csv)", type=["xlsx", "csv"], key="imp_cafe")
    if not up:
        return
    d = pd.read_csv(up, dtype=str) if up.name.endswith(".csv") else pd.read_excel(up, dtype=str)
    d = d.fillna("")

    def col(*k):
        return next((c for c in d.columns if any(x in str(c) for x in k)), None)
    cc, cr, cn, cu = col("카테고리", "분류"), col("지역"), col("카페명", "이름"), col("URL", "url", "링크")
    st.caption(f"읽을 칸 → 카테고리:{cc} 지역 구분:{cr} 카페명:{cn} URL:{cu}")
    if not (cn and cu):
        st.error("카페명·URL 칸이 필요합니다.")
        return
    merged = {}
    for _, r in d.iterrows():
        base, _ = cafe_base(r[cu])
        if not base:
            continue
        cat = str(r[cc]) if cc else ""
        t = "지역맘" if "지역맘" in cat else ("맘" if "맘" in cat else ("남성" if "남성" in cat else "2030뷰티"))
        size = "대형" if "대형" in cat else ("소형" if "소형" in cat else "")
        reg = next((x for x in ["서울", "경기", "인천", "충청", "전라", "경상", "강원", "제주"] if x in cat), "")
        branch_word = str(r[cr]).strip() if cr else ""
        m = merged.setdefault(base, {"name": r[cn], "alts": set(), "ctype": t, "size": size if t != "지역맘" else "",
                                     "region": reg if t == "지역맘" else "", "branches": set()})
        if r[cn] != m["name"]:
            m["alts"].add(r[cn])
        if branch_word:
            m["branches"].add(branch_word)
    prev = pd.DataFrame([{"URL": f"cafe.naver.com/{k}", "카페명": v["name"], "다른 표기": ", ".join(v["alts"]), "유형": v["ctype"],
                          "규모": v["size"], "지역": v["region"], "연결 지점": ", ".join(v["branches"]),
                          "이미 있음": bool(q1("SELECT id FROM cafes WHERE base_id=?", (k,)))} for k, v in merged.items()])
    st.dataframe(prev, hide_index=True, width="stretch")
    if st.checkbox("가져오기를 승인합니다 (이미 있는 카페는 건너뜀)") and st.button("가져오기", type="primary"):
        n = 0
        for k, v in merged.items():
            if q1("SELECT id FROM cafes WHERE base_id=?", (k,)):
                continue
            cid = ex("""INSERT INTO cafes(name,alt_names,url,base_id,ctype,size,region,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)""",
                     (v["name"], ", ".join(v["alts"]), f"https://cafe.naver.com/{k}", k, v["ctype"], v["size"], v["region"],
                      "진행 가능", now()))
            for bw in v["branches"]:
                if bw == "서울":
                    ex("INSERT INTO cafe_links(cafe_id,link_type,region) VALUES(?,?,?)", (cid, "지역", "서울"))
                    continue
                bid = resolve_branch(bw) or resolve_branch(bw + "점")
                if bid:
                    ex("INSERT INTO cafe_links(cafe_id,link_type,branch_id) VALUES(?,?,?)", (cid, "지점", bid))
            n += 1
        audit(user["name"], "카페 목록 불러오기", f"{n}개")
        st.success(f"{n}개 카페를 가져왔습니다.")


def _equipment(user):
    st.caption("보유장비 RAW 시트를 올립니다. 칸: 지점 · 분류 · 장비명 · 수량 · 입고일 · 비고. 장비명은 표준 장비명(다른 표기 포함)으로 맞추고, "
               "지점명은 '경기광주' → '경기광주점'처럼 통일합니다. 같은 지점·장비 중복 행은 하나로 정리합니다.")
    up = st.file_uploader("보유장비 (.xlsx/.csv)", type=["xlsx", "csv"], key="imp_eq")
    if not up:
        return
    d = pd.read_csv(up, dtype=str) if up.name.endswith(".csv") else pd.read_excel(up, dtype=str)
    d = d.fillna("")

    def col(*k):
        return next((c for c in d.columns if any(x in str(c) for x in k)), None)
    cb, ccat, cn, cq, cd, cnote = col("지점"), col("분류", "카테고리"), col("장비"), col("수량"), col("입고"), col("비고")
    std = {}
    for s in q("SELECT * FROM equip_std"):
        std[norm_name(s["name"])] = s["id"]
        for a in (s["aliases"] or "").split(","):
            if a.strip():
                std[norm_name(a)] = s["id"]
    out, seen = [], set()
    for _, r in d.iterrows():
        bid = resolve_branch(r[cb]) or resolve_branch(str(r[cb]) + "점")
        sid = std.get(norm_name(r[cn]))
        key = (bid, sid or norm_name(r[cn]))
        dup = key in seen
        seen.add(key)
        out.append({"지점(원본)": r[cb], "지점": bid, "장비(원본)": r[cn], "표준명": sid, "분류": r[ccat] if ccat else "",
                    "수량": r[cq] if cq else 1, "입고일": r[cd] if cd else "", "비고": r[cnote] if cnote else "", "중복": dup})
    df = pd.DataFrame(out)
    st.dataframe(df.assign(지점=df["지점"].map(lambda x: "✅" if x else "❓"), 표준명=df["표준명"].map(lambda x: "✅" if x else "➕ 새 표준명")),
                 hide_index=True, width="stretch")
    add_new = st.checkbox("표준명에 없는 장비는 새 표준명으로 추가", value=True)
    if st.checkbox("가져오기를 승인합니다") and st.button("가져오기", type="primary"):
        n = 0
        for r in out:
            if not r["지점"] or r["중복"]:
                continue
            sid = r["표준명"]
            if not sid:
                if not add_new or not r["장비(원본)"].strip():
                    continue
                sid = ex("INSERT OR IGNORE INTO equip_std(name,category) VALUES(?,?)", (r["장비(원본)"].strip(), r["분류"] or "기타")) or \
                    q1("SELECT id FROM equip_std WHERE name=?", (r["장비(원본)"].strip(),))["id"]
            if q1("SELECT id FROM branch_equipment WHERE branch_id=? AND std_id=? AND active=1", (r["지점"], sid)):
                continue
            ex("""INSERT INTO branch_equipment(branch_id,std_id,qty,in_date,note,updated_at,updated_by) VALUES(?,?,?,?,?,?,?)""",
               (r["지점"], sid, int(r["수량"]) if str(r["수량"]).isdigit() else 1, str(r["입고일"])[:10] or None, r["비고"], now(), user["name"]))
            n += 1
        audit(user["name"], "보유장비 불러오기", f"{n}행")
        st.success(f"{n}행 가져왔습니다.")
'''

# ============================================================================
# views.notices
# ============================================================================
MODULES['views.notices'] = r'''"""알림 (화면 상단 종 + 홈의 '내 할 일'). 역할별로 자기 알림만."""
import pandas as pd
import streamlit as st

from core.db import ex, q


def render(ctx):
    user = ctx["user"]
    st.title("🔔 알림")
    rows = q("SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 300", (user["id"],))
    unread = [r for r in rows if not r["read"]]
    c1, c2 = st.columns([3, 1])
    c1.caption(f"읽지 않은 알림 {len(unread)}건")
    if c2.button("모두 읽음", width="stretch", disabled=not unread):
        ex("UPDATE notifications SET read=1 WHERE user_id=?", (user["id"],))
        st.rerun()
    kinds = sorted({r["kind"] for r in rows})
    f = st.multiselect("종류", kinds)
    rows = [r for r in rows if not f or r["kind"] in f]
    if not rows:
        st.info("알림이 없습니다.")
        return
    st.dataframe(pd.DataFrame([{"": "🔵" if not r["read"] else "", "종류": r["kind"], "내용": r["message"], "시각": r["created_at"]}
                               for r in rows]), hide_index=True, width="stretch", height=600)
'''

# ============================================================================
# views.publish
# ============================================================================
MODULES['views.publish'] = r'''"""발행·운영 (관리자·실행사 전용 — 지점 담당자·작가에게는 보이지 않음)"""
import io
import math
import zipfile
from datetime import date

import pandas as pd
import streamlit as st

from core.common import (ACC_PURPOSE, ACC_STATUS, ADMIN, BOARD, EXEC, audit, branch_name, get_setting,
                         notify_role, to_date, user_options)
from core.db import ex, now, q, q1, qv, today
from core.ops import (account_cafe_check, account_comment_check, accounts_for_cafe, cafe_precheck, eligible_cafes,
                      mark_images_used, ms_images, plan_publish_dates, publish_backlog, ready_branches, resolve_as,
                      save_publication, try_fetch_link, update_check, update_cafe_delete_rates)


def render(ctx):
    user, role, month = ctx["user"], ctx["role"], ctx["month"]
    st.title("🚀 발행·운영")
    tabs = st.tabs(["📤 발행", "🔑 카페 계정", "🔒 계정 현황", "🛠️ 발행 후 관리·AS", "⚠️ 이슈", "📌 게시판 요청"])
    with tabs[0]:
        _publish(user, role, month)
    with tabs[1]:
        _accounts(user, role)
    with tabs[2]:
        _account_status(month)
    with tabs[3]:
        _after(user, month)
    with tabs[4]:
        _issues(user, month)
    with tabs[5]:
        _board_requests(user, month)


# ── 발행 ────────────────────────────────────────────────────────────────────
def _publish(user, role, month):
    plan_publish_dates(month)
    for w in publish_backlog(month):
        st.error("발행 밀림: " + w)
    ready = ready_branches(month)
    if not ready:
        st.info("아직 20건이 모두 '완료'된 지점이 없습니다.")
        return
    # 기본 정렬: 담당자 → 지점 (담당자 이름은 표시하지 않음)
    info = q(f"""SELECT bm.branch_id, bm.planned_publish, bm.manager_id, b.name FROM branch_month bm
                 JOIN branches b ON b.id=bm.branch_id WHERE bm.month=? AND bm.branch_id IN ({','.join('?' * len(ready))})
                 ORDER BY bm.manager_id, b.name""", [month] + ready)
    td = today()
    rows = []
    for r in info:
        n = qv("SELECT COUNT(*) FROM publications WHERE month=? AND branch_id=? AND url<>''", (month, r["branch_id"]), 0)
        rows.append({"지점": r["name"], "발행 예정일": r["planned_publish"], "발행": f"{n}/20",
                     "오늘": "📌 오늘 발행" if r["planned_publish"] == td and n < 20 else
                     ("⚫ 지연" if r["planned_publish"] and r["planned_publish"] < td and n < 20 else ""),
                     "id": r["branch_id"]})
    today_list = [r for r in rows if r["오늘"]]
    done_n = sum(r["발행"] == "20/20" for r in rows)
    c1, c2 = st.columns([1, 2])
    c1.metric("오늘 발행할 지점", len(today_list))
    c1.metric("발행 완료 지점", f"{done_n}/{len(rows)}")
    c2.dataframe(pd.DataFrame(rows).drop(columns=["id"]), hide_index=True, width="stretch", height=220)

    bsel = st.selectbox("발행할 지점", [r["지점"] for r in rows], key="pub_branch")
    bid = next(r["id"] for r in rows if r["지점"] == bsel)
    mss = q("SELECT * FROM manuscripts WHERE month=? AND branch_id=? ORDER BY no", (month, bid))
    pubs = {p["ms_id"]: p for p in q("SELECT * FROM publications WHERE month=? AND branch_id=?", (month, bid))}
    tbl = []
    for m in mss:
        p = pubs.get(m["id"], {})
        cafe = q1("SELECT name FROM cafes WHERE id=?", (p.get("cafe_id"),)) if p else None
        acc = q1("SELECT acc_id FROM accounts WHERE id=?", (p.get("account_id"),)) if p else None
        tbl.append({"번호": m["no"], "유형": m["mtype"], "상태": m["status"], "제목": m["title"],
                    "카페": cafe and cafe["name"], "계정": acc and acc["acc_id"], "발행일": p.get("pub_date"),
                    "URL": p.get("url"), "이미지": len(ms_images(m["id"]))})
    st.dataframe(pd.DataFrame(tbl).fillna(""), hide_index=True, width="stretch", height=300)

    st.markdown("##### 원고별 발행 입력")
    no = st.selectbox("원고 번호", [m["no"] for m in mss], key=f"pubno_{bid}",
                      format_func=lambda n: f"{n}번 · {next(m for m in mss if m['no'] == n)['mtype']}")
    ms = next(m for m in mss if m["no"] == no)
    old = pubs.get(ms["id"])
    with st.expander("원고 내용 보기 / 이미지 내려받기", expanded=False):
        st.markdown(f"**{ms['title']}**")
        st.write(ms["body"])
        for c, r in [("c1", "r1"), ("c2", "r2"), ("c3", "r3")]:
            if ms[c]:
                st.markdown(f"💬 {ms[c]}  \n↳ {ms[r] or ''}")
        imgs = ms_images(ms["id"])
        if imgs:
            st.image([i["path"] for i in imgs], width=140, caption=[i["filename"] for i in imgs])
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as z:
                for i in imgs:
                    z.write(i["path"], i["filename"])
            if st.download_button("🖼️ 이 원고 이미지 한 번에 받기", buf.getvalue(), file_name=f"{bsel}_{no}번_이미지.zip",
                                  key=f"dlimg_{ms['id']}"):
                mark_images_used(ms["id"])

    cands = eligible_cafes(ms)
    cands.sort(key=lambda c: (not c["적합"], -c["사용 가능 계정"]))
    with st.expander("카페 후보 · 사전 체크 결과"):
        st.dataframe(pd.DataFrame(cands).drop(columns=["id"]), hide_index=True, width="stretch")
    copts = {f"{'✅' if c['적합'] else '❌'} {c['카페']} ({c['유형']}·{c['상태']}·계정 {c['사용 가능 계정']})": c["id"] for c in cands}
    keys = list(copts)
    idx = next((i for i, k in enumerate(keys) if old and copts[k] == old["cafe_id"]), 0)
    if not keys:
        st.warning("등록된 카페가 없습니다.")
        return
    ck = st.selectbox("카페 선택", keys, index=idx, key=f"cafe_{ms['id']}")
    cafe_id = copts[ck]
    block, msgs = cafe_precheck(ms, cafe_id, exclude_pub=old and old["id"])
    for m in msgs:
        (st.error if m.startswith("❌") else st.warning)(m)
    pdate = st.date_input("발행일", value=to_date(old and old["pub_date"]) or date.today(), key=f"pd_{ms['id']}")
    accs = accounts_for_cafe(cafe_id, pdate)
    aopts = {f"{'✅' if a['가능'] else '⛔'} {a['계정']} ({a['닉네임'] or '-'}) — {a['상태']}": a for a in accs}
    if not aopts:
        st.warning("사용 중인 카페 침투 계정이 없습니다. '카페 계정' 탭에서 등록하세요.")
        return
    ak = st.selectbox("계정 (지금 이 카페에 쓸 수 있는 계정)", list(aopts), key=f"acc_{ms['id']}")
    acc = aopts[ak]
    url = st.text_input("카페침투 URL", value=(old and old["url"]) or "", key=f"url_{ms['id']}")
    force = False
    if block and role == ADMIN:
        force = st.checkbox("관리자 확인 후 예외로 저장", key=f"force_{ms['id']}")
    if st.button("💾 발행 저장 (URL을 넣으면 '사용 완료')", type="primary", disabled=not acc["가능"]):
        ok, m2 = save_publication(ms["id"], cafe_id, acc["id"], url, pdate.isoformat(), user, force)
        if ok:
            st.success("저장했습니다.")
            st.rerun()
        else:
            for m in m2:
                st.error(m)


# ── 카페 계정 ───────────────────────────────────────────────────────────────
def _accounts(user, role):
    st.caption("실행사가 직접 등록·교체합니다. 같은 아이디는 두 번 등록되지 않고, 추가·교체하면 관리자에게 알림이 갑니다.")
    df = pd.DataFrame(q("SELECT id, acc_id, nickname, purpose, status, memo, created_at FROM accounts ORDER BY status, acc_id"))
    if df.empty:
        df = pd.DataFrame(columns=["id", "acc_id", "nickname", "purpose", "status", "memo", "created_at"])
    ed = st.data_editor(df, num_rows="dynamic", hide_index=True, width="stretch", key="acc_ed",
                        disabled=["id", "created_at"],
                        column_config={"id": None, "acc_id": "카페 아이디", "nickname": "닉네임",
                                       "purpose": st.column_config.SelectboxColumn("용도", options=ACC_PURPOSE),
                                       "status": st.column_config.SelectboxColumn("상태", options=ACC_STATUS),
                                       "memo": "메모", "created_at": "등록일"})
    if st.button("💾 계정 저장 (중복 검사)", type="primary"):
        seen, errs = set(), []
        for r in ed.to_dict("records"):
            aid = str(r.get("acc_id") or "").strip()
            if not aid:
                continue
            if aid in seen:
                errs.append(f"'{aid}' 가 두 번 입력되었습니다.")
            seen.add(aid)
        if errs:
            for e in errs:
                st.error(e)
            return
        old = {r["id"]: r for r in q("SELECT * FROM accounts")}
        for r in ed.to_dict("records"):
            aid = str(r.get("acc_id") or "").strip()
            if not aid:
                continue
            rid = r.get("id")
            if rid and not (isinstance(rid, float) and math.isnan(rid)) and int(rid) in old:
                o = old[int(rid)]
                ch = {k: (o[k], r[k]) for k in ("acc_id", "nickname", "purpose", "status", "memo") if (o[k] or "") != (r[k] or "")}
                if ch:
                    ex("UPDATE accounts SET acc_id=?, nickname=?, purpose=?, status=?, memo=? WHERE id=?",
                       (aid, r["nickname"], r["purpose"], r["status"] or "사용 중", r["memo"], int(rid)))
                    ex("INSERT INTO account_log(account_id,at,user,action,detail) VALUES(?,?,?,?,?)",
                       (int(rid), now(), user["name"], "변경", str(ch)))
            else:
                if q1("SELECT id FROM accounts WHERE acc_id=?", (aid,)):
                    st.error(f"'{aid}' 는 이미 등록된 아이디입니다.")
                    continue
                new = ex("INSERT INTO accounts(acc_id,nickname,purpose,status,memo,created_at,created_by) VALUES(?,?,?,?,?,?,?)",
                         (aid, r["nickname"], r["purpose"] or "둘 다", r["status"] or "사용 중", r["memo"], now(), user["name"]))
                ex("INSERT INTO account_log(account_id,at,user,action,detail) VALUES(?,?,?,?,?)",
                   (new, now(), user["name"], "등록", aid))
                if role == EXEC:
                    notify_role(ADMIN, "계정", f"카페 계정이 추가되었습니다: {aid}")
        st.success("저장했습니다.")
        st.rerun()

    st.markdown("##### 🔁 계정 교체")
    act = q("SELECT * FROM accounts WHERE status='사용 중' ORDER BY acc_id")
    if act:
        c1, c2, c3 = st.columns(3)
        o = c1.selectbox("바꿀 계정", [a["acc_id"] for a in act], key="rep_old")
        n = c2.text_input("새 아이디", key="rep_new")
        nick = c3.text_input("새 닉네임", key="rep_nick")
        if st.button("교체하기"):
            if not n.strip() or q1("SELECT id FROM accounts WHERE acc_id=?", (n.strip(),)):
                st.error("새 아이디가 비었거나 이미 등록되어 있습니다.")
            else:
                old = q1("SELECT * FROM accounts WHERE acc_id=?", (o,))
                ex("UPDATE accounts SET status='교체됨' WHERE id=?", (old["id"],))
                new = ex("""INSERT INTO accounts(acc_id,nickname,purpose,status,replaced_from,created_at,created_by)
                            VALUES(?,?,?,?,?,?,?)""", (n.strip(), nick, old["purpose"], "사용 중", old["id"], now(), user["name"]))
                ex("INSERT INTO account_log(account_id,at,user,action,detail) VALUES(?,?,?,?,?)",
                   (new, now(), user["name"], "교체", f"{o} → {n.strip()}"))
                if role == EXEC:
                    notify_role(ADMIN, "계정", f"카페 계정이 교체되었습니다: {o} → {n.strip()}")
                st.success("교체했습니다. 이전 계정 기록은 남고 새 계정은 기록 없이 시작합니다.")
                st.rerun()
    with st.expander("계정 변경 이력"):
        st.dataframe(pd.DataFrame(q("""SELECT l.at 시각, a.acc_id 계정, l.user 누가, l.action 무엇, l.detail 내용
                                        FROM account_log l LEFT JOIN accounts a ON a.id=l.account_id ORDER BY l.id DESC LIMIT 200""")),
                     hide_index=True, width="stretch")


# ── 계정 현황 ───────────────────────────────────────────────────────────────
def _account_status(month):
    lim = int(get_setting("comment_month_limit"))
    target = int(get_setting("comment_month_target"))
    need = math.ceil(target / lim)
    cm_accs = q("SELECT * FROM accounts WHERE status='사용 중' AND purpose IN ('댓글 침투','둘 다')")
    usable = [a for a in cm_accs if account_comment_check(a["id"], month)[0]]
    c = st.columns(3)
    c[0].metric("댓글 침투 필요 계정", f"{need}개", help=f"월 {target}개 ÷ 계정당 {lim}개")
    c[1].metric("이번 달 사용 가능", f"{len(usable)}개")
    c[2].metric("카페 침투 사용 중 계정", qv("SELECT COUNT(*) FROM accounts WHERE status='사용 중' AND purpose IN ('카페 침투','둘 다')", default=0))
    if len(usable) < need:
        st.error(f"댓글 침투 계정이 {need - len(usable)}개 모자랍니다.")

    rows = []
    for a in q("SELECT * FROM accounts ORDER BY status, acc_id"):
        ok, msg, n = account_comment_check(a["id"], month)
        last = q("""SELECT c.name, MAX(p.pub_date) d, COUNT(*) n FROM publications p JOIN cafes c ON c.id=p.cafe_id
                    WHERE p.account_id=? GROUP BY c.id ORDER BY d DESC""", (a["id"],))
        blocked = [f"{l['name']}({account_cafe_check(a['id'], q1('SELECT id FROM cafes WHERE name=?', (l['name'],))['id'])[1]})"
                   for l in last if not account_cafe_check(a["id"], q1("SELECT id FROM cafes WHERE name=?", (l["name"],))["id"])[0]]
        rows.append({"계정": a["acc_id"], "닉네임": a["nickname"], "용도": a["purpose"], "상태": a["status"],
                     "이번 달 발행": qv("SELECT COUNT(*) FROM publications WHERE account_id=? AND month=?", (a["id"], month), 0),
                     "댓글": msg, "막힌 카페 (다시 쓸 수 있는 날)": ", ".join(blocked),
                     "경고": ", ".join(f"{l['name']} {l['n']}회" for l in last if l["n"] >= 3)})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption("같은 계정이 같은 카페에 3회 이상 쓰이면 '경고'에 표시됩니다. 숫자(10일·40개·35개)는 설정에서 바꿀 수 있습니다.")


# ── 발행 후 관리 ────────────────────────────────────────────────────────────
def _after(user, month):
    st.caption(f"삭제 = 링크가 열리지 않음 / 댓글 {get_setting('as_comment_min')}개 이하 = 댓글 작업 미완료 / "
               f"발행 {get_setting('as_view_after_days')}일 지난 뒤 조회수 {get_setting('as_view_min')} 이하 = 조회수 부족 → AS 목록")
    rows = q("""SELECT p.*, b.name bname, m.no, c.name cafe FROM publications p JOIN branches b ON b.id=p.branch_id
                JOIN manuscripts m ON m.id=p.ms_id LEFT JOIN cafes c ON c.id=p.cafe_id
                WHERE p.month=? AND p.url<>'' ORDER BY b.name, m.no""", (month,))
    if not rows:
        st.info("발행된 링크가 없습니다.")
        return
    df = pd.DataFrame([{"id": r["id"], "지점": r["bname"], "번호": r["no"], "카페": r["cafe"], "URL": r["url"],
                        "발행일": r["pub_date"], "조회수": r["views"], "댓글 수": r["comments"],
                        "삭제됨": r["check_state"] == "삭제됨", "상태": r["check_state"], "AS": r["as_state"],
                        "마지막 확인": r["last_checked"]} for r in rows])
    ed = st.data_editor(df, hide_index=True, width="stretch", key=f"after_{month}",
                        disabled=["id", "지점", "번호", "카페", "URL", "발행일", "상태", "AS", "마지막 확인"],
                        column_config={"id": None, "URL": st.column_config.LinkColumn("URL")})
    c1, c2, c3 = st.columns(3)
    if c1.button("💾 확인 결과 저장", type="primary", width="stretch"):
        for r in ed.to_dict("records"):
            v = None if pd.isna(r["조회수"]) else int(r["조회수"])
            cm = None if pd.isna(r["댓글 수"]) else int(r["댓글 수"])
            update_check(r["id"], v, cm, bool(r["삭제됨"]), user)
        st.rerun()
    if c2.button("🔗 링크 열리는지 확인", width="stretch"):
        with st.spinner("확인 중…"):
            for r in rows:
                ok, code = try_fetch_link(r["url"])
                if ok is False:
                    update_check(r["id"], r["views"], r["comments"], True, user)
                elif ok:
                    ex("UPDATE publications SET last_checked=? WHERE id=?", (now(), r["id"]))
        st.rerun()
    up = c3.file_uploader("수집 결과 CSV/엑셀 (URL·조회수·댓글수)", type=["csv", "xlsx"], key="after_up",
                          label_visibility="collapsed")
    if up is not None and st.button("CSV 반영"):
        d = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up)
        cols = {c: c for c in d.columns}
        uc = next((c for c in d.columns if "url" in str(c).lower() or "링크" in str(c)), None)
        vc = next((c for c in d.columns if "조회" in str(c)), None)
        cc = next((c for c in d.columns if "댓글" in str(c)), None)
        n = 0
        for _, x in d.iterrows():
            p = q1("SELECT * FROM publications WHERE url=?", (str(x[uc]).strip(),)) if uc else None
            if p:
                update_check(p["id"], int(x[vc]) if vc and not pd.isna(x[vc]) else p["views"],
                             int(x[cc]) if cc and not pd.isna(x[cc]) else p["comments"], False, user)
                n += 1
        st.success(f"{n}건 반영")

    st.markdown("##### 🛠️ AS 목록")
    as_rows = [r for r in rows if r["as_state"] == "AS 대기"]
    days = int(get_setting("as_days"))
    if not as_rows:
        st.success("AS 대기 없음")
    for r in as_rows:
        opened = to_date(r["as_opened_at"])
        late = opened and (date.today() - opened).days > days
        with st.container(border=True):
            st.markdown(f"**{r['bname']} {r['no']}번** · {r['cafe']} · {r['check_state']} "
                        f"{'⚫ 기한 지남' if late else ''}  \n{r['url']}")
            cc1, cc2 = st.columns([3, 1])
            nu = cc1.text_input("새 링크 (재발행 시)", key=f"asurl_{r['id']}")
            if cc2.button("처리 완료", key=f"asdone_{r['id']}"):
                resolve_as(r["id"], nu, user)
                st.rerun()

    st.markdown("##### 📈 카페별 삭제율 · 댓글 작업 미완료 비율")
    stat = q("""SELECT c.name 카페, c.status 상태, COUNT(*) 발행, SUM(p.check_state='삭제됨') 삭제,
                       SUM(p.check_state='댓글 작업 미완료') "댓글 미완료"
                FROM publications p JOIN cafes c ON c.id=p.cafe_id WHERE p.url<>'' GROUP BY c.id ORDER BY 삭제 DESC""")
    if stat:
        d = pd.DataFrame(stat)
        d["삭제율(%)"] = (d["삭제"] * 100 / d["발행"]).round(1)
        d["댓글 미완료율(%)"] = (d["댓글 미완료"] * 100 / d["발행"]).round(1)
        st.dataframe(d, hide_index=True, width="stretch")
        update_cafe_delete_rates(user)


# ── 이슈 ────────────────────────────────────────────────────────────────────
def _issues(user, month):
    with st.form("issue_new"):
        c = st.columns(3)
        kind = c[0].selectbox("종류", ["게시글 삭제", "계정 제재", "기타"])
        bs = {b["name"]: b["id"] for b in q("SELECT id,name FROM branches WHERE active=1 ORDER BY name")}
        br = c[1].selectbox("지점", ["(없음)"] + list(bs))
        accs = {a["acc_id"]: a["id"] for a in q("SELECT id,acc_id FROM accounts ORDER BY acc_id")}
        ac = c[2].selectbox("계정", ["(없음)"] + list(accs))
        desc = st.text_area("내용")
        action = st.text_input("대응 방안")
        rework = st.checkbox("재작업 필요")
        stop = st.checkbox("이 계정을 '제재·정지'로 바꾸기")
        if st.form_submit_button("이슈 등록"):
            ex("""INSERT INTO issues(month,branch_id,account_id,kind,description,action,rework,created_at,created_by)
                  VALUES(?,?,?,?,?,?,?,?,?)""", (month, bs.get(br), accs.get(ac), kind, desc, action, int(rework), now(), user["name"]))
            if stop and accs.get(ac):
                ex("UPDATE accounts SET status='제재·정지' WHERE id=?", (accs[ac],))
                ex("INSERT INTO account_log(account_id,at,user,action,detail) VALUES(?,?,?,?,?)",
                   (accs[ac], now(), user["name"], "제재·정지", desc))
            notify_role(ADMIN, "이슈", f"이슈가 등록되었습니다: {kind} {br if br != '(없음)' else ''}")
            st.rerun()
    df = pd.DataFrame(q("""SELECT i.id, i.created_at 등록, b.name 지점, a.acc_id 계정, i.kind 종류, i.description 내용,
                                  i.action 대응, i.rework 재작업, i.status 상태
                           FROM issues i LEFT JOIN branches b ON b.id=i.branch_id LEFT JOIN accounts a ON a.id=i.account_id
                           ORDER BY i.id DESC"""))
    if df.empty:
        st.caption("등록된 이슈가 없습니다.")
        return
    df["재작업"] = df["재작업"].astype(bool)
    ed = st.data_editor(df, hide_index=True, width="stretch", key="iss_ed",
                        disabled=["id", "등록", "지점", "계정", "종류"],
                        column_config={"id": None, "상태": st.column_config.SelectboxColumn("상태", options=["접수", "대응 중", "완료"])})
    if st.button("이슈 저장"):
        for r in ed.to_dict("records"):
            ex("UPDATE issues SET description=?, action=?, rework=?, status=? WHERE id=?",
               (r["내용"], r["대응"], int(r["재작업"]), r["상태"], r["id"]))
        st.rerun()


# ── 게시판 업로드 요청 ─────────────────────────────────────────────────────
def _board_requests(user, month):
    st.caption("지점·카페·게시판·일정을 지정하면 게시판 담당의 할 일로 뜹니다.")
    with st.form("bt_new"):
        c = st.columns(4)
        bs = {b["name"]: b["id"] for b in q("SELECT id,name FROM branches WHERE active=1 ORDER BY name")}
        cs = {c_["name"]: c_["id"] for c_ in q("SELECT id,name FROM cafes WHERE archived=0 ORDER BY name")}
        br = c[0].selectbox("지점", list(bs))
        cf = c[1].selectbox("카페", list(cs)) if cs else None
        board = c[2].text_input("게시판")
        due = c[3].date_input("일정")
        who = user_options(BOARD)
        assignee = st.selectbox("게시판 담당", ["(누구나)"] + list(who))
        note = st.text_input("메모")
        if st.form_submit_button("요청 등록"):
            ex("""INSERT INTO board_tasks(month,branch_id,cafe_id,board,due,note,assignee_id,created_at,created_by)
                  VALUES(?,?,?,?,?,?,?,?,?)""", (month, bs[br], cs.get(cf), board, due.isoformat(), note, who.get(assignee), now(), user["name"]))
            from core.common import notify
            notify(list(who.values()) if assignee == "(누구나)" else who[assignee], "할 일",
                   f"[{br}] 게시판 업로드 요청: {cf} / {board} / {due}")
            st.rerun()
    st.dataframe(pd.DataFrame(q("""SELECT t.due 일정, b.name 지점, c.name 카페, t.board 게시판, t.status 상태, t.done_by 처리, t.done_at 처리일
                                   FROM board_tasks t LEFT JOIN branches b ON b.id=t.branch_id LEFT JOIN cafes c ON c.id=t.cafe_id
                                   WHERE t.month=? ORDER BY t.due""", (month,))), hide_index=True, width="stretch")
'''

# ============================================================================
# views.report
# ============================================================================
MODULES['views.report'] = r'''"""보고서: 실행사 기입 → 관리자 1차 확인 → 지점 담당자 확인 → 관리자 최종본 (로컬은 지점 확인 없음)"""
import pandas as pd
import streamlit as st

from core.common import ADMIN, EXEC, HOSPITALS, MANAGER, month_label, my_branch_ids, to_excel, user_name
from core.db import ex, now, q, q1, qv
from core.ops import (report_admin_pass, report_auto_check, report_finalize, report_issue_update, report_manager_ok,
                      report_manager_request, report_request_confirm, report_rows)
from core.sheets import build_report_sheets, gsheets_available, push_gsheet

PUB_CNT = "SELECT COUNT(*) FROM publications WHERE month=? AND branch_id=? AND url<>''"
STAGE_ICON = {"작성 중": "✏️ 작성 중", "관리자 확인": "🔎 관리자 확인", "지점 확인": "🏥 지점 확인", "수정 중": "🛠️ 수정 중",
              "최종 대기": "📝 최종 대기", "최종 확정": "🔒 최종 확정"}


def _df(rows, external):
    d = pd.DataFrame([{"pub_id": r["pub_id"], "NO": r["no"], "유형": r["mtype"], "발행일": r["pub_date"], "카페명": r["cafe_name"],
                       "카페링크": r["cafe_url"], "카페 아이디": r["acc_id"], "제목": r["title"], "카페침투 URL": r["url"],
                       "조회수": r["views"]} for r in rows])
    if external and not d.empty:
        d = d.drop(columns=["카페 아이디"])
    return d


def render(ctx):
    user, role, month = ctx["user"], ctx["role"], ctx["month"]
    st.title("📊 보고서")
    if role == ADMIN:
        tabs = st.tabs(["📋 확인 흐름", "📤 보고서 만들기"])
        with tabs[0]:
            _flow(ctx)
        with tabs[1]:
            _make(user, month)
    else:
        _flow(ctx)


def _flow(ctx):
    user, role, month = ctx["user"], ctx["role"], ctx["month"]
    bs = q("""SELECT b.*, bm.report_stage, bm.manager_id FROM branches b JOIN branch_month bm ON bm.branch_id=b.id AND bm.month=?
              WHERE b.active=1 ORDER BY b.name""", (month,))
    if role == MANAGER:
        mine = set(my_branch_ids(user, month))
        bs = [b for b in bs if b["id"] in mine and b["hospital"] != "로컬"]
    # 담당자별 확인 현황
    if role == ADMIN:
        stat = {}
        for b in bs:
            if b["hospital"] == "로컬":
                continue
            k = user_name(b["manager_id"]) or "(미배정)"
            s = stat.setdefault(k, [0, 0])
            s[0] += 1
            s[1] += b["report_stage"] in ("최종 대기", "최종 확정")
        st.markdown("**담당자별 확인 현황** — " + " · ".join(f"{k} {v[1]}/{v[0]}" for k, v in stat.items()))
        tot = [b for b in bs if b["hospital"] != "로컬"]
        st.caption(f"전체 {len(tot)}개 지점 중 {sum(b['report_stage'] in ('최종 대기', '최종 확정') for b in tot)}개 확인")
    if not bs:
        st.info("보고서를 볼 지점이 없습니다.")
        return
    ov = pd.DataFrame([{"지점": b["name"], "병원": b["hospital"], "단계": STAGE_ICON.get(b["report_stage"], b["report_stage"]),
                        "발행": str(qv(PUB_CNT, (month, b["id"]), 0)) + "/20",
                        "열린 요청": qv("SELECT COUNT(*) FROM report_issues WHERE month=? AND branch_id=? AND status IN ('접수됨','처리 중')",
                                      (month, b["id"]), 0)} for b in bs])
    st.dataframe(ov, hide_index=True, width="stretch", height=min(400, 40 + 35 * len(ov)))
    bname = st.selectbox("지점", [b["name"] for b in bs], key="rp_b")
    b = next(x for x in bs if x["name"] == bname)
    bid, stage = b["id"], b["report_stage"]
    bm = q1("SELECT * FROM branch_month WHERE month=? AND branch_id=?", (month, bid))
    st.markdown(f"### {bname} · {STAGE_ICON.get(stage)}" + (" · 🔒 잠김" if bm["report_locked"] else ""))
    rows = report_rows(month, bid)
    issues = q("SELECT * FROM report_issues WHERE month=? AND branch_id=? ORDER BY id DESC", (month, bid))

    if role == EXEC:
        st.dataframe(_df(rows, False).drop(columns=["pub_id"]), hide_index=True, width="stretch")
        st.caption("발행일·카페·카페 아이디·URL은 '발행·운영 > 발행'에서 입력합니다.")
        open_is = [i for i in issues if i["status"] in ("접수됨", "처리 중")]
        if open_is:
            st.markdown("##### 수정 요청")
            for i in open_is:
                no = qv("SELECT m.no FROM publications p JOIN manuscripts m ON m.id=p.ms_id WHERE p.id=?", (i["pub_id"],))
                who = "지점 확인 요청" if i["source"] == "지점 확인" else "관리자 확인"
                with st.container(border=True):
                    c1, c2, c3 = st.columns([4, 1, 1])
                    c1.markdown(f"**{no or '-'}번** · {who} · {i['reason']}  \n<span class='small'>{i['created_at']} · {i['status']}</span>",
                                unsafe_allow_html=True)
                    if c2.button("처리 중", key=f"ip_{i['id']}"):
                        report_issue_update(i["id"], "처리 중", user)
                        st.rerun()
                    if c3.button("반영 완료", key=f"id_{i['id']}", type="primary"):
                        report_issue_update(i["id"], "반영 완료", user)
                        st.rerun()
        if stage == "작성 중" and not bm["report_locked"]:
            if st.button("📤 기입 완료 · 확인 요청", type="primary"):
                report_request_confirm(month, bid, user)
                st.rerun()
        return

    if role == MANAGER:
        # 외부용 버전(실행사·카페 아이디 칸 제외)만 본다
        d = _df(rows, True)
        st.dataframe(d.drop(columns=["pub_id"]), hide_index=True, width="stretch")
        mine = [i for i in issues if i["source"] == "지점 확인"]
        if mine:
            st.markdown("##### 내가 보낸 수정 요청")
            st.dataframe(pd.DataFrame([{"요청": i["reason"], "상태": {"접수됨": "접수됨", "처리 중": "처리 중",
                                                                  "반영 완료": "반영 완료", "확인 완료": "확인 완료"}[i["status"]],
                                        "요청일": i["created_at"]} for i in mine]), hide_index=True, width="stretch")
        if stage in ("지점 확인", "수정 중"):
            c1, c2 = st.columns(2)
            if c1.button("✅ 이상 없음", type="primary", width="stretch"):
                if report_manager_ok(month, bid, user):
                    st.success("확인했습니다.")
                    st.rerun()
                else:
                    st.warning("처리 중인 수정 요청이 있습니다. 반영된 뒤 다시 확인해 주세요.")
            with c2.popover("✏️ 행별 수정 요청", width="stretch"):
                opts = {f"{r['no']}번 · {r['title'] or ''}": r["pub_id"] for r in rows if r["pub_id"]}
                if opts:
                    k = st.selectbox("행", list(opts))
                    reason = st.text_input("수정할 내용")
                    if st.button("요청 보내기") and reason:
                        report_manager_request(month, bid, opts[k], reason, user)
                        st.rerun()
        else:
            st.info("아직 지점 확인 단계가 아닙니다." if stage not in ("최종 대기", "최종 확정") else "확인이 끝났습니다.")
        return

    # ── 관리자 ───────────────────────────────────────────────────────────────
    problems, n_pub = report_auto_check(month, bid)
    c1, c2, c3 = st.columns(3)
    c1.metric("발행 건수", f"{n_pub}/20")
    c2.metric("자동 체크 문제", len(problems))
    c3.metric("열린 수정 요청", sum(i["status"] in ("접수됨", "처리 중") for i in issues))

    d = _df(rows, False)
    locked = bool(bm["report_locked"])
    st.markdown("##### 보고서 (최종본 편집은 관리자만)")
    ed = st.data_editor(d, hide_index=True, width="stretch", key=f"rp_ed_{bid}", disabled=locked or ["pub_id", "NO", "유형", "카페명", "카페링크", "카페 아이디", "제목"],
                        column_config={"pub_id": None, "카페침투 URL": st.column_config.LinkColumn("카페침투 URL")})
    if not locked and st.button("💾 최종본 편집 저장"):
        for r in ed.to_dict("records"):
            if r["pub_id"] and not pd.isna(r["pub_id"]):
                ex("UPDATE publications SET pub_date=?, url=?, views=? WHERE id=?",
                   (r["발행일"], r["카페침투 URL"], None if pd.isna(r["조회수"]) else int(r["조회수"]), int(r["pub_id"])))
        st.rerun()

    if problems:
        st.markdown("##### 자동 체크 (빈칸·형식·유형 매칭·중복·발행 건수)")
        sel = []
        for i, (r, reason) in enumerate(problems):
            if st.checkbox(f"{r['no']}번 — {reason}", value=True, key=f"pr_{bid}_{i}") and r["pub_id"]:
                sel.append((r["pub_id"], reason))
    if stage == "관리자 확인":
        c1, c2 = st.columns(2)
        if problems and c1.button("↩️ 체크한 행 사유 붙여 되돌리기", width="stretch"):
            report_admin_pass(month, bid, user, returns=sel)
            st.rerun()
        if c2.button("✅ 1차 확인 통과 → " + ("최종 대기(로컬)" if b["hospital"] == "로컬" else "지점 담당자 확인"),
                     type="primary", width="stretch"):
            report_admin_pass(month, bid, user)
            st.rerun()
    if stage == "최종 대기":
        if st.button("🔒 최종본 확정 (보고서 잠금)", type="primary"):
            report_finalize(month, bid, user)
            st.rerun()
    if locked and st.button("🔓 잠금 풀기"):
        ex("UPDATE branch_month SET report_locked=0, report_stage='최종 대기' WHERE month=? AND branch_id=?", (month, bid))
        st.rerun()
    if issues:
        with st.expander(f"수정 요청 기록 ({len(issues)}) — 참조"):
            st.dataframe(pd.DataFrame([{"출처": i["source"], "요청자": i["created_by"], "내용": i["reason"], "상태": i["status"],
                                        "요청일": i["created_at"], "반영일": i["resolved_at"]} for i in issues]),
                         hide_index=True, width="stretch")


def _make(user, month):
    st.caption("보고일에 버튼 하나로 병원별 보고서를 만듭니다. 탭: 한눈에 보기 / 카페 침투 보고서 / 댓글 침투 보고서 / 지점별. "
               "외부용은 실행사·카페 아이디 칸을 빼고, AS가 끝난 최종 링크만 넣습니다.")
    c1, c2 = st.columns(2)
    hosp = c1.selectbox("병원", HOSPITALS + ["전체"], key="mk_h")
    ver = c2.radio("버전", ["외부용", "내부용"], horizontal=True, key="mk_v")
    ext = ver == "외부용"
    sheets = build_report_sheets(month, hosp, ext)
    with st.expander("미리보기", expanded=True):
        tab = st.selectbox("탭", list(sheets), key="mk_tab")
        st.dataframe(sheets[tab], hide_index=True, width="stretch")
    title = f"{month_label(month)} {hosp} 보고서 ({ver})"
    c1, c2 = st.columns(2)
    data = to_excel(sheets)
    if c1.download_button("📥 엑셀로 받기", data, file_name=f"{title}.xlsx", width="stretch"):
        ex("INSERT INTO reports_generated(month,hospital,version,link,created_at,created_by) VALUES(?,?,?,?,?,?)",
           (month, hosp, ver, "(엑셀 다운로드)", now(), user["name"]))
    if gsheets_available():
        share = st.text_input("공유할 이메일 (쉼표)", key="mk_share")
        if c2.button("📊 [보고서 만들기] 구글 시트 생성", type="primary", width="stretch"):
            with st.spinner("구글 시트 만드는 중…"):
                url = push_gsheet(title, sheets, [s.strip() for s in share.split(",") if s.strip()])
            ex("INSERT INTO reports_generated(month,hospital,version,link,created_at,created_by) VALUES(?,?,?,?,?,?)",
               (month, hosp, ver, url, now(), user["name"]))
            st.success(f"만들었습니다: {url}")
    else:
        c2.info("구글 시트 연결 전 — README '구글 시트 연결'을 하면 여기서 바로 시트를 만듭니다.")
    hist = q("SELECT created_at 생성일, hospital 병원, version 버전, link 링크, created_by 만든사람 FROM reports_generated WHERE month=? ORDER BY id DESC", (month,))
    if hist:
        st.markdown("##### 만든 보고서 (월별 보관 — 로컬 지점은 이 링크를 원장님께 전달)")
        st.dataframe(pd.DataFrame(hist), hide_index=True, width="stretch",
                     column_config={"링크": st.column_config.LinkColumn()})
'''

# ============================================================================
# views.requests
# ============================================================================
MODULES['views.requests'] = r'''"""요청 접수: 클라이언트 요청을 접수하고 일정·담당자를 정한 뒤 진행 상태를 추적"""
import pandas as pd
import streamlit as st

from core.common import ADMIN, HOSPITALS, MANAGER, audit, notify, user_name, user_options
from core.db import ex, now, q


def render(ctx):
    user, role = ctx["user"], ctx["role"]
    st.title("📨 요청 접수")
    people = user_options()
    bs = {b["name"]: b["id"] for b in q("SELECT id,name FROM branches WHERE active=1 ORDER BY name")}
    with st.form("req_new"):
        c = st.columns(4)
        h = c[0].selectbox("병원", HOSPITALS)
        br = c[1].selectbox("지점", ["(전체)"] + list(bs))
        rcv = c[2].date_input("접수일")
        due = c[3].date_input("기한")
        content = st.text_area("요청 내용")
        who = st.selectbox("담당자", ["(미정)"] + list(people)) if role == ADMIN else "(미정)"
        if st.form_submit_button("접수"):
            ex("""INSERT INTO client_requests(hospital,branch_id,content,received,due,assignee_id,created_at,created_by)
                  VALUES(?,?,?,?,?,?,?,?)""", (h, bs.get(br), content, rcv.isoformat(), due.isoformat(), people.get(who), now(), user["name"]))
            if people.get(who):
                notify(people[who], "요청", f"요청이 접수되었습니다: {content[:40]}")
            audit(user["name"], "요청 접수", content[:80])
            st.rerun()
    rows = q("""SELECT r.*, b.name bname FROM client_requests r LEFT JOIN branches b ON b.id=r.branch_id
                ORDER BY CASE r.status WHEN '완료' THEN 1 ELSE 0 END, r.due""")
    if role == MANAGER:
        rows = [r for r in rows if r["assignee_id"] in (None, user["id"]) or r["created_by"] == user["name"]]
    if not rows:
        st.info("접수된 요청이 없습니다.")
        return
    df = pd.DataFrame([{"id": r["id"], "병원": r["hospital"], "지점": r["bname"], "내용": r["content"], "접수일": r["received"],
                        "기한": r["due"], "담당자": user_name(r["assignee_id"]), "상태": r["status"], "메모": r["note"]} for r in rows])
    ed = st.data_editor(df, hide_index=True, width="stretch", key="req_ed", disabled=["id", "병원", "지점", "접수일"],
                        column_config={"id": None,
                                       "담당자": st.column_config.SelectboxColumn("담당자", options=[""] + list(people)),
                                       "상태": st.column_config.SelectboxColumn("상태", options=["접수", "진행 중", "완료", "보류"])})
    if st.button("저장"):
        for r in ed.to_dict("records"):
            ex("UPDATE client_requests SET content=?, due=?, assignee_id=?, status=?, note=? WHERE id=?",
               (r["내용"], r["기한"], people.get(r["담당자"]), r["상태"], r["메모"], r["id"]))
        st.rerun()
'''

# ============================================================================
# views.settings
# ============================================================================
MODULES['views.settings'] = r'''"""설정·사용자·월 운영 (관리자)"""
import json
from datetime import date

import pandas as pd
import streamlit as st

from core.common import (DEFAULT_SETTINGS, ROLES, all_months, audit, get_setting, hash_pw, month_label, next_month,
                         set_setting)
from core.db import ex, now, q, q1
from core.ops import start_month

LABELS = {
    "cafe_repost_days": "같은 계정+같은 카페 발행 금지 일수", "comment_month_limit": "계정당 월 댓글 한도",
    "comment_warn_at": "댓글 주의 시작 개수", "comment_month_target": "월 댓글 목표",
    "deadline_warn_days": "마감 경고(초록) 시작 D-N", "as_days": "AS 처리 기한(일)", "report_fix_hours": "보고서 수정 요청 처리 기한(시간)",
    "publish_per_day": "하루 발행 지점 수", "default_dl_setting_day": "[다음 달 시작] 세팅 기한(일)",
    "default_dl_writing_day": "[다음 달 시작] 작성 기한(일)", "default_dl_publish_day": "[다음 달 시작] 발행 기한(일)",
    "as_comment_min": "댓글 N개 이하 → 댓글 작업 미완료", "as_view_min": "조회수 N 이하 → 조회수 부족",
    "as_view_after_days": "조회수 판단 시점(발행 후 N일)", "cafe_delete_rate_warn": "카페 삭제율 N% 넘으면 '주의'",
    "comment_max_chars": "댓글 최대 글자(공백 제외)", "dup_compare_months": "지난 원고 중복 비교 기간(개월)",
    "high_price": "고단가 기준(원)", "local_mom_min": "지역맘 부족 기준(개)", "image_slots": "원고당 이미지 칸 수",
    "image_keep_days": "사용 완료 이미지 보관(일)",
}


def render(ctx):
    user, month = ctx["user"], ctx["month"]
    st.title("⚙️ 설정·사용자")
    tabs = st.tabs(["📅 월 운영", "🔢 기준 숫자", "🧩 매칭·분류·금지어", "👤 사용자", "🗑️ 데이터"])

    with tabs[0]:
        months = all_months()
        nm = next_month(max(months)) if months else f"{date.today().year:04d}-{date.today().month:02d}"
        st.markdown(f"**[다음 달 시작]** — {month_label(nm)}: 지점·담당자·작가·원고 재료를 이월하고, 지점별 20건 틀을 새로 만듭니다. "
                    "보유장비는 지점에 붙어 있어 그대로 이어집니다.")
        y, m = map(int, nm.split("-"))
        c = st.columns(3)
        ds = c[0].date_input("세팅 기한", date(y, m, min(28, int(get_setting("default_dl_setting_day")))))
        dw = c[1].date_input("작성 기한", date(y, m, min(28, int(get_setting("default_dl_writing_day")))))
        dp = c[2].date_input("발행 기한", date(y, m, min(28, int(get_setting("default_dl_publish_day")))))
        if st.button(f"🔄 [다음 달 시작] {month_label(nm)}", type="primary"):
            n = start_month(nm, user["name"], {"setting": ds.isoformat(), "writing": dw.isoformat(), "publish": dp.isoformat()},
                            carry_from=max(months) if months else None)
            st.session_state.month = nm
            st.success(f"{n}개 지점 이월, 20건 틀을 만들었습니다.")
            st.rerun()
        st.caption("지점별로 다른 마감일은 '작가 배정·마감'에서 고칩니다.")

    with tabs[1]:
        vals = {}
        cols = st.columns(3)
        for i, (k, lab) in enumerate(LABELS.items()):
            v = get_setting(k)
            vals[k] = cols[i % 3].number_input(lab, value=float(v) if isinstance(v, float) else int(v),
                                               key=f"set_{k}", step=1 if not isinstance(v, float) else 0.05)
        th = st.slider("중복 문장 기준 (8글자 조각 겹침 비율)", 0.3, 1.0, float(get_setting("dup_threshold")), 0.05)
        hours = st.text_input("마감 당일 알림 시각 (쉼표)", ",".join(str(h) for h in get_setting("alert_hours")))
        kmin = get_setting("keyword_min")
        c = st.columns(3)
        km = {t: c[i].number_input(f"키워드 최소 횟수 · {t}", 0, 10, int(kmin.get(t, 1))) for i, t in enumerate(["정보성", "후기성", "슈퍼세트"])}
        f1 = st.checkbox("체험단 메뉴 보이기 (3단계)", value=bool(get_setting("feature_experience")))
        f2 = st.checkbox("요청 접수 메뉴 보이기", value=bool(get_setting("feature_requests")))
        if st.button("저장", type="primary", key="save_nums"):
            for k, v in vals.items():
                set_setting(k, v, user["name"])
            set_setting("dup_threshold", th, user["name"])
            set_setting("alert_hours", [int(x) for x in hours.split(",") if x.strip().isdigit()], user["name"])
            set_setting("keyword_min", km, user["name"])
            set_setting("feature_experience", f1, user["name"])
            set_setting("feature_requests", f2, user["name"])
            st.success("저장했습니다.")

    with tabs[2]:
        st.markdown("**병원별 매칭 규칙** — 원고 유형별로 쓸 수 있는 카페 유형 (JSON)")
        mr = st.text_area("매칭 규칙", json.dumps(get_setting("match_rules"), ensure_ascii=False, indent=1), height=260)
        cats = st.text_input("장비 분류 순서 (쉼표)", ", ".join(get_setting("equip_categories")))
        bw = st.text_area("추가 금지어 (줄바꿈) — 스킬 검수기 금지어에 더해서 검사", "\n".join(get_setting("extra_banned_words")))
        if st.button("저장", type="primary", key="save_rules"):
            try:
                set_setting("match_rules", json.loads(mr), user["name"])
            except json.JSONDecodeError as e:
                st.error(f"매칭 규칙 형식 오류: {e}")
                return
            set_setting("equip_categories", [c.strip() for c in cats.split(",") if c.strip()], user["name"])
            set_setting("extra_banned_words", [w.strip() for w in bw.splitlines() if w.strip()], user["name"])
            st.success("저장했습니다.")

    with tabs[3]:
        df = pd.DataFrame(q("SELECT id, username, name, role, active FROM users ORDER BY role, name"))
        df["active"] = df["active"].astype(bool)
        ed = st.data_editor(df, hide_index=True, width="stretch", key="users_ed", disabled=["id", "username"],
                            column_config={"id": None, "username": "아이디", "name": "이름",
                                           "role": st.column_config.SelectboxColumn("역할", options=ROLES), "active": "사용"})
        if st.button("사용자 저장"):
            for r in ed.to_dict("records"):
                ex("UPDATE users SET name=?, role=?, active=? WHERE id=?", (r["name"], r["role"], int(r["active"]), r["id"]))
            audit(user["name"], "사용자 수정", "")
            st.rerun()
        with st.form("new_user"):
            c = st.columns(4)
            un = c[0].text_input("아이디")
            nm_ = c[1].text_input("이름 (배정 시트 이름과 같게)")
            rl = c[2].selectbox("역할", ROLES)
            pw = c[3].text_input("비밀번호", type="password")
            if st.form_submit_button("계정 만들기"):
                if not (un and nm_ and pw):
                    st.error("모두 입력해 주세요.")
                elif q1("SELECT id FROM users WHERE username=?", (un,)):
                    st.error("이미 있는 아이디입니다.")
                else:
                    ex("INSERT INTO users(username,pw,name,role,created_at) VALUES(?,?,?,?,?)", (un, hash_pw(pw), nm_, rl, now()))
                    audit(user["name"], "계정 생성", f"{un} {nm_} {rl}")
                    st.success("만들었습니다.")
        with st.form("pw_reset"):
            c = st.columns(2)
            who = c[0].selectbox("비밀번호 바꿀 사람", [r["username"] for r in q("SELECT username FROM users ORDER BY username")])
            npw = c[1].text_input("새 비밀번호", type="password")
            if st.form_submit_button("변경") and npw:
                ex("UPDATE users SET pw=? WHERE username=?", (hash_pw(npw), who))
                audit(user["name"], "비밀번호 변경", who)
                st.success("변경했습니다.")

    with tabs[4]:
        st.warning("데모 데이터를 지우고 실제 운영을 시작할 때 씁니다. 사용자·설정은 남기고 나머지를 모두 지웁니다.")
        if st.checkbox("모든 업무 데이터를 지우는 것에 동의합니다") and st.button("업무 데이터 비우기"):
            for t in ["manuscripts", "ms_history", "publications", "report_issues", "comment_targets", "board_tasks", "issues",
                      "images", "notifications", "client_requests", "reports_generated", "branch_month", "months",
                      "branch_equipment", "cafe_links", "cafe_log", "cafes", "accounts", "account_log", "branch_aliases",
                      "branches", "equip_std"]:
                ex(f"DELETE FROM {t}")
            audit(user["name"], "업무 데이터 비우기", "")
            st.session_state.pop("month", None)
            st.success("비웠습니다. 지점·장비·카페를 '기존 시트 불러오기'로 가져오세요.")
'''

# ============================================================================
# views.single
# ============================================================================
MODULES['views.single'] = r'''"""단건 작성: 카페 상위노출 원고(지점 요청 건), 이미지 캡션 글, 질문글, 의료 후기 — 시트 없이 입력하고 결과를 복사."""
import streamlit as st

from core import ai
from core.common import audit
from core.db import q

GUIDE = {
    "카페 상위노출 원고": ("uandi-wongo", "지점·키워드·장비·특이사항을 적어 주세요. 예) 건대점 / 건대 울쎄라 / 울쎄라피 프라임 / 정보성 1건"),
    "이미지 캡션 글": ("cafe-image-caption", "블로그 원문을 붙이고 키워드·글자수(공백 포함/제외)·키워드 개수를 적어 주세요."),
    "질문글": ("naver-cafe-question", "어떤 카페에 어떤 상황으로 묻는 글인지 적어 주세요."),
    "의료 후기": ("naver-cafe-medical-review", "어느 병원에서 무슨 시술을 받았고 어땠는지 적어 주세요."),
}


def render(ctx):
    user = ctx["user"]
    st.title("📝 단건 작성")
    st.caption("시트 없이 필요할 때 바로 씁니다. 스킬을 그대로 불러 작성하고, 결과는 복사해서 쓰면 됩니다.")
    kind = st.selectbox("작성 유형", list(GUIDE))
    skill, hint = GUIDE[kind]
    st.caption(f"연결 스킬: `{skill}`")
    c1, c2 = st.columns(2)
    branch = c1.selectbox("지점 (선택)", ["(없음)"] + [b["name"] for b in q("SELECT name FROM branches WHERE active=1 ORDER BY name")])
    kw = c2.text_input("주요 키워드", placeholder="예: 건대 인모드")
    prompt = st.text_area("요청 내용", height=180, placeholder=hint)
    if st.button("🚀 작성하기", type="primary"):
        if not (kw or prompt):
            st.warning("키워드나 요청 내용을 입력해 주세요.")
            return
        full = f"지점: {branch}\n키워드: {kw}\n\n{prompt}"
        if not ai.available():
            st.warning("Claude API 키가 없어 AI 작성은 꺼져 있습니다. README의 'AI 연결'을 참고해 키를 넣어 주세요.")
            return
        with st.spinner("작성 중…"):
            try:
                out = ai.single(kind, full)
            except Exception as e:
                st.error(f"AI 호출 실패: {e}")
                return
        st.session_state.single_out = out
        audit(user["name"], "단건 작성", f"{kind} {branch} {kw}")
    if st.session_state.get("single_out"):
        st.text_area("결과 (복사해서 사용)", st.session_state.single_out, height=380)
        st.code(st.session_state.single_out, language=None)
'''

# ============================================================================
# views.sync
# ============================================================================
MODULES['views.sync'] = r'''"""지점 담당자 자동 배정: 포스팅 담당자 배정 시트(월별 탭)를 읽어 변경점을 먼저 보여주고 승인하면 적용"""
import pandas as pd
import streamlit as st

from core.common import month_label, norm_name
from core.db import ex, q
from core.ops import apply_assignment, assignment_diff
from core.sheets import parse_assignment_sheet


def render(ctx):
    user, month = ctx["user"], ctx["month"]
    st.title("👥 담당자 배정 동기화")
    st.caption("배정 시트 파일(엑셀로 내려받은 것)을 올리고 월 탭(예: 2026.10)을 고르면 '지점명'과 '블로그 포스팅'(8월까지는 '사수') 칸을 "
               "칸 이름으로 읽습니다. 유앤아이·블루비뇨 행만 읽고 로컬은 빼요. 지난달과 달라진 점을 먼저 보여주고, 승인하면 적용합니다.")
    up = st.file_uploader("배정 시트 (.xlsx)", type=["xlsx"])
    if not up:
        return
    xl = pd.ExcelFile(up)
    y, m = month.split("-")
    guess = next((s for s in xl.sheet_names if s.replace(" ", "") in (f"{y}.{int(m)}", f"{y}.{m}")), xl.sheet_names[0])
    sheet = st.selectbox("탭", xl.sheet_names, index=xl.sheet_names.index(guess))
    try:
        parsed, cols = parse_assignment_sheet(up, sheet)
    except ValueError as e:
        st.error(str(e))
        return
    st.caption(f"읽은 칸: {cols} · {len(parsed)}행")
    diffs = assignment_diff(month, parsed)
    df = pd.DataFrame(diffs)
    unmatched = df[df["branch_id"].isna()]
    if len(unmatched):
        st.warning(f"프로그램 지점과 이어지지 않은 이름 {len(unmatched)}개 — 아래에서 대응표를 만들어 주세요.")
        bs = {b["name"]: b["id"] for b in q("SELECT id,name FROM branches WHERE active=1 ORDER BY name")}
        for i, r in unmatched.iterrows():
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(r["배정 시트 지점명"])
            pick = c2.selectbox("지점", ["(건너뛰기)"] + list(bs), key=f"map_{i}", label_visibility="collapsed")
            if c3.button("대응 저장", key=f"mapb_{i}") and pick != "(건너뛰기)":
                ex("INSERT OR REPLACE INTO branch_aliases(alias,branch_id) VALUES(?,?)", (norm_name(r["배정 시트 지점명"]), bs[pick]))
                st.rerun()
    ch = df[df["변경"]]
    st.markdown(f"#### {month_label(month)} 변경 {len(ch)}건")
    if len(ch):
        st.dataframe(ch[["프로그램 지점", "현재 담당", "새 담당", "계정 없음"]].assign(
            변경=lambda d: d["현재 담당"].fillna("") + " → " + d["새 담당"]), hide_index=True, width="stretch")
        if ch["계정 없음"].any():
            st.error("계정이 없는 사람: " + ", ".join(ch[ch["계정 없음"]]["새 담당"]) + " — 적용하면 관리자에게 계정 생성 알림이 갑니다.")
        if st.checkbox("확정된 배정을 공유받았고, 위 변경을 적용합니다"):
            if st.button("✅ 적용", type="primary"):
                n = apply_assignment(month, diffs, user)
                st.success(f"{n}건 반영했습니다. 바뀐 지점의 남은 할 일과 알림은 새 담당자에게 넘어갑니다.")
    else:
        st.success("달라진 점이 없습니다.")
    with st.expander("읽은 전체 행"):
        st.dataframe(df.drop(columns=["branch_id", "user_id"]), hide_index=True, width="stretch")
'''


def _load_modules():
    for pkg in ("core", "views", "rules"):
        m = types.ModuleType(pkg)
        m.__path__ = []
        sys.modules[pkg] = m
    for name, src in MODULES.items():
        pkg, sub = name.split(".")
        mod = types.ModuleType(name)
        mod.__file__ = os.path.join(_BASE, pkg, sub + ".py")   # 경로 계산용 (실제 파일은 없어도 됨)
        mod.__package__ = pkg
        sys.modules[name] = mod
        setattr(sys.modules[pkg], sub, mod)
        exec(compile(src, f"<{name}>", "exec"), mod.__dict__)


_load_modules()

# =============================================================================
# 화면 시작점 (원래 app.py)
# =============================================================================

import streamlit as st

from core.common import (ADMIN, BOARD, EXEC, MANAGER, WRITER, all_months, check_pw, get_setting,
                         month_label)
from core.db import init_db, q, q1, qv
from core.ops import deadline_sweep
from core.seed import seed

st.set_page_config(page_title="마케팅 통합 관리", page_icon="🚀", layout="wide")


@st.cache_resource
def _boot():
    init_db()
    seed()
    return True


_boot()

st.markdown("""
<style>
mark {background:#fff2a8; padding:0 2px; border-radius:3px;}
.card {border:1px solid rgba(128,128,128,.35); border-radius:10px; padding:10px 14px; margin-bottom:8px;}
.cafe-post {border:1px solid rgba(128,128,128,.35); border-radius:10px; padding:16px; background:rgba(128,128,128,.05);}
.cafe-post h4 {margin:0 0 8px 0;}
.cmt {margin:6px 0 0 0; padding:6px 10px; border-left:3px solid #9ec5fe;}
.rpl {margin:4px 0 0 28px; padding:6px 10px; border-left:3px solid #c3e6cb;}
.small {font-size:.85em; opacity:.8;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 테스트 모드: 로그인 없이 사이드바에서 사람(역할)을 골라 바로 접속
# (운영 전환 시 계정별 로그인을 다시 붙이면 됩니다)
# ─────────────────────────────────────────────────────────────────────────────
_people = q("SELECT id, username, name, role FROM users WHERE active=1 ORDER BY CASE role "
            "WHEN '관리자' THEN 0 WHEN '지점 담당자' THEN 1 WHEN '원고 작가' THEN 2 WHEN '게시판 담당' THEN 3 ELSE 4 END, name")
_labels = [f"{p['role']} · {p['name']}" for p in _people]
_cur = st.session_state.get("user")
_idx = next((i for i, p in enumerate(_people) if _cur and p["id"] == _cur["id"]), 0)
st.sidebar.markdown("🧪 **테스트 모드** — 접속할 사람 선택")
_pick = st.sidebar.selectbox("접속 역할", _labels, index=_idx, key="test_user", label_visibility="collapsed")
_sel = _people[_labels.index(_pick)]
if not _cur or _cur["id"] != _sel["id"]:
    st.session_state.user = dict(_sel)
    st.session_state.pop("menu", None)

user = st.session_state.user
role = user["role"]

# ─────────────────────────────────────────────────────────────────────────────
# 메뉴 (역할별)
# ─────────────────────────────────────────────────────────────────────────────
MENUS = [
    ("home", "🏠 홈", [ADMIN, MANAGER, WRITER, BOARD, EXEC]),
    ("board", "📋 원고 보드", [ADMIN, MANAGER, WRITER, EXEC]),
    ("assign", "🗓️ 작가 배정·마감", [ADMIN]),
    ("single", "📝 단건 작성", [ADMIN, WRITER, EXEC]),
    ("publish", "🚀 발행·운영", [ADMIN, EXEC]),
    ("boardtask", "📌 게시판 업로드", [ADMIN, BOARD]),
    ("comments", "💬 댓글 침투", [ADMIN, EXEC]),
    ("report", "📊 보고서", [ADMIN, MANAGER, EXEC]),
    ("images", "🎨 AI 이미지 보관함", [ADMIN]),
    ("requests", "📨 요청 접수", [ADMIN, MANAGER]),
    ("experience", "🧪 체험단", [ADMIN]),
    ("branch", "🏢 지점·보유장비", [ADMIN, MANAGER, WRITER, EXEC]),
    ("cafe", "☕ 카페 목록", [ADMIN, EXEC]),
    ("sync", "👥 담당자 배정 동기화", [ADMIN]),
    ("import", "📥 기존 시트 불러오기", [ADMIN]),
    ("settings", "⚙️ 설정·사용자", [ADMIN]),
    ("audit", "🧾 변경 이력", [ADMIN]),
]
if not get_setting("feature_experience"):
    MENUS = [m for m in MENUS if m[0] != "experience"]
if not get_setting("feature_requests"):
    MENUS = [m for m in MENUS if m[0] != "requests"]
allowed = [m for m in MENUS if role in m[2]]
keys = [m[0] for m in allowed]
if st.session_state.get("menu") not in keys + ["notices"]:
    st.session_state.menu = keys[0]

# ── 사이드바 ────────────────────────────────────────────────────────────────
sb = st.sidebar
sb.markdown(f"### 👤 {user['name']}  \n<span class='small'>{role}</span>", unsafe_allow_html=True)

months = all_months()
if not months:
    from datetime import date
    from core.ops import start_month
    start_month(f"{date.today().year:04d}-{date.today().month:02d}", "system")
    months = all_months()
if st.session_state.get("month") not in months:
    st.session_state.month = months[0]
st.session_state.month = sb.selectbox("📅 운영 월", months, index=months.index(st.session_state.month),
                                      format_func=month_label)
month = st.session_state.month

deadline_sweep(month)
unread = qv("SELECT COUNT(*) FROM notifications WHERE user_id=? AND read=0", (user["id"],), 0)
if sb.button(f"🔔 알림 {unread}건" if unread else "🔔 알림", width="stretch",
             type="primary" if st.session_state.menu == "notices" else "secondary"):
    st.session_state.menu = "notices"
    st.rerun()

st.session_state.mine_only = sb.toggle("🙋 내 담당만 보기", value=st.session_state.get("mine_only", role in (MANAGER, WRITER)))
sb.markdown("---")
for key, label, _ in allowed:
    if sb.button(label, key=f"m_{key}", width="stretch",
                 type="primary" if st.session_state.menu == key else "secondary"):
        st.session_state.menu = key
        for k in ("home_filter", "home_card", "eq_branch"):
            st.session_state.pop(k, None)
        st.rerun()
sb.markdown("---")
sb.caption("마케팅 통합 관리 v3.0")

# ─────────────────────────────────────────────────────────────────────────────
# 화면
# ─────────────────────────────────────────────────────────────────────────────
ctx = {"user": user, "role": role, "month": month, "mine": st.session_state.mine_only}
page = st.session_state.menu

if page == "home":
    from views.home import render
elif page == "notices":
    from views.notices import render
elif page == "board":
    from views.board import render
elif page == "assign":
    from views.assign import render
elif page == "single":
    from views.single import render
elif page == "publish":
    from views.publish import render
elif page == "boardtask":
    from views.boardtask import render
elif page == "comments":
    from views.comments import render
elif page == "report":
    from views.report import render
elif page == "images":
    from views.images import render
elif page == "requests":
    from views.requests import render
elif page == "experience":
    from views.experience import render
elif page == "branch":
    from views.branch import render
elif page == "cafe":
    from views.cafe import render
elif page == "sync":
    from views.sync import render
elif page == "import":
    from views.importer import render
elif page == "settings":
    from views.settings import render
elif page == "audit":
    from views.audit import render
render(ctx)
