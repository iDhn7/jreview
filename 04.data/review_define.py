"""
모듈명 : 리뷰내용을 분석해서 긍정/부정/중립 및 원래 세부 감정까지 분석하는 모듈
작성일 : 2026.06.11
작성자 : 정정훈

※ 필요 패키지 설치
    pip install transformers torch sentencepiece pandas tqdm
"""

import warnings
warnings.filterwarnings("ignore")

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import pandas as pd

MODEL_NAME = "hun3359/klue-bert-base-sentiment"
MAX_LENGTH = 128

_isLoaded  = False
_tokenizer = None
_model     = None
_id2label  = None     # 모델의 원본 60개 감정 레이블 저장
_label_mapping = {}  # 60개 원본 레이블 -> [긍정, 부정, 중립] 맵핑 딕셔너리


def load_model():
    global _tokenizer, _model, _id2label, _label_mapping, _isLoaded

    if _isLoaded == True :
        return

    print(f"모델 로딩 중... ({MODEL_NAME})")
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    _model     = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    _model.eval()
    
    # 원본 감정 레이블 맵 복사
    _id2label = _model.config.id2label
    
    # hun3359 모델의 60개 대화 감정 레이블을 맛집/일반 리뷰용 3-class로 그룹화 맵핑
    for idx, lbl in _id2label.items():
        lbl_lower = lbl.lower()
        if "기쁨" in lbl_lower or "만족" in lbl_lower or "흥분" in lbl_lower or "느긋" in lbl_lower:
            _label_mapping[idx] = "긍정"
        elif "당황" in lbl_lower:
            _label_mapping[idx] = "중립"
        else:
            # 분노, 슬픔, 불안, 상처 등은 모두 부정으로 분류
            _label_mapping[idx] = "부정"
            
    print(f"로딩 완료  |  변환 레이블 그룹: ['긍정', '부정', '중립']\n")
    _isLoaded = True


def run_review_predict(review: str) -> dict:
    """
    review : 리뷰 문자열 (단일)
    반환   : {"감성": "긍정", "원래감성": "기쁨", "긍정확률": 0.92, "부정확률": 0.05, "중립확률": 0.03}
    """
    load_model()

    inputs = _tokenizer(review, return_tensors="pt",
                        truncation=True, max_length=MAX_LENGTH)

    with torch.no_grad():
        logits = _model(**inputs).logits
        probs = F.softmax(logits, dim=-1).numpy()[0]

    # 1. 60개 감정 중 가장 높은 확률을 가진 원본 감정(인덱스) 찾기
    orig_max_idx = probs.argmax()
    original_sentiment = _id2label[orig_max_idx]

    # 2. 긍정, 부정, 중립 확률을 누적할 딕셔너리 초기화
    sentiment_probs = {"긍정": 0.0, "부정": 0.0, "중립": 0.0}

    # 3. 60개 소프트맥스 확률을 3가지 카테고리로 합산
    for idx, prob in enumerate(probs):
        target_label = _label_mapping[idx]
        sentiment_probs[target_label] += prob

    # 소수점 4자리로 반올림 처리
    pos_p = round(float(sentiment_probs["긍정"]), 4)
    neg_p = round(float(sentiment_probs["부정"]), 4)
    neu_p = round(float(sentiment_probs["중립"]), 4)

    # 변환된 카테고리[긍정, 부정, 중립] 중 가장 높은 확률을 최종 감성으로 선택
    final_sentiment = max(sentiment_probs, key=sentiment_probs.get)

    """
    return {
        "감성"    : final_sentiment,
        "원래감성": original_sentiment,  # ◀ 모델이 판단한 60개 중 최상위 원래 감정 추가
        "긍정확률": pos_p,
        "부정확률": neg_p,
        "중립확률": neu_p,
    }
    """
    if final_sentiment == "긍정" :
        return "P", pos_p
    if final_sentiment == "부정" :
        return "N", neg_p    
    
    #중립
    return "J", neu_p  

# ── 실행 예시 ──────────────────────────────────────────────────
if __name__ == "__main__":

    # CSV를 읽지 않고 테스트할 수 있는 샘플 코드 (필요 시 주석 해제)
    """
    reviews = [
        "국물이 진하고 깊어요. 해장에 완벽한 집이에요!",
        "가격이 너무 비싸고 양도 적어서 실망했어요.",
        "그냥 평범한 맛이에요. 특별하진 않았어요.",
    ]

    for review in reviews:
        result = run_predict(review)
        print(f"리뷰  : {review}")
        print(f"결과  : {result}\n")
    """

    df = pd.read_csv("04.data/review.csv", encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    review_list = df["리뷰내용"].fillna("").astype(str).tolist()

    count = 0
    for review in review_list:
        result = run_review_predict(review)
        print(f"리뷰  : {review}")
        print(f"결과  : {result}\n")
        print("=" * 40)        
        count = count + 1
        if count > 100:
            break


"""
x, y = run_review_predict("정말 맛있어요.")
print(f"긍부정 여부 : {x}")
print(f"긍부정 확률 : {y}")
"""

