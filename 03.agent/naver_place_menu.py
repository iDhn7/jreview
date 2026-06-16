'''
모듈명 : 네이버 지도에서 업체마다  메뉴 목록 밑 내용 수집
작성일 : 26.06.10
최종 변경일 : 26.06.16
작성자 : 조태현
구현내용 : 
수집된 업체 코드로 플레이 라이트로 메뉴 목록  수집(csv진행예정)
메뉴 부터 모든 업체 하기에는 시간이 모자랄수 있기때문에 각 상권마다 30개씩 진행 예정
bizes로 시작되는 특이케이스 주소는 사용 X (실질 서비스가 아니라 프로젝트를 위한 데이터수집)
판다스 라이브러리 사용 예정
코드 작성 정리
# uv 프로젝트 환경에 playwright 추가
uv add playwright
# playwright 브라우저 설치
uv run playwright install


로직
csv 업체 코드로 홈페이지 접속후
크롤링 데이터 수집
csv파일로 저장
'''





from time import strftime
from datetime import datetime, timedelta
import random
import re
import sys
import time
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
import pandas as pd


csv_path       =  "C:\\Users\\MYCOM\\Desktop\\크롤링연습\\3차 크롤링 자동화\\data\\"
naver_list_csv =  csv_path + "naver_list.csv"
naver_menu_csv =  csv_path + "naver_menu.csv"

# options.add_argument('headless') # 브라우저 창을 띄우지 않고 실행하려면 주석해제
def ReadCSV() :  
    df = pd.read_csv(naver_list_csv)
    return df["store_code"]

    codes      = []
    code_list  = ReadCSV()
    for code in code_list :
        codes.append(code)

def menuinfo(codes) :


# 1. 플레이라이트를 시작합니다.
        with sync_playwright() as p:
            
            # 2. 브라우저 옵션 설정 (셀레늄의 uc.Chrome 옵션과 동일)
            browser        = p.chromium.launch(
                headless   = False,  # 화면에 크롬 창을 띄움
                args       = ["--disable-notifications","--disable-blink-features=AutomationControlled"])
            
            # 3. 사람 브라우저처럼 위장하기 위한 컨텍스트 설정
            context        = browser.new_context(
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.1.1.100 Safari/537.36",
                viewport   = {"width": 1920, "height": 1080},
                locale="ko-KR",  # 언어 설정도 사람이 쓰는 것처럼 추가
                timezone_id="Asia/Seoul"
            )
            
            # 4. 실제 작업할 새 페이지 열기
            page           = context.new_page()
            
            # # 5. ★ 언디텍티드 핵심 (스텔스 모드 적용)
            # page.add_init_script("""
            #     Object.defineProperty(navigator, 'webdriver', {
            #         get: () => undefined
            #     });
            # """)
            # 데이터 넣을 공간 정의
            df = None
            
            for store_code in codes:
                # DB에서 꺼네서 적용해야됨 지금은 임시 주소 
                page.goto(f"https://pcmap.place.naver.com/restaurant/{store_code}/menu/list")
                # 안의 내용 텍스트 가져오기

                menu_list_base_count         = page.locator("div.place_section_content").first.locator("li").count()
                print(f"업체의 메뉴 개수 : {menu_list_base_count}개")
                menu_list_base               = page.locator("div.place_section_content").first.locator("li")
                for i in range(menu_list_base_count) : 
                    try : 
                        menu_cotegory        = menu_list_base.nth(i).locator("div.RzEpB").first.text_content(timeout=500).strip()
                    except : 
                        menu_cotegory        = "메뉴카테고리없음"
                        print(f"{i}번째 메뉴 카테고리 없음")
                    try :
                        menu_name_raw        = menu_list_base.nth(i).locator("div.hbpDw").text_content(timeout=500).strip()
                        menu_name            = menu_name_raw.replace(",", "").strip()
                    except : 
                        print(f"{i}번째 메뉴명 없음")
                        continue
                    try :
                        menu_description_raw = menu_list_base.nth(i).locator("div.FfCFG").text_content(timeout=500).strip()
                        no_comma             = menu_description_raw.replace(",", "")
                        menu_description     = re.sub(r'\s+', '', no_comma).strip()
                    except : 
                        print(f"{i}번째 메뉴설명 없음")
                        menu_description     = "메뉴설명없음"
                    try :
                        menu_price_raw       = menu_list_base.nth(i).locator("div.GXS1X").text_content(timeout=500).strip()
                        menu_price           = menu_price_raw.replace(",", "")
                    except : 
                        print(f"{i}번째 메뉴가격 없음")
                        menu_price           = "메뉴가격없음"
                    
                    print(f"{store_code},{menu_name},{menu_cotegory},{menu_description},{menu_price}")
                    
                    time.sleep(1.5)
                    data = {
                        '업체코드'      : [store_code], 
                        '메뉴명'        : [menu_name], 
                        '메뉴카테고리'  : [menu_cotegory],
                        '메뉴설명'      : [menu_description],
                        '메뉴가격'      : [menu_price]   
                    }
                    df1    = pd.DataFrame(data)
                    if df is None :
                        df = df1
                    else :
                        df = pd.concat([df, df1])
                    df.to_csv(naver_menu_csv, index=False)
                print(f"{i}번째 {store_code} 저장완료")
            browser.close()


menuinfo(ReadCSV())
