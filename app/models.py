from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import backref

KST = timezone(timedelta(hours=9)) #한국시간 정의

from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kakao_id = db.Column(db.String(100), unique=True, nullable=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    nickname = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True) # 고유번호
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) #판매자 id
    Hometeam_name = db.Column(db.String(50), nullable=False)  # KBO 구단명
    awayteam_name = db.Column(db.String(50), nullable=False)  # KBO 구단명
    sub_category = db.Column(db.String(100))  # 상세 구간
    seat = db.Column(db.String(100), nullable=True)  # 좌석 정보
    quantity = db.Column(db.Integer, nullable=False)  # 티켓 수량
    price = db.Column(db.Integer, nullable=False) #가격
    pin = db.Column(db.String(100), nullable=False)  # 거래 중요 데이터
    status = db.Column(db.String(20), default='판매중') #상태 관리
    game_date = db.Column(db.DateTime, nullable=False) #경기일자
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(KST), nullable=False) #판매티켓 생성 날짜 및 시간

    seller = db.relationship('User', backref=db.backref('ticket_set'))    

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True) # 고유번호
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False) # 티켓 클래스의 티켓 고유번호
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # User 클래스의 user.id  티켓구매자
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(KST), nullable=False) # 티켓 거래 날짜 및 시간

    ticket = db.relationship('Ticket', backref=db.backref('order', uselist=False))
    buyer = db.relationship('User', backref=db.backref('order_set'))

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(50), unique=True, nullable=False)
    logo_image = db.Column(db.String(100), nullable=False)