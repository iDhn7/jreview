

#   REVIEW 가공: 날짜를 년/월/일로 쪼개고, 텍스트에서 긍/부정 점수를 산출합니다.

#   WORD 가공: 가공된 리뷰 본문에서 띄어쓰기 기준으로 단어를 추출하고, 부모 리뷰의 긍/부정 속성을 물려받습니다.

#  STORE 가공: 업체 목록과 정보를 하나로 합치고(Merge), REVIEW 테이블을 참조하여 식당별 전체 리뷰 대비 긍정률(%)을 자동 계산합니다.

#  MENU 가공: 대표 메뉴에 뱃지를 달고, REVIEW 테이블을 뒤져서 해당 메뉴가 리뷰에서 몇 번 언급되었는지 언급수(Count)를 계산합니다.

import pandas as pd
import numpy as np
import re
from  review_define import run_reivew_predict
from review_report import review_improvement_report

class DataProcess :
    def __init__(self):
        self.df_info = pd.read_csv('04.data/store_info.csv')
        self.df_menu = pd.read_csv('04.data/menu.csv')
        self.df_review = pd.read_csv('04.data/review.csv')

    def DBOpen(self) :
        self.db = DBManager()
        self.db.DBOpen()

    def DBClose(self) :
        self.db.DBClose() :

    def ProcessInfo(self) :
        # 업체 정보를 데이터베이스에 등록한다.
        for i in range(0,len(df_info)) :
            sql  = "insert into (STORE_CODE,STORE_NAME,ADDRESS_DO,ADDRESS_JI,PHONE,BUSINESS_HOURS,PARKING,AMENITY,LAT,LNG,CATEGORY,STAR,STORE_IMAGE_URL,AREA,PN_RATE,REPORT)"
            sql += "vaues ("
            sql += f"'{ df_info.iloc[i]["업체코드"] }',"
            sql += f"'{ df_info.iloc[i]["업체명"] }',"
            
            items = df_review[ df_review["업체코드"] == "ST001"]
            print(items)
            review_list = []
            for j in range(0,len(items)) :
                review_list.append(items.iloc[j]["리뷰내용"])

            report = review_improvement_report(review_list)
            sql += f"'{ report }',"
            db.RunSQL(sql)

    def ProcessMenu(self) :
        # 업체 메뉴 정보를 데이터베이스에 등록한다.
        pass

    def ProcessReview(self) :
        # 업체 리뷰 정보를 데이터베이스에 등록한다.
        pass    

    def ProcessWord(self) :
        # 업체 리뷰 정보를 데이터베이스에 등록한다.
        pass        

data = DataProcess()
data.DBOpen()

data.ProcessInfo()
data.ProcessMenu()
data.ProcessReview()
data.ProcessWord()

data.DBClose()
