from openai import OpenAI  # OpenAI API 클라이언트 라이브러리
import streamlit as st  # Streamlit 라이브러리 (웹 애플리케이션 제작)
from dotenv import load_dotenv  # 환경 변수 로드
import os  # OS 라이브러리 (환경 변수 접근)
import shelve  # Key-Value 데이터 저장 라이브러리

# 환경 변수 로드 (.env 파일에서 OPENAI_API_KEY 읽기)
load_dotenv()

# Streamlit 애플리케이션 제목 설정
st.title("Streamlit Chatbot Interface")

# 사용자와 봇의 아바타 설정 (UI에 표시될 이모지)
USER_AVATAR = "👤"
BOT_AVATAR = "🤖"

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # 환경 변수에서 API 키 가져옴

# 세션 상태에 openai_model 초기화 (세션별로 모델 선택 가능)
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"  # 기본 모델 설정

# 채팅 기록 로드 함수
def load_chat_history():
    with shelve.open("chat_history") as db:  # "chat_history"라는 Shelve 파일 열기
        return db.get("messages", [])  # "messages" 키의 값을 가져옴 (없으면 빈 리스트 반환)

# 채팅 기록 저장 함수
def save_chat_history(messages):
    with shelve.open("chat_history") as db:  # "chat_history" Shelve 파일 열기
        db["messages"] = messages  # "messages" 키에 대화 기록 저장

# 세션 상태에서 메시지 초기화 또는 로드
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()  # Shelve에서 메시지 불러오기

# 사이드바 설정
with st.sidebar:
    # "Delete Chat History" 버튼
    if st.button("Delete Chat History"):  
        st.session_state.messages = []  # 세션 상태의 메시지를 빈 리스트로 초기화
        save_chat_history([])  # Shelve에서도 대화 기록 초기화

# 대화 기록 표시
for message in st.session_state.messages:
    # 사용자 메시지와 봇 메시지를 구분하여 아바타 설정
    avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):  # 메시지 UI 블록 생성
        st.markdown(message["content"])  # 메시지 내용 출력

# 메인 대화 입력 및 처리
if prompt := st.chat_input("How can I help?"):  # 사용자 입력 필드
    # 사용자 입력 메시지 세션 상태에 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):  # 사용자 메시지 출력
        st.markdown(prompt)

    # OpenAI API 호출 및 봇 응답 처리
    with st.chat_message("assistant", avatar=BOT_AVATAR):  # 봇 메시지 UI 블록 생성
        message_placeholder = st.empty()  # 봇 메시지를 실시간으로 업데이트할 자리 확보
        full_response = ""  # 전체 응답을 저장할 변수
        # OpenAI API에 메시지 스트림 생성
        for response in client.chat.completions.create(
            model=st.session_state["openai_model"],  # 세션 상태에 저장된 모델 사용
            messages=st.session_state["messages"],  # 현재까지의 대화 기록 전달
            stream=True,  # 스트리밍 모드 활성화
        ):
            # 스트리밍 데이터에서 응답 내용 추가
            full_response += response.choices[0].delta.content or ""
            # 현재 응답 내용 표시 (마지막에 "|" 추가로 스트리밍 진행 중 표시)
            message_placeholder.markdown(full_response + "|")
        # 스트리밍 완료 후 최종 메시지 표시
        message_placeholder.markdown(full_response)

    # 봇의 응답을 대화 기록에 추가
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# 대화 기록 저장 (모든 대화가 끝난 후 Shelve에 저장)
save_chat_history(st.session_state.messages)
