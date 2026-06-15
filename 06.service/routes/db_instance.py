
# 설명 : 순환 참조(Circular Import) 방지를 위한 전역 DB 매니저 인스턴스 격리 파일입니다.
from modules.DBManager import DBManager as dbm

# 💡 전역에서 공유할 공통 db 상자를 여기서 생성합니다.
db = dbm()