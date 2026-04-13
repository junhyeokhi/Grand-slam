import requests
from flask import current_app
from flask import Blueprint, flash, redirect, render_template, request, url_for, g
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from app.form import UserLoginForm
from app.models import User, Ticket
import functools


from app import db

from app.form import UserCreateForm
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

# 블루프린트 생성.
# url_prefix='/auth를 설정하면 모든 주소 앞에 /auth가 자동
bp = Blueprint('auth', __name__, url_prefix='/auth')


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
def mypage():
    return render_template('auth/mypage.html')

# 5. 상품등록페이지 연결 (주소: /auth/ticket_creat)
@bp.route('/ticket_create/')
def ticket_create():
    return render_template('auth/ticket_create.html')


@bp.route('/subpage/')
def subpage():
    return render_template('auth/subpage.html')

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
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

@bp.route('/ticket/<int:ticket_id>/')
def detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    return render_template('auth/subpage.html', ticket=ticket)
