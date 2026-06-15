'''
main.py
작성자 : 이승현
작성일 : 2026-06-11
설명 : Flask 웹 애플리케이션의 진입점입니다. DBManager 클래스를 사용하여 MySQL 데이터베이스에 연결하고, 기본 라우트를 설정하여 index.html을 렌더링합니다.

[워크플로우]
0. 환경 구성: dotenv를 사용하여 환경 변수를 로드하고 Flask 애플리케이션을 초기화합니다.
1. DB 연결: DBManager 클래스를 인스턴스화하고, DBOpen 메서드를 호출하여 MySQL 데이터베이스에 연결합니다.
2. 라우트 설정: "/" 경로에 대한 라우트를 설정하여 index.html을 렌더링합니다.
3. 애플리케이션 실행: Flask 애플리케이션을 실행하여 웹 서버를 시작합니다.

[설치 방법]
pip install flask python-dotenv pymysql
'''
from flask import Flask, render_template, request, jsonify
import dotenv
import os

from routes.db_instance import db

# [워크플로우 0단계: 환경 구성]
dotenv.load_dotenv()
app = Flask(__name__)

# [워크플로우 1단계: DB 연결]
db.DBOpen(
    host=os.getenv("host"),
    id=os.getenv("user"),
    pw=os.getenv("passwd"),
    dbname=os.getenv("dbname")
)
print(os.getenv("host"), os.getenv("user"), os.getenv("passwd"), os.getenv("dbname"))

# 블루프린트 임포트 및 등록 조립 구역
# db 객체가 먼저 메모리에 바인딩된 후 하위 라우터를 import해야 순서 에러가 안 납니다
from routes.main_route import main_bp
from routes.store_route import store_bp

# 각각의 하위 블루프린트 합체
app.register_blueprint(main_bp)
app.register_blueprint(store_bp)

# [워크플로우 3단계: 애플리케이션 실행]
if __name__ == "__main__" :
    print("Blueprint 성공 JReview 백엔드 엔진 구동을 시작")
    app.run(host="0.0.0.0", port=8080, debug=True)