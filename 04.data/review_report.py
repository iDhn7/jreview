"""
모듈명 : Gemini API를 활용한 HTML 형식 리뷰 개선 리포트 생성 모듈
작성일 : 2026.06.11
작성자 : 정정훈

※ 필요 패키지 설치
    pip install google-genai
"""

import time
from google import genai
from google.genai import types

# 🔑 발급받으신 실제 Gemini API Key를 입력하세요.
GEMINI_API_KEY = "AIzaSyCJfpo3pvNSxapGgtfb16BFPt9IBxFgIik"

def review_improvement_report(reviews: list) -> str:
    """
    고객 리뷰 리스트를 받아 최대 4개의 개선사항을 지정된 HTML 구조로 생성합니다.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_ACTUAL_API_KEY_HERE":
        return "오류: GEMINI_API_KEY 변수에 올바른 API 키를 설정해 주세요."
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    reviews_text = "\n".join([f"- {review}" for review in reviews])
    
    # 구조화된 출력을 유도하기 위한 구체적인 시스템 지침 및 가이드라인
    prompt = f"""
당신은 고객 경험(CX) 데이터 분석 전문가입니다.
제공된 고객들의 맛집 리뷰 데이터를 종합적으로 분석하여, 가장 시급하게 개선해야 할 핵심 문제점을 최소 1개에서 '최대 4개'까지 도출해 주세요.

[분석할 고객 리뷰 데이터]
{reviews_text}

[출력 형식 가이드라인]
반드시 도출된 각 개선사항마다 아래의 HTML 양식을 정확하게 지켜서 리스트 형태로 출력해 주세요. 
html 코드 마크다운 기호(```html)나 다른 여백 텍스트는 일체 포함하지 말고, 오직 아래의 <div> 구조화된 태그들만 이어서 출력해야 합니다.

아이콘 종류 가이드:
- 심각한 문제/위생/대기: <div class="report-icon warn">⚠️</div>
- 즉시 변경 가능/서비스: <div class="report-icon info">💡</div>
- 시설/환경 개선: <div class="report-icon tool">🔧</div>

[반드시 준수해야 할 HTML 출력 포맷]
<div class="report-item">
  <div class="report-icon [아이콘클래스]">[아이콘]</div>
  <div class="report-text">
    <div class="report-label">[개선 분야 명칭]</div>
    <div class="report-desc">[리뷰 데이터 분석 기반의 구체적인 문제 현상 요약 및 정량적 추정, 그리고 권장 해결책 기술]</div>
  </div>
</div>
"""

    max_retries = 3
    delay = 2

    for attempt in range(max_retries):
        try:
            print(f"Gemini API HTML 리포트 생성 중... (시도 {attempt + 1}/{max_retries})")
            
            # 2.5 Flash 모델 호출
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2, # 형식을 엄격히 준수하도록 온도를 낮춤
                )
            )
            return response.text.strip()
            
        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "UNAVAILABLE" in error_msg:
                if attempt < max_retries - 1:
                    print(f"⚠️ 서버 일시적 과부하. {delay}초 후 재시도합니다...")
                    time.sleep(delay)
                    delay *= 2
                    continue
            return f"API 호출 중 에러가 발생했습니다: {error_msg}"


# ── 실행 예시 ──────────────────────────────────────────────────
if __name__ == "__main__":
    
    # 1. 빈 리뷰 리스트 생성
    customer_reviews = []
    
    # 2. append() 함수를 사용하여 리뷰 데이터를 순차적으로 추가
    customer_reviews.append("맛은 진짜 최고인데 주말 점심에 가니까 대기가 너무 길어요. 대기 공간도 없어서 밖에서 땀 흘리며 기다렸네요.")
    customer_reviews.append("직원 한 분이 서빙하면서 인상을 너무 쓰고 계셔서 주문할 때 눈치가 보였습니다. 서비스 교육이 필요할 듯.")
    customer_reviews.append("음식에서 아주 작은 비닐 조각 같은 게 나왔어요. 그냥 빼고 먹긴 했는데 위생 관리에 신경 좀 써주셔야 할 것 같습니다.")
    customer_reviews.append("테이블이 너무 끈적거려요. 바빠서 그런 건 알겠는데 행주로 대충 닦으시는 것 같더라고요.")
    customer_reviews.append("고기 퀄리티나 밑반찬 구성은 아주 만족스럽습니다. 부모님 모시고 가기엔 좋은데 예약 시스템이 있으면 좋겠어요.")
    customer_reviews.append("주차장이 협소해서 차 댈 데가 없어서 골목을 세 바퀴나 돌았습니다. 차량 가지고 가시는 분들 참고하세요.")
    customer_reviews.append("웨이팅 순번 번호표 뽑는 기계가 고장 났는지 앞사람이랑 순서 꼬여서 한바탕 소란이 있었네요. 안내 직원도 없고 속터짐.")
    
    html_report = review_improvement_report(customer_reviews)
    
    print("\n" + "="*20 + " 생성된 HTML 리포트 소스 " + "="*20)
    print(html_report)
    print("="*64)

