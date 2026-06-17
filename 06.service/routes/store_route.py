# 📝 routes/store_route.py
from flask import Blueprint, request, jsonify, current_app

# 'store_view'라는 이름의 상세 페이지 하위 청사진 설계도를 선언합니다.
store_bp = Blueprint('store_view', __name__)

# 중립 격리 파일에서 db 객체를 안전하게 수입
from routes.db_instance import db

@store_bp.route("/api/store")
def get_store_detail():
    store_code = request.args.get('code')
    detail_data = {}
    if not store_code:
        return jsonify({"error": "store_code가 누락되었습니다."}), 400
    
    # STORE 테이블 조회
    store_sql = """
        SELECT s.*, 
               (SELECT COUNT(*) FROM REVIEW r WHERE r.STORE_CODE = s.STORE_CODE) AS REVIEW_CNT
        FROM STORE s
        WHERE s.STORE_CODE = %s;
    """
    if db.OpenSQL(store_sql, (store_code,)):
        # 현재 리스트 형태에서 0번 딕셔너리 뽑아오기 기믹 유지
        detail_data['store'] = db.getData(0) if db.getTotal() > 0 else {}
        db.CloseSQL()
    
    # MENU 테이블 조회
    menu_sql = "SELECT MENU_NAME, MENU_PRICE, CNT, BEST FROM MENU WHERE STORE_CODE = %s;"
    if db.OpenSQL(menu_sql, (store_code,)):
        detail_data['menus'] = db.getAll()
        db.CloseSQL()
        
    # REVIEW 테이블 조회
    review_sql = "SELECT CONTENT, REVIEW_PN, PN_SCORE, MONTH FROM REVIEW WHERE STORE_CODE = %s;"
    if db.OpenSQL(review_sql, (store_code,)):
        detail_data['reviews'] = db.getAll()
        db.CloseSQL()
        
    # WORD 테이블 조회
    # 언급 횟수 카운트, 가장 많이 언급된 순으로 20개 
    word_sql = """
        SELECT WORD, WORD_PN, COUNT(*) AS CNT
        FROM WORD 
        WHERE REVIEW_CODE IN (SELECT REVIEW_CODE FROM REVIEW WHERE STORE_CODE = %s)
        GROUP BY WORD, WORD_PN
        ORDER BY CNT DESC
        LIMIT 20;
    """
    if db.OpenSQL(word_sql, (store_code,)):
        detail_data['words'] = db.getAll()
        db.CloseSQL()

    # 30일간 일별 긍부정 추이 그래프
    # 오늘 날짜 기준 30일 전 범위에서 하루 단위로 
    # 그 날의 각각의 리뷰 별로 P또는 N이면 1로 COUNT해서 총 개수 세기
    trend_sql = """
        SELECT 
            WRITTEN_DT,
            COUNT(CASE WHEN REVIEW_PN = 'P' THEN 1 END) AS POS_CNT,
            COUNT(CASE WHEN REVIEW_PN = 'N' THEN 1 END) AS NEG_CNT
        FROM REVIEW
        WHERE STORE_CODE = %s 
          AND WRITTEN_DT >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY WRITTEN_DT
        ORDER BY WRITTEN_DT ASC;
    """

    if db.OpenSQL(trend_sql, (store_code,)):
        # datetime 이므로 자바스크립트가 읽기 편하게 문자열로 가공
        # 날짜 객체인지 확인 후 리스트 속 딕셔너리로 가공
        raw_trends = db.getAll()
        detail_data['daily_trends'] = [
            {
                "date": t['WRITTEN_DT'].strftime('%m-%d') if hasattr(t['WRITTEN_DT'], 'strftime') else str(t['WRITTEN_DT'])[5:10],
                "pos_cnt": t['POS_CNT'],
                "neg_cnt": t['NEG_CNT']
            }
            for t in raw_trends
        ]
        db.CloseSQL()

    #detail_data['KAKAO_API_KEY'] = current_app.config.get('KAKAO_API_KEY')
    
    return jsonify(detail_data)