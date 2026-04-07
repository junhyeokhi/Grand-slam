from datetime import datetime
from sqlalchemy.orm import backref

from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team_name = db.Column(db.String(50), nullable=False)  # KBO 구단명
    sub_category = db.Column(db.String(100))  # 상세 구간
    price = db.Column(db.Integer, nullable=False)
    pin = db.Column(db.String(100), nullable=False)  # 거래 중요 데이터
    status = db.Column(db.String(20), default='판매중')  # 상태 관리


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
