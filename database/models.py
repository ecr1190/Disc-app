from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    
    # リレーションシップ
    test_results = db.relationship('TestResult', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # リレーションシップ
    members = db.relationship('User', backref='team', lazy=True)
    
    def __repr__(self):
        return f'<Team {self.name}>'

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    is_fixed = db.Column(db.Boolean, default=False)  # 固定問題かどうか
    
    # リレーションシップ
    choices = db.relationship('Choice', backref='question', lazy=True)
    
    def __repr__(self):
        return f'<Question {self.id}>'

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    choice_text = db.Column(db.Text, nullable=False)
    disc_type = db.Column(db.String(1), nullable=False)  # D, I, S, C, N のいずれか
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    
    # N値の特殊処理用フィールド
    is_most_applicable = db.Column(db.String(1), nullable=True)  # 「最も当てはまる」で選択された時のDISC値
    is_least_applicable = db.Column(db.String(1), nullable=True)  # 「最も当てはまらない」で選択された時のDISC値
    
    def __repr__(self):
        return f'<Choice {self.disc_type}: {self.choice_text[:20]}...>'

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)
    
    # DISC値の保存（N値も追加）
    graph_1_d = db.Column(db.Integer, nullable=False)  # 最も当てはまる D値
    graph_1_i = db.Column(db.Integer, nullable=False)  # 最も当てはまる I値
    graph_1_s = db.Column(db.Integer, nullable=False)  # 最も当てはまる S値
    graph_1_c = db.Column(db.Integer, nullable=False)  # 最も当てはまる C値
    graph_1_n = db.Column(db.Integer, nullable=False, default=0)  # 最も当てはまる N値
    
    graph_2_d = db.Column(db.Integer, nullable=False)  # 最も当てはまらない D値
    graph_2_i = db.Column(db.Integer, nullable=False)  # 最も当てはまらない I値
    graph_2_s = db.Column(db.Integer, nullable=False)  # 最も当てはまらない S値
    graph_2_c = db.Column(db.Integer, nullable=False)  # 最も当てはまらない C値
    graph_2_n = db.Column(db.Integer, nullable=False, default=0)  # 最も当てはまらない N値
    
    graph_3_d = db.Column(db.Integer, nullable=False)  # 差分 D値
    graph_3_i = db.Column(db.Integer, nullable=False)  # 差分 I値
    graph_3_s = db.Column(db.Integer, nullable=False)  # 差分 S値
    graph_3_c = db.Column(db.Integer, nullable=False)  # 差分 C値
    graph_3_n = db.Column(db.Integer, nullable=False, default=0)  # 差分 N値
    
    # セグメント番号
    segment_1 = db.Column(db.String(10), nullable=False)  # グラフI セグメント
    segment_2 = db.Column(db.String(10), nullable=False)  # グラフII セグメント
    segment_3 = db.Column(db.String(10), nullable=False)  # グラフIII セグメント
    
    # プロファイルパターン
    profile_pattern_1 = db.Column(db.String(50), nullable=False)  # グラフI パターン
    profile_pattern_2 = db.Column(db.String(50), nullable=False)  # グラフII パターン
    profile_pattern_3 = db.Column(db.String(50), nullable=False)  # グラフIII パターン
    
    # ステージIIの結果（JSON形式で保存）
    stage_2_result = db.Column(db.Text, nullable=False)
    
    # ステージIIIの結果（JSON形式で保存）
    stage_3_result = db.Column(db.Text, nullable=False)
    
    # 回答履歴（JSON形式で保存）
    answers = db.Column(db.Text, nullable=False)
    
    def get_stage_2_result(self):
        return json.loads(self.stage_2_result)
    
    def get_stage_3_result(self):
        return json.loads(self.stage_3_result)
    
    def get_answers(self):
        return json.loads(self.answers)
    
    def __repr__(self):
        return f'<TestResult {self.id} for User {self.user_id}>'

class ProfilePattern(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    segment_code = db.Column(db.String(10), unique=True, nullable=False)  # 例: "7631"
    pattern_name = db.Column(db.String(50), nullable=False)  # 例: "創造者"
    
    # ステージIIIの詳細情報
    emotion = db.Column(db.Text, nullable=True)  # 情緒面
    goal = db.Column(db.Text, nullable=True)  # 目標
    judgment_criteria = db.Column(db.Text, nullable=True)  # 他人を判断する基準
    influence_factors = db.Column(db.Text, nullable=True)  # 他人に影響を及ぼす要素
    strengths = db.Column(db.Text, nullable=True)  # 組織内での長所
    excessive_aspects = db.Column(db.Text, nullable=True)  # 過剰になりやすい面
    under_pressure = db.Column(db.Text, nullable=True)  # プレッシャーがかかった時
    fears = db.Column(db.Text, nullable=True)  # 不安や恐れ
    improvement = db.Column(db.Text, nullable=True)  # 効果性を高めるには
    summary = db.Column(db.Text, nullable=True)  # 総合解説文
    
    def __repr__(self):
        return f'<ProfilePattern {self.segment_code}: {self.pattern_name}>'

class Stage2Trait(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    disc_type = db.Column(db.String(1), nullable=False)  # D, I, S, C のいずれか
    intensity = db.Column(db.Integer, nullable=False)  # 強度 (1-28)
    trait = db.Column(db.String(50), nullable=False)  # 特性
    
    def __repr__(self):
        return f'<Stage2Trait {self.disc_type}{self.intensity}: {self.trait}>'

class GraphSegment(db.Model):
    """
    グラフセグメントの対応表を格納するモデル
    graph_type: 1=グラフI, 2=グラフII, 3=グラフIII
    disc_type: D, I, S, C のいずれか
    value: DISC値
    intensity: 強度 (1-28)
    segment: セグメント (1-7)
    """
    id = db.Column(db.Integer, primary_key=True)
    graph_type = db.Column(db.Integer, nullable=False)  # 1, 2, または 3
    disc_type = db.Column(db.String(1), nullable=False)  # D, I, S, C のいずれか
    value = db.Column(db.Integer, nullable=False)  # DISC値
    intensity = db.Column(db.Integer, nullable=False)  # 強度 (1-28)
    segment = db.Column(db.Integer, nullable=False)  # セグメント (1-7)
    
    def __repr__(self):
        return f'<GraphSegment グラフ{self.graph_type}_{self.disc_type}値{self.value}: 強度{self.intensity}, セグメント{self.segment}>'