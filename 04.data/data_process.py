import os

import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

from service.modules.DBManager import DBManager


class DataProcess:
    def __init__(self):
       # .env 파일은 루트(D:\jreview)에 있으므로 한 단계 위('..')로 올라가서 찾습니다.
        load_dotenv(dotenv_path='D:\\jreview\\04.data\\service\\.env')
        
        # CSV 파일 로드 (경로 유지)
        self.df_info = pd.read_csv('04.data/store_info.csv')
        self.df_menu = pd.read_csv('04.data/menu.csv')
        self.df_review = pd.read_csv('04.data/review.csv')
        
        # DB 매니저 객체 생성
        self.db = DBManager()

    def DBOpen(self):
        # .env 값을 읽어 DBManager.DBOpen에 넘겨줍니다
        host = os.getenv('host')
        user = os.getenv('user')
        passwd = os.getenv('passwd')
        dbname = os.getenv('dbname')
        return self.db.DBOpen(host, user, passwd, dbname)

    def DBClose(self):
        self.db.DBClose()

    def ProcessInfo(self):
        print("\n--- STORE 데이터 등록 ---")
        sql = """
            INSERT INTO STORE 
            (STORE_CODE, STORE_NAME, ADDRESS_DO, ADDRESS_JI, PHONE, BUSINESS_HOURS, 
             PARKING, AMENITY, LAT, LNG, CATEGORY, STAR, STORE_IMAGE_URL, AREA, PN_RATE, AI_REPORT)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for i, row in self.df_info.iterrows():
            datas = (
                row['업체코드'], row['업체명'], row['주소'], None, 
                row['전화번호'], row['영업시간'], row['주차여부'], row['편의성정보'], 
                float(row['위도']), float(row['경도']), row['업체카테고리'], float(row['별점']), 
                row['업체사진'], None, 0.0, None
            )
            self.db.RunSQL(sql, datas)

    def ProcessMenu(self):
        print("\n--- MENU 데이터 등록 ---")
        sql = """
            INSERT INTO MENU (STORE_CODE, MENU_NAME, MENU_PRICE, CNT, BEST)
            VALUES (%s, %s, %s, %s, %s)
        """
        for i, row in self.df_menu.iterrows():
            content = str(row['메뉴내용']) if pd.notna(row['메뉴내용']) else ""
            is_best = 1 if '대표메뉴' in content else 0
            
            datas = (row['업체코드'], row['메뉴명'], int(row['메뉴가격']), 0, is_best)
            self.db.RunSQL(sql, datas)

    def ProcessReview(self):
        print("\n--- REVIEW 데이터 등록 ---")
        sql = """
            INSERT INTO REVIEW 
            (STORE_CODE, CONTENT, WRITTEN_DT, YEAR, MONTH, DAY, REVIEW_PN, PN_SCORE)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        for i, row in self.df_review.iterrows():
            dt = datetime.strptime(row['작성일'], "%Y-%m-%d")
            datas = (
                row['업체코드'], row['리뷰내용'], row['작성일'], 
                dt.year, dt.month, dt.day, None, 0.0
            )
            self.db.RunSQL(sql, datas)

# 메인 실행 흐름
if __name__ == "__main__":
    data = DataProcess()
    if data.DBOpen():
        try:
            data.ProcessInfo()
            data.ProcessMenu()
            data.ProcessReview()
            print("\n STORE, MENU, REVIEW 데이터 이관이 완료되었습니다!")
        except Exception as e:
            print(f"오류 발생: {e}")
        finally:
            data.DBClose()