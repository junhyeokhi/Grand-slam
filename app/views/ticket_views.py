from datetime import datetime
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
import requests
from app.models import Order, Ticket
from app.views.auth_views import login_required
from constants import KBO_TEAMS
from app import db
from werkzeug.security import generate_password_hash

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

# 프론트엔드에서 결제 성공 시!
@bp.route('/pay/success')
def pay_success():
    # 1. 토스가 URL에 붙여서 보낸 데이터 3가지 받기
    payment_key = request.args.get('paymentKey')
    order_id = request.args.get('orderId')
    amount = request.args.get('amount')

    # 2. 토스 개발자 센터에서 발급받은 '시크릿 키' (반드시 test_sk_ 로 시작!)
    TOSS_SECRET_KEY = "test_gsk_docs_OaPz8L5KdmQXkzRz3y47BMw6"

    # 3. 토스 서버로 '결제 최종 승인' API 요청 보내기
    url = "https://api.tosspayments.com/v1/payments/confirm"
    data = {
        "paymentKey": payment_key,
        "orderId": order_id,
        "amount": amount
    }

    # requests 라이브러리로 POST 요청 (auth 파라미터에 시크릿 키를 넣으면 알아서 인증해 줍니다)
    response = requests.post(url, json=data, auth=(TOSS_SECRET_KEY, ''))

    # 4. 토스 서버의 응답 결과 확인
    if response.status_code == 200:
        # 승인 성공시
        # URL 속 티켓 아이디 가져오기
        ticket_id = request.args.get('ticket_id')
        ticket = Ticket.query.get_or_404(ticket_id)
        # 티켓 상태변경
        ticket.status = '판매완료'
        
        new_order = Order(
            ticket_id=ticket.id,
            buyer_id=session.get('user_id') # 세션에 저장된 로그인 유저 ID
        )
        
        db.session.add(new_order)
        
        try:
            db.session.commit()
            flash("결제가 성공적으로 완료되었습니다!")
            return redirect(url_for('auth.mypage'))
        
        except Exception as e:
            # 만약 DB 저장 중 에러가 나면, 변경 사항을 되돌리고(rollback) 에러를 알립니다.
            db.session.rollback()
            print(f"DB 저장 에러: {e}") # 터미널 창에서 원인 확인용
            flash("결제는 승인되었으나 시스템 저장 중 문제가 발생했습니다. 관리자에게 문의해주세요.")
            return redirect(url_for('main.index'))
        
    else:
        # 💥 승인 실패 (금액이 조작되었거나, 한도가 초과된 경우 등)
        error_data = response.json()
        error_msg = error_data.get('message', '알 수 없는 결제 에러가 발생했습니다.')
        
        flash(f"결제 실패: {error_msg}")
        return redirect(url_for('main.index'))

@bp.route('/pay/fail')
def pay_fail():
    # 결제 실패 시 에러 메시지를 받아서 화면에 띄워줍니다
    error_msg = request.args.get('message', '결제가 취소되었거나 실패했습니다.')
    flash(error_msg)
    return redirect(url_for('main.index')) # 홈 화면이나 티켓 상세로 돌아가기

#  상품등록페이지 연결 (주소: /auth/ticket_create)
@bp.route('/ticket_create/', methods=['GET', 'POST'])
@login_required # 로그인 데코레이터 추가
def ticket_create():
    if request.method == 'POST':
        # 폼 데이터 추출
        hometeam_name = request.form.get('hometeam')
        sub_category = request.form.get('sub_category') # 경기 정보 (장소 및 요일)
        awayteam_name = request.form.get('awayteam')
        game_date_str = request.form.get('game_date') # YYYY-MM-DD
        game_time_hour = request.form.get('game_time_hour') # HH
        game_time_minute = request.form.get('game_time_minute') # MM
        seat_grade = request.form.get('seat_grade')
        seat_detail = request.form.get('seat') # 'seat_detail' input의 name은 'seat' (상세 위치)
        quantity = request.form.get('quantity', type=int)
        price = request.form.get('price', type=int)
        user_pin = request.form.get('pin') # 사용자가 입력한 PIN 번호

        # 필수 필드 검증
        if not all([hometeam_name, sub_category, awayteam_name, game_date_str, game_time_hour,
                    game_time_minute, seat_grade, seat_detail, quantity, price, user_pin]):
            flash('모든 필수 필드를 입력해주세요.', 'danger')
            return render_template('ticket/ticket_create.html') 
        # game_date와 game_time을 조합하여 datetime 객체 생성
        try:
            # YYYY-MM-DD HH:MM 형식의 문자열 생성
            game_datetime_str = f"{game_date_str} {game_time_hour}:{game_time_minute}"
            game_datetime = datetime.strptime(game_datetime_str, '%Y-%m-%d %H:%M')
        except ValueError:
            flash('유효하지 않은 날짜 또는 시간 형식입니다.', 'danger')
            return render_template('ticket/ticket_create.html')

        # 'seat' 필드에 좌석 등급과 상세 위치를 조합하여 저장
        full_seat_info = f"{seat_grade} {seat_detail}".strip()

        # 사용자가 입력한 PIN 번호를 암호화
        hashed_pin = generate_password_hash(user_pin)
        # Ticket 객체 생성
        ticket = Ticket(
            seller_id=g.user.id, # 현재 로그인된 사용자 ID
            Hometeam_name=hometeam_name,
            awayteam_name=awayteam_name,
            sub_category=sub_category,
            seat=full_seat_info,
            quantity=quantity,
            price=price, # 1매당 가격
            pin=hashed_pin, # 암호화된 PIN 저장
            game_date=game_datetime
        )

        # DB에 저장
        db.session.add(ticket)
        db.session.commit()

        flash('티켓이 성공적으로 등록되었습니다!', 'success')
        return redirect(url_for('main.index')) # 등록 후 메인 페이지로 리다이렉트

    # GET 요청 시 폼 렌더링
    return render_template('ticket/ticket_create.html')