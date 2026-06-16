'''
모듈명 : 네이버 지도에서 업체마다  메뉴 목록 밑 내용 수집
작성일 : 26.06.12
최종 변경일 : 26.06.16
작성자 : 조태현
구현내용 : 
업체 코드별 리뷰 수집
리뷰 수집기준 : 25년도 5월부터 현재까지 
수집항목 : 업체코드, ID(작성자), 리뷰 내용, 작성일, 평가 카테고리(맛있어요, 아늑해요) 

# uv 프로젝트 환경에 playwright 추가
uv add playwright
# playwright 브라우저 설치
uv run playwright install

로직
페이지 접속 후 목록의 날짜 확인(처음 10개 더보기 누르르시 10개식 추가됨)
로딩된 목록의 날짜 확인후 지정한 날짜와 비교(지정 날짜보다 아래의 날짜면 다음 진행 아닐시 더보기 클릭)
목록 날짜나 100개 넘어갈시 다음 단계로 진행(시간이슈)
데이터 크롤링 후 수집
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


# D:\작업용폴더\3차 크롤링 자동화\data
 # options.add_argument('headless') # 브라우저 창을 띄우지 않고 실행하려면 주석해제
csv_path          =  "D:\\작업용폴더\\3차 크롤링 자동화\\data\\"
naver_list_csv    = csv_path + "naver_list.csv"
naver_review_csv  = csv_path + "naver_review.csv"
CUTOFF_DATE       = "2026-05-30"
# print(CUTOFF_DATE)
 # options.add_argument('headless') # 브라우저 창을 띄우지 않고 실행하려면 주석해제
def ReadCSV() :  
    df = pd.read_csv(naver_list_csv)
    return df["store_code"]

    codes      = []
    code_list  = ReadCSV()
    for code in code_list :
        codes.append(code)

def review_crawl(codes):
# 1. 플레이라이트를 시작합니다.
        with sync_playwright() as p:
            
            # 2. 브라우저 옵션 설정 (셀레늄의 uc.Chrome 옵션과 동일)
            browser = p.chromium.launch(
                headless=False,  # 화면에 크롬 창을 띄움
                args=["--disable-notifications","--disable-blink-features=AutomationControlled"])
            
            # 3. 사람 브라우저처럼 위장하기 위한 컨텍스트 설정
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="ko-KR",  # 언어 설정도 사람이 쓰는 것처럼 추가
                timezone_id="Asia/Seoul"
            )
            
            # 4. 실제 작업할 새 페이지 열기
            page = context.new_page()
            # 판다스 데이터 넣을 변수 생성
            df = None
            for store_code in codes:

                page.goto(f"https://pcmap.place.naver.com/restaurant/{store_code}/review/visitor?reviewSort=recent")
                
                page.wait_for_load_state("networkidle")
            
                print("접속 성공!")
                time.sleep(5)

                # 최신순으로 누르기
                page.click("//div[@class='place_option_area mlywZ']//a[@class='place_btn_option'][@role='option']")
                # new_list_button.click()
                time.sleep(2)
                def check_should_stop(page):
                # 현재 페이지에 로드된 모든 리뷰 요소를 가져옵니다.
                    li_elements = page.locator('li.place_apply_pui.EjjAW')
                    review_counts = li_elements.count()
                    print(f"\n--- [검사 시작] 현재 총 {review_counts}개의 리뷰를 검사합니다 ---")

                    for idxx in range(review_counts):
                        try:
                            target_span               = li_elements.nth(idxx).locator("xpath=./div[7]/div[2]/div[1]/span[1]/span[2]")
                            # 날짜 형식 변환 (%Y.%m.%d)
                            # 예: "2026년 4월 11일 토요일"
                            raw_text                  = target_span.inner_text().strip()  
                            print(f"[{idxx}번째] 추출된 텍스트: {raw_text}")
                            date_parts                = re.findall(r'\d+', raw_text)
                            time.sleep(0.5)
                            if len(date_parts) >= 3:
                                year                  = date_parts[0]
                                month                 = date_parts[1].zfill(2) # "5" -> "05" 로 변경
                                day                   = date_parts[2].zfill(2)   # "1" -> "01" 로 변경
                                
                                # 리뷰 날짜를 "2025-04-22" 포맷의 문장으로 조립
                                review_date_str       = f"{year}-{month}-{day}"
                                print(f"[{idxx}번째] 추출된 날짜문자열: {review_date_str}")
                                # 기준 날짜 말고 100개 기준 추가(시간 이슈)
                                if review_date_str < CUTOFF_DATE or review_counts >= 100:
                                    print(f" [{idxx}번째] 리뷰 날짜: {review_date_str} | 기준일({CUTOFF_DATE})보다 과거이므로 [멈춤]을 지시합니다!")
                                    # True를 반환하면 while True를 빠져나옴
                                    return True   
                                 

                                print(f" [{idxx}번째] 리뷰 날짜: {review_date_str}  (계속 수집)")

                        except Exception as e:
                            # 무한 루프가 돌 때 이 메시지가 주르륵 찍힌다면, XPath가 틀려서 날짜를 못 읽고 있는 것입니다!
                            # print(f" [{idxx}번째] 날짜 읽기 실패! (이유: {type(e).__name__}) -> 다음 리뷰로 넘어감")
                            continue
                    # 과거 날짜가 하나도 없으면 계속 더보기 클릭   
                    return False  
                
            # --- 실행 메인 루프 ---
                while True:
                # 1. [조회 및 결정] 현재 화면에서 멈춰야 할 과거 날짜가 나왔는지 판단
                    if check_should_stop(page):
                        print(">> [성공] 과거 날짜 조건을 만족하여 루프를 종료합니다. 버튼을 더 이상 누르지 않습니다.")
                        break  # while 루프 완전히 탈출
                    
                # 2. 과거 날짜가 없다면 아래로 내려와서 더보기 버튼을 누릅니다.
                    try:
                        more_button = page.locator('span.TeItc') 

                        if more_button.is_visible():
                            more_button.click()
                            print(">> [진행] 더보기 버튼 클릭 완료. 2초 대기...")
                            time.sleep(1)
                        else:
                            print(">> 더보기 버튼이 화면에 보이지 않아 종료합니다.")
                            break
                    except Exception as e:
                        print    (">> 더보기 버튼을 찾을 수 없거나 끝에 도달하여 종료합니다.")
                        break
                time.sleep(1)
                print            (" 모든 펼쳐내기 작업이 최종 종료되었습니다.")

                # 카테고리밑 더보기 때문에 버튼 모두 누르고난뒤 크롤링
                # 카테고리 밑에 있는 더보기 버튼 찾아서 모두 누르기
                # 1. 일단 전체 버튼이 몇 개인지 개수만 체크합니다.

                # 1. li 태그를 기준으로 전체 카테고리 상자 개수를 구합니다.
                # 클래스명 사이의 공백은 CSS 선택자에서 마침표(.)로 연결합니다.
                # 실제 li 개수
                items            = page.locator("//li[@class='place_apply_pui EjjAW']")
                total_items      = items.count()
                print            (f"총 {total_items}개의 카테고리 리스트(li)를 찾았습니다.")

                # 2. 개수만큼 반복합니다.
                for idr in range(total_items):
                    try:
                        # 동적 로딩 대응: 루프가 돌 때마다 li 목록을 매번 새로 가져옵니다.
                        #items = driver.find_elements(By.CSS_SELECTOR, "li.place_apply_pui")
                        # 위에서 더보기 눌러 갯수 동적 대응 불필요
                        current_item        = items.nth(idr)

                        # 현재 검사 중인 li 상자 자체를 화면 중앙으로 이동시킵니다. 셀레리움과 명령어 다름
                        current_item.scroll_into_view_if_needed()
                        time.sleep(0.5)

                        # 현재 li 상자 안에서만' 각각의 버튼을 찾습니다.
                        more_buttons        = current_item.locator("xpath=./div[5]/a[2]")
                        plus_buttons        = current_item.locator("xpath=./div[6]/a[1]")

                        # 해당 li 안에 버튼이 존재하는지 체크 (없으면 None)
                        target_button       = more_buttons if more_buttons.count() > 0 else None
                        target_plus_button  = plus_buttons if plus_buttons.count() > 0 else None

                        # 텍스트 읽어오기
                        button_text         = target_button.inner_text() if target_button else ""

                        # ------------------ [조건 분기 시작] ------------------

                        # [조건 1] 이 li 상자 안에 더보기 버튼이 있고, 글자도 '더보기'가 맞다면?
                        if target_button and "더보기" in button_text:
                            target_button.click()  # 일반 클릭 진행
                            print(f"[{idr + 1}/{total_items}] 해당 li의 '더보기' 버튼 클릭 완료 ")
                            time.sleep(2)  # 내용이 열리는 대기 시간

                        # [조건 2] '더보기' 글자가 없을 때만 이쪽 else로 들어옵니다.
                        else:
                            # 이 li 상자 안에 플러스 버튼이 존재한다면 바로 클릭!
                            if target_plus_button:
                                target_plus_button.click()  # 일반 클릭 진행
                                print(f"[{idr + 1}/{total_items}] 해당 li의 '플러스' 버튼 클릭 완료 ")
                                time.sleep(1)  # 내용이 열리는 대기 시간

                            # [조건 3] 둘 다 해당하지 않는 경우 패스
                            else:
                                print(f"[{idr + 1}/{total_items}] 누를 버튼이 없는 구역이라 패스합니다. ")

                    # ----------------------------------------------------
                    except Exception as e:
                        # 클릭 실패나 에러가 나도 프로그램을 멈추지 않고 다음 li로 넘어갑니다.
                        print(f"[{idr + 1}/{total_items}] 처리 중 실패 (에러 무시 후 다음 진행): {e}")
                # 리스트 개수 세기
                review_counts           = page.locator("//li[@class='place_apply_pui EjjAW']")
                review_counts_id        = review_counts.count()

                for idxxx in range(review_counts_id):
                    # 데이터 없음으로 인한 멈춤 방지 try 사용
                    try:
                        
                        reviewer_id_tag            = review_counts.nth(idxxx).locator("xpath=./div[1]/a[2]/div[1]/span[1]/span[1]")
                        if reviewer_id_tag.inner_text():
                            reviewer_id            = reviewer_id_tag.inner_text()
                            print                  (reviewer_id)  # 출력결과: 댓글쓴이
                        else:
                            print                  ("댓글쓴이를 찾지 못했습니다.")
                        time.sleep(1.5)
                        # 밖에서 펼치기로 로드 끝난 이후라서 버튼 찾아서 모두 누르기 한뒤에 for 문 돌려야됨    
                        # 카테고리 클릭 눌러야 더보기 내용도 보임 + 카테고리 내용 확인 span class "pui__jhpEyP"
                        # 댓글 내용   
                        review_contents            = review_counts.nth(idxxx).locator("xpath=./div[5]/a[1]")

                        if review_contents.inner_text():
                            content_text_raw       = review_contents.inner_text()
                            no_comma               = content_text_raw.replace(",", "")
                            content_text           = re.sub(r'\s+', '', no_comma).strip()
                        else:
                            print                  ("댓글내용을 찾지 못했습니다.")
                        time.sleep(1.5)
                        # 댓글 카테고리
                        review_categorys           = review_counts.nth(idxxx).locator("xpath=./div[6]")

                        if review_categorys.inner_text():
                            review_category        = review_categorys.inner_text().replace("요", "요_")
                            # 출력결과: 댓글카테고리
                            print                  (review_category)  
                        else:
                            print                  ("댓글카테고리를 찾지 못했습니다.")
                        time.sleep(1.5)
                        # 방문 날짜
                        reviewer_today_tag         = review_counts.nth(idxxx).locator("xpath=./div[7]/div[2]/div[1]/span[1]/span[2]")
                        if reviewer_today_tag.inner_text():
                            reviewer_today         = reviewer_today_tag.inner_text()
                            # 출력결과: 방문날짜
                            print(reviewer_today)  
                        else:
                            print                  (f"[{idxxx}] 방문날짜를 찾지 못했습니다.")
                        time.sleep(1.5)

                    except Exception as e:
                        print                      (f" 리뷰 에러: {e}")


                    # 업체코드, ID(작성자), 리뷰 내용, 작성일, 평가 카테고리(맛있어요, 아늑해요) 
                    data = {
                        '업체코드':        [store_code], 
                        'ID(작성자)':      [reviewer_id], 
                        '리뷰 내용':       [content_text],
                        '작성일' :         [reviewer_today],
                        '평가 카테고리' :  [review_category]
                        
                    }
                    df1                  = pd.DataFrame(data)
                    if df is None :
                        df               = df1
                    else :
                        df               = pd.concat([df, df1])
                    df.to_csv(naver_review_csv, index=False)
                    print(f"{store_code}, {reviewer_id} ,{content_text}, {reviewer_today}, {review_category} ,데이터 확인 ")
                    
                    print(f"{idxxx}번째 {store_code} 저장완료")

                print(f"업체코드 마무리 확인용")

            browser.close()
            time.sleep(20)
review_crawl(ReadCSV())