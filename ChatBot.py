# 라이브러리
# 파이썬 표준 라이브러리
import os
import json
from datetime import  datetime
from operator import itemgetter

# 파이썬 서드파티 라이브러리
from dotenv import load_dotenv
import pandas as pd
import streamlit as st

from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.docstore.document import Document
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate

# 타이틀
st.markdown("""
    <style>
        .header {
            text-align: center;     
            font-size: 45px;   
            font-weight: bold;
            color: black;
        }   
    #    .header:hover {
    #         # color: #f72f08ff;
    #     }
        .prompt-box {
            margin-top: 10px;
            margin-bottom: 20px;
            padding: 20px;
            border: 2px solid #f0f0f0;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            background-color: #f7f7f7;
        }
        .prompt-box h3 {
            margin-bottom: 10px;
            color: #333;
            font-size: 20px;
            font-weight: bold;
        }
        .prompt-item {
            margin-bottom: 8px;
            font-size: 16px;
            color: #555;
        }
        .prompt-item span {
            font-weight: bold;
        }
            
        .helper {
            color: black; 
            width: 130px;
            height: 72%;
            padding: 20px;
            border: 1px solid #c0c0c0;
            position: fixed;
            top: 10%;
            left: -20px;
            background-color: white;
            display: flex;
            flex-direction: column;
            justify-content: space-evenly;  
            align-items: stretch; 
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }
            
        .helper button {
            width: 100%;
            margin-bottom: 5px;
            padding: 10px;
            color: white;
            background-color: #00aaff;
            border-radius: 5px;
            cursor: pointer;
            # margin-top: -30px
            font-weight: bold;
        }

        .helper button:hover {
            background-color: #f72f08ff;
        }

        .helper svg {
            width: 30px;
            height: 30px;
            fill: #f72f08ff;
            margin: 10px 0;
        }

        .helper svg:hover {
            fill: #f72f08ff;
        }

        .crypto-text {
            font-size: 18px;
            font-weight: bold;
            color: #000000;
            text-align: center;
            padding: 20px 0;
        }
            
        .helper div span:hover {
            color: #f72f08ff;  
            cursor: pointer; 
        }
            
    </style>
""", unsafe_allow_html=True)

# 전역 변수 및 환경 설정
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = openai_api_key

# 타이틀 표시
st.markdown('<div class="header">📈 암호화폐 기반 대화형 챗봇 💬</div>', unsafe_allow_html=True)
st.markdown('<p class="crypto-text">💡 암호화폐와 관련한 이야기를 입력하면 관련 정보를 바탕으로 대답합니다. 🚀</p>', unsafe_allow_html=True)

# 상태 관리 : 초기화
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = None

# helper 박스에 버튼 추가
st.markdown("""
    <div class="helper">
        <div class="home">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill-rule="evenodd" clip-rule="evenodd" d="M21 8.77217L14.0208 1.79299C12.8492 0.621414 10.9497 0.621413 9.77817 1.79299L3 8.57116V23.0858H10V17.0858C10 15.9812 10.8954 15.0858 12 15.0858C13.1046 15.0858 14 15.9812 14 17.0858V23.0858H21V8.77217ZM11.1924 3.2072L5 9.39959V21.0858H8V17.0858C8 14.8767 9.79086 13.0858 12 13.0858C14.2091 13.0858 16 14.8767 16 17.0858V21.0858H19V9.6006L12.6066 3.2072C12.2161 2.81668 11.5829 2.81668 11.1924 3.2072Z"></path></svg>
            <span>홈</span>
        </div>
        <div class="login">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M15.4857 20H19.4857C20.5903 20 21.4857 19.1046 21.4857 18V6C21.4857 4.89543 20.5903 4 19.4857 4H15.4857V6H19.4857V18H15.4857V20Z"></path><path d="M10.1582 17.385L8.73801 15.9768L12.6572 12.0242L3.51428 12.0242C2.96199 12.0242 2.51428 11.5765 2.51428 11.0242C2.51429 10.4719 2.962 10.0242 3.51429 10.0242L12.6765 10.0242L8.69599 6.0774L10.1042 4.6572L16.4951 10.9941L10.1582 17.385Z"></path></svg>
            <span>로그인</span>
        </div>
        <div class="add">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 6C12.5523 6 13 6.44772 13 7V11H17C17.5523 11 18 11.4477 18 12C18 12.5523 17.5523 13 17 13H13V17C13 17.5523 12.5523 18 12 18C11.4477 18 11 17.5523 11 17V13H7C6.44772 13 6 12.5523 6 12C6 11.4477 6.44772 11 7 11H11V7C11 6.44772 11.4477 6 12 6Z"></path><path fill-rule="evenodd" clip-rule="evenodd" d="M5 22C3.34315 22 2 20.6569 2 19V5C2 3.34315 3.34315 2 5 2H19C20.6569 2 22 3.34315 22 5V19C22 20.6569 20.6569 22 19 22H5ZM4 19C4 19.5523 4.44772 20 5 20H19C19.5523 20 20 19.5523 20 19V5C20 4.44772 19.5523 4 19 4H5C4.44772 4 4 4.44772 4 5V19Z"></path></svg>
            <span>추가</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# 추천 프롬프트 박스
st.markdown("""
    <div class="prompt-box">
        <h3>📝 추천 프롬프트</h3>
        <div class="prompt-item"><span>1) 💹</span> 암호화폐 시장의 최신 동향에 대해 알려줘</div>
        <div class="prompt-item"><span>2) 📊</span> 비트코인 가격 예측에 대해 말해줘</div>
        <div class="prompt-item"><span>3) 🤔</span> 김진우의 비밀을 설명해줘!</div>
    </div>
""", unsafe_allow_html=True)

# 데이터 불러오기
df_coin_high = pd.read_csv('./csv/coin_high_new.csv')
df_coin_low = pd.read_csv('./csv/coin_low_new.csv')
df_coin_volume = pd.read_csv('./csv/coin_volume_new.csv')

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

# OpenAIEmbeddings 모델로 임베딩 생성
embeddings = OpenAIEmbeddings()

vectorstore = FAISS.from_documents(documents = docs + split_texts, embedding = embeddings)

st.session_state.vectorstore = vectorstore

template = ("""
너는 코인데이터와 신문기사를 바탕으로 물음에 정확하게 답변하는 애널리스트이다. 공신력있는 보고서 형태로 작성해줘
            Context: {context}
            Question: {question}
            Answer:
"""
)

# --------------------------------------------------------
msgs = StreamlitChatMessageHistory(key="special_app_key")

# if len(msgs.messages) == 0:
#      msgs.add_ai_message("무엇을 도와드릴까요?", avatar="bitcoin.png")

prompt = ChatPromptTemplate.from_template(
    """너는 코인데이터와 신문기사를 바탕으로 물음에 정확하게 답변하는 애널리스트이다. 공신력있는 보고서 형태로 작성해줘

#Previous Chat History:
{chat_history}

#Question: 
{question} 

#Context: 
{context} 

#Answer:"""
)

llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
retriever = st.session_state.vectorstore.as_retriever()

chain = (
    {
        "context": itemgetter("question") | retriever,
        "question": itemgetter("question"),
        "chat_history": itemgetter("chat_history"),
    }
    | prompt
    | llm

)

chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: msgs,  
    input_messages_key='question',
    history_messages_key="chat_history",
)

# 이전 대화 기록!
for msg in msgs.messages:
    if msg.type == 'ai':  
        with st.chat_message(msg.type, avatar="bitcoin.png"):
            st.write(msg.content)
    elif msg.type == 'human':  
        st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <div style="flex-grow: 1; padding: 10px; background-color: #ffffff;">
                    {msg.content}
                </div>
            </div>
        """, unsafe_allow_html=True)

if input_text := st.chat_input():
    # 사용자가 입력한 텍스트 출력 (아이콘 없이 HTML 스타일 적용)
    st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <div style="flex-grow: 1; padding: 10px; background-color: #ffffff;">
                {input_text}
            </div>
        </div>
    """, unsafe_allow_html=True)

    config = {"configurable": {"session_id": "any"}}
    response = chain_with_history.invoke({"question": input_text}, config)

    with st.chat_message("assistant", avatar="bitcoin.png"):
        st.write(response.content)

