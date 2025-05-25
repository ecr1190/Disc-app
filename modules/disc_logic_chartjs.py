from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import login_required, current_user
from database.models import db, Question, Choice, TestResult, ProfilePattern, Stage2Trait
import random
import json
from datetime import datetime

disc_bp = Blueprint('disc', __name__)

@disc_bp.route('/test')
@login_required
def test():
    # 質問をランダムに24問選択
    questions = Question.query.all()
    selected_questions = random.sample(questions, min(24, len(questions)))
    
    # セッションに質問IDを保存
    session['question_ids'] = [q.id for q in selected_questions]
    
    # 各質問の選択肢をランダムに並び替える
    for question in selected_questions:
        question.shuffled_choices = list(question.choices)
        random.shuffle(question.shuffled_choices)
    
    return render_template('test.html', questions=selected_questions)

@disc_bp.route('/submit_test', methods=['POST'])
@login_required
def submit_test():
    question_ids = session.get('question_ids', [])
    if not question_ids:
        flash('テストセッションが無効です。もう一度お試しください。', 'danger')
        return redirect(url_for('disc.test'))
    
    # 回答データの収集
    most_choices = {}
    least_choices = {}
    
    for q_id in question_ids:
        most_key = f'most_{q_id}'
        least_key = f'least_{q_id}'
        
        if most_key in request.form and least_key in request.form:
            most_choices[q_id] = int(request.form[most_key])
            least_choices[q_id] = int(request.form[least_key])
    
    # 各DISCタイプのカウント
    most_counts = {'D': 0, 'I': 0, 'S': 0, 'C': 0}
    least_counts = {'D': 0, 'I': 0, 'S': 0, 'C': 0}
    
    for q_id, choice_id in most_choices.items():
        choice = Choice.query.get(choice_id)
        if choice:
            most_counts[choice.disc_type] += 1
    
    for q_id, choice_id in least_choices.items():
        choice = Choice.query.get(choice_id)
        if choice:
            least_counts[choice.disc_type] += 1
    
    # 差分の計算
    diff_counts = {
        'D': most_counts['D'] - least_counts['D'],
        'I': most_counts['I'] - least_counts['I'],
        'S': most_counts['S'] - least_counts['S'],
        'C': most_counts['C'] - least_counts['C']
    }
    
    # セグメント番号の計算
    segment_1 = calculate_segments(most_counts)
    segment_2 = calculate_segments(least_counts)
    segment_3 = calculate_segments(diff_counts)
    
    # プロファイルパターンの取得
    profile_pattern_1 = get_profile_pattern(segment_1)
    profile_pattern_2 = get_profile_pattern(segment_2)
    profile_pattern_3 = get_profile_pattern(segment_3)
    
    # ステージIIの結果計算
    stage_2_result = calculate_stage_2_result(diff_counts)
    
    # ステージIIIの結果取得
    stage_3_result = get_stage_3_result(segment_3)
    
    # 回答履歴の作成
    answers = {
        'most': {str(q_id): choice_id for q_id, choice_id in most_choices.items()},
        'least': {str(q_id): choice_id for q_id, choice_id in least_choices.items()}
    }
    
    # 結果の保存
    test_result = TestResult(
        user_id=current_user.id,
        graph_1_d=most_counts['D'],
        graph_1_i=most_counts['I'],
        graph_1_s=most_counts['S'],
        graph_1_c=most_counts['C'],
        graph_2_d=least_counts['D'],
        graph_2_i=least_counts['I'],
        graph_2_s=least_counts['S'],
        graph_2_c=least_counts['C'],
        graph_3_d=diff_counts['D'],
        graph_3_i=diff_counts['I'],
        graph_3_s=diff_counts['S'],
        graph_3_c=diff_counts['C'],
        segment_1=''.join(map(str, segment_1)),
        segment_2=''.join(map(str, segment_2)),
        segment_3=''.join(map(str, segment_3)),
        profile_pattern_1=profile_pattern_1,
        profile_pattern_2=profile_pattern_2,
        profile_pattern_3=profile_pattern_3,
        stage_2_result=json.dumps(stage_2_result, ensure_ascii=False),
        stage_3_result=json.dumps(stage_3_result, ensure_ascii=False),
        answers=json.dumps(answers, ensure_ascii=False)
    )
    
    db.session.add(test_result)
    db.session.commit()
    
    return redirect(url_for('disc.results', result_id=test_result.id))

@disc_bp.route('/results/<int:result_id>')
@login_required
def results(result_id):
    test_result = TestResult.query.get_or_404(result_id)
    
    # 結果が現在のユーザーのものであることを確認
    if test_result.user_id != current_user.id and not current_user.is_admin:
        flash('このページにアクセスする権限がありません。', 'danger')
        return redirect(url_for('index'))
    
    # グラフデータの準備 (Chart.js用)
    graph_1_data = {
        'labels': ['D', 'I', 'S', 'C'],
        'values': [test_result.graph_1_d, test_result.graph_1_i, test_result.graph_1_s, test_result.graph_1_c],
        'title': 'グラフI: 最も当てはまる'
    }
    
    graph_2_data = {
        'labels': ['D', 'I', 'S', 'C'],
        'values': [test_result.graph_2_d, test_result.graph_2_i, test_result.graph_2_s, test_result.graph_2_c],
        'title': 'グラフII: 最も当てはまらない'
    }
    
    graph_3_data = {
        'labels': ['D', 'I', 'S', 'C'],
        'values': [test_result.graph_3_d, test_result.graph_3_i, test_result.graph_3_s, test_result.graph_3_c],
        'title': 'グラフIII: 差分'
    }
    
    stage_2_result = json.loads(test_result.stage_2_result)
    stage_3_result = json.loads(test_result.stage_3_result)
    
    return render_template('results.html', 
                          test_result=test_result,
                          graph_1_data=graph_1_data,
                          graph_2_data=graph_2_data,
                          graph_3_data=graph_3_data,
                          stage_2_result=stage_2_result,
                          stage_3_result=stage_3_result)

def calculate_segments(counts):
    # 実際のセグメント計算ロジックはdb.xlsxを参照して実装する必要があります
    # ここでは簡易的な実装例を示します
    
    # D, I, S, Cの値からセグメント番号を取得
    d_segment = calculate_segment_for_type('D', counts['D'])
    i_segment = calculate_segment_for_type('I', counts['I'])
    s_segment = calculate_segment_for_type('S', counts['S'])
    c_segment = calculate_segment_for_type('C', counts['C'])
    
    return [d_segment, i_segment, s_segment, c_segment]

def calculate_segment_for_type(disc_type, value):
    # 値に応じたセグメントを返す簡易的な実装
    # 実際にはdb.xlsxの対応表を使用する必要があります
    if disc_type == 'D':
        if value >= 8: return 7
        elif value >= 6: return 6
        elif value >= 4: return 5
        elif value >= 2: return 4
        elif value >= 0: return 3
        elif value >= -2: return 2
        else: return 1
    elif disc_type == 'I':
        if value >= 8: return 7
        elif value >= 6: return 6
        elif value >= 4: return 5
        elif value >= 2: return 4
        elif value >= 0: return 3
        elif value >= -2: return 2
        else: return 1
    elif disc_type == 'S':
        if value >= 8: return 7
        elif value >= 6: return 6
        elif value >= 4: return 5
        elif value >= 2: return 4
        elif value >= 0: return 3
        elif value >= -2: return 2
        else: return 1
    elif disc_type == 'C':
        if value >= 8: return 7
        elif value >= 6: return 6
        elif value >= 4: return 5
        elif value >= 2: return 4
        elif value >= 0: return 3
        elif value >= -2: return 2
        else: return 1
    else:
        return 1  # デフォルト値

def get_profile_pattern(segments):
    # セグメント番号からプロファイルパターンを取得
    segment_code = ''.join(map(str, segments))
    pattern = ProfilePattern.query.filter_by(segment_code=segment_code).first()
    
    if pattern:
        return pattern.pattern_name
    else:
        # 完全一致がない場合、最も近いパターンを探す（簡易実装）
        return "未分類パターン"

def calculate_stage_2_result(diff_counts):
    """ステージIIの結果を計算する関数"""
    result = {}
    
    for disc_type, value in diff_counts.items():
        # 強度を算出（db.xlsxを参照して実装）
        intensity = calculate_intensity(disc_type, value)
        
        # 対応する特性を取得し、前後3つずつを含めた計7つの特性を取得
        traits = get_traits_around_intensity(disc_type, intensity, 3)
        
        result[disc_type] = {
            'intensity': intensity,
            'traits': traits
        }
    
    return result

def calculate_intensity(disc_type, value):
    """DISCの値から強度を計算する関数"""
    # 実際にはdb.xlsxの変換表を使用する必要があります
    # ここでは簡易的な計算を行います
    
    # 差分値から強度（1-28）への変換ロジック
    if disc_type == 'D':
        if value >= 10: return 28
        elif value >= 8: return 25
        elif value >= 6: return 22
        elif value >= 4: return 19
        elif value >= 2: return 16
        elif value >= 0: return 13
        elif value >= -2: return 10
        elif value >= -4: return 7
        elif value >= -6: return 4
        else: return 1
    elif disc_type == 'I':
        if value >= 10: return 28
        elif value >= 8: return 25
        elif value >= 6: return 22
        elif value >= 4: return 19
        elif value >= 2: return 16
        elif value >= 0: return 13
        elif value >= -2: return 10
        elif value >= -4: return 7
        elif value >= -6: return 4
        else: return 1
    elif disc_type == 'S':
        if value >= 10: return 28
        elif value >= 8: return 25
        elif value >= 6: return 22
        elif value >= 4: return 19
        elif value >= 2: return 16
        elif value >= 0: return 13
        elif value >= -2: return 10
        elif value >= -4: return 7
        elif value >= -6: return 4
        else: return 1
    elif disc_type == 'C':
        if value >= 10: return 28
        elif value >= 8: return 25
        elif value >= 6: return 22
        elif value >= 4: return 19
        elif value >= 2: return 16
        elif value >= 0: return 13
        elif value >= -2: return 10
        elif value >= -4: return 7
        elif value >= -6: return 4
        else: return 1
    else:
        return 14  # デフォルト値（中央値）

def get_traits_around_intensity(disc_type, intensity, num_around):
    """指定された強度の前後n個の特性を取得する関数"""
    traits = []
    
    # 指定された強度の特性を取得
    center_trait = Stage2Trait.query.filter_by(disc_type=disc_type, intensity=intensity).first()
    if center_trait:
        traits.append(center_trait.trait)
    
    # 前のn個の特性を取得
    for i in range(1, num_around + 1):
        prev_intensity = intensity - i
        if prev_intensity >= 1:
            trait = Stage2Trait.query.filter_by(disc_type=disc_type, intensity=prev_intensity).first()
            if trait:
                traits.insert(0, trait.trait)
    
    # 後のn個の特性を取得
    for i in range(1, num_around + 1):
        next_intensity = intensity + i
        if next_intensity <= 28:
            trait = Stage2Trait.query.filter_by(disc_type=disc_type, intensity=next_intensity).first()
            if trait:
                traits.append(trait.trait)
    
    return traits

def get_stage_3_result(segments):
    """ステージIIIの結果を取得する関数"""
    segment_code = ''.join(map(str, segments))
    pattern = ProfilePattern.query.filter_by(segment_code=segment_code).first()
    
    if pattern:
        return {
            'pattern_name': pattern.pattern_name,
            'emotion': pattern.emotion,
            'goal': pattern.goal,
            'judgment_criteria': pattern.judgment_criteria,
            'influence_factors': pattern.influence_factors,
            'strengths': pattern.strengths,
            'excessive_aspects': pattern.excessive_aspects,
            'under_pressure': pattern.under_pressure,
            'fears': pattern.fears,
            'improvement': pattern.improvement,
            'summary': pattern.summary
        }
    else:
        # パターンが見つからない場合のデフォルト値
        return {
            'pattern_name': '未分類パターン',
            'emotion': '情報がありません',
            'goal': '情報がありません',
            'judgment_criteria': '情報がありません',
            'influence_factors': '情報がありません',
            'strengths': '情報がありません',
            'excessive_aspects': '情報がありません',
            'under_pressure': '情報がありません',
            'fears': '情報がありません',
            'improvement': '情報がありません',
            'summary': 'このプロファイルパターンについての詳細情報はまだ登録されていません。'
        }

@disc_bp.route('/history')
@login_required
def history():
    """ユーザーの過去の診断結果一覧を表示"""
    test_results = TestResult.query.filter_by(user_id=current_user.id).order_by(TestResult.date_taken.desc()).all()
    return render_template('history.html', test_results=test_results)

@disc_bp.route('/team_analysis')
@login_required
def team_analysis():
    """チーム分析ページ（管理者のみ）"""
    if not current_user.is_admin:
        flash('この機能にアクセスする権限がありません。', 'danger')
        return redirect(url_for('index'))
    
    teams = db.session.query(db.func.distinct(User.team_id)).filter(User.team_id.isnot(None)).all()
    team_ids = [t[0] for t in teams]
    
    return render_template('team_analysis.html', team_ids=team_ids)

@disc_bp.route('/api/team_data/<int:team_id>')
@login_required
def team_data(team_id):
    """チームのDISC傾向データを提供するAPI"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # チームメンバーの最新のテスト結果を取得
    subquery = db.session.query(
        TestResult.user_id,
        db.func.max(TestResult.date_taken).label('latest_date')
    ).group_by(TestResult.user_id).subquery()
    
    team_results = db.session.query(TestResult).join(
        subquery, 
        db.and_(
            TestResult.user_id == subquery.c.user_id,
            TestResult.date_taken == subquery.c.latest_date
        )
    ).join(
        User, 
        TestResult.user_id == User.id
    ).filter(
        User.team_id == team_id
    ).all()
    
    # チームの平均DISC値を計算
    avg_d = sum(r.graph_3_d for r in team_results) / len(team_results) if team_results else 0
    avg_i = sum(r.graph_3_i for r in team_results) / len(team_results) if team_results else 0
    avg_s = sum(r.graph_3_s for r in team_results) / len(team_results) if team_results else 0
    avg_c = sum(r.graph_3_c for r in team_results) / len(team_results) if team_results else 0
    
    # 各メンバーのデータを準備
    member_data = [{
        'username': User.query.get(r.user_id).username,
        'values': {
            'D': r.graph_3_d,
            'I': r.graph_3_i,
            'S': r.graph_3_s,
            'C': r.graph_3_c
        },
        'pattern': r.profile_pattern_3
    } for r in team_results]
    
    return jsonify({
        'team_avg': {
            'D': avg_d,
            'I': avg_i,
            'S': avg_s,
            'C': avg_c
        },
        'members': member_data
    })