from flask import Blueprint, render_template

from app.form import UserCreateForm

# 블루프린트 생성.
# url_prefix='/auth를 설정하면 모든 주소 앞에 /auth가 자동
bp = Blueprint('auth', __name__, url_prefix='/auth')


# 2. 로그인 페이지 연결 (주소: /auth/login)
@bp.route('/login/')
def login():
    return render_template('auth/login.html')


# 3. 회원가입 페이지 연결 (주소: /auth/signup)
@bp.route('/signup/')
def signup():
    form = UserCreateForm()
    return render_template('auth/signup.html', form=form)


# 4. 마이페이지 연결 (주소: /auth/mypage)
@bp.route('/mypage/')
def mypage():
    return render_template('auth/mypage.html')


