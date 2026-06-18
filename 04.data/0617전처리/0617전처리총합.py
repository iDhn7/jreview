import os
import re
import requests # 위도 경도 카카오 api 통신용
import pandas as pd
from datetime import datetime
def clean_process(text):
    if not text:
        return ""
    text = text.replace("접기", " ")
    # 한글, 영어, 숫자, 감정 자음(ㅋ,ㅎ,ㅠ,ㅜ), 필수 부호(~,!,?,^)만 남기고 이모티콘 싹 청소
    clean_text = re.sub(r'[^가-힣a-zA-Z0-9ㄱ-ㅎㅏ-ㅣ.~!^]', ' ', text)
    
    return re.sub(r'\s+', ' ', clean_text).strip()

csv_path          =  "C:\\code\\jreview\\04.data\\csv_cwl\\"
#naver_info_csv    = csv_path + "naver_info.csv"
naver_info_csv    = csv_path + "naver_info_processed.csv"
naver_review_csv  = csv_path + "naver_review.csv"
naver_menu_csv    = csv_path + "naver_menu.csv"

clean_csv_path          =  "C:\\code\\jreview\\04.data\\0617전처리\\"
raw_clean_naver_info_csv    = clean_csv_path + "raw_clean_naver_info.csv"
clean_naver_info_csv    = clean_csv_path + "clean_naver_info.csv"
clean_naver_review_csv  = clean_csv_path + "clean_naver_review.csv"
clean_naver_menu_csv    = clean_csv_path + "clean_naver_menu.csv"


#================= // 메뉴전처리 // ==========================================================================
# 대표메뉴 전처리 함수
def menu_best(text):
    if not text:
        return ""
    if pd.isna(text) or not text or str(text).strip() == "":
        return 0
    clean_text = re.sub(r'[^가-힣a-zA-Z0-9ㄱ-ㅎㅏ-ㅣ.~!^]', ' ', text)

    if re.search(r'대표', clean_text) or re.search(r'인기', clean_text):
        return "1"
    
    print("대표메뉴 전처리 완료")
    return "0"
    #----------------메뉴 전처리 실행 함수------------------------
def menu_csv_process() :  
    if not os.path.exists(naver_menu_csv):
        print(f"🚨 에러: 원본 파일 [{naver_menu_csv}]을 찾을 수 없습니다. 경로를 확인해 주세요.")
        return
   
    print("🔄 1. 원본 CSV 파일 로드 중...")
    df = pd.read_csv(naver_menu_csv, encoding='cp949')
    #엑셀 인코딩 오류? cp949 인코딩
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.loc[:, ~df.columns.str.contains('메뉴설명')]
    
# 데이터가 비어있지 않은지 검사
    if df.empty:
        print("경고: CSV 파일에 데이터가 없습니다.")
        return
    
    # '메뉴명' 컬럼만 빼서 전처리 함수 적용
    if '메뉴명' in df.columns:
        print("메뉴명 텍스트 정제(clean_process) 가동 시작...")
        
        # .apply(clean_process)가 컬럼의 텍스트를 한 줄씩 빼와서 함수를 돌린 뒤 쏙 다시 채워줍니다.

        df['메뉴명'] = df['메뉴명'].apply(clean_process)
        df['메뉴내용'] = df['메뉴내용'].apply(menu_best)
        
    else:
        print("에러: CSV 파일 안에 '메뉴명'이라는 컬럼명이 존재하지 않습니다.")
        print(f"현재 존재하 컬럼 목록: {list(df.columns)}")
        return

    # 전처리가 완료된 깨끗한 데이터프레임을 새로운 CSV로 저장 마감
    print("새로운 CSV 파일 생성 중...")
    
    # 한글 깨짐을 방지하기 위해 utf-8-sig 인코딩 마감 스펙 적용
    df.to_csv(clean_naver_menu_csv, index=False, encoding='utf-8-sig')
    
    print("-" * 50)
    print(f"[작업 완료] 메뉴 전처리 성공!")
    print(f"▶ 원본 파일: {naver_menu_csv} ({len(df)}건)")
    print(f"▶ 정제 완료 파일: {clean_naver_menu_csv} 저장 성공!")
    print("-" * 50)

#================= // 리뷰전처리 // ==========================================================================

# datetime 변환 함수
def convert_to_datetime(text):
    # 데이터가 비어있거나 문자열이 아니면 내년 날짜나 무효값(NaT) 처리
    if pd.isna(text) or not isinstance(text, str):
        return pd.NaT
    
    # 숫자만 추출 정규식
    match = re.search(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', text)
    
    if match:
        # 년, 월, 일만
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        
        #datetime 포장
        return datetime(year, month, day)
    
    else:
        # 패턴 매칭에 실패했을 경우 판다스가 인식하는 빈 날짜(Not a Time)를 반환.
        return pd.NaT

def review_csv_process() :  
    if not os.path.exists(naver_review_csv):
        print(f"에러: 원본 파일 [{naver_review_csv}]을 찾을 수 없습니다. 경로를 확인해 주세요.")
        return
   
    print("🔄 1. 원본 CSV 파일 로드 중...")
    df = pd.read_csv(naver_review_csv, encoding='utf-8-sig')
    #여기는 엑셀 수정 x 라서 utf-8-sig
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.loc[:, ~df.columns.str.contains('작성자')]
    df = df.loc[:, ~df.columns.str.contains('평가')]
    
# 데이터가 비어있지 않은지 검사
    if df.empty:
        print("경고: CSV 파일에 데이터가 없습니다.")
        return
    
    # 3. [핵심 기믹] '리뷰 내용' 컬럼만 쏙 빼서 전처리 함수 일괄 적용 
    if '리뷰 내용' in df.columns:
        print("리뷰내용 텍스트 정제(clean_process) 가동 시작...")
        
        # .apply(clean_process)가 컬럼의 텍스트를 한 줄씩 빼와서 함수를 돌린 뒤 쏙 다시 채워줍니다.

        df['리뷰 내용'] = df['리뷰 내용'].apply(clean_process)
        df['작성일'] = df['작성일'].apply(convert_to_datetime)

        df = df.rename(columns={'리뷰 내용': '리뷰내용'})
        # 컬럼명 맞추기 나중에 data_proess.py 돌릴때 
    else:
        print("에러: CSV 파일 안에 '리뷰내용'이라는 컬럼명이 존재하지 않습니다.")
        print(f"현재 존재하 컬럼 목록: {list(df.columns)}")
        return

    # 4. 전처리가 완료된 깨끗한 데이터프레임을 새로운 CSV로 저장 마감
    print("새로운 CSV 파일 생성 중...")
    
    # 한글 깨짐을 방지하기 위해 utf-8-sig 인코딩 마감 스펙 적용
    df.to_csv(clean_naver_review_csv, index=False, encoding='utf-8-sig')
    
    print("-" * 50)
    print(f"[작업 완료] 리뷰 전처리 성공")
    print(f"▶ 원본 파일: {naver_review_csv} ({len(df)}건)")
    print(f"▶ 정제 완료 파일: {clean_naver_review_csv} 저장 성공!")
    print("-" * 50)


#================= // 인포 전처리 // ==========================================================================
# 주소 전처리 함수
def info_ad_clean(text):
    if not text:
        return ""
    text = text.replace("접기", " ")
    # 한글, 영어, 숫자, 감정 자음(ㅋ,ㅎ,ㅠ,ㅜ), 필수 부호(~,!,?,^)만 남기고 이모티콘 싹 청소
    clean_text = re.sub(r'[^가-힣a-zA-Z0-9ㄱ-ㅎㅏ-ㅣ.~!^]', ' ', text)
    match = re.search(r'도로명(.*?)복사', clean_text, re.DOTALL)

    return re.sub(r'\s+', ' ', match.group(1)).strip()
# 주차 전처리 함수
def info_pk_clean(text):
    if not text:
        return ""
    text = text.replace("접기", " ")
    # 한글, 영어, 숫자, 감정 자음(ㅋ,ㅎ,ㅠ,ㅜ), 필수 부호(~,!,?,^)만 남기고 이모티콘 싹 청소
    clean_text = re.sub(r'[^가-힣a-zA-Z0-9ㄱ-ㅎㅏ-ㅣ.~!^]', ' ', text)

    if re.search(r'불가', clean_text):
        return "불가"
    
    elif re.search(r'가능', clean_text):
        return "가능"
    
    print("주차 전처리 완료")
    return re.sub(r'\s+', ' ', clean_text.group(1)).strip()
# 별점 전처리 함수
def info_st_clean(text):
    if not text:
        return ""
    # 한글, 영어, 숫자, 감정 자음(ㅋ,ㅎ,ㅠ,ㅜ), 필수 부호(~,!,?,^)만 남기고 이모티콘 싹 청소
    clean_text = re.sub(r'[^0-9.^]', '', text)
    if clean_text:
        return float(clean_text)  
    else:
        return 0.0
    
# 카카오api 사용 위도 경도 추출
def get_lng_onvert(doro):
    """도로명 주소를 입력받아 (위도, 경도) 튜플을 반환하는 함수"""
    # 1. 카카오 디벨로퍼스에서 발급받은 REST API 키를 입력하세요.
    # 'KakaoAK ' 뒤에 한 칸 공백을 두고 키를 입력해야 합니다.
    api_key = "66f22981e5203648b3f5365e7be1b65b"

    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {"query": doro}

    try:
        # API 요청 보내기
        response = requests.get(url, headers=headers, params=params)

        # 상태 코드가 200(성공)인 경우 데이터 파싱
        if response.status_code == 200:
            result = response.json()

            # 검색 결과가 존재하는지 확인
            if result["documents"]:
                address_info = result["documents"][0]

                # 카카오 API는 경도(x), 위도(y) 순으로 반환하므로 주의하세요.
                lon = float(address_info["x"])  # 경도
                lat = float(address_info["y"])  # 위도
                print(f"주소 : {doro}")
                print(f"검색 완료 [위도 : {lon}, 경도 : {lat}]")
                return (lat, lon)
                
            else:
                print("검색 결과가 없습니다.")
                return 0.0
        else:
            print(f"API 요청 실패 (Status Code: {response.status_code})")
            return None

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        return None

#----------------인포 전처리 실행 함수------------------------
def info_csv_process() :  
    if not os.path.exists(naver_info_csv):
        print(f"에러: 원본 파일 [{naver_info_csv}]을 찾을 수 없습니다. 경로를 확인해 주세요.")
        return
   
    print("🔄 1. 원본 CSV 파일 로드 중...")
    df = pd.read_csv(naver_info_csv, encoding='utf-8-sig')
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.loc[:, ~df.columns.str.contains('요일')]
    df = df.loc[:, ~df.columns.str.contains('store_data')]
    df = df.loc[:, ~df.columns.str.contains('store_times_str')]

# 데이터가 비어있지 않은지 검사
    if df.empty:
        print("경고: CSV 파일에 데이터가 없습니다.")
        return
    
    # 3. [핵심 기믹] '리뷰 내용' 컬럼만 쏙 빼서 전처리 함수 일괄 적용 
    if 'store_address' in df.columns:
        print("store_address 텍스트 정제(info_ad_clean) 가동 시작...")
        
        # .apply(info_ad_clean)가 컬럼의 텍스트를 한 줄씩 빼와서 함수를 돌린 뒤 쏙 다시 채워줍니다.

        df['store_address'] = df['store_address'].apply(info_ad_clean)
        df['store_score_text'] = df['store_score_text'].apply(info_st_clean)
        df['store_parking'] = df['store_parking'].apply(info_pk_clean)
        

        df = df.rename(columns={'store_address': '주소'})
        df = df.rename(columns={'store_name': '업체명'})
        df = df.rename(columns={'store_code': '업체코드'})
        df = df.rename(columns={'store_category': '업체카테고리'})
        df = df.rename(columns={'store_phone': '전화번호'})
        df = df.rename(columns={'store_score_text': '별점'})
        df = df.rename(columns={'store_image_url': '업체사진'})
        df = df.rename(columns={'store_amenities_str': '편의성정보'})
        df = df.rename(columns={'store_parking': '주차여부'})
        df = df.rename(columns={'영업시간_정제': '영업시간'})
        # 컬럼명 맞추기 나중에 data_proess.py 돌릴때 
    else:
        print("에러: CSV 파일 안에 'store_address'이라는 컬럼명이 존재하지 않습니다.")
        print(f"현재 존재하 컬럼 목록: {list(df.columns)}")
        return

    # 4. 전처리가 완료된 깨끗한 데이터프레임을 새로운 CSV로 저장 마감
    print("새로운 CSV 파일 생성 중...")
    
    # 한글 깨짐을 방지하기 위해 utf-8-sig 인코딩 마감 스펙 적용
    df.to_csv(raw_clean_naver_info_csv, index=False, encoding='utf-8-sig')
    
    print("-" * 50)
    print(f"[작업 완료] 전처리 성공")
    print(f"▶ 원본 파일: {raw_clean_naver_info_csv} ({len(df)}건)")
    print(f"▶ 정제 완료 파일: {raw_clean_naver_info_csv} 저장 성공!")
    print("-" * 50)

    #--------------------위도 경도 추출 함수-----------------------------------------------------
    def ad_info_csv_process() :
        if not os.path.exists(raw_clean_naver_info_csv):
            print(f"에러: 원본 파일 [{raw_clean_naver_info_csv}]을 찾을 수 없습니다. 경로를 확인해 주세요.")
            return
    
        print("원본 CSV 파일 로드 중...")
        df = pd.read_csv(raw_clean_naver_info_csv, encoding='utf-8-sig')
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.loc[:, ~df.columns.str.contains('store_data')]

        if df.empty:
            print("경고: CSV 파일에 데이터가 없습니다.")
            return
        
        # 3. [핵심 기믹] '리뷰 내용' 컬럼만 쏙 빼서 전처리 함수 일괄 적용 
        if '주소' in df.columns:
            print("전처리 가동 시작...")
            
            ctuple = df['주소'].apply(get_lng_onvert)
            #올바른 주소가 아닌것들은 0.0으로 에외처리
            df['위도'] = ctuple.apply(lambda x: x[0] if isinstance(x, (tuple, list)) else 0.0)
            df['경도'] = ctuple.apply(lambda x: x[1] if isinstance(x, (tuple, list)) else 0.0)

            #df['위도'], df['경도'] = zip(*df['주소'].apply(get_lng_onvert))

        else:
            print("에러: 컬럼명이 존재하지 않습니다.")
            print(f"현재 존재하 컬럼 목록: {list(df.columns)}")
            return

        # 4. 전처리가 완료된 깨끗한 데이터프레임을 새로운 CSV로 저장 마감
        print("새로운 CSV 파일 생성 중...")
        
        # 한글 깨짐을 방지하기 위해 utf-8-sig 인코딩 마감 스펙 적용
        df.to_csv(clean_naver_info_csv, index=False, encoding='utf-8-sig')
        
        print("-" * 50)
        print(f"[작업 완료] 전처리 성공")
        print(f"▶ 원본 파일: {raw_clean_naver_info_csv} ({len(df)}건)")
        print(f"▶ 정제 완료 파일: {clean_naver_info_csv} 저장 성공!")
        print("-" * 50)

    ad_info_csv_process()
    

# 이 파일이 실행될 때 파이프라인 가동
if __name__ == "__main__":
    #menu_csv_process()
    review_csv_process()
    #info_csv_process()
    
    '''
    test_address = "서울특별시 강남구 테헤란로 521"
    coordinates = get_lng_onvert(test_address)

    if coordinates:
        print(f"주소: {test_address}")
        print(f"위도, 경도: {coordinates}")
    '''