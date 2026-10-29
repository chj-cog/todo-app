"""내 컴퓨터에서 도는 Todo 앱 (Streamlit + SQLite)

실행: streamlit run app.py
"""
import os
import sqlite3
from datetime import date

import streamlit as st
from dotenv import load_dotenv

# .env 파일에서 설정값을 읽어 옵니다. (없으면 기본값 todo.db)
load_dotenv()
DB_PATH = os.getenv("DB_PATH", "todo.db")


# ---------- DB(저장소) ----------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute(
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
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO todos (title, due_date, category) VALUES (?, ?, ?)",
            (title, due_date, category),
        )


# Read: 목록 보기
def list_todos(category=None):
    sql = "SELECT * FROM todos"
    params = ()
    if category:
        sql += " WHERE category = ?"
        params = (category,)
    # 안 끝난 일 먼저, 그다음 마감일 빠른 순 (마감일 없는 건 뒤로)
    sql += " ORDER BY done, due_date IS NULL, due_date, id"
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def list_categories():
    with get_conn() as conn:
        rows = conn.execute("SELECT DISTINCT category FROM todos ORDER BY category").fetchall()
    return [r["category"] for r in rows]


# Update: 완료 표시
def set_done(todo_id, done):
    with get_conn() as conn:
        conn.execute("UPDATE todos SET done = ? WHERE id = ?", (int(done), todo_id))


# Delete: 삭제
def delete_todo(todo_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))


# ---------- 화면 ----------
init_db()
st.set_page_config(page_title="나의 Todo", page_icon="✅")
st.title("✅ 나의 Todo")

# 1) 할 일 추가
with st.form("add_form", clear_on_submit=True):
    title = st.text_input("할 일", placeholder="예: 과제 제출하기")
    col1, col2 = st.columns(2)
    with col1:
        has_due = st.checkbox("마감일 정하기")
        due = st.date_input("마감일", value=date.today())
    with col2:
        category = st.text_input("카테고리", value="일반")
    if st.form_submit_button("추가", type="primary"):
        if title.strip():
            add_todo(
                title.strip(),
                due.isoformat() if has_due else None,
                category.strip() or "일반",
            )
            st.success("추가했어요!")
        else:
            st.warning("할 일을 입력해 주세요.")

st.divider()

# 2) 카테고리로 걸러 보기
choice = st.selectbox("카테고리별 보기", ["전체"] + list_categories())
todos = list_todos(None if choice == "전체" else choice)

if not todos:
    st.info("할 일이 없어요. 위에서 추가해 보세요!")

today = date.today().isoformat()
for t in todos:
    c_check, c_text, c_del = st.columns([1, 8, 1])

    # 3) 완료 표시 (체크하면 바로 DB에 저장)
    c_check.checkbox(
        "완료",
        value=bool(t["done"]),
        key=f"done_{t['id']}",
        label_visibility="collapsed",
        on_change=lambda i=t["id"]: set_done(i, st.session_state[f"done_{i}"]),
    )

    text = f"~~{t['title']}~~" if t["done"] else f"**{t['title']}**"
    tag = f"`#{t['category']}`"
    if t["due_date"]:
        if not t["done"] and t["due_date"] < today:
            due_text = f":red[📅 {t['due_date']} (지남)]"
        elif not t["done"] and t["due_date"] == today:
            due_text = f":orange[📅 {t['due_date']} (오늘)]"
        else:
            due_text = f"📅 {t['due_date']}"
    else:
        due_text = ""
    c_text.markdown(f"{text}  {tag}  {due_text}")

    # 4) 삭제
    if c_del.button("🗑️", key=f"del_{t['id']}", help="삭제"):
        delete_todo(t["id"])
        st.rerun()
