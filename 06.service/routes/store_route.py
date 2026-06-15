# 📝 routes/store_route.py
from flask import Blueprint, request, jsonify

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
    store_sql = "SELECT * FROM STORE WHERE STORE_CODE = %s;"
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
    review_sql = "SELECT CONTENT, REVIEW_PN, PN_SCORE FROM REVIEW WHERE STORE_CODE = %s LIMIT 10;"
    if db.OpenSQL(review_sql, (store_code,)):
        detail_data['reviews'] = db.getAll()
        db.CloseSQL()
        
    # WORD 테이블 조회
    word_sql = "SELECT WORD, WORD_PN FROM WORD WHERE REVIEW_CODE IN (SELECT REVIEW_CODE FROM REVIEW WHERE STORE_CODE = %s);"
    if db.OpenSQL(word_sql, (store_code,)):
        detail_data['words'] = db.getAll()
        db.CloseSQL()

    return jsonify(detail_data)