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
from langchain_core.documents import Document
import shelve
from openai import OpenAI


# 데이터 불러오기
with open(r'News_Data.json', 'r', encoding='utf-8') as f:
    data_json = json.load(f)
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# gpt4o 모델 설정
llm = ChatOpenAI(
    model='gpt-4o',
    temperature=0.2,
    openai_api_key=os.getenv('OPENAI_API_KEY')
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o"


# Load chat history from shelve file
def load_chat_history():
    with shelve.open("chat_history") as db:
        return db.get("messages", [])
    
def save_chat_history(messages):
    with shelve.open("chat_history") as db:
        db["messages"] = messages

# Initialize or load chat history
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

# Sidebar with a button to delete chat history
with st.sidebar:
    if st.button("Delete Chat History"):
        st.session_state.messages = []
        save_chat_history([])

#####################
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
            border: 2px solid #F0F0F0;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            background-color: #F7F7F7;
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
            height: 80%;
            padding: 20px;
            border: 1px solid #C0C0C0;
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
            background-color: #00AAFF;
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
    for news_info in data_json
]
splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
split_texts = splitter.split_documents(docs)

# 임베딩
embeddings = OpenAIEmbeddings()

#  FAISS 벡터 저장소 생성
vector_store = FAISS.from_documents(split_texts, embeddings)
st.session_state.vector_store = vector_store


###########
# 타이틀 표시
st.markdown('<div class="header">:상승세인_차트: 암호화폐 기반 대화형 챗봇 :말풍선:</div>', unsafe_allow_html=True)
st.markdown('<p class="crypto-text">:전구: 암호화폐와 관련한 이야기를 입력하면 관련 정보를 바탕으로 대답합니다. :로켓:</p>', unsafe_allow_html=True)

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
        <h3>:메모: 추천 프롬프트</h3>
        <div class="prompt-item"><span>1) :차트:</span> 암호화폐 시장의 최신 동향에 대해 알려줘</div>
        <div class="prompt-item"><span>2) :막대_차트:</span> 비트코인 가격 예측에 대해 말해줘</div>
        <div class="prompt-item"><span>3) :생각하는_얼굴:</span> 김진우의 비밀을 설명해줘!</div>
    </div>
""", unsafe_allow_html=True)
# 이전 대화 표시
# for message in st.session_state.messages_displayed:
#     if message['role'] == 'assistant':
#         # AI 메시지에만 비트코인 아이콘 설정
#         with st.chat_message(message['role'], avatar="bitcoin.png"):
#             st.write(message['content'])
#     else:
#         # 사용자 메시지에는 기본 아이콘 설정
#         st.markdown("""
#             <div style="display: flex; align-items: center; margin-bottom: 10px;">
#                 <div style="flex-grow: 1; padding: 10px; background-color: #FFFFFF;">
#                     {}</div>
#             </div>
#         """.format(message['content']), unsafe_allow_html=True)
#########################



# 사용자 입력 창을 생성합니다.
# - '메시지를 입력하세요.'라는 제목과 함께 텍스트 입력 상자를 표시합니다.
# - 사용자가 입력한 내용을 세션 상태의 'user_input' 키로 관리합니다.
# 세션 상태 초기화 (대화 기록 관리)
if "messages" not in st.session_state:
    st.session_state.messages = []  # 메시지 리스트 초기화

# 사용자 입력 창
prompt = st.text_input(
    '메시지를 입력하세요.',
    key='user_input',
    placeholder='메시지를 입력해주세요...',
    label_visibility="collapsed"
)

# 사용자 입력이 있을 경우 실행
if prompt:
    # 세션 상태에 사용자가 입력한 메시지를 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 사용자 메시지를 화면에 표시
    with st.chat_message("user"):  # 사용자 메시지 블록 생성
        st.markdown(prompt)  # 입력된 메시지를 출력

    # OpenAI 모델의 응답 생성
    with st.chat_message("assistant", avatar="bitcoin.png"):  # AI 메시지 블록 생성
        message_placeholder = st.empty()  # 스트리밍 응답을 표시하기 위한 빈 자리 생성
        full_response = ""  # 전체 응답 내용을 저장할 변수 초기화

        # OpenAI API를 호출하여 GPT 모델 응답 생성
        try:
            for response in openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # 사용 중인 OpenAI 모델 (변경 가능)
                messages=st.session_state["messages"],  # 이전 대화 기록 전달
                stream=True,  # 스트리밍 모드로 응답을 받아옴
            ):
                # 스트리밍 데이터에서 응답 텍스트를 하나씩 추가
                full_response += response.choices[0].delta.get("content", "")
                # 응답을 실시간으로 화면에 표시 (스트리밍 중인 응답)
                message_placeholder.markdown(full_response + "|")
            
            # 스트리밍이 끝난 후 최종 응답을 표시
            message_placeholder.markdown(full_response)
            
            # 생성된 AI 응답을 세션 상태에 추가
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        except Exception as e:
            # 에러 발생 시 화면에 오류 메시지 출력
            st.error(f"오류가 발생했습니다: {e}")





# <a href="https://www.flaticon.com/free-icons/bitcoin" title="bitcoin icons">Bitcoin icons created by Freepik - Flaticon</a>



