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


# db에 저장된 업체 코드 리스트 불러오는 코드 작성
codes = ["1163302976"]

# 1. 플레이라이트를 시작합니다.
with sync_playwright() as p:
    
    # 2. 브라우저 옵션 설정 (셀레늄의 uc.Chrome 옵션과 동일)
    browser = p.chromium.launch(
        headless=False,  # 화면에 크롬 창을 띄움
        args=["--disable-notifications","--disable-blink-features=AutomationControlled"])
    
    # 3. 사람 브라우저처럼 위장하기 위한 컨텍스트 설정
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1600, "height": 900})
    
    # 4. 실제 작업할 새 페이지 열기
    page = context.new_page()
    
    # 5. ★ 언디텍티드 핵심 (스텔스 모드 적용)
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    # # 6. 브라우저 종료 (with 문 안쪽 가장 마지막에 넣어주세요)
    # browser.close()

    for store_code in codes:
        # 리뷰를 25년도 1월부터 현재까지 수집하는 방식으로 작성(리뷰 작성일이 25년도 1월보다 이전이면 수집 종료하는 식으로)
        # 방문자 리뷰 먼저 수집하고, 그 다음에 블로그 리뷰 수집하는 방식으로 작성
        # 리뷰는 10개 단위로 나오고 그 뒤에 리뷰는 더보기 버튼을 클릭해야함 

        page.goto(f"https://pcmap.place.naver.com/restaurant/{store_code}/review/visitor?reviewSort=recent")
        page.wait_for_load_state("networkidle")
    
        print("접속 성공!")
        time.sleep(3)
        
        try:
            page.click("//div[contains(@class, 'place_option_area')]//a[@class='place_btn_option'][@role='option']")
            page.wait_for_load_state("networkidle")
            time.sleep(2) # 최신순 화면으로 DOM이 완전히 리로드될 때까지 확실하게 대기
            print("최신순 정렬 완료")
        except Exception as e:
            print(f"최신순 정렬 버튼 클릭 실패: {e}")

        try:
            # div id가_title인 것 찾고 그 안에 span 태그 중에서
            # 자신이나 하위 자식 class에 place_blind이 포함되면 모두 제외
            # 이유 : '플레이스 플러스'가 <span class=place_blind>으로 되어 있는데, 이 플레이스 플러스가 존재할때도 있고 없을 떄도 있어서 가게 이름을 정확히 긁어내기 위해서입니다.
            xpath_store_name = "//div[@id='_title']//span[not(descendant-or-self::*[contains(normalize-space(@class), 'place_blind')])]"
            store_name_element = page.locator(f"xpath={xpath_store_name}").first
            
            # 가게 이름이 화면에 완전히 뜰 때까지 최대 3초대기
            store_name_element.wait_for(state="visible", timeout=3000)
            
            store_name = store_name_element.inner_text().strip()
            print(f"가게 이름: {store_name}")
            
        except Exception as e:
            store_name = "알 수 없는 가게"
            print(f"가게 이름을 찾지 못했습니다: {e}")

        # 날짜를 긁고 비교 시작

        def get_and_check_reviews(page):
        # 1. 최초에 한 번 전체 개수를 확인합니다.
            elements_locator = page.locator("//li[contains(@class, 'place_apply_pui')]")
            review_counts = elements_locator.count()
            
            print(f"처음 찾은 총 리스트 아이템 개수: {review_counts}개")

            # 각 li 요소를 인덱스로 순회
            for idx in range(review_counts):
                try:
                    # # ⭐ [핵심] 루프를 돌 때마다 리스트를 새로 갱신(나갔다 다시 찾기)하여 깨짐을 방지합니다.
                    # 셀레리움과 달리 목록 비동기에 맞춰 갱신됨
                    # 현재 인덱스에 해당하는 li를 새로 고른 객체에서 안전하게 가져옵니다.
                    target_li = elements_locator.nth(idx)

                    # 방문일이 있는 태그를 찾아 한 단계 위 부모 태그에서 다시 '년'이 포함된 태그 찾고 텍스트 추출
                    xpath_date = ".//*[text()='방문일']/..//*[contains(text(), '년')]"
                    target_span = target_li.locator(f"xpath={xpath_date}").first

                    if target_span:
                        print(f"[{idx + 1}/{review_counts}] 추출된 텍스트: {target_span.inner_text()}")
                    else:
                        print(f"[{idx + 1}] 두 번째 pui__blind 요소를 찾지 못했습니다.")

                    time.sleep(1) # 대기 시간은 1초 정도로 조절하셔도 충분합니다.

                except Exception as e:
                    # 에러가 나더라도 어떤 에러인지 print로 확인하면 디버깅이 편합니다.
                    print(f"[{idx + 1}] 에러 발생으로 건너뜀: {e}")
                    time.sleep(1)
                    continue
                
            # 2. 함수가 종료될 때 구해놓은 개수 값을 바깥으로 반환(return)합니다.
            return review_counts

        final_counts = get_and_check_reviews(page)
    #-------------------------------------------------------------------------------------------------
        # --- [설정] 기준 날짜 정의 ---
        # 항상 '현재 아시아/서울 시간'을 기준으로 가져옵니다.
        seoul_tz = ZoneInfo("Asia/Seoul")
        today = datetime.now(seoul_tz)

        # 오늘 날짜에서 하루(1일)를 뺍니다.
        one_day_ago = today - timedelta(days=1)

        # 계산된 하루 전 날짜를 CUTOFF_DATE에 그대로 넣어줍니다.

        CUTOFF_DATE = one_day_ago.date()

        print(CUTOFF_DATE)


        def check_should_stop(page):
        # 현재 페이지에 로드된 모든 리뷰 요소를 가져옵니다.
            li_elements = page.locator("//li[contains(@class, 'place_apply_pui')]")
            review_counts = li_elements.count()
            print(f"\n--- [검사 시작] 현재 총 {review_counts}개의 리뷰를 검사합니다 ---")

            for idxx in range(review_counts):
                try:

                    target_li = li_elements.nth(idxx)
                    # 방문일이 있는 태그를 찾아 한 단계 위 부모 태그에서 다시 '년'이 포함된 태그 찾고 텍스트 추출
                    xpath_date = ".//*[text()='방문일']/..//*[contains(text(), '년')]"
                    target_span = target_li.locator(f"xpath={xpath_date}").first
                    #print(f"[{idxx}번째] 추출된 텍스트: {target_span.inner_text()}")
                    # 날짜 형식 변환 (%Y.%m.%d)
                    raw_text = target_span.inner_text().strip()  # 예: "2026년 4월 11일 토요일"
                    #print(f"[검사{idxx}번째] 추출된 텍스트: {raw_text}")
                    date_parts = re.findall(r'\d+', raw_text)
                    if len(date_parts) >= 3:
                    # 리뷰 날짜를 '날짜 객체'로 변환 (예: 2026-04-11)
                        review_date = datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2])).date()


                # 조건 비교
                    if review_date < CUTOFF_DATE:
                        print(f" [{idxx}번째] 리뷰 날짜: {review_date} | 기준일({CUTOFF_DATE})보다 과거이므로 [멈춤]을 지시합니다!")
                        return True  # True를 던져야 while문이 끝납니다.

                    print(f"   [{idxx}번째] 리뷰 날짜: {review_date} | 기준일 이후이므로 패스 (계속 수집)")

                except Exception as e:
                # 💡 [핵심 수정 2] 에러를 숨기지 않고 터미널에 찍어줍니다.
                # 무한 루프가 돌 때 이 메시지가 주르륵 찍힌다면, XPath가 틀려서 날짜를 못 읽고 있는 것입니다!
                    # print(f" [{idxx}번째] 날짜 읽기 실패! (이유: {type(e).__name__}) -> 다음 리뷰로 넘어감")
                    continue
                
            return False  # 과거 날짜가 하나도 없으면 계속 더보기 클릭

    # --- 실행 메인 루프 ---
        while True:
        # 1. [조회 및 결정] 현재 화면에서 멈춰야 할 과거 날짜가 나왔는지 판단
            if check_should_stop(page):
                print(">> [성공] 과거 날짜 조건을 만족하여 루프를 종료합니다. 버튼을 더 이상 누르지 않습니다.")
                break  # while 루프 완전히 탈출
            
        # 2. 과거 날짜가 없다면 아래로 내려와서 더보기 버튼을 누릅니다.
            try:
                xpath_more_btn = "//*[contains(@class, 'place_section_content')]//*[contains(text(), '펼쳐서')]"
                more_button = page.locator(f"xpath={xpath_more_btn}").first
                
                if more_button.is_displayed():
                    more_button.click()
                    print(">> [진행] 더보기 버튼 클릭 완료. 2초 대기...")
                    time.sleep(2)
                else:
                    print(">> 더보기 버튼이 화면에 보이지 않아 종료합니다.")
                    break
            except Exception as e:
                print(">> 더보기 버튼을 찾을 수 없거나 끝에 도달하여 종료합니다.")
                break

        print(" 모든 펼쳐내기 작업이 최종 종료되었습니다.")

            # 개수 확인용 아이디 (.pui__NMi-Dp) 기준

        # 카테고리밑 더보기 때문에 버튼 모두 누르고난뒤 크롤링
        # 카테고리 밑에 있는 더보기 버튼 찾아서 모두 누르기
        # 1. 일단 전체 버튼이 몇 개인지 개수만 체크합니다.

        # 1. li 태그를 기준으로 전체 카테고리 상자 개수를 구합니다.
        # 클래스명 사이의 공백은 CSS 선택자에서 마침표(.)로 연결합니다.
        # 실제 li 개수

        '''
        items = page.locator("//li[contains(@class, 'place_apply_pui')]")
        total_items = items.count()
        print(f"총 {total_items}개의 카테고리 리스트(li)를 찾았습니다.")

        # 2. 개수만큼 반복합니다.
        for idr in range(total_items):
            try:
                # 동적 로딩 대응: 루프가 돌 때마다 li 목록을 매번 새로 가져옵니다.
                #items = driver.find_elements(By.CSS_SELECTOR, "li.place_apply_pui")
                # 위에서 더보기 눌러 갯수 동적 대응 불필요
                current_item = items.nth(idr)

                # 현재 검사 중인 li 상자 자체를 화면 중앙으로 이동시킵니다. 셀레리움과 명령어 다름
                current_item.scroll_into_view_if_needed()
                time.sleep(0.5)

                # 현재 li 상자 안에서만' 각각의 버튼을 찾습니다.
                more_buttons = current_item.locator("xpath=./div[5]/a[2]")
                plus_buttons = current_item.locator("xpath=./div[6]/a[1]")

                # 해당 li 안에 버튼이 존재하는지 체크 (없으면 None)
                target_button = more_buttons if more_buttons.count() > 0 else None
                target_plus_button = plus_buttons if plus_buttons.count() > 0 else None

                # 텍스트 읽어오기
                button_text = target_button.inner_text() if target_button else ""

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
                        time.sleep(2)  # 내용이 열리는 대기 시간

                    # [조건 3] 둘 다 해당하지 않는 경우 패스
                    else:
                        print(f"[{idr + 1}/{total_items}] 누를 버튼이 없는 구역이라 패스합니다. ")

            # ----------------------------------------------------
            except Exception as e:
                # 클릭 실패나 에러가 나도 프로그램을 멈추지 않고 다음 li로 넘어갑니다.
                print(f"[{idr + 1}/{total_items}] 처리 중 실패 (에러 무시 후 다음 진행): {e}")

        '''

        # review_date = driver.find_elements(By.XPATH, "./li[@class='place_apply_pui EjjAW']")
        # review_counts = len(review_date)
        review_counts = page.locator("//li[contains(@class, 'place_apply_pui')]")
        review_counts_id = review_counts.count()
        for idxxx in range(review_counts_id):

            # lazyload-wrapper 때문에 이미지 불러오기 위한 리뷰 위치로 가는 스크롤
            review_counts.nth(idxxx).scroll_into_view_if_needed()
            time.sleep(0.5)

            xpath_date = ".//*[text()='방문일']/..//*[contains(text(), '년')]"
            today_overlap_date = review_counts.nth(idxxx).locator(f"xpath={xpath_date}").first
            #print(f"test: {today_overlap_date.inner_text()}")  # 출력결과: 방문 날짜
            if today_overlap_date.count() > 0 and today_overlap_date.inner_text():
                raw_date_text = today_overlap_date.inner_text().strip()
    
                try:
                    # "2025년 6월 23일 월요일"에서 숫자만 추출
                    match = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", raw_date_text)
                    
                    if match:
                        # 월과 일이 1자리 수일 때를 대비해 zfill(2)로 두 자리("06", "05")로 맞춰줍니다.
                        year = match.group(1)
                        month = match.group(2).zfill(2)
                        day = match.group(3).zfill(2)
            
                        # CUTOFF_DATE와 똑같은 형식(YYYY-MM-DD)의 문자열로 조립
                        review_date_str = f"{year}-{month}-{day}"
            
                        # 변환된 날짜가 지정해 둔 CUTOFF_DATE와 다르면 바로 브레이크!
                        '''
                        if review_date_str != CUTOFF_DATE:
                            print(f"-> [종료] 기준일({CUTOFF_DATE})과 다른 날짜({review_date_str}) 발견! 수집을 중단합니다.")
                            break
                            
                        '''
                        
                        # 데이터 속성 'profile'인 a태그 찾고 그 밑에 span들 중 자식이 없는 것(텍스트만을 가진)
                        xpath_id = ".//a[@data-pui-click-code='profile']//span[not(*)]"
                        reviewer_id_tag = review_counts.nth(idxxx).locator(f"xpath={xpath_id}").first
                        # TAG가 존재할때만 .inner_text() 실행하게끔 방어막
                        if reviewer_id_tag.count() > 0 and reviewer_id_tag.inner_text():
                            reviewer_id = reviewer_id_tag.inner_text()
                            print(f"작성자: {reviewer_id}")  # 출력결과: 댓글쓴이
                        else:
                            print("리뷰작성자를를 찾지 못했습니다.")
                        # 밖에서 펼치기로 로드 끝난 이후라서 버튼 찾아서 모두 누르기 한뒤에 for 문 돌려야됨    
                        # # 카테고리 클릭 눌러야 더보기 내용도 보임 + 카테고리 내용 확인 span class "pui__jhpEyP"
                        # 댓글 내용

                        # rvshowmore 중에서 적힌 글자가 '더보기' 아닌 진짜 본문만
                        xpath_content = ".//a[@data-pui-click-code='rvshowmore'][not(text()='더보기')]"
                        review_contents = review_counts.nth(idxxx).locator(f"xpath={xpath_content}").first

                        if review_contents.count() > 0 and review_contents.inner_text():
                            content_text = review_contents.inner_text()
                            print(f"리뷰내용: {content_text}")  # 출력결과: 댓글내용
                        else:
                            print("리뷰내용을 찾지 못했습니다.")
                        time.sleep(2)

                        # 리뷰 이미지 URL 
                        # class가 place_thumb인 태그 찾고 그 밑에 img 태그 찾기
                        xpath_img = ".//*[@class='place_thumb']//img"
                        review_imgs_locator = review_counts.nth(idxxx).locator(f"xpath={xpath_img}")
                        # .all사용하여 모든 이미지 url 쪼개서 파이썬 리스트로 만들기
                        img_elements = review_imgs_locator.all()
                        # 쪼개진 요소들을 하나씩 순회하고 src 속성이 존재하면 img_urls 리스트에 추가
                        img_urls = [el.get_attribute("src") for el in img_elements if el.get_attribute("src")] 

                        if img_urls:
                            print(f"이미지URL 총 {len(img_urls)}개: {img_urls}")  # 출력결과: 리뷰이미지URL
                            print("-" * 100)
                        else:
                            print("리뷰이미지를 찾지 못했습니다.")
                            print("-" * 100)
                        time.sleep(2)

                        # 댓글 카테고리
                        '''
                        review_categorys = review_counts.nth(idxxx).locator("xpath=./div[6]")

                        if review_categorys.inner_text():
                            review_category = review_categorys.inner_text().replace("요", "요, ").rstrip(", ")
                            print(review_category)  # 출력결과: 댓글카테고리
                        else:
                            print("댓글카테고리를 찾지 못했습니다.")
                        '''

                        # 방문 날짜

                        xpath_date = ".//*[text()='방문일']/..//*[contains(text(), '년')]"
                        reviewer_today_tag = review_counts.nth(idxxx).locator(f"xpath={xpath_date}")
                        if reviewer_today_tag.inner_text():
                            reviewer_today = reviewer_today_tag.inner_text()
                            #print(reviewer_today)  # 출력결과: 방문날짜
                        else:
                            print(f"[{idxxx}] 두 번째 pui__blind 요소를 찾지 못했습니다.") 
                        time.sleep(2)
                        print(f"[{idxxx + 1}] 기준일과 일치함 수집 진행: {review_date_str}")
            
                    else:
                        # 날짜에 맞는 데이터만 수집
                        print(f"[{idxxx + 1}] 최근 리뷰({raw_date_text})이므로 계속 진행...")
            
                except Exception as e:
                    print(f"최신화 날짜 비교 에러: {e}")
            else:
                print("최신화 날짜를 찾지 못했습니다.")
            









        print(f"업체 이름:{store_name},업체코드:{store_code},마무리 확인용")

    browser.close()
    