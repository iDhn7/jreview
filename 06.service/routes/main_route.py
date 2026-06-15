# 📝 routes/main_route.py
from flask import Blueprint, render_template
import os

# 'main_view'라는 이름의 하위 청사진 설계도를 선언합니다.
main_bp = Blueprint('main_view', __name__)

# 중립 격리 파일에서 db 객체를 안전하게 수입
from routes.db_instance import db

@main_bp.route("/")
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
    sql_params = target_areas + target_areas
    if db.OpenSQL(graph3_sql, sql_params):
        trend_recent = db.getAll()
        db.CloseSQL()

    return render_template(
        "index.html", 
        businesses=businesses, 
        trend_area=trend_area, 
        trend_season=trend_season, 
        trend_recent=trend_recent
    )