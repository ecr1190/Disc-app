import os
import secrets

class Config:
    # アプリケーションの基本設定
    SECRET_KEY = secrets.token_hex(16)
    
    # データベース設定
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Sql1190@localhost/disc_app'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # セッション設定
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    
    # セキュリティ設定
    CSRF_ENABLED = True
    WTF_CSRF_ENABLED = True
    
    # アプリケーション固有の設定
    QUESTIONS_PER_TEST = 24  # テストで表示する質問数
    
    # アップロードフォルダ設定
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    
    # メール設定（必要に応じて）
    MAIL_SERVER = 'smtp.example.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'user@example.com'
    MAIL_PASSWORD = 'password'
    MAIL_DEFAULT_SENDER = 'noreply@example.com'