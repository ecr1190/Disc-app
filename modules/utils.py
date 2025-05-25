import secrets
import string
import os
from flask import current_app
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def generate_secure_token(length=16):
    """セキュアなランダムトークンを生成する"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def admin_required(f):
    """管理者のみがアクセスできるようにするデコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('この機能にアクセスする権限がありません。', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def ensure_dir(directory):
    """ディレクトリが存在することを確認し、なければ作成する"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_safe_filename(filename):
    """安全なファイル名を生成する"""
    # ファイル名から安全でない文字を削除
    keepcharacters = (' ', '.', '_', '-')
    return ''.join(c for c in filename if c.isalnum() or c in keepcharacters).strip()

def save_uploaded_file(file, directory):
    """アップロードされたファイルを安全に保存する"""
    if file:
        filename = get_safe_filename(file.filename)
        # 一意のファイル名を生成
        unique_filename = f"{generate_secure_token(8)}_{filename}"
        filepath = os.path.join(directory, unique_filename)
        ensure_dir(directory)
        file.save(filepath)
        return unique_filename
    return None