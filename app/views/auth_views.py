from flask import Blueprint, flash, redirect, render_template, request, url_for, g
import requests
# from flask import current_app # 사용되지 않아 주석 처리 또는 삭제 가능
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from app.form import UserLoginForm
from datetime import datetime
from app.models import User, Ticket
import functools


from app import db

from app.form import UserCreateForm
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

# 블루프린트 생성.
# url_prefix='/auth를 설정하면 모든 주소 앞에 /auth가 자동
bp = Blueprint('auth', __name__, url_prefix='/auth')

# 모든 요청 전에 실행되어 g.user를 세팅하는 함수
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)

# 로그인이 필요한 페이지에 적용할 데코레이터
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('로그인이 필요합니다.')
            return redirect(url_for('auth.login', next=request.url)) # next 파라미터 추가
        return view(**kwargs)
    return wrapped_view

# 2. 로그인 페이지 연결 (주소: /auth/login)
@bp.route('/login/', methods=['GET', 'POST'])
def login():
    form = UserLoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        error = None
        #고유값인 email로 사용자를 찾습니다.
        user = User.query.filter_by(email=form.email.data).first()
        
        if not user:
            error = '존재하지 않는 사용자입니다.'
        # 비밀번호 검증 (암호화된 비번과 입력된 비번 비교)
        elif not check_password_hash(user.password, form.password.data):
            error = '비밀번호가 올바르지 않습니다.'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            
            # 이전 페이지 정보(next)가 있으면 그곳으로, 없으면 메인으로 리다이렉트
            _next = request.args.get('next', '')
            return redirect(_next) if _next else redirect(url_for('main.index'))
            
        flash(error)
    return render_template('auth/login.html', form=form)


# 3. 회원가입 페이지 연결 (주소: /auth/signup)
@bp.route('/signup/', methods=['GET', 'POST'])
def signup():
    form = UserCreateForm()
    if request.method == 'POST' and form.validate_on_submit():
        # 1. 중복 사용자 체크 (이메일 및 닉네임)
        user_by_email = User.query.filter_by(email=form.email.data).first()
        user_by_nick = User.query.filter_by(nickname=form.nickname.data).first()
        
        if user_by_email:
            flash('이미 가입된 이메일입니다.')
        elif user_by_nick:
            flash('이미 사용 중인 닉네임입니다.')
        else:
            # 주소 합치기 (기본주소 + 상세주소)
            # 템플릿의 상세주소 input name인 'detailAddress' 값
            full_address = f"{form.address.data} {request.form.get('detailAddress', '')}".strip()

            # DB 저장
            user = User(
                username=form.username.data,
                nickname=form.nickname.data,
                email=form.email.data,
                password=generate_password_hash(form.password1.data),
                phone=form.phone.data,
                address=full_address
            )
            db.session.add(user)
            db.session.commit()
            
            flash(f'{user.nickname}님, 가입을 환영합니다! 로그인 해주세요.')
            return redirect(url_for('auth.login'))

    return render_template('auth/signup.html', form=form)


# 4. 마이페이지 연결 (주소: /auth/mypage)
@bp.route('/mypage/')
@login_required # 로그인 데코레이터 추가
def mypage():
    return render_template('auth/mypage.html')

# 5. 상품등록페이지 연결 (주소: /auth/ticket_create)
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
            return render_template('auth/ticket_create.html') 
        # game_date와 game_time을 조합하여 datetime 객체 생성
        try:
            # YYYY-MM-DD HH:MM 형식의 문자열 생성
            game_datetime_str = f"{game_date_str} {game_time_hour}:{game_time_minute}"
            game_datetime = datetime.strptime(game_datetime_str, '%Y-%m-%d %H:%M')
        except ValueError:
            flash('유효하지 않은 날짜 또는 시간 형식입니다.', 'danger')
            return render_template('auth/ticket_create.html')

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
    return render_template('auth/ticket_create.html')

@bp.route('/subpage/<int:ticket_id>')
def subpage(ticket_id):
    # DB에서 해당 티켓을 찾기
    ticket = Ticket.query.get_or_404(ticket_id)
    # 찾은 ticket 데이터를 HTML로 리턴
    return render_template('auth/subpage.html', ticket=ticket)


# 카카오 로그인 구현
@bp.route('/kakao/login')
def kakao_login():
    # 카카오 인증 서버로 사용자를 보냅니다.
    kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code"
    return redirect(kakao_auth_url)

@bp.route('/kakao/callback')
def kakao_callback():
    code = request.args.get("code")
    
    # 1. 토큰 요청
    token_url = "https://kauth.kakao.com/oauth/token"
    headers = {'Content-type': 'application/x-www-form-urlencoded;charset=utf-8'}
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "code": code,
        "client_secret": CLIENT_SECRET  
    }
    
    token_res = requests.post(token_url, data=data, headers=headers).json()
        
    access_token = token_res.get("access_token")

    if not access_token:
        return f"토큰 발급 실패: {token_res.get('error_description', '알 수 없는 오류')}"

    # 2. 유저 정보 요청
    user_info_url = "https://kapi.kakao.com/v2/user/me"
    user_headers = {"Authorization": f"Bearer {access_token}"}
    user_res = requests.get(user_info_url, headers=user_headers).json()

    # 카카오가 준 정보 추출
    kakao_id = str(user_res.get("id")) 
    kakao_email = user_res.get("kakao_account", {}).get("email")
    kakao_nickname = user_res.get("properties", {}).get("nickname", "카카오유저")

    # 세션 비우고 시작
    session.clear()
    # DB에서 'kakao_id'로 사용자 찾기
    user = User.query.filter_by(kakao_id=kakao_id).first()

    if not user:
        # 같은 이메일로 이미 가입한 일반 회원이 있는지 (계정 통합용)
        user = User.query.filter_by(email=kakao_email).first()
        
        if user:
            # 이미 이메일로 가입한 사람이면 kakao_id만 업데이트해서 연결
            user.kakao_id = kakao_id
            db.session.commit()
            flash(f"{user.nickname}님의 기존 계정에 카카오 로그인이 연결되었습니다.")
        else:
            # 처음 온 사람이면 새로 가입 DB추가
            user = User(
                username=kakao_nickname,
                nickname=kakao_nickname,
                email=kakao_email,
                kakao_id=kakao_id,  # 새로 만든 컬럼에 저장!
                password=generate_password_hash(f"kakao_{kakao_id}"),
                phone="010-0000-0000",
                address="카카오 로그인 유저"
            )
            db.session.add(user)
            db.session.commit()
            flash(f"{kakao_nickname}님, 카카오 계정으로 첫 가입을 축하합니다!")
    else:
        flash(f"{user.nickname}님, 환영합니다!")

    # 4. 세션에 로그인 정보 저장
    session['user_id'] = user.id

    # 5. 메인 페이지로 이동!
    return redirect(url_for('main.index'))
  
@bp.route('/ticket/<int:ticket_id>/')
def detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    return render_template('auth/subpage.html', ticket=ticket)
