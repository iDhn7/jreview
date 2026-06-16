"""
모듈명 : 맛집 리뷰를 이용한 LangChain / LCEL 기반 RAG 서비스 모듈
작성일 : 2026.06.16
pip install torch transformers langchain-core langchain-groq langchain-huggingface langchain-community faiss-cpu pandas sentence-transformers
"""

import os
import dotenv
import requests
import json
import traceback
import pandas as pd
from operator import itemgetter

# LangChain Core & LCEL 파이프라인 모듈
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 세션 기반 대화 기록(메모리) 관리 모듈
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

# 💡 튕김 방지 및 오프라인 보안을 위한 FAISS 및 HuggingFace 고성능 컴포넌트
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

try:
    from DBManager import DBManager
except ImportError:
    from modules.DBManager import DBManager 

class RAGManager:
    def __init__(self):
        current_file_path = os.path.abspath(__file__)          
        modules_dir = os.path.dirname(current_file_path)       
        service_dir = os.path.dirname(modules_dir)             
        project_root = os.path.dirname(service_dir)            

        env_path_service = os.path.join(service_dir, '.env')
        env_path_root = os.path.join(project_root, '.env')

        if os.path.exists(env_path_service):
            dotenv.load_dotenv(dotenv_path=env_path_service, override=True)
            print(f"✅ [.env 로드 완료]: {env_path_service}")
        elif os.path.exists(env_path_root):
            dotenv.load_dotenv(dotenv_path=env_path_root, override=True)
            print(f"✅ [.env 로드 완료]: {env_path_root}")
        else:
            dotenv.load_dotenv()
            print("⚠️ 기본 환경 변수를 로드합니다.")

        self.db = DBManager()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
        # FAISS 인덱스 로컬 저장 경로
        self.faiss_db_path = os.path.join(service_dir, "faiss_index")
        
        # 💡 [방화벽 차단 우회] 로컬 컴퓨터의 CPU/GPU 자원을 쓰는 완벽한 오프라인 bge-m3 모델 선언
        print("📥 LangChain 임베딩 컴포넌트 로드 중 (HuggingFace bge-m3 로컬 전개)...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={'device': 'cpu'}, # GPU 가용시 'cuda' 변경 가능
            encode_kwargs={'normalize_embeddings': True}
        )
        
        self.retriever = None
        self.bot_chain = None
        self.store_chat_histories = {}

    def DBOpen(self):
        return self.db.DBOpen(
            host    = os.getenv("host"),
            id      = os.getenv("user"),
            pw      = os.getenv("passwd"),
            dbname  = os.getenv("dbname")
        )  
        
    def DBClose(self):
        self.db.DBClose()

    def BuildVectorDB(self):
        """MySQL의 REVIEW와 STORE 데이터를 Join하여 FAISS 지식 베이스를 빌드합니다."""
        try:
            # 💡 가게 상세 정보까지 함께 조회하는 SQL
            sql = """
                SELECT 
                    r.REVIEW_CODE,
                    r.STORE_CODE,
                    r.CONTENT,
                    s.STORE_NAME,
                    s.ADDRESS_JI,
                    s.CATEGORY,
                    s.PARKING,
                    s.AMENITY,
                    s.STAR,
                    s.PN_RATE
                FROM REVIEW r
                JOIN STORE s ON r.STORE_CODE = s.STORE_CODE
            """
            if not self.db.OpenSQL(sql): return False
            reviews = self.db.getAll()
            
            if not reviews:
                print("⚠️ MySQL에 적재할 데이터가 없습니다.")
                return False

            print(f"🔄 총 {len(reviews)}건의 리뷰 및 매장 연동 데이터 추출 완료.")
            
            documents_context = []
            metadatas = []
            
            for row in reviews:
                # 데이터 누락 방지를 위한 기본값 처리
                store_name = row.get('STORE_NAME', '정보 없음')
                address = row.get('ADDRESS_JI', '정보 없음')
                category = row.get('CATEGORY', '식당')
                parking = row.get('PARKING', '정보 없음')
                amenity = row.get('AMENITY', '정보 없음')
                star = row.get('STAR', 0.0)
                pn_rate = row.get('PN_RATE', 0.0)
                content = row.get('CONTENT', '')

                # 💡 LLM이 매장 맥락을 완벽히 이해할 수 있도록 텍스트 구조 고도화
                context_text = (
                    f"가게 이름: {store_name}\n"
                    f"카테고리: {category}\n"
                    f"주소: {address}\n"
                    f"주차 여부: {parking} | 편의시설: {amenity}\n"
                    f"별점: {star}점 | 긍정률: {pn_rate}%\n"
                    f"리뷰 내용: {content}\n"
                    f"----------------------------------------"
                )
                documents_context.append(context_text)
                
                # 메타데이터 정보도 확장 (추후 필터링 및 매칭용)
                metadatas.append({
                    "mysql_review_code": row['REVIEW_CODE'],
                    "STORE_CODE": row['STORE_CODE'],
                    "STORE_NAME": store_name,
                    "CATEGORY": category
                })
            
            print("[RAG] 확장된 매장/리뷰 데이터 기반 벡터라이징 및 FAISS 인덱스 구축 시작...")
            vector_store = FAISS.from_texts(
                texts=documents_context,
                embedding=self.embeddings,
                metadatas=metadatas
            )
            
            vector_store.save_local(self.faiss_db_path)
            print(f"✨ FAISS 인덱스 로컬 빌드 최종 성공! 저장 경로: {self.faiss_db_path}")
            
            self.retriever = vector_store.as_retriever(search_kwargs={"k": 3})
            return True
        except Exception as e:
            print(f"❌ 벡터 DB 빌드 에러: {e}")
            traceback.print_exc()
            return False
        finally:
            self.db.CloseSQL()

    def InitRetriever(self):
        """이미 빌드된 로컬 FAISS 인덱스가 있다면 재빌드 없이 인덱스 파일에서 곧바로 로드합니다."""
        if os.path.exists(self.faiss_db_path):
            print("📦 기구축된 로컬 FAISS 인덱스 파일을 감지했습니다. 디스크에서 직접 로드합니다.")
            vector_store = FAISS.load_local(self.faiss_db_path, self.embeddings, allow_dangerous_deserialization=True)
            self.retriever = vector_store.as_retriever(search_kwargs={"k": 3})
            return True
        else:
            print("⚠️ 기구축된 인덱스가 없습니다. BuildVectorDB()를 먼저 실행해야 합니다.")
            return False

    def CreateConversationalChain(self):
        """LangChain Expression Language (LCEL) 메모리 장착형 파이프라인 조립"""
        if not self.retriever:
            raise ValueError("검색기(Retriever)가 초기화되지 않았습니다.")

        # ChatGroq 공식 가동 모델 바인딩
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=self.groq_api_key,
            temperature=0.2
        )

        # 시스템 프롬프트 백엔드 응답 규격(JSON 포맷 강제화) 세팅
        contextual_prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "당신은 전주 지역 맛집 리뷰를 분석하여 요약하는 RAG AI 컨설턴트 어시스턴트입니다.\n"
                "제공된 [식당 리뷰 데이터 문맥]에 기반하여 사용자의 질문에 한국어로 친절하게 답변하고, 이와 관련된 '추천 질문 3개'를 함께 생성해야 합니다.\n"
                "인프라 연동을 위해 반드시 아래 명시된 JSON 포맷 규격으로만 최종 응답을 반환하세요. 다른 서론이나 설명 텍스트는 절대 섞지 마십시오:\n\n"
                "{{\n"
                "  \"answer\": \"여기에 친절한 한국어 답변 요약 작성 (리뷰 내용을 바탕으로 구체적인 피드백 포함)\",\n"
                "  \"recommended_queries\": [\"추천 질문 1\", \"추천 질문 2\", \"추천 질문 3\"]\n"
                "}}\n\n"
                "[식당 리뷰 데이터 문맥]\n{context}"
            )),
            MessagesPlaceholder(variable_name="history"), 
            ("human", (
                "[사용자 질문]\n"
                "{input}"
            ))
        ])

        def format_docs(docs):
            # 검색된 문서 객체들을 하나의 스트링 컨텍스트로 결합
            contexts = []
            for doc in docs:
                contexts.append(f"[검색 내용]: {doc.page_content} (메타: {json.dumps(doc.metadata)})")
            return "\n".join(contexts)

        # LCEL 파이프라인 결합
        rag_chain = (
            RunnablePassthrough.assign(
                context=itemgetter("input") | self.retriever | format_docs
            )
            | contextual_prompt
            | llm
            | StrOutputParser()
        )

        def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
            if session_id not in self.store_chat_histories:
                self.store_chat_histories[session_id] = InMemoryChatMessageHistory()
            return self.store_chat_histories[session_id]

        # 최종 가동 세션 관리형 대화식 체인 할당
        self.bot_chain = RunnableWithMessageHistory(
            rag_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="history"
        )
        print("⚙️ LCEL 대화형 RAG 파이프라인 조립 및 가동 준비 완료.")

    def RunQuery(self, query, session_id="default_session"):
        """이전 프로젝트의 콘솔 호출 규격을 유지하는 표준 실행 메서드 (최신 LangChain invoke 반영)"""
        if not self.bot_chain:
            self.CreateConversationalChain()
            
        print(f"Groq-LCEL 기반 RAG 파이프라인 가동: '{query}' [세션: {session_id}]")
        config = {"configurable": {"session_id": session_id}}
        
        # 1. 💡 [최신 규격으로 변경] get_relevant_documents -> invoke
        searched_docs = []
        store_codes = []
        try:
            if hasattr(self, 'retriever') and self.retriever:
                # 🚀 최신 랭체인은 invoke(query)를 사용하여 문서를 검색합니다.
                searched_docs = self.retriever.invoke(query)
                
                # 검색된 문서들의 메타데이터에서 STORE_CODE만 중복 없이 추출
                store_codes = list(set([
                    doc.metadata.get("STORE_CODE") 
                    for doc in searched_docs 
                    if doc.metadata.get("STORE_CODE")
                ]))
        except Exception as retriever_err:
            print(f"⚠️ FAISS 검색기에서 STORE_CODE 동적 추출 중 오류: {retriever_err}")

        # 최종 응답 추출 및 스트리밍 출력 처리
        full_response = ""
        for chunk in self.bot_chain.stream({"input": query}, config=config):
            full_response += chunk
            
        # JSON 문자열 파싱 및 후속 MySQL 연동
        try:
            parsed_data = json.loads(full_response)
            groq_answer = parsed_data.get("answer", "답변 추출 에러")
            recommended_queries = parsed_data.get("recommended_queries", [])
        except Exception:
            # 완벽한 예외방어용 백업 코드
            groq_answer = full_response
            recommended_queries = ["정확한 질문 추천을 생성하지 못했습니다."]

        # 과거 매칭용 가게 코드 후속 탐색 로직 연동 완료 (동적 IN 절 쿼리)
        recommendations = []
        try:
            # 검색된 맛집 일련번호(STORE_CODE)가 존재할 때만 MySQL에 동적 조회 요청
            if store_codes and self.DBOpen():
                # SQL IN 절에 매핑하기 위해 포맷팅 (예: '12345', '67890')
                placeholders = ", ".join([f"'{code}'" for code in store_codes])
                
                sql = f"""
                    SELECT STORE_CODE, STORE_NAME, ADDRESS_JI, CATEGORY, PN_RATE 
                    FROM STORE 
                    WHERE STORE_CODE IN ({placeholders})
                    ORDER BY PN_RATE DESC
                """
                print(f"SQL (동적 추천) :\n{sql}") # 콘솔에서 정상 격리 확인용 로그
                
                self.db.OpenSQL(sql)
                store_rows = self.db.getAll()
                
                if store_rows:
                    for row in store_rows:
                        recommendations.append({
                            "store_code": row['STORE_CODE'],
                            "store_name": row['STORE_NAME'],
                            "address": row['ADDRESS_JI'],
                            "category": row['category'] if 'category' in row else row.get('CATEGORY', ''),
                            "pn_rate": int(row['PN_RATE']) if row['PN_RATE'] is not None else 0
                        })
                self.db.DBClose()
            
            # 백업용 방어 코드 (코드가 없을 시 상위 1개 추출 유지)
            elif not store_codes and self.DBOpen():
                sql = "SELECT STORE_CODE, STORE_NAME, ADDRESS_JI, CATEGORY, PN_RATE FROM STORE ORDER BY PN_RATE DESC LIMIT 1"
                print(f"SQL (백업용) :\n{sql}")
                
                self.db.OpenSQL(sql)
                store_rows = self.db.getAll()
                if store_rows:
                    for row in store_rows:
                        recommendations.append({
                            "store_code": row['STORE_CODE'],
                            "store_name": row['STORE_NAME'],
                            "address": row['ADDRESS_JI'],
                            "category": row['CATEGORY'],
                            "pn_rate": int(row['PN_RATE']) if row['PN_RATE'] is not None else 0
                        })
                self.db.DBClose()

        except Exception as db_err:
            print(f"MySQL 연동 중 오류: {db_err}")

        # 참조용 리뷰 텍스트 리스트 가공
        referenced_contents = [doc.page_content.split("리뷰 내용: ")[-1].strip() for doc in searched_docs] if searched_docs else ["FAISS 검색 연동됨"]

        return True, {
            "answer": groq_answer,
            "referenced_reviews": referenced_contents,
            "recommendations": recommendations,
            "recommended_queries": recommended_queries 
        }

if __name__ == "__main__":
    print("\n=== 🛠️ RAGManager LangChain/LCEL 컴포넌트 디버깅 및 가동 ===")
    rag = RAGManager()
    
    # 1. 인덱스가 있다면 가져오고, 없다면 새로 빌드 처리 진행
    if not rag.InitRetriever():
        if rag.DBOpen():
            rag.BuildVectorDB()
            rag.DBClose()
        else:
            print("❌ DB 연결 실패로 최초 벡터 빌드를 수행할 수 없습니다.")
            os._exit(1)
            
    # 2. 파이프라인 컴포넌트 체인 가동
    rag.CreateConversationalChain()
    
    # 3. 콘솔 테스트 인터페이스 동작 테스트
    print("\n" + "="*50)
    print(" 전주 맛집 RAG 챗봇 가동 (종료 키워드: q)")
    print("="*50)
    
    session_config = "team_project_session_01"
    
    while True:
        query = input("\n 질문 입력: ")
        if query.lower() in ['q', 'quit', 'exit', '종료']:
            break
        if not query.strip(): continue
            
        print("-" * 50)
        success, result = rag.RunQuery(query, session_id=session_config)
        
        if success:
            print(f"\n🤖 AI 분석 결과:\n{result['answer']}")
            print(f"\n💡 추천 질문 데이터 목록: {result['recommended_queries']}")
            print(f"\n🎯 실시간 DB 연동 가게 추천: {result['recommendations']}")
        print("-" * 50)
        
    print("=== 디버깅 및 구축 완료 ===")