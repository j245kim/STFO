import streamlit as st
import pandas as pd
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI

import os
from dotenv import load_dotenv
import pandas as pd
from langchain.docstore.document import Document
import json
from datetime import  datetime


load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

# gpt 4o 모델 설정
llm = ChatOpenAI(
    model = 'gpt-4o',
    temperature = 0.5,
    openai_api_key = os.getenv('OPENAI_API_KEY')
)

# 타이틀
st.title('가상화폐')
st.markdown('코인에 대하여 질문하시면 저장된 뉴스 데이터를 기반으로 질문에 답변합니다.')

# 상태 관리 : 초기화
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = None
if 'memory' not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(memory_key = 'chat_history', return_messages = True)
if 'messages_displayed' not in st.session_state:
    st.session_state.messages_displayed = []

# 데이터 불러오기
df_coin_high = pd.read_csv('coin_high.csv')
df_coin_low = pd.read_csv('coin_low.csv')
df_coin_volume = pd.read_csv('coin_volume.csv')

investing_path = 'C:\github\STFO\Investing_Data.json'
hankyung_path = 'C:\github\STFO\Hankyung_Data.json'

with open(investing_path,'r',encoding="utf-8") as file:
    data1 = json.load(file) 

with open(hankyung_path,'r',encoding="utf-8") as file:
    data2 = json.load(file) 

data_all = data1 + data2

# Json을 faiss가 읽을 수 있는 document로 바꾸기
documents = []
for item in data_all:
    if 'news_content' in item and item['news_content']: 
        raw_date = item.get("news_first_upload_time")
        parsed_date = datetime.strptime(raw_date, '%Y-%m-%d %p %I:%M').isoformat() if raw_date else None
        
        raw_date_after = item.get("news_last_upload_time")
        parsed_date_after = datetime.strptime(raw_date_after, '%Y-%m-%d %p %I:%M').isoformat() if raw_date_after else None

        documents.append(
            Document(
                page_content=item["news_content"],  # 텍스트 본문
                metadata={
                    "title": item.get("news_title"),
                    "url": item.get("news_url"),
                    "website": item.get("news_website"),
                    "news_first_upload_time": parsed_date,
                    "news_last_upload_time" : parsed_date_after
                }
            )
        )


# 문서 분할
splitter = CharacterTextSplitter(chunk_size=100, chunk_overlap=10)
split_texts = splitter.split_documents(documents)

#  OpenAIEmbeddings 모델로 임베딩 생성
embeddings = OpenAIEmbeddings()

vectorstore = FAISS.from_documents(documents = split_texts, embedding = embeddings)

st.session_state.vectorstore = vectorstore

input_message = st.chat_input('메세지를 입력하세요.')

prompt = f"""
너는 코인데이터와 신문기사를 바탕으로 물음에 정확하게 답변하는 애널리스트이다. 공신력있는 보고서 형태로 작성해줘
<코인 데이터> : <고가 = {df_coin_high},저가 = {df_coin_low},거래량 = {df_coin_volume}>
<질문>
<{input_message}>
"""

# 사용자 입력이 비어있지 않으면 처리
if prompt:
    # 사용자 메세지 기록
    st.session_state.memory.chat_memory.add_user_message(prompt)

    try:
        retriever = st.session_state.vectorstore.as_retriever()
        chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=st.session_state.memory
        )

        # AI 응답 생성
        response = chain({'question': prompt})
        ai_response = response['answer']

        # AI 메세지 기록
        st.session_state.memory.chat_memory.add_ai_message(ai_response)

        # 메세지 표시
        st.session_state.messages_displayed.append({'role': 'user', 'content': prompt})
        st.session_state.messages_displayed.append({'role': 'assistant', 'content': ai_response})

    except Exception as e:
        st.error(f'오류가 발생했습니다. : {str(e)}')

else:
    st.error("메세지를 입력해주세요.")

# 이전 대화 표시
for message in st.session_state.messages_displayed:
    with st.chat_message(message['role']):
        st.write(message['content'])