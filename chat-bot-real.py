import streamlit as st
import pyupbit
import pandas as pd
# from langchain.document_loaders import WebBaseLoader
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
import numpy as np
import faiss
import pandas as pd
from langchain.docstore.document import Document
from langchain.docstore import InMemoryDocstore
import json
from datetime import  datetime


load_dotenv()

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

# 데이터 저장
Bit_df = pyupbit.get_ohlcv("KRW-BTC",count = 2200, period=1,interval= "minute240", to="20241204")
Ether_df = pyupbit.get_ohlcv("KRW-ETH",count = 2200, period=1,interval= "minute240", to="20241204")
tether_df = pyupbit.get_ohlcv("KRW-USDT",count = 2200, period=1,interval= "minute240", to="20241204")
Doge_df = pyupbit.get_ohlcv("KRW-DOGE",count = 2200, period=1,interval= "minute240", to="20241204")
Sand_df = pyupbit.get_ohlcv("KRW-SAND",count = 2200, period=1,interval= "minute240", to="20241204")
XRP_df = pyupbit.get_ohlcv("KRW-XRP",count = 2200, period=1,interval= "minute240", to="20241204")
Solana_df = pyupbit.get_ohlcv("KRW-SOL",count = 2200, period=1,interval= "minute240", to="20241204")
Shib_df = pyupbit.get_ohlcv("KRW-SHIB",count = 2200, period=1,interval= "minute240", to="20241204")

bit_high = Bit_df['high']
dog_high = Doge_df['high']
eth_high = Ether_df['high']
sol_high = Solana_df['high']
sand_high = Sand_df ['high']
shib_high = Shib_df['high']
XRP_high = XRP_df['high']
tether_high = tether_df['high']

coin_list = [Bit_df,Ether_df,tether_df,Doge_df,Sand_df,XRP_df,Solana_df,Shib_df]
coin_list_name = ['Bit','Ether','tether','Doge','Sand','XRP','Solana','Shib']
coin_list_high = []
for i in coin_list:
    coin_list_high.append(i['high'])

df_coin_high = pd.concat(coin_list_high,axis=1,keys=coin_list_name)

#마크다운으로 저장
markdown_docs = []
for timestamp, row in df_coin_high.iterrows():
    markdown_doc = f"# Date: {timestamp.date()}\n\n"
    for coin, price in row.items():
        markdown_doc += f"- **{coin}**: {price}\n"
    markdown_docs.append(markdown_doc)
    
# 마크다운을 LangChain 문서 객체로 변환
docs = [Document(page_content=doc) for doc in markdown_docs]

# 뉴스 데이터(JSON)을 불러오기
news_docs_path = 'data_indexing.json'
with open(news_docs_path,'r',encoding='utf-8') as file:
    news_docs = json.load(file)

# Json을 faiss가 읽을 수 있는 document로 바꾸기
documents = []
for item in news_docs:
    if 'news_content' in item and item['news_content']:  # 'news_content'가 있는 경우만 처리
        raw_date = item.get("news_last_upload_time")
        parsed_date = datetime.strptime(raw_date, '%Y-%m-%d %p %I:%M').isoformat() if raw_date else None

        documents.append(
            Document(
                page_content=item["news_content"],  # 텍스트 본문
                metadata={
                    "title": item.get("news_title"),
                    "author": item.get("author"),
                    "url": item.get("news_url"),
                    "website": item.get("news_website"),
                    "date": parsed_date
                }
            )
        )


# 문서 분할
splitter = CharacterTextSplitter(chunk_size=100, chunk_overlap=10)
split_texts = splitter.split_documents(documents)

#  OpenAIEmbeddings 모델로 임베딩 생성
embeddings = OpenAIEmbeddings()

vectorstore = FAISS.from_documents(documents = docs + split_texts, embedding = embeddings)

st.session_state.vectorstore = vectorstore

prompt = st.chat_input('메세지를 입력하세요.')

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