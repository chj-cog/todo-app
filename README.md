# ✅ 나의 Todo 앱

내 컴퓨터에서 실행하는 할 일 관리 앱입니다.

👉 **바로 써 보기: https://kwkworks-todo.streamlit.app**
(무료 서버라 데이터는 모두가 함께 쓰고, 서버가 다시 시작되면 초기화될 수 있어요.)

## 기능
- **기본(CRUD)**: 할 일 추가 / 목록 보기 / 완료 표시 / 삭제
- **추가 기능 1. 마감일 표시**: 오늘 마감은 주황색, 기한이 지난 일은 빨간색으로 보여요.
- **추가 기능 2. 카테고리(태그)**: 할 일마다 카테고리를 붙이고, 카테고리별로 골라 볼 수 있어요.

## 사용한 도구 (모두 무료)
| 도구 | 역할 |
|---|---|
| Python | 프로그래밍 언어 |
| Streamlit | 파이썬만으로 웹 화면을 만드는 라이브러리 |
| SQLite | 파일 하나(`todo.db`)로 된 무료 DB. 껐다 켜도 데이터가 남아요. |
| python-dotenv | `.env` 파일의 설정값을 읽어 와요. |

## DB 구조 (`todos` 테이블)
| 열 | 종류 | 설명 |
|---|---|---|
| id | INTEGER (자동 증가) | 고유 번호 |
| title | TEXT (필수) | 할 일 내용 |
| done | INTEGER (0/1) | 완료 여부 |
| due_date | TEXT (비워도 됨) | 마감일 (YYYY-MM-DD) |
| category | TEXT (기본값 '일반') | 카테고리 |

## 실행 방법 (Windows)
```bash
py -m pip install -r requirements.txt
copy .env.example .env
py -m streamlit run app.py
```
브라우저에서 http://localhost:8501 이 자동으로 열려요.

## 비밀값 관리
- 설정값은 코드에 직접 쓰지 않고 `.env` 파일에 둡니다.
- `.env`와 `todo.db`는 `.gitignore`에 넣어서 GitHub에 올라가지 않아요. 공유용으로는 `.env.example`만 올립니다.
