// DISC測定アプリケーション - メイン JavaScript

// ドキュメント読み込み完了時に実行
document.addEventListener('DOMContentLoaded', function() {
    
    // フェードインアニメーション
    const fadeElements = document.querySelectorAll('.card');
    fadeElements.forEach(function(element, index) {
        setTimeout(function() {
            element.classList.add('fadeIn');
        }, index * 100);
    });
    
    // フラッシュメッセージの自動非表示
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // フォームバリデーション強化
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // パスワード強度チェッカー
    const passwordField = document.getElementById('password');
    const strengthMeter = document.getElementById('password-strength-meter');
    
    if (passwordField && strengthMeter) {
        passwordField.addEventListener('input', function() {
            const password = this.value;
            const strength = checkPasswordStrength(password);
            
            // 強度メーターの更新
            strengthMeter.value = strength.score;
            
            // 強度メッセージの更新
            const strengthText = document.getElementById('password-strength-text');
            if (strengthText) {
                strengthText.textContent = strength.message;
                strengthText.className = ''; // クラスをリセット
                strengthText.classList.add(strength.class);
            }
        });
    }
    
    // DISC測定テストページの機能
    setupDISCTest();
    
    // 結果ページのタブ切り替え保存
    const resultTabs = document.getElementById('resultTabs');
    if (resultTabs) {
        const triggerTabList = resultTabs.querySelectorAll('button');
        triggerTabList.forEach(function(triggerEl) {
            triggerEl.addEventListener('click', function() {
                // 選択したタブをローカルストレージに保存
                localStorage.setItem('lastResultTab', triggerEl.getAttribute('id'));
            });
        });
        
        // 前回選択したタブを復元
        const lastTab = localStorage.getItem('lastResultTab');
        if (lastTab) {
            const tabToShow = document.getElementById(lastTab);
            if (tabToShow) {
                const tab = new bootstrap.Tab(tabToShow);
                tab.show();
            }
        }
    }
});

// パスワード強度チェック関数
function checkPasswordStrength(password) {
    let score = 0;
    const feedback = {
        score: 0,
        message: '非常に弱い',
        class: 'text-danger'
    };
    
    if (!password) {
        return feedback;
    }
    
    // 長さチェック
    if (password.length >= 8) {
        score += 1;
    }
    if (password.length >= 12) {
        score += 1;
    }
    
    // 複雑さチェック
    if (/[A-Z]/.test(password)) { // 大文字
        score += 1;
    }
    if (/[a-z]/.test(password)) { // 小文字
        score += 1;
    }
    if (/[0-9]/.test(password)) { // 数字
        score += 1;
    }
    if (/[^A-Za-z0-9]/.test(password)) { // 特殊文字
        score += 1;
    }
    
    // スコアに基づくフィードバック
    feedback.score = Math.min(5, score);
    
    if (score <= 1) {
        feedback.message = '非常に弱い';
        feedback.class = 'text-danger';
    } else if (score <= 2) {
        feedback.message = '弱い';
        feedback.class = 'text-warning';
    } else if (score <= 3) {
        feedback.message = '普通';
        feedback.class = 'text-info';
    } else if (score <= 4) {
        feedback.message = '強い';
        feedback.class = 'text-primary';
    } else {
        feedback.message = '非常に強い';
        feedback.class = 'text-success';
    }
    
    return feedback;
}

// DISC測定テスト関連の機能セットアップ
function setupDISCTest() {
    const testForm = document.getElementById('discTestForm');
    if (!testForm) return;
    
    // フォーム送信前のバリデーション
    testForm.addEventListener('submit', function(event) {
        // 全ての質問が回答されているか確認
        const questions = document.querySelectorAll('.question-card');
        let allAnswered = true;
        
        questions.forEach(function(question) {
            const mostChoice = question.querySelector('.most-choice:checked');
            const leastChoice = question.querySelector('.least-choice:checked');
            
            if (!mostChoice || !leastChoice) {
                allAnswered = false;
            }
        });
        
        if (!allAnswered) {
            event.preventDefault();
            alert('すべての質問に回答してください。各質問で「最も当てはまる」と「最も当てはまらない」の両方を選択する必要があります。');
        }
    });
    
    // 選択肢のラジオボタンUIの強化
    document.querySelectorAll('.choice-item').forEach(function(item) {
        item.addEventListener('click', function(e) {
            // ラベル内のラジオボタンをクリック
            const radio = this.querySelector('input[type="radio"]');
            if (radio && e.target !== radio) {
                radio.checked = true;
                
                // 選択変更イベントを発火
                const event = new Event('change');
                radio.dispatchEvent(event);
            }
        });
    });
    
    // 進捗バーの更新
    function updateProgress() {
        const totalQuestions = document.querySelectorAll('.question-card').length;
        const answeredCount = document.querySelectorAll('.question-card').length;
        let completedCount = 0;
        
        document.querySelectorAll('.question-card').forEach(function(question) {
            const mostChoice = question.querySelector('.most-choice:checked');
            const leastChoice = question.querySelector('.least-choice:checked');
            
            if (mostChoice && leastChoice) {
                completedCount++;
            }
        });
        
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            const progress = Math.round((completedCount / totalQuestions) * 100);
            progressBar.style.width = progress + '%';
            progressBar.setAttribute('aria-valuenow', progress);
            progressBar.textContent = progress + '%';
        }
    }
    
    // ラジオボタン変更時に進捗更新
    document.querySelectorAll('.most-choice, .least-choice').forEach(function(radio) {
        radio.addEventListener('change', updateProgress);
    });
    
    // 初期進捗更新
    updateProgress();
}