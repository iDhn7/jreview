"""
모듈명 : 네이버 지도에서 업체마다  url 수집
작성일 : 26.06.10
최종 변경일 : 26.06.16
작성자 : 조태현
구현내용 : 
수집된 업체 코드로 플레이 라이트로 수집(csv진행예정)
코드 작성 정리 
# uv 프로젝트 환경에 playwright 추가
uv add playwright
# playwright 브라우저 설치
uv run playwright install


로직

홈페이지 정보 창 접속
정보들 크롤링
홈페이지 홈 창 접속
크롤링
csv 양식으로 데이터 저장
"""



from time import strftime
from datetime import datetime, timedelta
import random
import re
import sys
import time
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup
import csv
import os

# 1. CSV 읽기 함수 (여전히 가장 깔끔하게 데이터를 읽어옵니다)
def ReadCSV(csv_list_path):
    data = []
    with open(csv_list_path, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if not row['store_name']: continue
            data.append(dict(row))
    return data

csv_file_path = "C:\\Users\\MYCOM\\Desktop\\크롤링연습\\3차 크롤링 자동화\\data\\naver_list.csv"
csv_file_temp = "C:\\Users\\MYCOM\\Desktop\\크롤링연습\\3차 크롤링 자동화\\data\\naver_info.csv"


if os.path.exists(csv_file_temp):
    os.remove(csv_file_temp)

# 2. CSV 파일 로드
all_stores = ReadCSV(csv_file_path)



def store_info(all_stores):
    #코드 담을 공간
    codes = []
    for store in all_stores:
        # 루프가 돌면서 1647184627, 2099020069 ... 순서대로 숫자가 담깁니다.
        codes.append(store['store_code'])


    with sync_playwright() as p:
        print("플레이라이트 시작...")
        
        # 브라우저 옵션 설정 (셀레늄의 uc.Chrome 옵션과 동일)
        browser = p.chromium.launch(
            headless=False,  # 화면에 크롬 창을 띄움
            args=["--disable-notifications","--disable-blink-features=AutomationControlled"])
        
        # 사람 브라우저처럼 위장하기 위한 컨텍스트 설정
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="ko-KR",  # 언어 설정도 사람이 쓰는 것처럼 추가
            timezone_id="Asia/Seoul"
        )
        
        # 실제 작업할 새 페이지 열기
        page = context.new_page() 
        
        #  언디텍티드  스텔스 모드 적용( 스텔스 감지하는것 같아서 사용 X )
        # page.add_init_script("""
        #     Object.defineProperty(navigator, 'webdriver', {
        #         get: () => undefined
        #     });
        # """)

        for store_code in codes:

            print(f"현재 업체 코드: {store_code}")

            # 업체 정보(업체소개, 편의시설) 수집하는 코드 작성
            # 이름,업체소개,편의시설,주차
            try:
                # 처음 들어갈떄 바로 블로그 리뷰로가게 주소 설정
                page.goto(f"https://pcmap.place.naver.com/restaurant/{store_code}/information")

                page.wait_for_load_state("domcontentloaded")

                print("접속 성공!")


                # 1.  가계이름
                page.wait_for_selector("span.GHAhO", timeout=10000)
                # 'GHAhO' 클래스를 가진 첫 번째 span 태그 찾기
                store_name_tag              = page.locator("span.GHAhO").text_content(timeout=500)
                if store_name_tag:
                    store_name              = store_name_tag.strip()
                    print(store_name)  
                else:
                    print("가게 이름을 찾지 못했습니다.")

                # 2.  카테고리 정보
                store_category_tag          = page.locator("span.lnJFt")
                if store_category_tag:
                    store_category          = store_category_tag.text_content(timeout=500)
                    print(store_category)

                else:
                    print("카테고리 정보를 찾지 못했습니다.")
                
                
                # 3. 업체 사진주소 한개만 대표이미지
                store_image_url             = page.locator("#business_1").get_attribute("src")
                
                time.sleep(3)
                if store_image_url:
                    print(f"업체사진주소: {store_image_url}")
                else:
                    store_image_url         = "업체사진주소없음"
                    print(f"업체사진주소: {store_image_url}")
                time.sleep(3)
                
                # 4.  편의시설
                try :
                    store_amenities_tags    = page.locator("ul.Uva5I li").all_text_contents()
        
                    # 찾은 태그들에서 텍스트만 뽑아서 공백을 제거하고 리스트로 만듭니다.
                    # (빈 텍스트가 있다면 걸러내는 조건도 추가)
                    store_amenities         = [tag.strip() for tag in store_amenities_tags if tag.strip()]
        
                    # 데이터가 있을 때와 없을 때 예외 처리 후 출력
                    if store_amenities:
                        # 리스트 안의 요소들을 구분(_)로 연결해서 하나의 문자열로 만듭니다.
                        store_amenities_str = "_".join(store_amenities)
                        print(f"편의시설: {store_amenities_str}")
                    else:
                        store_amenities_str = "편의시설 정보 없음"
                        print(store_amenities_str)
                except:
                    print("편의시설이 없습니다.")
                    store_amenities_str     = "편의시설 정보 없음"
                

                # 5. 주차 관련
                try:
                    store_parking           = page.locator('div.place_section_content div.pu5zX').text_content()
                    if store_parking:
                        # .text로 글자만 가져오고, .strip()으로 앞뒤 공백 제거
                        print(store_parking.strip())  
                    else:
                        print("주차 정보 없음")
                except:
                    print("주차 정보가 없습니다.")
                    
                # 페이지 변경전 확인용 프린트
                print(f" {store_name},{store_amenities_str},{store_parking},{store_category}")
                # 혹시 몰라서 밴 당할 위험 감소 딜레이
                time.sleep(10)
                # 홈 화면에서 정보 따오기
                # 업체이름, 방문자 리뷰 수 ,블로그 리뷰수, 주소 , 영업시간 , 전화번호,  
                page.goto(f"https://pcmap.place.naver.com/restaurant/{store_code}/home")
                page.wait_for_load_state("domcontentloaded")

                print("홈 화면 이동 완료")

                # 6. 주소
                # 지번과 도로명 모두 받아올려면 클릭후 생성되는 주소 가져와야됨
                page.locator('div.PIbes div').first.locator('div a').click()
                time.sleep(3)

                store_address            = page.locator('div.Y31Sf')
                # 찾은 태그들에서 텍스트만 뽑아서 공백을 제거하고 리스트로 만듭니다.
                # (빈 텍스트가 있다면 걸러내는 조건도 추가)
                store_address            = store_address.text_content().strip()                
                # 데이터가 있을 때와 없을 때 예외 처리 후 출력
                if store_address:
                    print(f"주소: {store_address}")
                else:
                    store_address = "주소없음"
                print(store_address)
                time.sleep(3)
                page.locator('span.pz7wy').click()
                time.sleep(3)

                # 7. 전화번호
                store_phone              = page.locator('span.xlx7Q')
                # (빈 텍스트가 있다면 걸러내는 조건도 추가)
                store_phone              = store_phone.text_content().strip()
                # 데이터가 있을 때와 없을 때 예외 처리 후 출력
                if store_phone:
                    print(f"전화번호: {store_phone}")
                else:
                    store_phone          = "전화번호없음"
                    print(f"전화번호: {store_phone}")
                
                time.sleep(3)
                



                # 8. 영업시간
                # 클릭해서 영업시간 데이터 가져오기 
                store_time               = page.locator('div.A_cdD').click()
        
                # 영업시간 로드안됨으로 인해 클릭해서 확인
                time.sleep(3)
                
                raw_times                = page.locator('a.gKP9i.RMgN0 *').all_text_contents()

                # 공백 제거 및 빈 텍스트 필터링
                store_text_times         = [text.strip() for text in raw_times if text.strip()]

                # 데이터가 있을 때와 없을 때 예외 처리 후 출력
                if store_text_times:
                    # 리스트 안의 요소들을 쉼표(,)로 연결해서 하나의 문자열로 만듭니다.
                    store_times_str      = "_".join(store_text_times)
                    print(f"{store_times_str}")
                else:
                    store_times_str      = "영업시간 정보 없음"
                    print(store_times_str)
                # 영업시간 클릭 해제 
                page.locator('div.A_cdD').click()
                time.sleep(3)

                # 별점 데이터 없는 경우 대비 트라이 사용
                try :            
                    store_score          = page.locator("span.PXMot.LXIwF").all_text_contents()
                    if store_score:
                        # 리스트의 첫 번째 알맹이('4.5')만 쏙 빼서 저장합니다.
                        store_score_text = store_score[0].strip()
                    else:
                        # 리스트가 비어있다면([]) 화면에 클래스가 없는 것이므로 '별점없음' 입력
                        store_score_text = "별점없음"
                    time.sleep(3)
                except Exception as e:
                    store_score_text     = "별점없음"

                print(store_score_text)
                time.sleep(3)
                store_data_x = "0"
                store_data_y = "0"
                data = {
                    "store_name"         : store_name,
                    "store_code"         : store_code,
                    "store_category"     : store_category,
                    "store_address"      : store_address,
                    "store_phone"        : store_phone,
                    "store_times_str"    : store_times_str,
                    "store_score_text"   : store_score_text,
                    "store_data_x"       : store_data_x,
                    "store_data_y"       : store_data_y,
                    "store_image_url"    : store_image_url,
                    "store_amenities_str": store_amenities_str,
                    "store_parking"      : store_parking

                }
                # 업체명, 업체코드, 업체카테고리, 주소, 전화번호, 영업시간, 별점, 위도, 경도 ,업체사진, 편의성 정보, 주차여부

                fieldnames               = ["store_name", "store_code", "store_category", "store_address",
                    "store_phone", "store_times_str", "store_score_text","store_data_x", "store_data_y","store_image_url",
                    "store_amenities_str", "store_parking"
                ]
        
                # 파일이 새로 생성되는 건지(헤더를 써야 하는지) 확인하기 위한 조건
                file_exists              = os.path.isfile(csv_file_temp)
        
                # 'a' 모드로 열어서 기존 데이터 아래에 계속 누적(Append)시킵니다.
                # encoding="utf-8-sig"로 해야 엑셀에서 열었을 때 한글이 깨지지 않습니다!
                with open(csv_file_temp, mode="a", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
            
                    # 파일이 처음 만들어질 때만 맨 위에 제목(헤더)을 적어줍니다.
                    if not file_exists:
                        writer.writeheader()

                    # 데이터 형식 위에 따름    
                    writer.writerow(data)
            
                print(f"-> {data['store_name']} CSV 저장 완료!")
                print("="*100)
                
            except Exception as e1:
                print(f"오류 발생: {e1}")
        browser.close()
store_info(all_stores)

#  위도 경도 위치는 따로 크롤링 X 컬럼만 저장 예정



