"""
모듈명 : 네이버 지도에서 업체마다  url 수집
작성일 : 26.06.08
최종 변경일 : 26.06.08
작성자 : 조태현
구현내용 : 
맨처음 네이버 지도에서 수집하는 코드
페이지 넘어가면서 3페이지 진행중 메모리 아웃으로 페이지 하드코딩 한개씩 진행하면 csv 수집중
지금 올린 이파일은 전체 페이지 긁는 코딩으로 되어있음
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
from urllib.parse import unquote
import csv
import os

    # 1. 플레이라이트를 시작합니다.
with sync_playwright() as p:
    
    # 2. 브라우저 옵션 설정 (셀레늄의 uc.Chrome 옵션과 동일)
    browser = p.chromium.launch(
        headless=False,  # 화면에 크롬 창을 띄움
        args=["--disable-notifications","--disable-blink-features=AutomationControlled"])
    
    # 3. 사람 브라우저처럼 위장하기 위한 컨텍스트 설정
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.1.6 Safari/537.36",
        viewport={"width": 1920, "height": 1080})
    
    # 4. 실제 작업할 새 페이지 열기
    page = context.new_page()
    
    # 5. ★ 언디텍티드 핵심 (스텔스 모드 적용)
    page.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    """)

    region = ["전북대"]# ,"한옥마을","객사","신시가지"]
    for i in region:
        url = f"https://map.naver.com/p/search/전주%20{i}%20맛집"
        # https://map.naver.com/p/search/전주%20전북대%20맛집
        print(url)
        print(i,"지역의 맛집 정보를 크롤링합니다")
        page.goto(url)
        time.sleep(10)
        
        


        # iframe 전환
        search_frame = page.frame_locator("#searchIframe")
        # 클래스 이름에 'mBN2s'가 포함되어 있고, 텍스트가 정확히 '숫자(1-5)'인 'a' 태그 찾기 네이버엔 1-5까지 숫자 밖에 없기떄문에 하드코딩
        for idxx in range (1,6):
            search_frame.locator("a.mBN2s").get_by_text(re.compile(f"^{idxx}$")).click()

            time.sleep(8) # 결과를 확인하기 위한 대기

            # 스크롤 설정값
            scroll_pause_time = 3.0  # 스크롤 간 대기 시간
            load_wait_time = 5.0     # 마지막 도달 후 대기 시간

            # 1. 스크롤 가능한 컨테이너 찾기
            scroll_container = search_frame.locator("#_pcmap_list_scroll_container")

            # 2. 초기 높이 저장
            last_height = scroll_container.evaluate("element => element.scrollHeight")

            while True:
                # 3. 컨테이너 내부를 끝까지 스크롤
                scroll_container.evaluate("element => element.scrollTop = element.scrollHeight")
                time.sleep(scroll_pause_time)

            # 4. 새로운 높이 측정
                new_height = scroll_container.evaluate("element => element.scrollHeight")
            
            # 5. 높이가 변하지 않았으면 종료 (혹시 모를 로딩을 위해 한 번 더 확인)
                if new_height == last_height:
                    time.sleep(load_wait_time)
                    new_height = scroll_container.evaluate("element => element.scrollHeight")
                    if new_height == last_height:
                        print("모든 항목 로드 완료")
                        break
                    
                last_height = new_height

            list_items = search_frame.locator(".UEzoS.rTjJo").all()
            item_count = len(list_items)
            print(f"찾은 리스트 아이템 개수: {item_count}개")

            # min(40, item_count)를 사용하면 if 조건문 분기가 아예 필요 없어집니다.
            for idx in range(0, min(40, item_count)):
                # iframe을 새로 바꿨기 때문에, 현재 화면(searchIframe) 기준으로 요소를 매번 새로 찾아야 합니다.
                # iframe 세션 만료로 인해 인덱스 확인불가 상황이 자꾸지속됨
                current_items = search_frame.locator(".TYaxT").all()
                # 이제 인덱스 범위를 바로위에서 확인하고 진행
                current_items[idx].click()
                time.sleep(3)       

            print("지정한 범위 수집 완료, 다음 작업 바로 시작!")


       #     직접 확인하지않으면 데이터 로드 되지않아 개수 확인용
            # list_itemxs = search_frame.locator(".UEzoS.rTjJo").all()
            # item_countx = len(list_itemxs)
            item_countx = search_frame.locator(".UEzoS.rTjJo").count()
            print(f"찾은 리스트 아이템 개수: {item_countx}개")

            # sys.exit()

            # 여러 요소 가져오기

            store_locator = search_frame.locator(".TYaxT")
            item_countx = store_locator.count()      
            for idxx in range(item_countx):
                current_store = store_locator.nth(idxx)

                # 가게 이름 추출
                store_names = current_store.text_content().strip()

                # 상세 페이지 링크 추출, href 속성이 #으로 되어 있어서, 클릭 후 url 추출하는 방식으로 진행해야 할 듯
                current_store.click()
                page.wait_for_timeout(2500)
                target_url = unquote(page.url)
            
                if i == "전북대":
                    area = "A"
                elif i == "신시가지":
                    area = "B"
                else:
                    area = "C"
                store_code = target_url.split("place/")[1].split("?")[0]
                # 크롤링한 데이터를 임시 리스트에 저장하는 코드 (후에 db에 저장할 때 사용)
                data = {
                    "store_name": store_names,
                    "target_url": target_url ,
                    "store_code": store_code,
                    "area" : area 

                }
                print(data)
                # 💡 [CSV 저장 로직 시작]
                csv_file_path = "naver_stores.csv"
        
                # CSV 파일에 들어갈 열 이름(헤더) 정의
                fieldnames = ["store_name", "store_code", "area"]
        
                # 파일이 새로 생성되는 건지(헤더를 써야 하는지) 확인하기 위한 조건
                file_exists = os.path.isfile(csv_file_path)
        
                # 'a' 모드로 열어서 기존 데이터 아래에 계속 누적(Append)시킵니다.
                # encoding="utf-8-sig"로 해야 엑셀에서 열었을 때 한글이 깨지지 않습니다!
                with open(csv_file_path, mode="a", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
            
                    # 파일이 처음 만들어질 때만 맨 위에 제목(헤더)을 적어줍니다.
                    if not file_exists:
                        writer.writeheader()
                
                # 💡 기존 data 딕셔너리에서 필요한 3가지 값만 골라내어 CSV에 한 줄 씁니다.
                    writer.writerow({
                    "store_name": data["store_name"],
                    "store_code": data["store_code"],
                    "area": data["area"]
                    })
            
                print(f"-> {data['store_name']} CSV 저장 완료!")
                # 업체 상세 정보 url을 다음처럼 만들어서 각각 크롤링하는 코드 작성
                # 메뉴는 url 형식이 달라서 직접 클릭을 한 후에 데이터를 크롤링하는 방식으로 진행해야 할 듯
                # review_url = f"https://pcmap.place.naver.com/restaurant/{store_code}/review"
                # info_url = f"https://pcmap.place.naver.com/restaurant/{store_code}/information"
                # photo_url = f"https://pcmap.place.naver.com/restaurant/{store_code}/photo?filterType=업체"

                # 다시 iframe으로 돌아오기
                # driver.switch_to.default_content()
                # search_frame = page.frame_locator("#searchIframe")


    # 임    시 리스트에 저장된 데이터를 db에 저장하는 코드

    