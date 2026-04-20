from datetime import datetime, timedelta
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
import requests
from app.models import Notification, Order, Ticket
from app.views.auth_views import login_required
from constants import KBO_TEAMS
from app import db
from werkzeug.security import generate_password_hash
from sqlalchemy import or_,func


# 티켓카드 이름 간소화
TEAM_SHORT_NAMES = {
    '두산베어스': '두산',
    '삼성라이온즈': '삼성',
    'NC다이노스': 'NC',
    'SSG랜더스': 'SSG',
    'LG트윈스': 'LG',
    '롯데자이언츠': '롯데',
    'KIA타이거즈': 'KIA',
    '키움히어로즈': '키움',
    '한화이글스': '한화',
    'KT위즈': 'KT'
}

# 등록 시 팀 이름 통일
TEAM_NORMALIZE = {
    '두산': '두산베어스',
    '삼성': '삼성라이온즈',
    'NC': 'NC다이노스',
    'SSG': 'SSG랜더스',
    'LG': 'LG트윈스',
    '롯데': '롯데자이언츠',
    'KIA': 'KIA타이거즈',
    '키움': '키움히어로즈',
    '한화': '한화이글스',
    'KT': 'KT위즈'
}

bp = Blueprint('ticket', __name__, url_prefix='/ticket')



@bp.route('/list')
def ticket_list():

    # 1. 새롭게 추가된 부분: 검색창 로직 (가장 먼저 실행)
    kw = request.args.get('kw', '').strip()
    
    if kw:
        teams = ["두산베어스", "LG트윈스", "한화이글스", "SSG랜더스", "삼성라이온즈", 
                 "NC다이노스", "KTwiz", "롯데자이언츠", "KIA타이거즈", "키움히어로즈"]
        
        found_team = next((t for t in teams if kw.upper() in t.upper()), None)
        
        if found_team:
            return redirect(url_for('ticket.ticket_list', team=found_team))

    awayteam = request.args.get('awayteam', '')
    seat = request.args.get('seat', '')
    quantity = request.args.get('quantity', '')
    game_date = request.args.get('game_date', '')
    team = request.args.get('team', '')
    option = request.args.get('option', '')
    page = request.args.get('page', 1, type=int)

    query = Ticket.query

    # 판매중만 보고 싶으면 같이 넣기
    query = query.filter(Ticket.status == '판매중')

    # 네비바에서 선택한 홈팀 필터
    if team:
        query = query.filter(Ticket.Hometeam_name == team)

    # 네비바에서 선택한 서브카테고리 필터
    if option:
        query = query.filter(Ticket.sub_category == option)

    # 상대팀 필터
    if awayteam:
        query = query.filter(Ticket.awayteam_name == awayteam)

    # 좌석 필터 (상세 좌석 번호 또는 좌석 등급 포함 검색)
    if seat:
        query = query.filter(or_(Ticket.seat.contains(seat), Ticket.seat_grade.contains(seat)))

    # 수량 필터
    if quantity:
        query = query.filter(Ticket.quantity == int(quantity))

    # 경기 날짜 필터
    if game_date:
        try:
            selected_date = datetime.strptime(game_date, '%Y-%m-%d')
            next_date = selected_date + timedelta(days=1)

            query = query.filter(
                Ticket.game_date >= selected_date,
                Ticket.game_date < next_date
            )
        except ValueError:
            pass

    # 같은 팀 vs 같은 팀 제외
    query = query.filter(Ticket.Hometeam_name != Ticket.awayteam_name)

    tickets = query.order_by(Ticket.created_at.desc()).paginate(
        page=page,
        per_page=10,
        error_out=False
    )

    selected_team_data = None
    for t in KBO_TEAMS:
        if t['name'] == team:
            selected_team_data = t
            break

    # 카드에서 쓸 짧은 팀명 붙여주기
    team_short_map = {
        '두산베어스': '두산',
        'LG트윈스': 'LG',
        '한화이글스': '한화',
        'SSG랜더스': 'SSG',
        '삼성라이온즈': '삼성',
        'NC다이노스': 'NC',
        'KT위즈': 'KT',
        '롯데자이언츠': '롯데',
        'KIA타이거즈': 'KIA',
        '키움히어로즈': '키움'
    }

    for ticket in tickets.items:
        ticket.awayteam_short = team_short_map.get(ticket.awayteam_name, ticket.awayteam_name)

    return render_template(
        'ticket.html',
        tickets=tickets,
        kbo_teams=KBO_TEAMS,
        selected_team_data=selected_team_data,
        team=team,
        option=option
    )

# 프론트엔드에서 결제 성공 시!
@bp.route('/pay/success')
def pay_success():
    # 1. 토스가 URL에 붙여서 보낸 데이터 3가지 받기
    payment_key = request.args.get('paymentKey')
    order_id = request.args.get('orderId')
    amount = request.args.get('amount')

    # 2. 토스 개발자 센터에서 발급받은 '시크릿 키'
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

        # 구매자 알림
        buyer_noti_msg = f"'{ticket.Hometeam_name}전' 티켓 결제가 완료되었습니다."
        buyer_noti_link = url_for('ticket.ticket_history', tab='purchase') # 알림 클릭 시 구매 내역 페이지로 이동
        
        buyer_noti = Notification(
            user_id=g.user.id, 
            message=buyer_noti_msg, 
            link=buyer_noti_link
        )
        db.session.add(buyer_noti)

        # 판매자 알림
        seller_noti_msg = f"등록하신 '{ticket.Hometeam_name}전' 티켓이 판매되었습니다."
        seller_noti_link = url_for('ticket.ticket_history', tab='sales') # 알림 클릭 시 판매 내역 페이지로 이동
        
        seller_noti = Notification(
            user_id=ticket.seller_id,
            message=seller_noti_msg,
            link=seller_noti_link
        )
        db.session.add(seller_noti)

        # 결제 금액 검증: 토스에서 받은 금액과 DB에 저장된 티켓의 총 금액을 비교
        expected_total_amount = ticket.price * ticket.quantity
        if int(amount) != expected_total_amount:
            db.session.rollback() # 금액 불일치 시 롤백
            flash("결제 금액이 일치하지 않습니다. 관리자에게 문의해주세요.")
            print(f"결제 금액 불일치: Toss 응답 금액 {amount}, 예상 금액 {expected_total_amount}")
            return redirect(url_for('main.index'))

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
            return render_template('auth/order_success.html', ticket=ticket)
        
        except Exception as e:
            # 만약 DB 저장 중 에러가 나면, 변경 사항을 되돌리고(rollback) 에러를 알립니다.
            db.session.rollback()
            print(f"DB 저장 에러: {e}") # 터미널 창에서 원인 확인용
            flash("결제는 승인되었으나 시스템 저장 중 문제가 발생했습니다. 관리자에게 문의해주세요.")
            return redirect(url_for('main.index'))
        
    else:
        #  승인 실패 (금액이 조작되었거나, 한도가 초과된 경우 등)
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

        #  사용자가 입력한 PIN 번호를 암호화 // 구매자에게 보이기 위해선 암호화 임시 제거 추후 다른방향모색
        # hashed_pin = generate_password_hash(user_pin)

        # Ticket 객체 생성
        ticket = Ticket(
            seller_id=g.user.id, # 현재 로그인된 사용자 ID
            Hometeam_name=hometeam_name,
            awayteam_name=awayteam_name,
            sub_category=sub_category,
            seat_grade=seat_grade,
            seat=seat_detail,
            quantity=quantity,
            price=price, # 1매당 가격
            pin=user_pin, # 암호화된 PIN 저장
            game_date=game_datetime
        )

        # DB에 저장
        db.session.add(ticket)
        db.session.commit()

        flash('티켓이 성공적으로 등록되었습니다!', 'success')
        return redirect(url_for('main.index')) # 등록 후 메인 페이지로 리다이렉트

    # GET 요청 시 폼 렌더링
    return render_template('ticket/ticket_create.html')

# 티켓 상세정보 페이지 연결 (주소: /ticket/ticket_detail/<int:ticket_id>)
@bp.route('/ticket_detail/<int:ticket_id>/')
@login_required
def ticket_detail(ticket_id):
    # DB에서 해당 티켓을 찾기
    ticket = Ticket.query.get_or_404(ticket_id)
    # 찾은 ticket 데이터를 HTML로 리턴

    return render_template('ticket/ticket_detail.html', ticket=ticket)

# 구매/판매 완료된 티켓 상세 정보 확인 페이지 (새로 추가)
@bp.route('/view_detail/<int:ticket_id>/')
@login_required
def view_ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # 권한 체크: 판매자이거나 구매자인 경우에만 접근 허용
    is_seller = (g.user.id == ticket.seller_id)
    is_buyer = (ticket.order and g.user.id == ticket.order.buyer_id)
    if not (is_seller or is_buyer):
        flash("접근 권한이 없습니다.", "danger")
        return redirect(url_for('main.index'))
        
    # 이 페이지는 구매/판매 완료된 티켓의 상세 정보를 보여주며, 결제 위젯은 없습니다.
    return render_template('ticket/ticket_view_detail.html', ticket=ticket)

# 거래내역
@bp.route('/history/')
@login_required
def ticket_history():
    tab = request.args.get('tab', 'purchase')
    page = request.args.get('page', 1, type=int)
    # 구매 내역: 내가 산 주문(Order)들 (최신순)
    purchases = Order.query.filter_by(buyer_id=g.user.id).order_by(Order.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    
    # 판매 내역: 내가 등록한 티켓(Ticket)들 (최신순)
    sales = Ticket.query.filter_by(seller_id=g.user.id).order_by(Ticket.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('ticket/ticket_history.html', 
                           purchases=purchases, 
                           sales=sales,
                           tab=tab)

# 구매확정 처리 라우트 (주소: /ticket/confirm_purchase/<order_id>/)
@bp.route('/confirm_purchase/<int:order_id>/', methods=['POST'])
@login_required
def confirm_purchase(order_id):
    # 넘어온 주문번호로 Order 찾기
    order = Order.query.get_or_404(order_id)
    # 본인 확인 티켓 구매자가 맞는지 검증
    if order.buyer_id != g.user.id:
        flash("권한이 없습니다.")
        return redirect(url_for('ticket.ticket_history'))
    # 3. 티켓 상태를 '거래완료'로 변경
    order.ticket.status = '거래완료'
    
    # 4. 판매자에게 구매 확정 알림 전송
    seller_noti_msg = f"등록하신 '{order.ticket.Hometeam_name}전' 티켓의 구매 확정 및 정산이 진행됩니다."
    seller_noti_link = url_for('ticket.ticket_history', tab='sales')
    seller_noti = Notification(
        user_id=order.ticket.seller_id,
        message=seller_noti_msg,
        link=seller_noti_link
    )
    db.session.add(seller_noti)
    
    # 5. DB 저장
    try:
        db.session.commit()
        flash("구매확정이 완료되었습니다. 판매자에게 정산이 진행됩니다.")
    except Exception as e:
        db.session.rollback()
        print(f"구매확정 에러: {e}")
        flash("처리 중 오류가 발생했습니다.")
        
    # 처리가 끝나면 다시 거래 내역(탭) 페이지로 이동
    return redirect(url_for('ticket.ticket_history'))

# 티켓삭제
@bp.route('/ticket_delete/<int:ticket_id>/')
@login_required
def delete_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if g.user.id != ticket.seller_id:
        flash('삭제권한이 없습니다')
        return redirect(url_for('ticket.ticket_detail', ticket_id=ticket_id))
    db.session.delete(ticket)
    db.session.commit()
    flash('상품이 성공적으로 삭제되었습니다.', 'success')
    return redirect(url_for('auth.mypage'))

# 티켓 수정
@bp.route('/ticket_modify/<int:ticket_id>/', methods=['GET', 'POST'])
@login_required
def ticket_modify(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # 권한 체크: 판매자 본인인지 확인
    if g.user.id != ticket.seller_id:
        flash('수정 권한이 없습니다.', 'danger')
        return redirect(url_for('ticket.view_ticket_detail', ticket_id=ticket_id))
        
    if request.method == 'POST':
        ticket.Hometeam_name = request.form.get('hometeam')
        ticket.sub_category = request.form.get('sub_category')
        ticket.awayteam_name = request.form.get('awayteam')
        ticket.seat_grade = request.form.get('seat_grade')
        ticket.seat = request.form.get('seat')
        ticket.quantity = request.form.get('quantity', type=int)
        ticket.price = request.form.get('price', type=int)
        ticket.pin = request.form.get('pin')
        
        game_date_str = request.form.get('game_date')
        game_time_hour = request.form.get('game_time_hour')
        game_time_minute = request.form.get('game_time_minute')
        
        try:
            game_datetime_str = f"{game_date_str} {game_time_hour}:{game_time_minute}"
            ticket.game_date = datetime.strptime(game_datetime_str, '%Y-%m-%d %H:%M')
        except ValueError:
            flash('유효하지 않은 날짜 또는 시간 형식입니다.', 'danger')
            return render_template('ticket/ticket_create.html', ticket=ticket)
            
        db.session.commit()
        flash('티켓 정보가 성공적으로 수정되었습니다.', 'success')
        return redirect(url_for('ticket.view_ticket_detail', ticket_id=ticket.id))
        
    return render_template('ticket/ticket_create.html', ticket=ticket)

   

# 1. 장바구니에 티켓 담기 
@bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    ticket_id = request.json.get('ticket_id')

    if 'cart' not in session:

        session['cart'] = []

    if ticket_id not in session['cart']:
        session['cart'].append(ticket_id)

        session.modified = True 

    return jsonify({
        "status": "success", 
        "cart_count": len(session['cart'])
    })

# 2. 장바구니 페이지 렌더링 
@bp.route('/cart')
def cart_page():
    cart_ids = session.get('cart', [])

    if cart_ids:

        cart_tickets = Ticket.query.filter(Ticket.id.in_(cart_ids)).all()
    else:
        cart_tickets = []

    return render_template('ticket/cart.html', tickets=cart_tickets)

# 3.  장바구니에서 삭제 
@bp.route('/cart/remove/<int:ticket_id>')
def remove_from_cart(ticket_id):
    cart = session.get('cart', [])
    
    if ticket_id in cart:
        cart.remove(ticket_id)
        session['cart'] = cart
        session.modified = True
        # flash("장바구니에서 삭제되었습니다.") # 필요하면 주석 해제
    
    return redirect(url_for('ticket.cart_page'))

#4. 장바구니에서 선택한 항목들만 골라서 삭제하기 (프론트엔드 -> 백엔드)
@bp.route('/cart/remove_selected', methods=['POST'])
def remove_selected_cart():
    # 프론트에서 보낸 ID 리스트 받기
    ticket_ids = request.json.get('ticket_ids', [])
    cart = session.get('cart', [])

    # 선택된 ID들만 장바구니 세션에서 제외
    # 리스트 컴프리헨션을 써서 포함되지 않은 것들만 남깁니다.
    new_cart = [tid for tid in cart if str(tid) not in [str(sid) for sid in ticket_ids]]
    
    session['cart'] = new_cart
    session.modified = True
    
    return jsonify({"status": "success"})

# 5. 모든 페이지에서 장바구니 숫자를 바로 쓸 수 있게 해주는 기능
@bp.app_context_processor
def inject_cart_count():
    # 세션에서 cart 리스트를 가져온 뒤 그 길이를 반환
    cart_ids = session.get('cart', [])
    return dict(current_cart_count=len(cart_ids))