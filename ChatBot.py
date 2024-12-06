import json

import streamlit as st
from langchain.document_loaders import WebBaseLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
import bs4
from langchain_teddynote import logging
from langchain_core.documents import Document

# 데이터 불러오기
with open(r'C:\Users\RMARKET\Desktop\STFO\STFO\News_Data.json', 'r', encoding='utf-8') as f:
    data_json = json.load(f)

load_dotenv()

# gpt4o 모델 설정
llm = ChatOpenAI(
    model='gpt-4o',
    temperature=0.2,
    openai_api_key=os.getenv('OPENAI_API_KEY')
)

# 타이틀
st.title('암호화폐 기반 대화형 챗봇')
st.markdown('암호화폐와 관련한 이야기를 입력하면 관련 정보를 바탕으로 대답합니다.')

# 상태 관리 : 초기화
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None
if 'memory' not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
if 'messages_displayed' not in st.session_state:
    st.session_state.messages_displayed = []


# 뉴스 로드
docs = [
        Document(page_content=news_info['news_content'], metadata={"source": news_info['news_url']})
            for news_info in data_json]

splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
split_texts = splitter.split_documents(docs)

# 임베딩
embeddings = OpenAIEmbeddings()
# FAISS 벡터 저장소 생성
vector_store = FAISS.from_documents(split_texts, embeddings)

st.session_state.vector_store = vector_store

prompt = st.chat_input('메시지를 입력하세요.')
if prompt:
    if st.session_state.vector_store is None:
        st.error('뉴스를 먼저 로드해주세요.')
    else:
        # 사용자 메시지 기록
        st.session_state.memory.chat_memory.add_user_message(prompt)
        try:
            retriever = st.session_state.vector_store.as_retriever()
            chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=retriever,
                memory=st.session_state.memory
            )
            # AI 응답 생성
            response = chain({'question': prompt})
            ai_response = response['answer']
             
            # AI 메시지 기록
            st.session_state.memory.chat_memory.add_ai_message(ai_response)

            # 메시지 표시
            st.session_state.messages_displayed.append({'role': 'user', 'content': prompt})
            st.session_state.messages_displayed.append({'role': 'assistant', 'content': ai_response})
        except Exception as e:
            st.error(f'오류가 발생했습니다. : {str(e)}')

# 이전 대화 표시
for message in st.session_state.messages_displayed:
    with st.chat_message(message['role']):
        st.write(message['content'])

# import json

# with open(r'C:\Users\RMARKET\Desktop\STFO\STFO\News_Data.json', 'r', encoding='utf-8') as f:
#     data_json = json.load(f)

# print(data_json)