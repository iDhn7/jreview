'''
main.py
작성자 : 이승현
작성일 : 2026-06-11
설명 : Flask 웹 애플리케이션의 진입점입니다. DBManager 클래스를 사용하여 MySQL 데이터베이스에 연결하고, 기본 라우트를 설정하여 index.html을 렌더링합니다.

[워크플로우]
0. 환경 구성: dotenv를 사용하여 환경 변수를 로드하고 Flask 애플리케이션을 초기화합니다.
1. DB 연결: DBManager 클래스를 인스턴스화하고, DBOpen 메서드를 호출하여 MySQL 데이터베이스에 연결합니다.
2. 라우트 설정: "/" 경로에 대한 라우트를 설정하여 index.html을 렌더링합니다.
3. 애플리케이션 실행: Flask 애플리케이션을 실행하여 웹 서버를 시작합니다.

[설치 방법]
pip install flask python-dotenv pymysql
'''
from flask import Flask, render_template, request, jsonify
import dotenv
import os
from modules.DBManager import DBManager as dbm

# [워크플로우 0단계: 환경 구성]
dotenv.load_dotenv()
app = Flask(__name__)

# [워크플로우 1단계: DB 연결]
db = dbm()
db.DBOpen(
    host=os.getenv("host"),
    id=os.getenv("user"),
    pw=os.getenv("passwd"),
    dbname=os.getenv("dbname")
)
print(os.getenv("host"), os.getenv("user"), os.getenv("passwd"), os.getenv("dbname"))

# [워크플로우 2단계: 라우트 설정(메인)]
@app.route("/")
def index():
    # 상권 리스트 정의 
    target_areas = ('전북대', '신시가지', '객사', '한옥마을')

    # 메인 화면 업체 목록 조회
    businesses_sql = """
        SELECT 
            s.STORE_CODE, s.STORE_NAME, s.ADDRESS_DO, s.CATEGORY, 
            s.STAR, s.STORE_IMAGE_URL, s.AREA, s.PN_RATE,
            (SELECT COUNT(*) FROM REVIEW r WHERE r.STORE_CODE = s.STORE_CODE) AS REVIEW_CNT
        FROM STORE s
        WHERE s.AREA IN (%s, %s, %s, %s);
    """
    businesses = []
    if db.OpenSQL(businesses_sql, target_areas):
        businesses = db.getAll()
        db.CloseSQL()

    # [GRAPH 1] 상권별 긍부정 평가
    graph1_sql = """
        SELECT 
            AREA,
            ROUND(AVG(PN_RATE), 1) AS AVG_PN_RATE,
            ROUND(100 - AVG(PN_RATE), 1) AS AVG_NN_RATE
        FROM STORE
        WHERE AREA IN (%s, %s, %s, %s)
        GROUP BY AREA;
    """
    trend_area = []
    if db.OpenSQL(graph1_sql, target_areas):
        trend_area = db.getAll()
        db.CloseSQL()

    # [GRAPH 2] 상권별 계절 추이
    graph2_sql = """
        SELECT 
            s.AREA,
            CASE 
                WHEN r.MONTH IN (3, 4, 5) THEN '봄 (3-5월)'
                WHEN r.MONTH IN (6, 7, 8) THEN '여름 (6-8월)'
                WHEN r.MONTH IN (9, 10, 11) THEN '가을 (9-11월)'
                ELSE '겨울 (12-2월)'
            END AS SEASON,
            COUNT(r.REVIEW_CODE) AS TOTAL_REVIEWS
        FROM STORE s
        JOIN REVIEW r ON s.STORE_CODE = r.STORE_CODE
        WHERE s.AREA IN (%s, %s, %s, %s)
        GROUP BY s.AREA, SEASON
        ORDER BY s.AREA, FIELD(SEASON, '봄 (3-5월)', '여름 (6-8월)', '가을 (9-11월)', '겨울 (12-2월)');
    """
    trend_season = []
    if db.OpenSQL(graph2_sql, target_areas):
        trend_season = db.getAll()
        db.CloseSQL()

    # [GRAPH 3] 최근 상권 트렌드
    graph3_sql = """
        SELECT 
            s.AREA,
            COUNT(r.REVIEW_CODE) AS RECENT_REVIEW_CNT,
            ROUND(
                (COUNT(r.REVIEW_CODE) / (
                    SELECT COUNT(*) 
                    FROM REVIEW sub_r
                    JOIN STORE sub_s ON sub_r.STORE_CODE = sub_s.STORE_CODE
                    WHERE sub_r.WRITTEN_DT >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                      AND sub_s.AREA IN (%s, %s, %s, %s)
                )) * 100, 1
            ) AS RATIO
        FROM STORE s
        JOIN REVIEW r ON s.STORE_CODE = r.STORE_CODE
        WHERE r.WRITTEN_DT >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
          AND s.AREA IN (%s, %s, %s, %s)
        GROUP BY s.AREA
        ORDER BY RECENT_REVIEW_CNT DESC;
    """
    trend_recent = []
    if db.OpenSQL(graph3_sql, target_areas + target_areas):
        trend_recent = db.getAll()
        db.CloseSQL()

    return render_template(
        "index.html", 
        businesses=businesses, 
        trend_area=trend_area, 
        trend_season=trend_season, 
        trend_recent=trend_recent
    )

# [워크플로우 2단계: 라우트 설정(상세)]
@app.route("/api/store")
def get_store_detail():
    store_code = request.args.get('code')
    detail_data = {}
    if not store_code:
        return jsonify({"error": "store_code가 누락되었습니다."}), 400
    
    # STORE 테이블 조회
    store_sql = "SELECT * FROM STORE WHERE STORE_CODE = %s;"
    if db.OpenSQL(store_sql, (store_code,)):
        detail_data['store'] = db.getAll()
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

# [워크플로우 3단계: 애플리케이션 실행]
if __name__ == "__main__" :
    app.run(host="0.0.0.0", port=8080, debug=True)