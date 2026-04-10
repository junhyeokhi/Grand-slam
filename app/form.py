from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField
from wtforms.validators import DataRequired, Length, EqualTo, Email


class UserCreateForm(FlaskForm):
    email = EmailField('이메일', validators=[
        DataRequired('이메일은 필수 항목입니다.'),
        Email()
    ])
    username = StringField('이름', validators=[DataRequired('이름은 필수 항목입니다.'), Length(min=2, max=50)])
    nickname = StringField('닉네임', validators=[
        DataRequired('닉네임은 필수 항목입니다.'),
        Length(min=2, max=50)
    ])
    password1 = PasswordField('비밀번호', validators=[
        DataRequired('비밀번호는 필수 항목입니다.'),
        EqualTo('password2', message='비밀번호가 일치하지 않습니다.')
    ])
    password2 = PasswordField('비밀번호 확인', validators=[
        DataRequired('비밀번호 확인은 필수 항목입니다.')
    ])
    phone = StringField('전화번호', validators=[
        DataRequired('전화번호는 필수 항목입니다.')
    ])
    # 주소는 카카오 API로 입력받으므로 StringField로
    address = StringField('주소', validators=[
        DataRequired('주소는 필수 항목입니다.')
    ])


class UserLoginForm(FlaskForm):
    email = StringField('이메일', validators=[DataRequired('이메일은 필수 항목입니다.'), Email()])
    password = PasswordField('비밀번호', validators=[DataRequired('비밀번호는 필수 항목입니다.')])
