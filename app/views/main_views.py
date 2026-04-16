# app/views/main_views.py
from flask import Blueprint, render_template

from app.models import Ticket
from constants import KBO_TEAMS

bp = Blueprint('main', __name__, url_prefix='/')


@bp.route('/')
def index():
    # '판매중'인 티켓을 최신순으로 4개만 가져옵니다.
    recent_tickets = Ticket.query.filter_by(status='판매중').order_by(Ticket.created_at.desc()).limit(4).all()

    return render_template('index.html', recent_tickets=recent_tickets)