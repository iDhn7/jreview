

#   REVIEW 가공: 날짜를 년/월/일로 쪼개고, 텍스트에서 긍/부정 점수를 산출합니다.

#   WORD 가공: 가공된 리뷰 본문에서 띄어쓰기 기준으로 단어를 추출하고, 부모 리뷰의 긍/부정 속성을 물려받습니다.

#  STORE 가공: 업체 목록과 정보를 하나로 합치고(Merge), REVIEW 테이블을 참조하여 식당별 전체 리뷰 대비 긍정률(%)을 자동 계산합니다.

#  MENU 가공: 대표 메뉴에 뱃지를 달고, REVIEW 테이블을 뒤져서 해당 메뉴가 리뷰에서 몇 번 언급되었는지 언급수(Count)를 계산합니다.

import pandas as pd
import numpy as np
import re

#이모티콘 청소 함수
def clean_for_db(text):
    if not text:
        return ""
    text = text.replace("접기", " ")
    # 한글, 영어, 숫자, 감정 자음, 필수 부호남기고 이모티콘 싹 청소
    clean_text = re.sub(r'[^가-힣a-zA-Z0-9ㄱ-ㅎㅏ-ㅣ.~!?^ ]', ' ', text)
    return re.sub(r'\s+', ' ', clean_text).strip()

print("데이터 전처리 파이프라인을 시작합니다...")

# ==========================================
# Step 1: 데이터 불러오기 (Extract)
# ==========================================
df_list = pd.read_csv('store_list.csv')
df_info = pd.read_csv('store_info.csv')
df_menu = pd.read_csv('menu.csv')
df_review = pd.read_csv('review.csv')

# ==========================================
# Step 2: REVIEW (리뷰 테이블) 가공
# ==========================================
# 1. 리뷰 식별자(PK) 생성
#df_review['REVIEW_CODE'] = range(1, len(df_review) + 1)

# 2. 날짜 분리
df_review['WRITTEN_DT'] = pd.to_datetime(df_review['작성일'])
df_review['STORE_CODE'] = df_review['업체코드'].apply(clean_for_db)
df_review['CONTENT'] = df_review['리뷰 내용'].apply(clean_for_db)
df_review['YEAR'] = df_review['WRITTEN_DT'].dt.year
df_review['MONTH'] = df_review['WRITTEN_DT'].dt.month
df_review['DAY'] = df_review['WRITTEN_DT'].dt.day

# 4. DB 규격에 맞게 컬럼명 정리 (REVIEW_PN, PN_SCORE는 추후 감성 분석 후 채울 예정)
db_review = df_review[['STORE_CODE', 'CONTENT', 'WRITTEN_DT', 'YEAR', 'MONTH', 'DAY']]
print("REVIEW 테이블 가공 완료")

'''
# ==========================================
# Step 3: WORD (워드 클라우드 테이블) 가공(WORD_PN도 후에 추가)
# ==========================================
word_data = []
word_counter = 1

# 리뷰를 한 줄씩 돌면서 단어 추출
for idx, row in db_review.iterrows():
    words = str(row['CONTENT']).split() # 띄어쓰기 기준으로 단어 분리
    for w in words:
        if len(w) >= 2: # 2글자 이상인 의미 있는 단어만 추출
            word_data.append({
                'WORD_CODE': word_counter,
                'REVIEW_CODE': row['REVIEW_CODE'],
                'WORD': w.replace('.', '').replace(',', '').replace('!', ''), # 특수문자 제거
            })
            word_counter += 1

db_word = pd.DataFrame(word_data)
'''

# ==========================================
# Step 4: STORE (업체 정보 테이블) 가공
# ==========================================

#STORE (업체 정보 테이블) 가공 중 ADDRESS_JI 처리
def get_ji_address(full_address):
    # 예시: '전북 전주시 완산구 팔달로 180' -> '전북 전주시 완산구' 까지만 우선 추출
    # 실제 데이터셋에 지번 정보가 없다면, 시/군/구까지만 넣는 것이 가장 안전합니다.
    parts = full_address.split(' ')
    if len(parts) >= 3:
        return f"{parts[0]} {parts[1]} {parts[2]}"
    return full_address

# 1. 목록과 상세 정보 병합 (JOIN)
df_store_merged = pd.merge(df_info, df_list[['업체코드', '상권']], on='업체코드', how='left')

'''
# 2. 업체별 긍정률 계산 (리뷰 테이블 활용)
# 업체별로 긍정(P)과 부정(N) 개수를 셉니다.
pn_counts = db_review.groupby(['STORE_CODE', 'REVIEW_PN']).size().unstack(fill_value=0)
if 'P' not  in pn_counts: pn_counts['P'] = 0
if 'N' not in pn_counts: pn_counts['N'] = 0
# 긍정률 공식: P / (P + N) * 100
pn_counts['PN_RATE'] = (pn_counts['P'] / (pn_counts['P'] + pn_counts['N']) * 100).round(1)

# 3. 계산된 긍정률을 STORE 데이터에 붙이기
df_store_merged = pd.merge(df_store_merged, pn_counts[['PN_RATE']], left_on='업체코드', right_index=True, how='left')
df_store_merged['PN_RATE'] = df_store_merged['PN_RATE'].fillna(0) # 리뷰가 없으면 0%
'''
# 4. DB 규격에 맞게 컬럼명 정리
db_store = df_store_merged.rename(columns={
    '업체코드': 'STORE_CODE', '업체명': 'STORE_NAME', '주소': 'ADDRESS_DO',
    '전화번호': 'PHONE', '영업시간': 'BUSINESS_HOURS', '주차여부': 'PARKING',
    '편의성 정보': 'AMENITY', '위도': 'LAT', '경도': 'LNG', 
    '업체카테고리': 'CATEGORY', '별점': 'STAR', '업체사진': 'STORE_IMAGE_URL', '상권': 'AREA'
})
# 지번 주소 등 부족한 컬럼은 빈 값으로 생성하여 뼈대 맞추기
db_store['ADDRESS_JI'] = db_store['ADDRESS_DO'].apply(get_ji_address)
db_store = db_store[['STORE_CODE', 'STORE_NAME', 'ADDRESS_DO', 'ADDRESS_JI', 'PHONE', 'BUSINESS_HOURS', 'PARKING', 'AMENITY', 'LAT', 'LNG', 'CATEGORY', 'STAR', 'STORE_IMAGE_URL', 'AREA']]
print("STORE 테이블 가공 완료")

# ==========================================
# Step 5: MENU (메뉴 테이블) 가공
# ==========================================
# 1. 메뉴 식별자 생성
df_menu['MENU_CODE'] = range(1, len(df_menu) + 1)

# 2. 대표 메뉴 뱃지 판별 (boolean 처리)
df_menu['BEST'] = df_menu['메뉴 카테고리'].apply(lambda x: True if '대표' in str(x) else False)

# 3. 리뷰에서 메뉴 언급 횟수 찾기
def get_mention_count(store_code, menu_name):
    # 해당 업체의 리뷰만 가져오기
    store_reviews = db_review[db_review['STORE_CODE'] == store_code]['CONTENT']
    # 리뷰 본문에 메뉴 이름이 포함된 횟수 계산
    count = sum(store_reviews.str.contains(menu_name, na=False))
    return count

df_menu['CNT'] = df_menu.apply(lambda row: get_mention_count(row['업체코드'], row['메뉴명']), axis=1)
df_menu['MENU_NAME'] = df_menu['메뉴명'].apply(clean_for_db)
df_menu['STORE_CODE'] = df_menu['업체코드'].apply(clean_for_db)
df_menu['MENU_PRICE'] = df_menu['메뉴 가격'] # .apply(clean_for_db)

#df_menu['MENU_PRICE'] = df_menu['메뉴 가격'].apply(clean_for_db)
# 4. DB 규격에 맞게 컬럼명 정리
db_menu = df_menu[['STORE_CODE', 'MENU_NAME', 'MENU_PRICE', 'BEST']]
print("MENU 테이블 가공 완료")

# ==========================================
# Step 6: 최종 결과물 CSV로 저장 (Load 준비)
# ==========================================

db_store.to_csv('전처리_STORE.csv', index=False, encoding='utf-8-sig')
db_review.to_csv('전처리_REVIEW.csv', index=False, encoding='utf-8-sig')
db_menu.to_csv('전처리_MENU.csv', index=False, encoding='utf-8-sig')
#db_word.to_csv('최종_DB용_WORD.csv', index=False, encoding='utf-8-sig')

print("완료! '전처리_' 으로 시작하는 4개의 파일이 생성되었습니다.")

