'''
DBManager.py
작성자 : 이승현
작성일 : 2026-06-11
설명 : DB 연결, SQL 실행, 결과 관리 등을 담당하는 클래스입니다.

[워크플로우]
0. 초기화: DB 연결과 커서 관리를 위한 변수들을 초기화합니다.
1. DB 연결: DBOpen 메서드를 통해 MySQL 데이터베이스에 연결합니다.
2. SQL 실행: RunSQL 메서드를 사용하여 INSERT, UPDATE, DELETE 등의 SQL 명령을 실행합니다. OpenSQL 메서드는 SELECT 쿼리를 실행하여 결과를 저장합니다.
3. 결과 관리: getData, getTotal, getAll 메서드를 통해 쿼리 결과를 관리하고 접근할 수 있도록 합니다.
4. 자원 반환: DBClose 메서드를 통해 DB 연결을 종료하고 자원을 반환합니다.

[설치 방법]
pip install pymysql
'''
import pymysql
import pymysql.cursors

class DBManager:
    def __init__(self):
        # [워크플로우 0단계: 초기화] 
        self.con = None
        self.cursor = None
        self.datas = [] 
 
    def DBOpen(self, host, id, pw, dbname):
        # [워크플로우 1단계: DB 연결]
        try:
            self.con = pymysql.connect(
                host=host,
                database=dbname,
                user=id,
                password=pw,
                charset="utf8",
                cursorclass=pymysql.cursors.DictCursor
            )
            print("DB에 연결되었습니다.")
            return True
        except Exception as e:
            print(f"DB 연결 실패: {e}")
            return False
       
    def DBClose(self):
        # [워크플로우 4단계: 자원 반환]
        try:
            if self.con:
                self.con.close()
                print("DB 연결이 해제되었습니다 (자원 반환 완료).")
            return True
        except Exception as e:
            print(f"DB 해제 실패: {e}")
            return False

    def RunSQL(self, sql, datas=None): # datas가 없는 쿼리도 있을 수 있으므로 기본값 None 설정
        # [워크플로우 2단계: SQL 실행]
        print(f"SQL : \n{sql}")
        print(f"datas : \n{datas}")
        try:
            self.cursor = self.con.cursor()
            # datas가 있으면 바인딩, 없으면 그냥 실행
            count = self.cursor.execute(sql, datas) if datas else self.cursor.execute(sql)
            
            if count < 1:
                print("데이터를 변경하지 못했습니다. (영향을 받은 행 없음)")
                self.con.rollback()
                self.cursor.close()
                return False
            else:
                print(f"{count}개의 데이터가 변경되었습니다.")
                self.con.commit()
                new_pk = self.cursor.lastrowid
                self.cursor.close()
                
                if new_pk == 0:
                    return 0, count
                else:
                    return new_pk, count
        except Exception as e:
            print(f"RunSQL 에러: {e}")
            if self.con:
                self.con.rollback()
            return False

    def OpenSQL(self, sql, datas=None):
        # [워크플로우 2단계: SQL 실행]
        print(f"SQL : \n{sql}")
        try:
            self.cursor = self.con.cursor()
            if datas:
                self.cursor.execute(sql, datas)
            else:
                self.cursor.execute(sql)
            
            self.datas = self.cursor.fetchall()
            return True
        except Exception as e:
            print(f"OpenSQL 에러: {e}")
            self.datas = [] # 에러 발생 시 기존 데이터 초기화
            return False

    def CloseSQL(self):
        # [워크플로우 2단계: SQL 실행]
        try:
            if self.cursor:
                self.cursor.close()
            return True
        except Exception as e:
            print(f"커서 종료 에러: {e}")
            return False

    def getData(self, index):
        # [워크플로우 3단계: 결과 관리]
        if 0 <= index < self.getTotal():
            return self.datas[index]
        else:
            print("유효하지 않은 인덱스 접근입니다.")
            return None

    def getTotal(self):
        # [워크플로우 3단계: 결과 관리]
        return len(self.datas) if self.datas else 0

    def getAll(self):
        # [워크플로우 3단계: 결과 관리]
        return self.datas if self.datas else []