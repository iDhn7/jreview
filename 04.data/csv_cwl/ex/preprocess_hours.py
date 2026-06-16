import pandas as pd
import re
import os

def clean_time_detail(text):
    if not text:
        return ""
    
    # 불필요한 단어 제거 및 정리
    text = text.replace("접기", "").strip()
    if not text:
        return ""
        
    if '정기휴무' in text:
        return "정기휴무"
        
    # 1. 브레이크타임 추출 (예: 15:00 - 17:00 브레이크타임)
    break_time = ""
    break_match = re.search(r'(\d{2}:\d{2}\s*-\s*\d{2}:\d{2})\s*브레이크타임', text)
    if break_match:
        break_time = break_match.group(1).strip()
        text = text.replace(break_match.group(0), "")
        
    # 2. 라스트오더 추출 (예: 20:20 라스트오더 또는 14:20, 20:20 라스트오더)
    last_order = ""
    last_match = re.search(r'([\d{2}:\d{2},\s]*\d{2}:\d{2})\s*라스트오더', text)
    if last_match:
        last_order = last_match.group(1).strip()
        text = text.replace(last_match.group(0), "")
        
    # 3. 메인 영업시간 추출
    main_time = ""
    # "12:00 - 다음 날 00:40" 또는 "11:00 - 21:00" 패턴
    main_match = re.search(r'(\d{2}:\d{2}\s*-\s*(?:다음\s*날\s*)?\d{2}:\d{2})', text)
    if main_match:
        main_time = main_match.group(1).strip()
    else:
        # "오후17:30 ~ 새벽04:00" 같은 물결표시(~) 패턴 매칭
        wave_match = re.search(r'((?:오후|새벽|오전)?\s*\d{2}:\d{2}\s*~\s*(?:오후|새벽|오전)?\s*\d{2}:\d{2})', text)
        if wave_match:
            main_time = wave_match.group(1).strip()
            
    # 정제된 텍스트 결합
    result_parts = []
    if main_time:
        result_parts.append(main_time)
    elif "24시간 영업" in text or "24시간영업" in text:
        result_parts.append("24시간 영업")
    elif "연중무휴" in text and not main_time:
        result_parts.append("연중무휴 (영업시간 미기재)")
        
    extra_info = []
    if break_time:
        extra_info.append(f"브레이크타임: {break_time}")
    if last_order:
        extra_info.append(f"라스트오더: {last_order}")
        
    if extra_info:
        result_parts.append(f"({', '.join(extra_info)})")
        
    if result_parts:
        return " ".join(result_parts)
    
    # 패턴 매칭이 안 되면 원본에서 공백만 다듬어 반환
    return text.strip()

def parse_store_times(time_str):
    days = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    days_data = {day: "" for day in days}
    
    if not isinstance(time_str, str) or not time_str.strip():
        return days_data
        
    parts = [p.strip() for p in time_str.split('_') if p.strip()]
    
    day_map = {
        '월': '월요일', '화': '화요일', '수': '수요일',
        '목': '목요일', '금': '금요일', '토': '토요일', '일': '일요일'
    }
    
    # 1단계: '매일' 이나 '24시간' 등 공통 설정 파싱
    has_daily = False
    daily_time = ""
    for part in parts:
        if part.startswith('매일'):
            rest = part[2:].lstrip('_')
            cleaned = clean_time_detail(rest)
            if cleaned:
                daily_time = cleaned
                has_daily = True
                break
                
    if has_daily:
        for day in days:
            days_data[day] = daily_time

    # 2단계: 개별 요일별 구체 정보 덮어쓰기
    for part in parts:
        first_char = part[0]
        if first_char in day_map:
            target_day = day_map[first_char]
            rest = part[1:].lstrip('_')
            
            if '정기휴무' in rest:
                days_data[target_day] = "정기휴무"
                continue
                
            cleaned = clean_time_detail(rest)
            if cleaned:
                days_data[target_day] = cleaned

    # 3단계: 정기휴무 관련 특수 패턴 검사 (예: "화정기휴무 (매주 화요일)")
    for part in parts:
        for kor_day, full_day in day_map.items():
            if f"{kor_day}정기휴무" in part.replace(" ", "") or f"매주{kor_day}요일" in part.replace(" ", ""):
                days_data[full_day] = "정기휴무"
                
    # 4단계: 만약 아직도 다 비어있고 '24시간'이나 '연중무휴' 키워드가 존재하면 적용
    if not any(days_data.values()):
        for part in parts:
            if '24시간' in part:
                for day in days:
                    days_data[day] = "24시간 영업"
                break
            elif '연중무휴' in part:
                for day in days:
                    days_data[day] = "연중무휴"
                break

    return days_data

def main():
    file_dir = r"D:\작업용폴더\영업시간 전처리"
    input_file = os.path.join(file_dir, "naver_info.csv")
    output_file = os.path.join(file_dir, "naver_info_processed.csv")
    
    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file, encoding='utf-8')
    
    # 결과를 담을 리스트 생성
    parsed_results = []
    
    for idx, row in df.iterrows():
        time_str = row.get('store_times_str', '')
        parsed = parse_store_times(time_str)
        
        # 월~일 데이터 요약 컬럼 생성 (예: 월: 11:00... | 화: 정기휴무 ...)
        summary_parts = []
        for day in ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]:
            short_day = day[0]
            val = parsed[day]
            if val:
                summary_parts.append(f"{short_day}: {val}")
            else:
                summary_parts.append(f"{short_day}: 정보 없음")
        parsed['영업시간_정제'] = " | ".join(summary_parts)
        
        parsed_results.append(parsed)
        
    # 파싱 결과를 데이터프레임으로 변환
    parsed_df = pd.DataFrame(parsed_results)
    
    # 기존 데이터프레임에 새로 생성한 컬럼들 추가
    result_df = pd.concat([df, parsed_df], axis=1)
    
    # 파일 저장
    print(f"Saving to {output_file}...")
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print("Pre-processing completed successfully!")

if __name__ == "__main__":
    main()
