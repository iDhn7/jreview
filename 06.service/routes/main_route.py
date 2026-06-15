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

    # 2. ★ 파이썬에서 리스트를 9개까지만 자르기 (추가된 코드) ★
    businesses = businesses[:9]
    # 프론트엔드로 전달할 최종 데이터를 담을 리스트
    formatted_businesses = []
     
    for biz in businesses: 
        # db.getAll()의 반환 형태가 딕셔너리(dict)라고 가정합니다.
        # (만약 튜플 형태라면 biz['STORE_NAME'] 대신 biz[1]과 같이 인덱스로 접근해야 합니다.)
        
        pn_rate = biz.get('PN_RATE', 0.0)
        pn_rate = pn_rate if pn_rate is not None else 0.0
        
        # 긍정(pos), 부정(neg) 비율 계산 
        # (PN_RATE가 0~100 사이의 백분율 값이라고 가정)
        pos_val = int(pn_rate)
        neg_val = 100 - pos_val
        
        # 카테고리 기반 임의 아이콘 설정 (프론트엔드 예시 형태에 맞춤)
        category = biz.get('CATEGORY', '기타')
        icon = '🍽️'
        if category and ('카페' in category or '빵' in category):
            icon = '🥐'
        elif category and '한식' in category:
            icon = '🍚'
            
        # JS 객체 구조에 맞춰 딕셔너리 생성
        biz_data = {
            "id": biz.get('STORE_CODE'),      # DB 스키마가 VARCHAR이므로 문자열 타입 유지
            "name": biz.get('STORE_NAME'),
            "icon": icon,
            "category": category,
            "location": biz.get('ADDRESS_DO'), 
            "reviews": biz.get('REVIEW_CNT', 0), # 서브쿼리로 가져온 리뷰 수
            "rating": biz.get('STAR', 0.0),      # DB 스키마의 FLOAT 타입 유지
            "pos": pos_val,
            "neg": neg_val,
            "desc": "", # 현재 SELECT 문에 설명 컬럼(AI_REPORT 등)이 없으므로 빈 문자열 처리
            "image_url": biz.get('STORE_IMAGE_URL'), # 프론트엔드 이미지 렌더링용 추가
            "menu": []  # 메뉴 테이블(MENU) 쿼리가 제공되지 않아 우선 빈 배열로 초기화
        }
        
        formatted_businesses.append(biz_data)

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

    
    
    # [GRAPH 2] 상권별 계절 추이 (SQL의 ORDER BY FIELD는 제거해도 무방합니다)
    graph2_sql = """
        SELECT 
            s.AREA,
            CASE 
                WHEN MONTH(r.WRITTEN_DT) IN (3, 4, 5) THEN '봄 (3-5월)'
                WHEN MONTH(r.WRITTEN_DT) IN (6, 7, 8) THEN '여름 (6-8월)'
                WHEN MONTH(r.WRITTEN_DT) IN (9, 10, 11) THEN '가을 (9-11월)'
                ELSE '겨울 (12-2월)'
            END AS SEASON,
            COUNT(r.REVIEW_CODE) AS TOTAL_REVIEWS
        FROM STORE s
        JOIN REVIEW r ON s.STORE_CODE = r.STORE_CODE
        WHERE s.AREA IN (%s, %s, %s, %s)
        GROUP BY s.AREA, SEASON;
    """
    trend_season = []
    if db.OpenSQL(graph2_sql, target_areas):
        trend_season = db.getAll()
        db.CloseSQL()

    # ================= [★ 순서 강제 및 0개 데이터 보정 로직] =================
    # 내가 원하는 순서대로 리스트를 고정합니다.
    seasons_order = ['봄 (3-5월)', '여름 (6-8월)', '가을 (9-11월)', '겨울 (12-2월)']
    
    # DB 결과를 빠르게 찾을 수 있도록 딕셔너리로 변환합니다.
    season_dict = {(row['AREA'], row['SEASON']): row['TOTAL_REVIEWS'] for row in trend_season}
    
    # 모든 상권과 모든 계절(4개)이 무조건 순서대로 채워지도록 재조립합니다.
    fixed_trend_season = []
    for area in target_areas:
        for season in seasons_order:
            # 데이터가 없으면 자동으로 0이 들어갑니다.
            count = season_dict.get((area, season), 0) 
            fixed_trend_season.append({
                'AREA': area,
                'SEASON': season,
                'TOTAL_REVIEWS': count
            })
    # =========================================================================

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
        trend_season=fixed_trend_season,
       # trend_season=trend_season, 
        trend_recent=trend_recent
    )


