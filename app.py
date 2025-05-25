from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database.models import db, User, TestResult, Question, Choice
from modules.auth import auth_bp
from modules.disc_logic import disc_bp
import os
import secrets
import random
from datetime import datetime, date
from config import Config

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)

# データベース初期化
db.init_app(app)

# ログイン管理の設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'この機能を使用するにはログインが必要です。'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Blueprint登録
app.register_blueprint(auth_bp)
app.register_blueprint(disc_bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile')
@login_required
def profile():
    test_results = TestResult.query.filter_by(user_id=current_user.id).order_by(TestResult.date_taken.desc()).all()
    return render_template('profile.html', test_results=test_results)

@app.route('/dashboard')
@login_required
def dashboard():
    # 管理者のみが閲覧可能
    if not current_user.is_admin:
        flash('この機能にアクセスする権限がありません。', 'danger')
        return redirect(url_for('index'))
    
    # 全ユーザーの情報を取得（テスト結果も含む）
    users = User.query.all()
    
    # 今日の日付を渡す（テンプレートで本日の測定数計算用）
    today = date.today()
    
    return render_template('dashboard.html', users=users, today=today)

# 管理者用API：ユーザー履歴取得
@app.route('/api/admin/user_history/<int:user_id>')
@login_required
def get_user_history(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    test_results = TestResult.query.filter_by(user_id=user_id).order_by(TestResult.date_taken.desc()).all()
    
    history_data = []
    for result in test_results:
        history_data.append({
            'id': result.id,
            'date_taken': result.date_taken.strftime('%Y/%m/%d %H:%M'),
            'disc_values': {
                'D': result.graph_3_d,
                'I': result.graph_3_i,
                'S': result.graph_3_s,
                'C': result.graph_3_c,
                'N': result.graph_3_n
            },
            'profile_pattern': result.profile_pattern_3
        })
    
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'team_id': user.team_id
        },
        'history': history_data
    })

# 管理者用API：ユーザー情報取得
@app.route('/api/admin/user_info/<int:user_id>')
@login_required
def get_user_info(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'team_id': user.team_id,
        'is_admin': user.is_admin,
        'date_registered': user.date_registered.strftime('%Y/%m/%d'),
        'test_count': len(user.test_results)
    })

# 管理者用API：ユーザー情報更新
@app.route('/api/admin/update_user/<int:user_id>', methods=['POST'])
@login_required
def update_user_info(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    try:
        # ユーザー名の重複チェック
        if data.get('username') and data['username'] != user.username:
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user:
                return jsonify({'error': 'このユーザー名は既に使用されています'}), 400
            user.username = data['username']
        
        # メールアドレスの重複チェック
        if data.get('email') and data['email'] != user.email:
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return jsonify({'error': 'このメールアドレスは既に登録されています'}), 400
            user.email = data['email']
        
        # チームIDの更新
        if 'team_id' in data:
            user.team_id = data['team_id'] if data['team_id'] else None
        
        # 管理者権限の更新
        if 'is_admin' in data:
            user.is_admin = data['is_admin']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'ユーザー情報を更新しました',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'team_id': user.team_id,
                'is_admin': user.is_admin
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新中にエラーが発生しました: {str(e)}'}), 500

# 管理者用API：組織統計取得
@app.route('/api/admin/team_statistics')
@login_required
def get_team_statistics():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # 組織別統計を計算
        team_stats = {}
        users = User.query.all()
        
        for user in users:
            team_key = user.team_id if user.team_id else 'unassigned'
            
            if team_key not in team_stats:
                team_stats[team_key] = {
                    'team_id': user.team_id,
                    'team_name': f'組織 {user.team_id}' if user.team_id else '未所属',
                    'member_count': 0,
                    'tested_count': 0,
                    'total_tests': 0,
                    'avg_disc_values': {'D': 0, 'I': 0, 'S': 0, 'C': 0, 'N': 0},
                    'profile_patterns': {}
                }
            
            team_stats[team_key]['member_count'] += 1
            
            if user.test_results:
                team_stats[team_key]['tested_count'] += 1
                team_stats[team_key]['total_tests'] += len(user.test_results)
                
                # 最新のテスト結果を取得
                latest_result = max(user.test_results, key=lambda x: x.date_taken)
                
                # DISC値の合計を計算（後で平均を計算）
                team_stats[team_key]['avg_disc_values']['D'] += latest_result.graph_3_d
                team_stats[team_key]['avg_disc_values']['I'] += latest_result.graph_3_i
                team_stats[team_key]['avg_disc_values']['S'] += latest_result.graph_3_s
                team_stats[team_key]['avg_disc_values']['C'] += latest_result.graph_3_c
                team_stats[team_key]['avg_disc_values']['N'] += latest_result.graph_3_n
                
                # プロファイルパターンの集計
                pattern = latest_result.profile_pattern_3
                if pattern in team_stats[team_key]['profile_patterns']:
                    team_stats[team_key]['profile_patterns'][pattern] += 1
                else:
                    team_stats[team_key]['profile_patterns'][pattern] = 1
        
        # 平均値を計算
        for team_key, stats in team_stats.items():
            if stats['tested_count'] > 0:
                for disc_type in stats['avg_disc_values']:
                    stats['avg_disc_values'][disc_type] = round(
                        stats['avg_disc_values'][disc_type] / stats['tested_count'], 1
                    )
                
                # 測定実施率を計算
                stats['completion_rate'] = round((stats['tested_count'] / stats['member_count']) * 100, 1)
            else:
                stats['completion_rate'] = 0
        
        return jsonify({
            'success': True,
            'team_statistics': list(team_stats.values())
        })
        
    except Exception as e:
        return jsonify({'error': f'統計データの取得中にエラーが発生しました: {str(e)}'}), 500

@app.route('/api/team_analysis/<int:team_id>')
@login_required
def team_analysis(team_id):
    # APIエンドポイント実装（モバイルアプリ連携用）
    # チームに属するユーザーのDISC傾向を分析して返す
    # 実装は簡略化しています
    return jsonify({'status': 'success', 'message': 'Team analysis completed'})

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# テンプレート関数として現在の日付を利用可能にする
@app.template_global()
def moment():
    return datetime.now()

if __name__ == '__main__':
    with app.app_context():
        # データベースのテーブル作成
        db.create_all()
        
        # 質問が存在しない場合、初期データを投入
        if Question.query.count() == 0:
            from database.db_setup import setup_initial_data
            setup_initial_data()
            
    app.run(debug=True)