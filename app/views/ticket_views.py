from flask import Blueprint, render_template, request

bp = Blueprint('ticket', __name__, url_prefix='/ticket')  # /ticket 경로 묶음 생성

@bp.route('/list')
def ticket_list():
    team = request.args.get('team')      # URL에서 team 값 가져오기
    option = request.args.get('option')  # URL에서 option 값 가져오기
    return render_template('ticket.html', team=team, option=option)  # HTML로 값 전달