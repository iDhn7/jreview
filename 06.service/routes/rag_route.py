# 📝 routes/rag_route.py
from flask import Blueprint, request, jsonify
import os

# 'rag_view'라는 이름의 RAG 전담 하위 청사진 설계도를 선언합니다.
rag_bp = Blueprint('rag_view', __name__)

# 전역 변수로 관리하되, 안전하게 초기화
rag_manager = None

# 기존 프로젝트 구조와 싱크를 맞춰 RAGManager 임포트 및 초기화 시퀀스 실행
try:
    from modules.RAGManager import RAGManager
    rag_manager = RAGManager()
    
    # 💡 [핵심 추가] RAG 인덱스 자동 로드 및 초기화 시퀀스 작동
    # 1. 이미 빌드된 파일이 있는지 확인하고 로드 시도
    if not rag_manager.InitRetriever():
        print("📦 기구축된 FAISS 인덱스가 없습니다. 최초 1회 실시간 빌드를 시작합니다...")
        # 2. 파일이 없다면 MySQL REVIEW 테이블을 긁어서 최초 빌드 진행
        if rag_manager.DBOpen():
            rag_manager.BuildVectorDB()
            rag_manager.DBClose()
        else:
            print("❌ RAG 초기화 실패: MySQL 데이터베이스 연결을 열 수 없습니다.")
            
    # 3. 랭체인 LCEL 대화형 체인(bot_chain) 조립 및 대기 상태 전환
    rag_manager.CreateConversationalChain()
    print("✨ [RAG Blueprint] RAG 엔진 및 로컬 검색기가 완벽하게 초기화되었습니다.")

except Exception as e:
    print(f"❌ RAGManager 모듈 및 컴포넌트 로드 실패: {e}")
    rag_manager = None


@rag_bp.route("/api/rag", methods=["POST"])
def ask_rag_assistant():
    """
    RAG AI 어시스턴트 질의처리를 담당하는 비동기 API 엔드포인트
    """
    if not rag_manager:
        return jsonify({
            "answer": "서버의 AI 모듈이 정상적으로 로드되지 않았습니다. 관리자에게 문의하세요.",
            "referenced_reviews": [], "recommendations": [], "recommended_queries": []
        }), 500

    try:
        # 프론트엔드가 보낸 JSON 데이터 수신
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "질문(query) 내용이 누락되었습니다."}), 400
        
        user_query = data['query']
        print(f"🤖 [RAG Blueprint] 분석 요청 접수: {user_query}")
        
        # RAGManager의 핵심 검색/생성 함수 호출 (성공여부, 결과 딕셔너리 구조)
        success, result = rag_manager.RunQuery(user_query)
        
        if not success or not result:
            return jsonify({
                "answer": "죄송합니다. 리뷰 빅데이터를 분석하는 과정에서 일시적인 에러가 발생했습니다. 잠시 후 다시 시도해 주세요.",
                "referenced_reviews": [],
                "recommendations": [],
                "recommended_queries": []
            }), 200
            
        # 정형화된 JSON 패킷 반환
        return jsonify({
            "answer": result.get("answer", ""),
            "referenced_reviews": result.get("referenced_reviews", []),
            "recommendations": result.get("recommendations", []),
            "recommended_queries": result.get("recommended_queries", [])
        })

    except Exception as e:
        print(f"❌ /api/rag 비동기 처리 중 내부 치명적 예외 에러 발생: {e}")
        return jsonify({"error": "서버 내부 분석 오류가 발생했습니다."}), 500