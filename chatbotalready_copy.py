import streamlit as st
import pandas as pd
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain_openai import ChatOpenAI

import os
from dotenv import load_dotenv
import pandas as pd
from langchain.docstore.document import Document
import json
from datetime import  datetime
from langchain.prompts import PromptTemplate

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = openai_api_key





# 타이틀
st.title('가상화폐')
st.markdown('코인에 대하여 질문하시면 저장된 뉴스 데이터를 기반으로 질문에 답변합니다.')

# 상태 관리 : 초기화
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = None

# 데이터 불러오기
df_coin_high = pd.read_csv('coin_high_new.csv')
df_coin_low = pd.read_csv('coin_low_new.csv')
df_coin_volume = pd.read_csv('coin_volume_new.csv')

df_coin_high.index = pd.to_datetime(df_coin_high.index, errors='coerce')

markdown_docs = []
for timestamp, row in df_coin_high.iterrows():
    markdown_doc = f"# Date: {timestamp.date()}\n\n"
    for coin, price in row.items():
        markdown_doc += f"- **{coin}**: {price}\n"
    markdown_docs.append(markdown_doc)

docs = [Document(page_content=doc) for doc in markdown_docs]





news_docs_path = 'data_indexing.json'
with open(news_docs_path,'r',encoding='utf-8') as file:
    data_all = json.load(file)

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

vectorstore = FAISS.from_documents(documents = docs + split_texts, embedding = embeddings)

st.session_state.vectorstore = vectorstore

template = ("""
너는 코인데이터와 신문기사를 바탕으로 물음에 정확하게 답변하는 애널리스트이다. 공신력있는 보고서 형태로 작성해줘
            Question: {question}
            Answer:
"""
)

# --------------------------------------------------------

# Optionally, specify your own session_state key for storing messages
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

msgs = StreamlitChatMessageHistory(key="special_app_key")

if len(msgs.messages) == 0:
    msgs.add_ai_message("무엇을 도와드릴까요?")

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", template),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)
model = ChatOpenAI(
                        model = 'gpt-4o-mini',
                        temperature = 0.5,
                        openai_api_key = openai_api_key
                    )
retriever = st.session_state.vectorstore.as_retriever()
chain = prompt | model | retriever

chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: msgs,  # Always return the instance created earlier
    input_messages_key='question',
    history_messages_key="history",
)

import streamlit as st

for msg in msgs.messages:
    st.chat_message(msg.type).write(msg.content)

if prompt := st.chat_input():
    st.chat_message("human").write(prompt)

    # As usual, new messages are added to StreamlitChatMessageHistory when the Chain is called.
    config = {"configurable": {"session_id": "any"}}
    response = chain_with_history.invoke({"question": prompt}, config)
    st.chat_message("ai").write(response.content)
# --------------------------------------------------------