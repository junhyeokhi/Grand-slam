from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, TelField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

# Assuming UserCreateForm already exists in this file
class UserCreateForm(FlaskForm):
    email = EmailField('이메일', validators=[DataRequired('이메일은 필수 항목입니다.'), Email('유효한 이메일 주소를 입력해주세요.')])
    username = StringField('이름', validators=[DataRequired('이름은 필수 항목입니다.'), Length(min=2, max=50)])
    nickname = StringField('닉네임', validators=[DataRequired('닉네임은 필수 항목입니다.'), Length(min=2, max=50)])
    password1 = PasswordField('비밀번호', validators=[DataRequired('비밀번호는 필수 항목입니다.'), Length(min=8, message='비밀번호는 최소 8자 이상이어야 합니다.')])
    password2 = PasswordField('비밀번호 확인', validators=[DataRequired('비밀번호 확인은 필수 항목입니다.'), EqualTo('password1', '비밀번호가 일치하지 않습니다.')])
    phone = TelField('전화번호', validators=[DataRequired('전화번호는 필수 항목입니다.'), Length(min=10, max=20)])
    address = StringField('주소', validators=[DataRequired('주소는 필수 항목입니다.')])

class UserLoginForm(FlaskForm):
    email = EmailField('이메일', validators=[DataRequired('이메일은 필수 항목입니다.'), Email('유효한 이메일 주소를 입력해주세요.')])
    password = PasswordField('비밀번호', validators=[DataRequired('비밀번호는 필수 항목입니다.')])


class UserEditForm(FlaskForm):
    email = EmailField('이메일', validators=[DataRequired('이메일은 필수 항목입니다.'), Email('유효한 이메일 주소를 입력해주세요.')])
    username = StringField('이름', validators=[DataRequired('이름은 필수 항목입니다.'), Length(min=2, max=50)])
    nickname = StringField('닉네임', validators=[DataRequired('닉네임은 필수 항목입니다.'), Length(min=2, max=50)])
    password = PasswordField('새 비밀번호', validators=[Optional(), Length(min=8, message='비밀번호는 최소 8자 이상이어야 합니다.')])
    password2 = PasswordField('새 비밀번호 확인', validators=[EqualTo('password', '비밀번호가 일치하지 않습니다.')])
    phone = TelField('전화번호', validators=[DataRequired('전화번호는 필수 항목입니다.'), Length(min=10, max=20)])
    address = StringField('주소', validators=[DataRequired('주소는 필수 항목입니다.')])

class FindIdForm(FlaskForm):
    username = StringField('이름', validators=[DataRequired('이름을 입력해주세요.')])
    phone = StringField('전화번호', validators=[DataRequired('전화번호를 입력해주세요.')])

class ResetPasswordForm(FlaskForm):
    email = EmailField('아이디 (이메일)', validators=[DataRequired('이메일을 입력해주세요.'), Email('유효한 이메일 주소를 입력해주세요.')])
    username = StringField('이름', validators=[DataRequired('이름을 입력해주세요.')])
    phone = StringField('전화번호', validators=[DataRequired('전화번호를 입력해주세요.')])
    new_password = PasswordField('새로운 비밀번호', validators=[
        DataRequired('새로운 비밀번호를 입력해주세요.'),
        Length(min=8, message='비밀번호는 최소 8자 이상이어야 합니다.')
    ])
    new_password_confirm = PasswordField('새로운 비밀번호 확인', validators=[
        DataRequired('비밀번호 확인을 입력해주세요.'),
        EqualTo('new_password', message='새 비밀번호와 일치하지 않습니다.')
    ])

class AdditionalInfoForm(FlaskForm):
    phone = TelField('전화번호', validators=[DataRequired('전화번호는 필수 항목입니다.'), Length(min=10, max=20)])
    address = StringField('주소', validators=[DataRequired('주소는 필수 항목입니다.')])