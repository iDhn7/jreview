"""
모듈명 : 맛집 리뷰 데이터 파이프라인 (ETL) 및 AI 리포트 자동화 적재
작성일 : 26.06.15
최종 변경일 : 26.06.15
작성자 : 송민석, 손민건
구현내용 : 
CSV 파일(식당리스트, 식당정보, 메뉴, 리뷰)을 읽어와 전처리 후 MySQL DB에 적재하는  프로그램.
초기에는 데이터 적재와 AI 분석을 한 번에 묶어서 처리하려 했으나, API 토큰 제한과 중간 멈춤 현상 발생.
이를 해결하기 위해 기본 데이터 적재 함수와 AI 리포트 생성 함수를 분리함.
Ai 리포트의 경우 토큰제한문제로 19개까지 생성 


"""

import os
import time
from konlpy.tag import Okt

import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

from review_report import review_improvement_report
from review_define import run_review_predict

from modules.DBManager import DBManager

#STORE (업체 정보 테이블) 가공 중 ADDRESS_JI 처리
def get_ji_address(full_address):
    # 예시: '전북 전주시 완산구 팔달로 180' -> '전북 전주시 완산구' 까지만 우선 추출
    # 실제 데이터셋에 지번 정보가 없다면, 시/군/구까지만 넣는 것이 가장 안전합니다.
    parts = full_address.split(' ')
    if len(parts) >= 3:
        return f"{parts[0]} {parts[1]} {parts[2]}"
    return full_address

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

    def ProcessInfo(self):
        print("\n--- STORE 데이터 등록 ---")


        '''
        """
        기존 데이터를 삭제한다.
        """    
        self.db.RunSQL("DELETE FROM WORD")
        self.db.RunSQL("DELETE FROM REVIEW")
        self.db.RunSQL("DELETE FROM MENU")
        self.db.RunSQL("DELETE FROM STORE")
        '''

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
            
            """
            #업체리뷰 목록 얻기
            review_list = []
            items = self.df_review[ self.df_review["업체코드"] == code ]["리뷰내용"]
            for j in range(0,len(items)) :
                review_list.append(str(items.iloc[j]))
            ai_report = review_improvement_report(review_list)
            """

            # adderss_ji 전처리 함수 불러와서 사용. Nan 대비 해서 예외 처리
            raw_address = str(row['주소']).strip() if pd.notna(row['주소']) else ""
            ji_address  = get_ji_address(raw_address) if raw_address else ""

            datas = (
                row['업체코드'], row['업체명'], row['주소'], ji_address, 
                row['전화번호'], row['영업시간'], row['주차여부'], row['편의성정보'], 
                float(row['위도']), float(row['경도']), row['업체카테고리'], float(row['별점']), 
                row['업체사진'], area, 0.0, None
            )
            self.db.RunSQL(sql, datas)            

    def ProcessMenu(self):
        print("\n--- MENU 데이터 등록 ---")

        """
        기존 데이터를 삭제한다.
        """
        self.db.RunSQL("DELETE FROM MENU")

        sql = """
            INSERT INTO MENU (STORE_CODE, MENU_NAME, MENU_PRICE, CNT, BEST)
            VALUES (%s, %s, %s, %s, %s)
        """
        for i, row in self.df_menu.iterrows():
            content = str(row['메뉴내용']) if pd.notna(row['메뉴내용']) else ""
            is_best = 1 if '대표메뉴' in content else 0
            # 숫자가 아닌 값 예외
            try:
                price = int(row['메뉴가격'])
            except (ValueError, TypeError):
                price = 0   # '무료' 등 숫자가 아닌 값 방어
            datas = (row['업체코드'], row['메뉴명'], price, 0, is_best)
            self.db.RunSQL(sql, datas)

    def ProcessReview(self):
        print("\n--- REVIEW 데이터 등록 ---")
        
        okt   = Okt()

        """
        기존 데이터를 삭제한다.
        """
        self.db.RunSQL("DELETE FROM WORD")
        self.db.RunSQL("DELETE FROM REVIEW")
                
        sql = """
            INSERT INTO REVIEW 
            (STORE_CODE, CONTENT, WRITTEN_DT, YEAR, MONTH, DAY, REVIEW_PN, PN_SCORE)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        total = len(self.df_review)

        for i, row in self.df_review.iterrows():
            print(f"{ i + 1 } / { total }번째 리뷰 처리중....")

            #긍정,부정 등을 검사한다.
            try:
                word_pn,pn_score = run_review_predict(row['리뷰내용']);
            except (ValueError, TypeError):
                print(f"  ↳ 리뷰내용 형식 오류, 건너뜀: {row['리뷰내용']}")
                continue

            # 코드 터짐 방지 예외처리
            try:
                dt = datetime.strptime(str(row['작성일']).strip(), "%Y-%m-%d")
            except (ValueError, TypeError):
                print(f"  ↳ 작성일 형식 오류, 건너뜀: {row['작성일']}")
                continue

            datas = (
                row['업체코드'], row['리뷰내용'], row['작성일'], 
                dt.year, dt.month, dt.day, word_pn, pn_score
            )
            self.db.RunSQL(sql, datas)

            self.db.OpenSQL("SELECT LAST_INSERT_ID() AS CODE")
            review_code = self.db.getData(0)["CODE"];  #등록된 리뷰 코드를 얻는다.
            self.db.CloseSQL()
            

            #리뷰 단어 처리
            #words = okt.morphs(row['리뷰내용'])   # 모든 품사를 추출
            #words = okt.nouns(row['리뷰내용'])      # 명사만 추출
            words = okt.pos(row['리뷰내용'])      # 명사만 추출
        
            sql_word = """
                INSERT INTO WORD 
                (REVIEW_CODE, WORD, WORD_PN)
                VALUES (%s, %s, %s)
            """            
            for item in words :
                word  = item[0]  #단어
                pumsa = item[1] #품사
                #print(f"{word}:{pumsa}")
                if pumsa == "Noun" or pumsa == "Adjective" or pumsa == "Verb" :
                    #명사,동사,형용사만 등록
                    datas = (
                        review_code, word,word_pn
                    )
                    self.db.RunSQL(sql_word, datas)
        '''
    def RunAfter(self) :
        #메뉴에 대한 언급횟수 업데이트 방향 
        SELECT MENU_CODE,MENU_NAME,STORE_CODE FROM MENU

        MENU_CODE = 1
        MENU_NAME  = "국밥"
        STORE_CODE = "ST001"

        SELECT COUNT(*) AS TOTAL 
        FROM REVIEW
        WHERE STORE_CODE = 'ST001' AND CONTENT LIKE '%국밥%'


        UPDATE MENU SET CNT = 10 WHERE MENU_CODE = 1
       '''
    def RunAfter(self) :
        print("\n--- 마무리 작업: 메뉴 언급 횟수 업데이트 ---")
        
       # "REVIEW(리뷰) 테이블에서 메뉴 이름이 들어간 리뷰 개수를 세어, MENU(메뉴) 테이블의 CNT 컬럼에 저장하는 쿼리입니다."
        sql = """
            UPDATE MENU M
            SET CNT = (
                SELECT COUNT(*) 
                FROM REVIEW R 
                WHERE R.STORE_CODE = M.STORE_CODE 
                AND R.CONTENT LIKE CONCAT('%', M.MENU_NAME, '%')
            )
        """
        
        try:
            self.db.RunSQL(sql)
            print("메뉴 언급 횟수(CNT) 업데이트가 성공적으로 완료되었습니다!")
        except Exception as e:
            print(f"메뉴 언급 횟수 업데이트 중 오류 발생: {e}")  
            # -----------------------------------------------------
        # 2. 추가된 로직: 식당별 평균 긍정 점수(PN_RATE) 업데이트
        # -----------------------------------------------------
        # REVIEW 테이블에 있는 해당 식당의 PN_SCORE(긍정 점수) 평균을 구해서 STORE에 덮어씁니다.
        # IFNULL을 써서 리뷰가 없는(Null) 식당은 0으로 처리합니다.
        
        sql = """
            UPDATE STORE S
            SET PN_RATE = (
                -- 기존: SELECT IFNULL(AVG(PN_SCORE), 0)
                -- 수정: 평균값에 100을 곱하고 반올림하여 정수로 변환
                SELECT IFNULL(ROUND(AVG(PN_SCORE) * 100), 0)
                FROM REVIEW R
                WHERE R.STORE_CODE = S.STORE_CODE
            )
        """
        try:
            self.db.RunSQL(sql)
            print("▶ 2. 식당별 평균 긍정률(PN_RATE) 일괄 업데이트 완료!")
        except Exception as e:
            print(f"PN_RATE 업데이트 오류: {e}")

        #AI 개선사항 업데이트  , "CSV 파일에서 읽어온 데이터프레임(df)의 리뷰 내용을 AI로 분석하여, 아직 결과가 없는 가게(STORE) 테이블의 데이터베이스에 분석 내용을 저장하는 코드
    def ProcessAIReport(self) :
        print("\n--- AI 개선사항 업데이트 ---")
        
        self.db.OpenSQL("SELECT STORE_CODE FROM STORE WHERE AI_REPORT IS NULL")
        targets = self.db.getAll()

        total = len(targets)
        for i, item in enumerate(targets):
            code = item['STORE_CODE']
            # 
            try:
                items = self.df_review[self.df_review["업체코드"] == code]["리뷰내용"]
                if not items.empty:
                    # AI 분석 함수
                    ai_report = review_improvement_report(items.astype(str).tolist())
                else:
                    ai_report = "리뷰 없음"
            except Exception as e:
                ai_report = f"분석 오류: {e}"

            #DB 업데이트
            sql = "UPDATE STORE SET AI_REPORT = %s WHERE STORE_CODE = %s"
            self.db.RunSQL(sql, (ai_report, code))

            print(f"{i + 1} / {total}번째 업체 업데이트 완료: {code}")
            time.sleep(1)

            '''
            review_list = []
            items = self.df_review[ self.df_review["업체코드"] == code ]["리뷰내용"]
            for j in range(0,len(items)) :
                review_list.append(str(items.iloc[j]))
            ai_report = review_improvement_report(review_list)
            '''

# 메인 실행 흐름
if __name__ == "__main__":
    data = DataProcess()
    if data.DBOpen():
        try:
            #기본 데이터 등록 처리
            #가게 데이터 등록 
            #data.ProcessInfo()
            #메뉴 데이터 등록 
            #data.ProcessMenu()
            #리뷰 데이터 등록
            #data.ProcessReview()

            #데이터 등록 후 마무리 작업처리
            #AI 리포트 등록, 이게 api 키쓰는 작업 
            #data.ProcessAIReport()
            #메뉴 언급 횟수 
            data.RunAfter()
            
            #print("\n STORE, MENU, REVIEW 데이터 이관이 완료되었습니다!")
            #print("\n AI 리포트 업데이트가 완료되었습니다!")
            print("\n 메뉴 언급 횟수 업데이트가 완료되었습니다!")
        except Exception as e:
            print(f"오류 발생: {e}")
        finally:
            data.DBClose()