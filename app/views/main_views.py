# app/views/main_views.py
from flask import Blueprint, render_template, redirect, url_for, flash, g

from app.models import Ticket, Notification
from constants import KBO_TEAMS
from app import db

bp = Blueprint('main', __name__, url_prefix='/')


@bp.route('/')
def index():
    # '판매중'인 티켓을 최신순으로 4개만 가져옵니다.
    recent_tickets = Ticket.query.filter_by(status='판매중').order_by(Ticket.created_at.desc()).limit(4).all()

    return render_template('index.html', recent_tickets=recent_tickets)

# 알림 읽음 처리 및 이동 라우트
@bp.route('/read_noti/<int:noti_id>')
def read_noti(noti_id):
    if g.user is None:
        return redirect(url_for('auth.login'))
        
    noti = Notification.query.get_or_404(noti_id)
    if noti.user_id != g.user.id:
        flash('권한이 없습니다.', 'danger')
        return redirect(url_for('main.index'))
        
    noti.is_read = True
    db.session.commit()
    
    # 알림에 연결된 주소가 있으면 그곳으로, 없으면 메인으로 이동
    return redirect(noti.link if noti.link else url_for('main.index'))