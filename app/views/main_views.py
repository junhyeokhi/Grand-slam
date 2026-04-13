# app/views/main_views.py
from flask import Blueprint, render_template

from app.models import Ticket
from constants import KBO_TEAMS

bp = Blueprint('main', __name__, url_prefix='/')


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/ticket/<int:ticket_id>/')
def detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    return render_template('subpage.html', ticket=ticket)