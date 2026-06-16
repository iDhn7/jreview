"""
모듈명 : 맛집 리뷰를 이용한 RAG 서비스 모듈 (HTTP requests 안정화 버전)
작성일 : 2026.06.16
"""

import os
import dotenv
import chromadb
from chromadb.utils import embedding_functions
import requests  # openai 라이브러리 충돌 방지를 위해 requests 사용
import json
import traceback

# 제공해주신 DBManager 클래스 임포트 방어 처리
try:
    from DBManager import DBManager
except ImportError:
    from modules.DBManager import DBManager 

class RAGManager :
    def __init__(self) :
        # 현재 파일 기준 경로 추적
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
        
        # 벡터 스토어 경로를 프로젝트 루트 아래에 생성되도록 고정
        self.db_path_name = os.path.join(service_dir, "chroma_db")
        self.collection_name = "review_collection"

    def DBOpen(self) :
        return self.db.DBOpen(
            host    = os.getenv("host"),
            id      = os.getenv("user"),
            pw      = os.getenv("passwd"),
            dbname  = os.getenv("dbname")
        )  
        
    def DBClose(self) :
        self.db.DBClose()

    def BuildVectorDB(self) :
        try:
            chroma_client = chromadb.PersistentClient(path=self.db_path_name)
            sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            collection = chroma_client.get_or_create_collection(
                name=self.collection_name, 
                embedding_function=sentence_transformer_ef
            )
            sql = "SELECT REVIEW_CODE, STORE_CODE, CONTENT FROM REVIEW"
            if not self.db.OpenSQL(sql): return False
            reviews = self.db.getAll()
            
            ids, documents, metadatas = [], [], []
            for row in reviews:
                ids.append(f"G-{str(row['REVIEW_CODE']).zfill(4)}")
                documents.append(row['CONTENT'])
                metadatas.append({"mysql_review_code": row['REVIEW_CODE'], "STORE_CODE": row['STORE_CODE']})

            if ids:
                collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
                print(f"ChromaDB 구축 성공 ({len(ids)}건)")
        except Exception as e:
            print(f"클러스터 구축 에러: {e}")
            return False
        finally:
            self.db.CloseSQL()
        return True

    def RunQuery(self, query) :
        print(f"Groq 기반 RAG + 추천 질문 파이프라인 가동: '{query}'")

        if not self.groq_api_key:
            print("❌ [오류] GROQ_API_KEY가 비어있습니다.")
            return False, None

        # ----------------------------------------------------------------------
        # STEP 1: ChromaDB 벡터 검색
        # ----------------------------------------------------------------------
        try:
            chroma_client = chromadb.PersistentClient(path=self.db_path_name)
            sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            collection = chroma_client.get_or_create_collection(
                name=self.collection_name, 
                embedding_function=sentence_transformer_ef
            )
            results = collection.query(query_texts=[query], n_results=3)
        except Exception as e:
            print(f"❌ [ChromaDB 검색 오류]: {e}")
            results = None
        
        retrieved_contexts = []
        referenced_reviews = []
        matched_store_codes = set()
        
        if results and results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                doc = results['documents'][0][i]
                meta = results['metadatas'][0][i] if results['metadatas'] else {}
                review_id = results['ids'][0][i]
                
                referenced_reviews.append(f"리뷰 #{review_id}")
                if 'STORE_CODE' in meta and meta['STORE_CODE']:
                    matched_store_codes.add(meta['STORE_CODE'])
                retrieved_contexts.append(f"[리뷰 참고 내용]: {doc}")
                
        context_str = "\n".join(retrieved_contexts) if retrieved_contexts else "참고할 리뷰 데이터가 부족합니다."

        # ----------------------------------------------------------------------
        # STEP 2: 순수 HTTP Requests 방식으로 Groq API 호출 (안정성 극대화)
        # ----------------------------------------------------------------------
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        system_prompt = (
            "당신은 전주 지역 맛집 리뷰를 분석하여 요약하는 RAG AI 어시스턴트입니다.\n"
            "제공된 [리뷰 참고 내용]에 기반하여 질문에 한국어로 친절하게 답변하고, '추천 질문 3개'를 만들어 주세요.\n"
            "반드시 아래의 JSON 규격으로만 응답해야 합니다. 다른 텍스트는 절대 섞지 마세요:\n"
            "{\n"
            "  \"answer\": \"여기에 친절한 한국어 답변 요약 작성 (평균 긍정 비율 수치 등을 포함)\",\n"
            "  \"recommended_queries\": [\"추천 질문 1\", \"추천 질문 2\", \"추천 질문 3\"]\n"
            "}"
        )
        
        user_prompt = f"[리뷰 참고 내용]\n{context_str}\n\n[사용자 질문]\n{query}"
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        
        groq_answer = "리뷰 분석 답변 생성 중 오류가 발생했습니다."
        recommended_queries = ["추천 질문 데이터를 가져오지 못했습니다."]
        
        try:
            print("🚀 Groq API 서버에 HTTP 요청 발송 중...")
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            # HTTP 에러가 발생하면 여기서 곧바로 Exception 유도
            response.raise_for_status() 
            
            res_json = response.json()
            raw_json_str = res_json['choices'][0]['message']['content']
            parsed_data = json.loads(raw_json_str)
            
            groq_answer = parsed_data.get("answer", groq_answer)
            recommended_queries = parsed_data.get("recommended_queries", recommended_queries)
            print("✅ Groq API 응답 및 파싱 성공!")
            
        except Exception as api_err:
            print(f"❌ [Groq API 상세 에러 발생]: {api_err}")
            if 'response' in locals() and response is not None:
                print(f"⚠️ 서버 응답 본문: {response.text}")
            # 무음 종료 방지를 위해 기본값 채워서 진행되도록 예외 처리 우회

        # ----------------------------------------------------------------------
        # STEP 3: MySQL 매칭 데이터 연동
        # ----------------------------------------------------------------------
        recommendations = []
        try:
            if matched_store_codes:
                format_strings = ','.join(['%s'] * len(matched_store_codes))
                sql = f"""
                    SELECT STORE_CODE, STORE_NAME, ADDRESS_JI, CATEGORY, PN_RATE 
                    FROM STORE 
                    WHERE STORE_CODE IN ({format_strings})
                    ORDER BY PN_RATE DESC LIMIT 2
                """
                self.db.OpenSQL(sql, tuple(matched_store_codes))
            else:
                sql = "SELECT STORE_CODE, STORE_NAME, ADDRESS_JI, CATEGORY, PN_RATE FROM STORE ORDER BY PN_RATE DESC LIMIT 1"
                self.db.OpenSQL(sql)
            
            store_rows = self.db.getAll()
            for row in store_rows:
                recommendations.append({
                    "store_code": row['STORE_CODE'],
                    "store_name": row['STORE_NAME'],
                    "address": row['ADDRESS_JI'],
                    "category": row['CATEGORY'],
                    "pn_rate": int(row['PN_RATE']) if row['PN_RATE'] is not None else 0
                })
        except Exception as db_err:
            print(f"MySQL 매칭 에러: {db_err}")
        finally:
            self.db.CloseSQL()
        
        return True, {
            "answer": groq_answer,
            "referenced_reviews": referenced_reviews,
            "recommendations": recommendations,
            "recommended_queries": recommended_queries 
        }

if __name__ == "__main__":
    print("\n=== 🛠️ RAGManager 단독 디버깅 모드 가동 ===")
    rag = RAGManager()
    
    print(f"🧐 [검증] GROQ_API_KEY 적재 상태: {bool(rag.groq_api_key)}")
    
    if not rag.DBOpen():
        print("❌ DB 연결 실패")
        os._exit(1)
        
    print("✅ DB 연결 성공! 최종 파이프라인 호출 시작")

    try:
        success, result = rag.RunQuery("콩나물 국밥 평가 좋은 곳은?")
        if success and result:
            print("\n=================== [🎉 최종 출력 결과] ===================")
            print(f"🤖 AI 분석 결과:\n{result['answer']}")
            print(f"\n📑 참조된 리뷰 리스트: {result['referenced_reviews']}")
            print(f"\n🎯 연동 추천 가게 테이블 데이터: {result['recommendations']}")
            print(f"\n💡 화면 출력용 추천 질문 세트: {result['recommended_queries']}")
            print("===========================================================\n")
        else:
            print("❌ 파이프라인에서 데이터를 정상 수신하지 못함")
    except Exception as main_err:
        print("❌ 메인 실행부 치명적 예외 발생")
        traceback.print_exc()

    rag.DBClose()
    print("=== 디버깅 완료 ===")