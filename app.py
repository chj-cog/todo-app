"""내 컴퓨터에서 도는 Todo 앱 (Streamlit + SQLite)

실행: py -m streamlit run app.py
"""
import calendar
import html
import os
import sqlite3
from contextlib import closing
from datetime import date, datetime, timedelta, timezone

import streamlit as st
from dotenv import load_dotenv

# .env 파일에서 설정값을 읽어 옵니다. (없으면 기본값 todo.db)
load_dotenv()
DB_PATH = os.getenv("DB_PATH", "todo.db")

# 서버가 어느 나라에 있든 한국 시간 기준으로 '오늘'을 계산합니다.
KST = timezone(timedelta(hours=9))

# 카테고리별 색 (이름에 따라 항상 같은 색이 붙어요)
PALETTE = ["#8B5CF6", "#22D3EE", "#F472B6", "#34D399", "#FBBF24", "#60A5FA", "#FB7185"]


def today_kst():
    return datetime.now(KST).date()


def category_color(name):
    return PALETTE[sum(map(ord, name)) % len(PALETTE)]


# ---------- DB(저장소) ----------
def run(sql, params=()):
    """SQL 한 줄을 실행하고, 결과 행을 돌려줍니다. 연결은 매번 깔끔하게 닫아요."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        with conn:  # 성공하면 저장(commit), 실패하면 되돌리기(rollback)
            return conn.execute(sql, params).fetchall()


def init_db():
    run(
        """
        CREATE TABLE IF NOT EXISTS todos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            title     TEXT    NOT NULL,
            done      INTEGER NOT NULL DEFAULT 0,
            due_date  TEXT,
            category  TEXT    NOT NULL DEFAULT '일반'
        )
        """
    )


# Create: 할 일 추가
def add_todo(title, due_date, category):
    run(
        "INSERT INTO todos (title, due_date, category) VALUES (?, ?, ?)",
        (title, due_date, category),
    )


# Read: 목록 보기
def list_todos():
    # 안 끝난 일 먼저, 그다음 마감일 빠른 순 (마감일 없는 건 뒤로)
    return run("SELECT * FROM todos ORDER BY done, due_date IS NULL, due_date, id")


# Update: 완료 표시
def set_done(todo_id, done):
    run("UPDATE todos SET done = ? WHERE id = ?", (int(done), todo_id))


# Delete: 삭제
def delete_todo(todo_id):
    run("DELETE FROM todos WHERE id = ?", (todo_id,))


# ---------- 구글 캘린더용 .ics 파일 만들기 ----------
def ics_escape(text):
    return (
        text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    )


def ics_fold(line):
    """캘린더 파일 규칙: 한 줄은 75바이트까지, 넘으면 다음 줄을 공백으로 시작해 이어 써요."""
    out, cur = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        if len(cur) + len(b) > (75 if not out else 74):
            out.append(cur.decode("utf-8"))
            cur = b""
        cur += b
    out.append(cur.decode("utf-8"))
    return "\r\n ".join(out)


def build_ics(todos):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//kwkworks//todo-app//KO",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:나의 Todo",
    ]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for t in todos:
        if not t["due_date"]:
            continue  # 마감일이 없는 일은 달력에 넣을 날짜가 없어요
        start = datetime.strptime(t["due_date"], "%Y-%m-%d").date()
        title = ("✓ " if t["done"] else "") + t["title"]
        lines += [
            "BEGIN:VEVENT",
            f"UID:todo-{t['id']}@kwkworks-todo",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{start:%Y%m%d}",
            f"DTEND;VALUE=DATE:{start + timedelta(days=1):%Y%m%d}",
            f"SUMMARY:{ics_escape(title)}",
            f"CATEGORIES:{ics_escape(t['category'])}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(ics_fold(line) for line in lines) + "\r\n"


# ---------- 디자인 ----------
CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css');
html, body, [class*="st-"]:not([data-testid="stIconMaterial"]), button, input, textarea {
    font-family: 'Pretendard Variable', Pretendard, -apple-system, sans-serif !important;
}
.block-container { max-width: 880px; padding-top: 3rem; }
header[data-testid="stHeader"] { background: transparent; }

.app-title { font-size: 1.9rem !important; font-weight: 700; letter-spacing: -0.03em; line-height: 1.2; }
.app-sub   { color: #8B8FA3; font-size: 0.95rem; margin: 0.2rem 0 1.4rem; }

.stats { display: flex; gap: 0.6rem; margin-bottom: 1.6rem; flex-wrap: wrap; }
.stat  { flex: 1; min-width: 120px; background: #14161F; border: 1px solid #23263A;
         border-radius: 14px; padding: 0.9rem 1rem; }
.stat b    { display: block; font-size: 1.5rem; font-weight: 700; letter-spacing: -0.02em; }
.stat span { color: #8B8FA3; font-size: 0.8rem; }

.todo-title       { font-size: 0.98rem; font-weight: 500; }
.todo-title.done  { color: #5A5E70; text-decoration: line-through; }
.chip { display: inline-block; font-size: 0.72rem; padding: 2px 9px; border-radius: 999px;
        margin-right: 6px; border: 1px solid; }
.due      { color: #8B8FA3; font-size: 0.78rem; }
.due.today { color: #FBBF24; }
.due.late  { color: #F87171; }

[data-testid="stVerticalBlockBorderWrapper"] { border-color: #23263A !important; border-radius: 14px !important; }
.stTabs [data-baseweb="tab-list"] { gap: 0.4rem; }
.stTabs [data-baseweb="tab"] { padding: 0.4rem 0.9rem; border-radius: 10px; }

/* 달력 */
.cal-title { text-align: center; font-size: 1.15rem; font-weight: 700; letter-spacing: -0.02em; margin-top: 0.35rem; }
.cal { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; margin-top: 0.6rem; }
.cal-head { text-align: center; color: #8B8FA3; font-size: 0.75rem; padding: 0.3rem 0; }
.cal-head.sun { color: #F87171; } .cal-head.sat { color: #60A5FA; }
.cal-day { min-height: 92px; background: #11131B; border: 1px solid #1C1F2C; border-radius: 10px;
           padding: 6px; overflow: hidden; }
.cal-day.other { opacity: 0.35; }
.cal-day.today { border-color: #8B5CF6; background: rgba(139,92,246,0.10); }
.cal-num { font-size: 0.75rem; color: #8B8FA3; margin-bottom: 4px; }
.cal-day.today .cal-num { color: #C4B5FD; font-weight: 700; }
.cal-ev { font-size: 0.72rem; border-radius: 5px; padding: 1px 5px; margin-bottom: 3px;
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #0B0D14; font-weight: 600; }
.cal-ev.done { opacity: 0.4; text-decoration: line-through; }
.cal-more { font-size: 0.7rem; color: #8B8FA3; }

/* 휴대폰에서도 달력 이동 버튼은 한 줄로 */
.st-key-cal_nav [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0.4rem; }
.st-key-cal_nav [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }
.st-key-cal_nav [data-testid="stColumn"]:nth-child(3) { flex: 4 1 0 !important; }
.st-key-cal_nav [data-testid="stColumn"]:nth-child(4) { flex: 1.6 1 0 !important; }
.st-key-cal_nav button { padding-left: 0.3rem; padding-right: 0.3rem; white-space: nowrap; }
@media (max-width: 640px) {
    .cal { gap: 2px; }
    .cal-day { min-height: 64px; padding: 3px; border-radius: 6px; }
    .cal-ev { font-size: 0.6rem; padding: 0 3px; }
}
</style>
"""


def month_grid_html(year, month, todos, today):
    """한 달 달력을 HTML로 그립니다. (일요일 시작)"""
    by_day = {}
    for t in todos:
        if t["due_date"]:
            by_day.setdefault(t["due_date"], []).append(t)

    cells = [
        f'<div class="cal-head{cls}">{name}</div>'
        for name, cls in zip("일월화수목금토", [" sun", "", "", "", "", "", " sat"])
    ]
    for week in calendar.Calendar(firstweekday=6).monthdatescalendar(year, month):
        for d in week:
            cls = "cal-day"
            if d.month != month:
                cls += " other"
            if d == today:
                cls += " today"
            items = by_day.get(d.isoformat(), [])
            evs = "".join(
                f'<div class="cal-ev{" done" if t["done"] else ""}" '
                f'style="background:{category_color(t["category"])}" title="{html.escape(t["title"])}">'
                f"{html.escape(t['title'])}</div>"
                for t in items[:3]
            )
            if len(items) > 3:
                evs += f'<div class="cal-more">+{len(items) - 3}개 더</div>'
            cells.append(f'<div class="{cls}"><div class="cal-num">{d.day}</div>{evs}</div>')
    return f'<div class="cal">{"".join(cells)}</div>'


# ---------- 화면 ----------
init_db()
st.set_page_config(page_title="나의 Todo", page_icon="✅", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)

today = today_kst()
todos = list_todos()
today_str = today.isoformat()

open_todos = [t for t in todos if not t["done"]]
due_today = [t for t in open_todos if t["due_date"] == today_str]
overdue = [t for t in open_todos if t["due_date"] and t["due_date"] < today_str]

st.markdown(
    f"""
    <div class="app-title">나의 Todo</div>
    <div class="app-sub">{today:%Y년 %m월 %d일} · 오늘도 하나씩 끝내 봐요</div>
    <div class="stats">
        <div class="stat"><b>{len(open_todos)}</b><span>남은 일</span></div>
        <div class="stat"><b style="color:#FBBF24">{len(due_today)}</b><span>오늘 마감</span></div>
        <div class="stat"><b style="color:#F87171">{len(overdue)}</b><span>기한 지남</span></div>
        <div class="stat"><b style="color:#34D399">{len(todos) - len(open_todos)}</b><span>완료</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# 인터넷(streamlit.app)에서 열었을 때만 시연용 안내를 보여 줘요.
if st.context.headers.get("Host", "").endswith("streamlit.app"):
    st.caption("ℹ️ 시연용 앱이에요. 방문자 모두가 같은 목록을 쓰고, 서버가 다시 시작되면 데이터가 초기화될 수 있어요.")

# 1) 할 일 추가
with st.form("add_form", clear_on_submit=True, border=True):
    c1, c2, c3 = st.columns([5, 2.2, 2])
    title = c1.text_input("할 일", placeholder="무엇을 해야 하나요?", max_chars=100)
    due = c2.date_input("마감일 (선택)", value=None, format="YYYY-MM-DD")
    category = c3.text_input("카테고리", value="일반", max_chars=20)
    if st.form_submit_button("추가하기", type="primary", use_container_width=True):
        if title.strip():
            add_todo(
                title.strip(),
                due.isoformat() if due else None,
                category.strip() or "일반",
            )
            st.rerun()
        else:
            st.warning("할 일을 입력해 주세요.")

tab_cal, tab_list = st.tabs(["📅  캘린더", "☰  목록"])

# 2) 캘린더 보기
with tab_cal:
    # 지금 보고 있는 달 (처음에는 이번 달)
    if "cal_month" not in st.session_state:
        st.session_state.cal_month = today.replace(day=1)
    shown_month = st.session_state.cal_month

    def move_month(step):
        m = st.session_state.cal_month
        idx = m.year * 12 + (m.month - 1) + step
        st.session_state.cal_month = date(idx // 12, idx % 12 + 1, 1)

    nav = st.container(key="cal_nav")
    n1, n2, n3, n4 = nav.columns([0.6, 0.6, 5, 1], vertical_alignment="center")
    n1.button("‹", on_click=move_month, args=(-1,), use_container_width=True)
    n2.button("›", on_click=move_month, args=(1,), use_container_width=True)
    n3.markdown(f'<div class="cal-title">{shown_month:%Y년 %m월}</div>', unsafe_allow_html=True)
    n4.button(
        "오늘",
        on_click=lambda: st.session_state.update(cal_month=today.replace(day=1)),
        use_container_width=True,
    )

    st.markdown(
        month_grid_html(shown_month.year, shown_month.month, todos, today),
        unsafe_allow_html=True,
    )
    st.caption("완료 표시와 삭제는 목록 탭에서 할 수 있어요. 마감일이 없는 일도 목록 탭에 있어요.")

# 3) 목록 보기
with tab_list:
    categories = sorted({t["category"] for t in todos})
    f1, f2 = st.columns([4, 1.4])
    choice = f1.pills("카테고리", ["전체"] + categories, default="전체", label_visibility="collapsed")
    hide_done = f2.toggle("완료 숨기기")

    shown = [
        t
        for t in todos
        if (choice in (None, "전체") or t["category"] == choice) and not (hide_done and t["done"])
    ]
    if not shown:
        st.caption("표시할 할 일이 없어요.")

    for t in shown:
        with st.container(border=True):
            c_check, c_text, c_del = st.columns([0.5, 8, 0.8], vertical_alignment="center")
            c_check.checkbox(
                "완료",
                value=bool(t["done"]),
                key=f"done_{t['id']}",
                label_visibility="collapsed",
                on_change=lambda i=t["id"]: set_done(i, st.session_state[f"done_{i}"]),
            )

            color = category_color(t["category"])
            chip = (
                f'<span class="chip" style="color:{color};border-color:{color}55">'
                f"{html.escape(t['category'])}</span>"
            )
            due_html = ""
            if t["due_date"]:
                if not t["done"] and t["due_date"] < today_str:
                    due_html = f'<span class="due late">{t["due_date"]} · 지남</span>'
                elif not t["done"] and t["due_date"] == today_str:
                    due_html = f'<span class="due today">{t["due_date"]} · 오늘</span>'
                else:
                    due_html = f'<span class="due">{t["due_date"]}</span>'
            done_cls = " done" if t["done"] else ""
            c_text.markdown(
                f'<div class="todo-title{done_cls}">{html.escape(t["title"])}</div>'
                f"<div>{chip}{due_html}</div>",
                unsafe_allow_html=True,
            )

            # 4) 삭제 (실수로 지우지 않게 한 번 더 확인)
            with c_del.popover("⋯"):
                st.caption("이 할 일을 삭제할까요?")
                if st.button("삭제", key=f"del_{t['id']}", type="primary"):
                    delete_todo(t["id"])
                    st.rerun()

# 5) 구글 캘린더로 내보내기
st.write("")
with st.expander("📤  구글 캘린더로 내보내기"):
    st.download_button(
        "캘린더 파일(.ics) 받기",
        data=build_ics(todos).encode("utf-8"),
        file_name="my-todo.ics",
        mime="text/calendar",
        use_container_width=True,
    )
    st.markdown(
        "1. 위 버튼으로 `my-todo.ics` 파일을 받아요.\n"
        "2. [구글 캘린더 가져오기 화면](https://calendar.google.com/calendar/r/settings/export)을 열어요.\n"
        "3. **컴퓨터에서 파일 선택** → `my-todo.ics` → **가져오기**를 누르면 끝!\n\n"
        "마감일이 있는 할 일만 들어가요. 할 일을 바꾼 뒤에는 파일을 새로 받아 다시 가져오면 돼요."
    )
