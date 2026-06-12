import os

import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

from review_report import review_improvement_report

from modules.DBManager import DBManager


class DataProcess:
    def __init__(self):
       # .env 파일은 루트(D:\jreview)에 있으므로 한 단계 위('..')로 올라가서 찾습니다.
        load_dotenv(dotenv_path='D:\\jreview\\04.data\\.env')
        
        # CSV 파일 로드 (경로 유지)
        self.df_list   = pd.read_csv('04.data/store_list.csv')
        self.df_info   = pd.read_csv('04.data/store_info.csv')
        self.df_menu   = pd.read_csv('04.data/menu.csv')
        self.df_review = pd.read_csv('04.data/review.csv')
        
        # DB 매니저 객체 생성
        self.db = DBManager()

    def DBOpen(self):
        # .env 값을 읽어 DBManager.DBOpen에 넘겨줍니다
        host   = os.getenv('host')
        user   = os.getenv('user')
        passwd = os.getenv('passwd')
        dbname = os.getenv('dbname')
        return self.db.DBOpen(host, user, passwd, dbname)

    def DBClose(self):
        self.db.DBClose()

    def DataClear(self) :
        """
        기존 데이터를 삭제한다.
        """
        self.db.RunSQL("DELETE FROM WORD")
        self.db.RunSQL("DELETE FROM REVIEW")
        self.db.RunSQL("DELETE FROM MENU")
        self.db.RunSQL("DELETE FROM STORE")


    def ProcessInfo(self):
        print("\n--- STORE 데이터 등록 ---")

        total = len(self.df_info)

        sql = """
            INSERT INTO STORE 
            (STORE_CODE, STORE_NAME, ADDRESS_DO, ADDRESS_JI, PHONE, BUSINESS_HOURS, 
             PARKING, AMENITY, LAT, LNG, CATEGORY, STAR, STORE_IMAGE_URL, AREA, PN_RATE, AI_REPORT)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        for i, row in self.df_info.iterrows():
            print(f"{ i + 1 } / { total }번째 업체 처리중....")

            code = row['업체코드']

            #상권(상권 구분 값 얻기)
            area = self.df_list[ self.df_list["업체코드"] == code ]["상권"]
            area = str(area.iloc[0]).strip()
            

            #업체리뷰 목록 얻기
            review_list = []
            items = self.df_review[ self.df_review["업체코드"] == code ]["리뷰내용"]
            for j in range(0,len(items)) :
                review_list.append(str(items.iloc[j]))
            ai_report = review_improvement_report(review_list)

            datas = (
                row['업체코드'], row['업체명'], row['주소'], None, 
                row['전화번호'], row['영업시간'], row['주차여부'], row['편의성정보'], 
                float(row['위도']), float(row['경도']), row['업체카테고리'], float(row['별점']), 
                row['업체사진'], area, 0.0, ai_report
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
            data.DataClear()
            data.ProcessInfo()
            """
            data.ProcessMenu()
            data.ProcessReview()
            """
            print("\n STORE, MENU, REVIEW 데이터 이관이 완료되었습니다!")
        except Exception as e:
            print(f"오류 발생: {e}")
        finally:
            data.DBClose()