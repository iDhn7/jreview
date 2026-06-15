# 원본csv의 경우 영업시간이 전처리하기 어렵게 되있음 (일단 data_process.py에서는 가짜데이터를 쓰기에 이부분은 필요가 없음 )
import re


def print_business_hours(raw_data):
    # 1. 현재 영업 상태 및 시작 시간 추출
    status_text = "영업시간 상세보기"
    status_match = re.search(r"(영업 전|영업 종료|영업 중)\s*(\d{2}:\d{2})", raw_data)
    if status_match:
        status_text = f"{status_match.group(1)} ({status_match.group(2)} 시작)"

    # 2. 요일별 기본 구조 정의 (순서 보장)
    days_order = ["월", "화", "수", "목", "금", "토", "일"]
    weekly_data = {
        day: {"time": "", "breakTime": "", "lastOrder": "", "isClosed": False}
        for day in days_order
    }

    # 3. 정규표현식 매칭
    pattern = re.compile(
        r"([월화수목금토일])(?:(\d{2}:\d{2}\s*-\s*\d{2}:\d{2})|(정기휴무))?\s*(\d{2}:\d{2}\s*-\s*\d{2}:\d{2}\s*브레이크타임)?\s*(\d{2}:\d{2}\s*라스트오더)?"
    )

    for match in pattern.finditer(raw_data):
        day = match.group(1)
        info = weekly_data[day]

        if match.group(3) or f"{day}정기휴무" in raw_data:
            info["isClosed"] = True
            continue

        if match.group(2) and not info["time"]:
            info["time"] = match.group(2).strip()
        if match.group(4) and not info["breakTime"]:
            info["breakTime"] = (
                match.group(4).replace("브레이크타임", "").strip()
            )
        if match.group(5) and not info["lastOrder"]:
            info["lastOrder"] = match.group(5).replace("라스트오더", "").strip()

    # 데이터 누락 방지 처리 (이전 영업시간 답습)
    last_valid_time = "11:00 - 22:00"
    for day in days_order:
        info = weekly_data[day]
        if not info["isClosed"] and not info["time"]:
            info["time"] = last_valid_time
        elif not info["isClosed"]:
            last_valid_time = info["time"]

    # 4. 하단 공지사항 확인
    notice_text = (
        "- 변경시 사전공지 예정"
        if "- 변경시 사전공지 예정" in raw_data
        else "- 찾아주셔서 감사합니다! 항상 행복한 하루 보내세요"
    )

    # ==========================================
    # 5. 커맨드창 예쁘게 프린트하기
    # ==========================================
    print("=" * 60)
    print(f" [현재 상태] {status_text}")
    print("=" * 60)

    for day in days_order:
        info = weekly_data[day]

        if info["isClosed"]:
            # 정기휴무일 출력
            print(f"[{day}요일]  정기휴무 (매주 {day}요일)")
        else:
            # 브레이크타임, 라스트오더 유무에 따른 문자열 처리
            break_str = (
                f" | ☕ 브레이크: {info['breakTime']}"
                if info["breakTime"]
                else ""
            )
            lo_str = (
                f" | 🕒 라스트오더: {info['lastOrder']}"
                if info["lastOrder"]
                else ""
            )

            # 포맷팅을 이용해 요일과 영업시간 열 맞춤
            print(f"[{day}요일]  {info['time']}{break_str}{lo_str}")

    print("-" * 60)
    print(f" 📢 공지: {notice_text}")
    print("=" * 60)


# --- 실행 및 테스트 ---
raw_input = """24시간 영업연중무휴연중무휴_24시간 영업연중무휴연중무휴_24시간 영업연중무휴연중무휴_24시간 영업_연중무휴연중무휴_연중무휴_연중무휴_매일00:00 - 24:00접기_매일00:00 - 24:00접기_매일00:00 - 24:00_매일_00:00 - 24:00_접기_접기"""

print_business_hours(raw_input)