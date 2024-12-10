import os
import json
import streamlit as st
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI

# JSON 파일 경로
path = 'chat_history.json'

# 대화 기록 로드 함수
def load_chat_history():
    """JSON 파일에서 대화 기록을 로드"""
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return [{'role': 'system', 'content': '당신은 간단하고 논리적으로 답변하는 교수님입니다.'}]

# 대화 기록 저장 함수
def save_chat_history(messages):
    """대화 기록을 JSON 파일에 저장"""
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(messages, file, ensure_ascii=False, indent=4)


# 뉴스 데이터 벡터 저장소 초기화
if "vector_store" not in st.session_state:
    embeddings = OpenAIEmbeddings()
    # 예시: 뉴스 데이터를 벡터화하여 FAISS에 저장 (데이터 필요)
    # st.session_state.vector_store = FAISS.from_documents(news_documents, embeddings)
    st.session_state.vector_store = None

# 대화 메모리 초기화
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# 대화 기록 불러오기 또는 초기화
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()




# 사용자 입력
prompt = st.text_input("메시지를 입력하세요.", key="user_input", placeholder="메시지를 입력해주세요...", label_visibility="collapsed")

# 사용자 입력 처리
if prompt:
    if st.session_state.vector_store is None:
        # 벡터 저장소가 없으면 에러 메시지 출력
        st.error("뉴스 데이터를 불러오지 못했습니다. 다시 시도해주세요.")
    else:
        # 사용자 메시지를 대화 기록에 추가
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 뉴스 데이터 벡터 저장소에서 검색 기능 활성화
        retriever = st.session_state.vector_store.as_retriever()
        chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=st.session_state.memory
        )

        try:
            # GPT 모델로 질문에 대한 응답 생성
            response = chain({"question": prompt})
            ai_response = response["answer"]

            # GPT 응답을 대화 기록에 추가
            st.session_state.messages.append({"role": "assistant", "content": ai_response})

            # 대화 내역 저장
            save_chat_history(st.session_state.messages)

            # 대화 표시
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                st.markdown(ai_response)

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

# 이전 대화 내역 표시
st.markdown("### 대화 내역")
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"**User**: {message['content']}")
    elif message["role"] == "assistant":
        st.markdown(f"**Assistant**: {message['content']}")
