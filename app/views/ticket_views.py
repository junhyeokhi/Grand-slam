from flask import Blueprint, render_template, request
from app.models import Ticket
from constants import KBO_TEAMS

bp = Blueprint('ticket', __name__, url_prefix='/ticket')

@bp.route('/list')
def ticket_list():
    awayteam = request.args.get('awayteam', '')
    seat = request.args.get('seat', '')
    quantity = request.args.get('quantity', '')
    team = request.args.get('team', '')
    option = request.args.get('option', '')

    query = Ticket.query

    if awayteam:
        query = query.filter(Ticket.awayteam_name == awayteam)

    if seat:
        query = query.filter(Ticket.seat.contains(seat))

    if quantity:
        query = query.filter(Ticket.quantity == int(quantity))

    tickets = query.order_by(Ticket.game_date.asc()).all()

    selected_team_data = None
    for t in KBO_TEAMS:
        if t['name'] == team:
            selected_team_data = t
            break

    return render_template(
        'ticket.html',
        tickets=tickets,
        team=team,
        option=option,
        kbo_teams=KBO_TEAMS,
        selected_team_data=selected_team_data
    )