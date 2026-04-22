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
    role = db.Column(db.String(20), default='user')
    is_deleted = db.Column(db.Boolean, default=False, nullable=False) #탈퇴 여부 꼬리표
    deleted_at = db.Column(db.DateTime, nullable=True)# 탈퇴 버튼을 누른 시간


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True) # 고유번호
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) #판매자 id
    Hometeam_name = db.Column(db.String(50), nullable=False)  # KBO 구단명
    awayteam_name = db.Column(db.String(50), nullable=False)  # KBO 구단명
    sub_category = db.Column(db.String(100))  # 상세 구간
    seat_grade = db.Column(db.String(100))  # 좌석 등급 (예: 3루 응원지정석)
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

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False) # 문의 제목
    content = db.Column(db.Text(), nullable=False)     # 문의 내용
    create_date = db.Column(db.DateTime(), nullable=False) # 작성일
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', backref=db.backref('question_set'))
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id', ondelete='SET NULL'), nullable=True) # 관련 티켓 (선택)
    ticket = db.relationship('Ticket', backref=db.backref('questions'))

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id', ondelete='CASCADE'), nullable=False) # 어떤 문의글에 대한 답변인지
    question = db.relationship('Question', backref=db.backref('answer_set'))
    content = db.Column(db.Text(), nullable=False)         # 답변 내용
    create_date = db.Column(db.DateTime(), nullable=False) # 작성일
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False) # 답변을 작성한 관리자
    user = db.relationship('User', backref=db.backref('admin_answer_set'))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # 알림 받을 사람
    message = db.Column(db.String(255), nullable=False) # 알림 내용 (예: "결제가 완료되었습니다.")
    link = db.Column(db.String(255), nullable=True)     # 클릭 시 이동할 주소 (예: 주문 내역 페이지)
    is_read = db.Column(db.Boolean, default=False)      # 읽음 여부 (안 읽었으면 뱃지 띄우기)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(KST), nullable=False)

    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic', order_by='desc(Notification.created_at)'))

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 이 부분을 추가하면 cart.ticket.title 처럼 티켓 정보에 바로 접근 가능합니다.
    user = db.relationship('User', backref=db.backref('cart_items', lazy=True))
    ticket = db.relationship('Ticket', backref=db.backref('in_carts', lazy=True))
