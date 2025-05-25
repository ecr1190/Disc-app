from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database.models import db, User
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo

auth_bp = Blueprint('auth', __name__)

# フォーム定義
class LoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    remember_me = BooleanField('ログイン状態を保存')
    submit = SubmitField('ログイン')

class RegistrationForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    password = PasswordField('パスワード', validators=[
        DataRequired(), 
        Length(min=8, message='パスワードは少なくとも8文字以上である必要があります'),
    ])
    password2 = PasswordField('パスワード（確認）', validators=[
        DataRequired(), 
        EqualTo('password', message='パスワードが一致しません')
    ])
    submit = SubmitField('登録')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('このユーザー名は既に使用されています。別のユーザー名を選択してください。')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('このメールアドレスは既に登録されています。')

class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('現在のパスワード', validators=[DataRequired()])
    new_password = PasswordField('新しいパスワード', validators=[
        DataRequired(), 
        Length(min=8, message='パスワードは少なくとも8文字以上である必要があります'),
    ])
    new_password2 = PasswordField('新しいパスワード（確認）', validators=[
        DataRequired(), 
        EqualTo('new_password', message='パスワードが一致しません')
    ])
    submit = SubmitField('パスワードを変更')

# ルート定義
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not check_password_hash(user.password_hash, form.password.data):
            flash('ユーザー名またはパスワードが正しくありません', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
        flash('ログインしました', 'success')
        return redirect(next_page)
    
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        flash('アカウントが作成されました。ログインしてください。', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', form=form)

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = PasswordChangeForm()
    if form.validate_on_submit():
        if not check_password_hash(current_user.password_hash, form.current_password.data):
            flash('現在のパスワードが正しくありません', 'danger')
            return redirect(url_for('auth.change_password'))
        
        current_user.password_hash = generate_password_hash(form.new_password.data)
        db.session.commit()
        flash('パスワードが変更されました', 'success')
        return redirect(url_for('profile'))
    
    return render_template('change_password.html', form=form)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    class ProfileForm(FlaskForm):
        username = StringField('ユーザー名', validators=[DataRequired(), Length(min=3, max=20)])
        email = StringField('メールアドレス', validators=[DataRequired(), Email()])
        submit = SubmitField('更新')
        
        def __init__(self, original_username, original_email, *args, **kwargs):
            super(ProfileForm, self).__init__(*args, **kwargs)
            self.original_username = original_username
            self.original_email = original_email
        
        def validate_username(self, username):
            if username.data != self.original_username:
                user = User.query.filter_by(username=username.data).first()
                if user is not None:
                    raise ValidationError('このユーザー名は既に使用されています。')
        
        def validate_email(self, email):
            if email.data != self.original_email:
                user = User.query.filter_by(email=email.data).first()
                if user is not None:
                    raise ValidationError('このメールアドレスは既に登録されています。')
    
    form = ProfileForm(current_user.username, current_user.email)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('プロフィールが更新されました', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    return render_template('edit_profile.html', form=form)