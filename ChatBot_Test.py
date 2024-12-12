# 라이브러리
# - 파이썬 표준 라이브러리
from typing import Generator

import os
import json
from collections import defaultdict

# - 파이썬 서드파티 라이브러리
from langchain_community.callbacks.openai_info import OpenAICallbackHandler

import streamlit as st
from dotenv import load_dotenv
from langchain_core.globals import set_llm_cache
from langchain_core.caches import InMemoryCache
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, FewShotPromptTemplate, PromptTemplate
from langchain_core.example_selectors.semantic_similarity import MaxMarginalRelevanceExampleSelector
from langchain_chroma import Chroma

from langchain_community.callbacks import get_openai_callback


from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

from langchain_core.documents import Document


# 전역 변수 및 환경설정
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = openai_api_key
folder_path = r'C:\Users\RMARKET\Desktop\STFO\STFO'
json_path = folder_path + r'\LLM_Info\llm_info.json'
# llm_info 불러오기
if os.path.exists(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        llm_info = json.load(f)
else:
    llm_info = defaultdict(list)

# 함수
# - LLM_Info에 전체 비용, 전체 프롬프트 토큰 갯수, 전체 답변 토큰 갯수, 전체 토큰 갯수를 추가하는 함수
def add_info(llm_info: dict[str, float, int],
             callback: Generator[OpenAICallbackHandler, None, None]) -> None:
    """llm_info에 비용, 토큰 갯수들을 추가하는 함수

    Args:
        llm_info: LLM 비용, 토큰 갯수 등의 정보를 가지고 있는 Dictionary
        callback: callback
    
    Returns:
        None
    
    """

    total_cost = callback.total_cost
    total_prompt_tokens = callback.prompt_tokens
    total_completion_tokens = callback.completion_tokens
    total_tokens = callback.total_tokens
    llm_info['Total_Cost(USD)'].append(total_cost)
    llm_info['Total_Prompt_Tokens'].append(total_prompt_tokens)
    llm_info['Total_Completion_Tokens'].append(total_completion_tokens)
    llm_info['Total_Tokens'].append(total_tokens)
    return None

# 데이터 불러오기
with open(r'C:\Users\RMARKET\Desktop\STFO\STFO\Data\Hankyung_Data.json', 'r', encoding='utf-8') as f:
    data_json = json.load(f)

# 인메모리 캐시를 사용
set_llm_cache(InMemoryCache())
# gpt4o 모델 설정
llm = ChatOpenAI(model='gpt-4o', temperature=0.2, openai_api_key=openai_api_key)

messages = [
                SystemMessage(content="당신은 여행사 직원입니다. 사용자에게 여행 일정을 제공할 수 있습니다."),
                HumanMessage(content="서울에서 관광객이 많이 찾는 3대 명소는 어디예요?"),
            ]

with get_openai_callback() as callback:
    aiMessage = chat.invoke(messages)
    print(aiMessage.content)
    messages.append(aiMessage)
    add_info(llm_info=llm_info, callback=callback)
    
    messages.append(HumanMessage(content="방금 당신이 알려준 3대 명소들에 대해 다시 알려주세요."))
    aiMessage = chat.invoke(messages)
    add_info(llm_info=llm_info, callback=callback)
    print(aiMessage.content)





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
        Document(page_content=news_info['news_content'], metadata={"source": news_info['news_url'], "title": news_info['news_title'],
                                                                   "date": news_info['news_first_upload_time']})
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