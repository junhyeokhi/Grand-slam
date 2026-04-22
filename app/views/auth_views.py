from flask import Blueprint, flash, redirect, render_template, request, url_for, g
import requests
# from flask import current_app # 사용되지 않아 주석 처리 또는 삭제 가능

from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from app.form import UserLoginForm
from datetime import datetime, timedelta
from app.models import User, Ticket, Question, Answer, Notification, Order
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

# 관리자 권한이 필요한 페이지에 적용할 데코레이터
def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user.role != 'admin':
            flash('관리자 권한이 필요합니다.', 'danger')
            return redirect(url_for('main.index'))
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
            
            # 로그인 성공 시: 탈퇴된 계정인지 확인
            if user.is_deleted:
                deadline = user.deleted_at + timedelta(days=30)
                if datetime.now() <= deadline:
                    user.is_deleted = False
                    user.deleted_at = None
                    db.session.commit()
                    flash("환영합니다! 탈퇴가 취소되고 계정이 성공적으로 복구되었습니다.", "success")
                else:
                    session.clear() # 완전히 삭제된 계정이므로 다시 세션 비우기
                    flash("탈퇴 후 30일이 경과하여 완전히 삭제된 계정입니다.", "danger")
                    return redirect(url_for('auth.login'))
            
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

# 6. 회원정보 수정 페이지 연결 (주소: /auth/edit_profile)
@bp.route('/edit_profile/', methods=['GET', 'POST'])
@login_required
def edit_profile():
    from app.form import UserEditForm # UserEditForm 임포트
    form = UserEditForm()
    
    if request.method == 'GET':
        # 현재 로그인된 사용자 정보로 폼 필드 미리 채우기
        form.email.data = g.user.email
        form.username.data = g.user.username
        form.nickname.data = g.user.nickname
        form.phone.data = g.user.phone
        
        # 저장된 주소를 기본 주소와 상세 주소로 분리하여 폼에 채움
        # User.address는 "기본주소 상세주소" 형식으로 저장되어 있다고 가정
        address_parts = g.user.address.split(' ', 1)
        form.address.data = address_parts[0] if address_parts else ''
        detail_address_value = address_parts[1] if len(address_parts) > 1 else ''
        
        return render_template('auth/edit_profile.html', form=form, detail_address_value=detail_address_value)
    
    elif request.method == 'POST' and form.validate_on_submit():
        # 이메일 변경 시 중복 확인 (단, 본인의 이메일은 허용)
        if form.email.data != g.user.email:
            user_by_email = User.query.filter_by(email=form.email.data).first()
            if user_by_email and user_by_email.id != g.user.id:
                flash('이미 사용 중인 이메일입니다.', 'danger')
                detail_address_value = request.form.get('detailAddress', '')
                return render_template('auth/edit_profile.html', form=form, detail_address_value=detail_address_value)
        
        # 닉네임 변경 시 중복 확인 (단, 본인의 닉네임은 허용)
        if form.nickname.data != g.user.nickname:
            user_by_nick = User.query.filter_by(nickname=form.nickname.data).first()
            if user_by_nick and user_by_nick.id != g.user.id:
                flash('이미 사용 중인 닉네임입니다.', 'danger')
                detail_address_value = request.form.get('detailAddress', '')
                return render_template('auth/edit_profile.html', form=form, detail_address_value=detail_address_value)

        # 사용자 정보 업데이트
        g.user.email = form.email.data
        g.user.username = form.username.data
        g.user.nickname = form.nickname.data
        g.user.phone = form.phone.data
        
        # 주소 업데이트 (기본 주소 + 상세 주소)
        full_address = f"{form.address.data} {request.form.get('detailAddress', '')}".strip()
        g.user.address = full_address

        # 새 비밀번호가 입력된 경우에만 비밀번호 업데이트
        if form.password.data:
            g.user.password = generate_password_hash(form.password.data)
        
        db.session.commit()
        flash('회원 정보가 성공적으로 수정되었습니다!', 'success')
        return redirect(url_for('auth.mypage')) # 수정 후 마이페이지로 리다이렉트
    
    # POST 요청에서 유효성 검사 실패 시, 입력된 값과 상세 주소를 다시 템플릿으로 전달
    detail_address_value = request.form.get('detailAddress', '')
    return render_template('auth/edit_profile.html', form=form, detail_address_value=detail_address_value)


# 회원탈퇴기능
@bp.route('/delete_user/')
@login_required
def delete_user():
    g.user.is_deleted = True
    g.user.deleted_at = datetime.now()
    db.session.commit()
    session.clear() # 탈퇴 후 자동 로그아웃
    flash('회원 탈퇴가 처리되었습니다. 30일 이내 다시 로그인하시면 계정이 복구됩니다.', 'success')
    return redirect(url_for('main.index'))
    
@bp.route('/logout/')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

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

@bp.route('/order/success/<int:ticket_id>/')
def order_success(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    # 템플릿의 for문을 위해 단일 객체도 리스트로 감싸서 전달합니다.
    return render_template('auth/order_success.html', tickets=[ticket])

# 나의 전체 알림 내역 페이지
@bp.route('/my_notifications/')
@login_required
def my_notifications():
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(user_id=g.user.id).order_by(Notification.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('auth/my_notifications.html', notifications=notifications)

# 모든 알림 일괄 읽음 처리
@bp.route('/read_all_notis/')
@login_required
def read_all_notis():
    Notification.query.filter_by(user_id=g.user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    # 이전 페이지(referrer)로 돌아가고, 정보가 없으면 메인 홈으로 이동합니다.
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/question/create/', methods=('GET', 'POST'))
@login_required  # 로그인이 필요한 기능
def create_question():
    if request.method == 'POST':
        subject = request.form['subject']
        content = request.form['content']
        ticket_id = request.form.get('ticket_id')
        
        if not ticket_id:
            ticket_id = None

        # DB에 저장
        question = Question(
            subject=subject,
            content=content,
            create_date=datetime.now(),
            user=g.user,
            ticket_id=ticket_id
        )
        db.session.add(question)
        db.session.commit()

        flash('문의가 성공적으로 등록되었습니다.')
        return redirect(url_for('auth.mypage'))  # 등록 후 마이페이지로 이동

    purchased_orders = Order.query.filter_by(buyer_id=g.user.id).order_by(Order.created_at.desc()).all()
    sold_tickets = Ticket.query.filter_by(seller_id=g.user.id).order_by(Ticket.created_at.desc()).all()
    return render_template('auth/question_form.html', purchased_orders=purchased_orders, sold_tickets=sold_tickets)

# 나의 문의 내역 페이지
@bp.route('/my_questions/')
@login_required
def my_questions():
    page = request.args.get('page', 1, type=int)
    # Question 모델에서 현재 로그인한 유저의 문의 내역을 최신순으로 정렬하여 페이징합니다.
    questions = Question.query.filter_by(user_id=g.user.id).order_by(Question.create_date.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('auth/my_questions.html', questions=questions)

# 문의 상세 내역 페이지
@bp.route('/question/<int:question_id>/')
@login_required
def question_detail(question_id):
    question = Question.query.get_or_404(question_id)
    if question.user_id != g.user.id:
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('auth.my_questions'))
    return render_template('auth/question_detail.html', question=question)

# 관리자: 전체 문의 내역 리스트
@bp.route('/admin/questions_list/')
@admin_required
def admin_questions_list():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')  # 'all', 'pending', 'completed'
    
    query = Question.query
    
    # 답변 상태에 따른 필터링 (answer_set 관계 활용)
    if status == 'pending':
        query = query.filter(~Question.answer_set.any())
    elif status == 'completed':
        query = query.filter(Question.answer_set.any())
        
    # 모든 사용자의 문의글을 최신순으로 정렬하여 가져옵니다.
    questions = query.order_by(Question.create_date.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('auth/admin_questions_list.html', questions=questions, status=status)

# 관리자: 문의 상세 및 답변 작성
@bp.route('/admin/question/<int:question_id>/', methods=['GET', 'POST'])
@admin_required
def admin_question_detail(question_id):
    question = Question.query.get_or_404(question_id)
    
    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            flash('답변 내용을 입력해주세요.', 'danger')
        else:
            answer = Answer(
                question_id=question.id,
                content=content,
                create_date=datetime.now(),
                user_id=g.user.id
            )
            db.session.add(answer)
            
            # 작성자(사용자)에게 답변 등록 알림 전송
            noti_msg = f"1:1 문의 '{question.subject}'에 답변이 등록되었습니다."
            noti_link = url_for('auth.question_detail', question_id=question.id)
            noti = Notification(
                user_id=question.user_id,
                message=noti_msg,
                link=noti_link
            )
            db.session.add(noti)
            
            db.session.commit()
            flash('답변이 성공적으로 등록되었습니다.', 'success')
            return redirect(url_for('auth.admin_question_detail', question_id=question.id))
            
    return render_template('auth/admin_question_detail.html', question=question)
