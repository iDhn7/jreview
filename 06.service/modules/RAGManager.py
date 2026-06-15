"""
모듈명 : 맛집 리뷰를 이용한 RAG 서비스 모듈
작성일 : 2026.06.15

pip install chromadb sentence-transformers pymysql openai
"""

import os
import dotenv
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
import json

# 제공해주신 DBManager 클래스 임포트
from DBManager import DBManager

class RAGManager :
    def __init__(self) :
        dotenv.load_dotenv()

        #DBManager 객체 생성 및 초기화 
        self.db = DBManager()

        #GROQ API를 얻는다.
        self.groq_api_key = os.getenv("GROQ_API_KEY")

        #vector db 의 경로 설정
        self.db_path_name = "./chroma_db"

        #collection명 설정
        self.collection_name   = "review_collection"

    def DBOpen(self) :
        # MySQL 데이터베이스 연결
        isConnected = self.db.DBOpen(
            host    = os.getenv("host"),
            id      = os.getenv("user"),
            pw      = os.getenv("passwd"),
            dbname  = os.getenv("dbname")
        )  
        if not isConnected:
            print("MySQL 연결에 실패하여 작업을 중단합니다.")
            return False
        return True
        
    def DBClose(self) :
        self.db.DBClose()

    def BuildVectorDB(self) :
        """
         MySQL 데이터 기반 ChromaDB RAG 구축
        """
        try:
            # ChromaDB 및 한국어 지원 임베딩 모델 설정
            # 로컬에 'chroma_db' 폴더를 생성하여 벡터 데이터를 영구 저장(Persistent)합니다.
            chroma_client = chromadb.PersistentClient(path=self.db_path_name)
            
            # 한국어 문장 유사도 성능이 우수한 텍스트 임베딩 모델 지정
            sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"  # 필요 시 대규모 한국어 모델로 교체 가능
            )
            
            # 'review_collection' 이름의 컬렉션 가져오거나 생성
            collection = chroma_client.get_or_create_collection(
                name=self.collection_name, 
                embedding_function=sentence_transformer_ef
            )

            # 4. MySQL에서 REVIEW 테이블 데이터 조회 (워크플로우 2단계)
            # RAG 검색의 핵심이 되는 리뷰 본문(CONTENT)과 매칭을 위한 STORE_CODE, REVIEW_CODE를 가져옵니다.
            sql = "SELECT REVIEW_CODE, STORE_CODE, CONTENT FROM REVIEW"
            
            if not self.db.OpenSQL(sql):
                print("SQL 실행 중 에러가 발생했습니다.")
                return False

            # 5. 쿼리 결과 가져오기 및 벡터 DB 적재 (워크플로우 3단계)
            reviews     = self.db.getAll()
            total_count = self.db.getTotal()
            
            print(f"총 {total_count}개의 리뷰 데이터를 MySQL로부터 성공적으로 가져왔습니다.")

            # ChromaDB 대량 배치 입력을 위한 리스트 준비
            ids = []
            documents = []
            metadatas = []

            for row in reviews:
                # ChromaDB의 ID는 텍스트(String) 형태여야 하므로 변환합니다.
                # 웹 화면 UI에 나오는 포맷에 매칭하기 쉬운 규칙을 사용하거나 숫자를 문자로 바꿉니다.
                review_id = f"G-{str(row['REVIEW_CODE']).zfill(4)}" # 예: 42 -> G-0042
                
                ids.append(review_id)
                documents.append(row['CONTENT'])
                
                # 메타데이터에 가게 코드(STORE_CODE)를 넣어 나중에 관련 업체 추천 시 MySQL과 join할 수 있게 합니다.
                metadatas.append({
                    "mysql_review_code": row['REVIEW_CODE'],
                    "STORE_CODE": row['STORE_CODE']
                })

            # 준비된 데이터를 ChromaDB에 한 번에 빌드(Upsert)
            if ids:
                print("리뷰 텍스트 임베딩 및 ChromaDB 적재 중... (시간이 다소 소요될 수 있습니다)")
                collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                print(f"성공적으로 {len(ids)}개의 리뷰가 ChromaDB 벡터 스토어에 구축되었습니다!")
            else:
                print("MySQL REVIEW 테이블에 적재된 데이터가 없습니다.")

        except Exception as e:
            print(f"데이터 구축 중 오류 발생: {e}")
            return False
            
        finally:
            # 6. SQL 커서 종료 및 DB 자원 반환 (워크플로우 4단계)
            self.db.CloseSQL()
        
        return True

    def RunQuery(self,query) :
        """
        사용자의 질문(query)을 받아 벡터DB 검색 
        -> Groq API를 통해 맛집 분석 답변 및 '추천 질문 3개'를 동시 생성
        -> MySQL 가게 정보 매칭을 거쳐 웹 UI 최종 데이터 반환
        """
        print(f"Groq 기반 RAG + 추천 질문 파이프라인 가동: '{query}'")

        # ----------------------------------------------------------------------
        # STEP 1: ChromaDB(벡터DB)에서 유사 리뷰 검색
        # ----------------------------------------------------------------------
        chroma_client = chromadb.PersistentClient(path=self.db_path_name)
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        collection = chroma_client.get_or_create_collection(
            name=self.collection_name, 
            embedding_function=sentence_transformer_ef
        )
        
        results = collection.query(
            query_texts=[query],
            n_results=3
        )
        
        retrieved_contexts = []
        referenced_reviews = []
        matched_store_codes = set()
        
        if results and results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                doc = results['documents'][0][i]
                meta = results['metadatas'][0][i] if results['metadatas'] else {}
                review_id = results['ids'][0][i]
                
                referenced_reviews.append(f"리뷰 #{review_id}")
                if 'STORE_CODE' in meta:
                    matched_store_codes.add(meta['STORE_CODE'])
                
                retrieved_contexts.append(f"[리뷰 참고 내용]: {doc}")
                
        context_str = "\n".join(retrieved_contexts)

        # ----------------------------------------------------------------------
        # STEP 2: Groq API를 활용한 답변 및 추천 질문 동시 생성
        # ----------------------------------------------------------------------
        client = OpenAI(api_key=self.groq_api_key, base_url="https://api.groq.com/openai/v1")
        
        # 한 번의 API 호출로 완벽하게 구조화된 응답을 받기 위해 JSON 포맷을 유도합니다.
        system_prompt = (
            "당신은 전주 지역 맛집 및 숙박 리뷰를 분석하여 요약하는 RAG AI 어시스턴트입니다.\n"
            "제공된 [리뷰 참고 내용]에 기반하여 사용자의 질문에 답변을 생성하고, 사용자가 이어서 질문할 만한 '추천 질문 3개'를 만들어 주세요.\n\n"
            "지침사항:\n"
            "1. 해당 카테고리나 장소의 '평균 긍정 비율(예: 84%)'을 본문에 자연스럽게 포함하세요.\n"
            "2. 타 업체나 일반 시설 대비 구체적인 비교 수치(예: 12%p 높습니다)를 언급하세요.\n"
            "3. 사용자가 한눈에 파악할 수 있도록 주요 '호평 키워드'와 '주의(부정) 키워드'를 명시하세요.\n"
            "4. 추천 질문은 사용자가 한옥마을 투어 시 궁금해할 법한 내용(예: 주차 팁, 베스트 메뉴, 대기 시간 등)으로 3개를 작성하세요.\n\n"
            "출력 포맷 파싱을 위해 반드시 아래의 JSON 규격으로만 출력하세요:\n"
            "{\n"
            "  \"answer\": \"여기에 친절한 어조의 한국어 답변 요약 작성\",\n"
            "  \"recommended_queries\": [\"추천 질문 1\", \"추천 질문 2\", \"추천 질문 3\"]\n"
            "}"
        )
        
        user_prompt = f"[리뷰 참고 내용]\n{context_str}\n\n[사용자 질문]\n{query}"
        
        groq_answer = "리뷰 분석 답변 생성 중 오류가 발생했습니다."
        recommended_queries = [
            "한옥마을 근처 주차하기 편한 맛집이 어디인가요?",
            "이 숙소의 대표 베스트 메뉴와 가격은 어떻게 되나요?",
            "주말 웨이팅 시간을 줄일 수 있는 꿀팁이 있나요?"
        ] # 에러 발생 시 적용할 기본 백업 추천 질문
        
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"} # JSON 객체 출력 보장 옵션
            )
            
            # Groq가 리턴한 JSON 문자열 파싱
            raw_json_str = response.choices[0].message.content
            parsed_data = json.loads(raw_json_str)
            
            groq_answer = parsed_data.get("answer", groq_answer)
            recommended_queries = parsed_data.get("recommended_queries", recommended_queries)
            
        except Exception as e:
            print(f"❌ Groq API 호출 또는 파싱 실패: {e}")
            return False, None

        # ----------------------------------------------------------------------
        # STEP 3: DBManager를 사용하여 MySQL에서 관련 업체 추천 상세 데이터 조회
        # ----------------------------------------------------------------------
        recommendations = []
                
        try:
            if matched_store_codes:
                format_strings = ','.join(['%s'] * len(matched_store_codes))
                sql = f"""
                    SELECT STORE_CODE, STORE_NAME, ADDRESS_JI, CATEGORY, PN_RATE 
                    FROM STORE 
                    WHERE STORE_CODE IN ({format_strings})
                    ORDER BY PN_RATE DESC
                    LIMIT 2
                """
                self.db.OpenSQL(sql, tuple(matched_store_codes))
            else:
                sql = """
                    SELECT STORE_CODE, STORE_NAME, ADDRESS_JI, CATEGORY, PN_RATE 
                    FROM STORE 
                    ORDER BY PN_RATE DESC 
                    LIMIT 1
                """
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
                
        except Exception as e:
            print(f"MySQL 추천 데이터 매칭 중 에러: {e}")
            return False, None
        finally:
            self.db.CloseSQL()
        
        # ----------------------------------------------------------------------
        # STEP 4: 최종 웹 UI 프론트엔드로 전달할 결과 반환
        # ----------------------------------------------------------------------
        return True, {
            "answer": groq_answer,
            "referenced_reviews": referenced_reviews,
            "recommendations": recommendations,
            "recommended_queries": recommended_queries  # 💡 새로 추가된 추천 질문 목록 리스트
        }

if __name__ == "__main__":
    rag = RAGManager()
    if rag.DBOpen() == False :
        print("DB 연결 오류가 발생하였습니다.")
        exit
    
    #RAG DB를 구축한다.
    #rag.BuildVectorDB()

    code, html = rag.RunQuery("콩나물 국밥 평가 좋은 곳은?")
    print(html)

    rag.DBClose()






