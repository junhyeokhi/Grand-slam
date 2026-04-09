# app/views/main_views.py
from flask import Blueprint, render_template
from constants import KBO_TEAMS

bp = Blueprint('main', __name__, url_prefix='/')


@bp.route('/')
def index():
    return render_template('index.html')
