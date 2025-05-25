// dashboard.js - 管理者ダッシュボード用JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // フィルタリング機能
    const teamFilter = document.getElementById('teamFilter');
    const resultFilter = document.getElementById('resultFilter');
    const membersTableBody = document.getElementById('membersTableBody');
    const refreshButton = document.getElementById('refreshData');
    
    // モーダル
    const userHistoryModal = new bootstrap.Modal(document.getElementById('userHistoryModal'));
    const editUserModal = new bootstrap.Modal(document.getElementById('editUserModal'));
    
    // フィルタリング関数
    function filterTable() {
        const teamValue = teamFilter.value;
        const resultValue = resultFilter.value;
        const rows = membersTableBody.querySelectorAll('tr');
        
        rows.forEach(row => {
            const teamId = row.getAttribute('data-team-id');
            const testCount = parseInt(row.getAttribute('data-test-count'));
            
            let showRow = true;
            
            // 組織フィルタ
            if (teamValue && teamId !== teamValue) {
                showRow = false;
            }
            
            // 結果フィルタ
            if (resultValue === 'tested' && testCount === 0) {
                showRow = false;
            } else if (resultValue === 'untested' && testCount > 0) {
                showRow = false;
            }
            
            row.style.display = showRow ? '' : 'none';
        });
        
        updateTeamStats();
    }
    
    // イベントリスナー
    teamFilter.addEventListener('change', filterTable);
    resultFilter.addEventListener('change', filterTable);
    refreshButton.addEventListener('click', () => location.reload());
    
    // ユーザー履歴表示
    document.querySelectorAll('.view-history-btn').forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            loadUserHistory(userId);
        });
    });
    
    // ユーザー編集
    document.querySelectorAll('.edit-user-btn').forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            loadUserEditForm(userId);
        });
    });
    
    // ユーザー編集保存
    document.getElementById('saveUserChanges').addEventListener('click', function() {
        saveUserChanges();
    });
    
    // ユーザー履歴読み込み
    function loadUserHistory(userId) {
        const historyContent = document.getElementById('userHistoryContent');
        const modalLabel = document.getElementById('userHistoryModalLabel');
        
        historyContent.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">読み込み中...</span></div></div>';
        
        fetch(`/api/admin/user_history/${userId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                modalLabel.textContent = `${data.user.username} の測定履歴`;
                
                if (data.history.length === 0) {
                    historyContent.innerHTML = '<p class="text-muted text-center">測定履歴がありません。</p>';
                    userHistoryModal.show();
                    return;
                }
                
                let historyHtml = `
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>測定日時</th>
                                    <th>DISC値</th>
                                    <th>プロファイル</th>
                                    <th>アクション</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                data.history.forEach(record => {
                    const discValues = record.disc_values;
                    let discHtml = '';
                    
                    // DISC値の表示
                    if (discValues.D !== 0) discHtml += `<span class="disc-value d-value" title="D型">${discValues.D}</span>`;
                    if (discValues.I !== 0) discHtml += `<span class="disc-value i-value" title="I型">${discValues.I}</span>`;
                    if (discValues.S !== 0) discHtml += `<span class="disc-value s-value" title="S型">${discValues.S}</span>`;
                    if (discValues.C !== 0) discHtml += `<span class="disc-value c-value" title="C型">${discValues.C}</span>`;
                    if (discValues.N > 0) discHtml += `<span class="disc-value n-value" title="N型">${discValues.N}</span>`;
                    
                    historyHtml += `
                        <tr>
                            <td>${record.date_taken}</td>
                            <td><div class="disc-values">${discHtml}</div></td>
                            <td><span class="badge bg-primary">${record.profile_pattern}</span></td>
                            <td>
                                <a href="/disc/results/${record.id}" class="btn btn-sm btn-info" target="_blank">
                                    <i class="fas fa-external-link-alt"></i> 詳細
                                </a>
                            </td>
                        </tr>
                    `;
                });
                
                historyHtml += `
                            </tbody>
                        </table>
                    </div>
                `;
                
                historyContent.innerHTML = historyHtml;
                userHistoryModal.show();
            })
            .catch(error => {
                console.error('履歴読み込みエラー:', error);
                historyContent.innerHTML = `<div class="alert alert-danger">履歴の読み込み中にエラーが発生しました: ${error.message}</div>`;
                userHistoryModal.show();
            });
    }
    
    // ユーザー編集フォーム読み込み
    function loadUserEditForm(userId) {
        const form = document.getElementById('editUserForm');
        const modalLabel = document.getElementById('editUserModalLabel');
        
        // フォームをリセット
        form.reset();
        document.getElementById('userId').value = userId;
        
        fetch(`/api/admin/user_info/${userId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                modalLabel.textContent = `${data.username} の編集`;
                document.getElementById('editUsername').value = data.username;
                document.getElementById('editEmail').value = data.email;
                document.getElementById('editTeamId').value = data.team_id || '';
                document.getElementById('editIsAdmin').checked = data.is_admin;
                
                editUserModal.show();
            })
            .catch(error => {
                console.error('ユーザー情報読み込みエラー:', error);
                alert(`ユーザー情報の読み込み中にエラーが発生しました: ${error.message}`);
            });
    }
    
    // ユーザー編集保存
    function saveUserChanges() {
        const form = document.getElementById('editUserForm');
        const formData = new FormData(form);
        const userId = formData.get('userId');
        
        const data = {
            username: formData.get('username'),
            email: formData.get('email'),
            team_id: formData.get('teamId') ? parseInt(formData.get('teamId')) : null,
            is_admin: formData.has('isAdmin')
        };
        
        fetch(`/api/admin/update_user/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            alert('ユーザー情報を更新しました。');
            editUserModal.hide();
            location.reload(); // ページを再読み込みして変更を反映
        })
        .catch(error => {
            console.error('ユーザー更新エラー:', error);
            alert(`更新中にエラーが発生しました: ${error.message}`);
        });
    }
    
    // 組織別統計更新
    function updateTeamStats() {
        const teamStatsContainer = document.getElementById('teamStatsContainer');
        const visibleRows = Array.from(membersTableBody.querySelectorAll('tr')).filter(row => row.style.display !== 'none');
        
        // 組織別にグループ化
        const teamStats = {};
        visibleRows.forEach(row => {
            const teamId = row.getAttribute('data-team-id');
            const testCount = parseInt(row.getAttribute('data-test-count'));
            
            if (!teamStats[teamId]) {
                teamStats[teamId] = {
                    memberCount: 0,
                    testedCount: 0,
                    totalTests: 0
                };
            }
            
            teamStats[teamId].memberCount++;
            if (testCount > 0) {
                teamStats[teamId].testedCount++;
                teamStats[teamId].totalTests += testCount;
            }
        });
        
        // 統計表示
        let statsHtml = '';
        Object.keys(teamStats).forEach(teamId => {
            const stats = teamStats[teamId];
            const teamName = teamId === 'none' ? '未所属' : `組織 ${teamId}`;
            const testRate = stats.memberCount > 0 ? Math.round((stats.testedCount / stats.memberCount) * 100) : 0;
            
            statsHtml += `
                <div class="team-stats-card">
                    <div class="team-stats-header">
                        <h6 class="mb-0">${teamName}</h6>
                        <span class="badge bg-info">${stats.memberCount}名</span>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <small class="text-muted">測定実施率</small>
                            <div class="progress mb-2">
                                <div class="progress-bar bg-success" style="width: ${testRate}%">${testRate}%</div>
                            </div>
                            <small class="text-muted">${stats.testedCount}/${stats.memberCount}名が測定済み</small>
                        </div>
                        <div class="col-md-6">
                            <small class="text-muted">総測定回数</small>
                            <h5 class="mb-0">${stats.totalTests}</h5>
                            <small class="text-muted">平均 ${stats.memberCount > 0 ? (stats.totalTests / stats.memberCount).toFixed(1) : 0} 回/人</small>
                        </div>
                    </div>
                </div>
            `;
        });
        
        teamStatsContainer.innerHTML = statsHtml || '<p class="text-muted">表示するデータがありません。</p>';
    }
    
    // 高度な統計読み込み
    function loadAdvancedTeamStats() {
        const teamStatsContainer = document.getElementById('teamStatsContainer');
        
        fetch('/api/admin/team_statistics')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                if (data.team_statistics.length === 0) {
                    teamStatsContainer.innerHTML = '<p class="text-muted">組織データがありません。</p>';
                    return;
                }
                
                let statsHtml = '';
                data.team_statistics.forEach(team => {
                    const avgDisc = team.avg_disc_values;
                    const patterns = Object.entries(team.profile_patterns)
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 3); // 上位3つのパターンを表示
                    
                    statsHtml += `
                        <div class="team-stats-card">
                            <div class="team-stats-header">
                                <h6 class="mb-0">${team.team_name}</h6>
                                <span class="badge bg-info">${team.member_count}名</span>
                            </div>
                            <div class="row">
                                <div class="col-md-4">
                                    <small class="text-muted">測定実施率</small>
                                    <div class="progress mb-2">
                                        <div class="progress-bar bg-success" style="width: ${team.completion_rate}%">${team.completion_rate}%</div>
                                    </div>
                                    <small class="text-muted">${team.tested_count}/${team.member_count}名</small>
                                </div>
                                <div class="col-md-4">
                                    <small class="text-muted">平均DISC値</small>
                                    <div class="disc-values mt-1">
                                        <span class="disc-value d-value" title="D型平均">${avgDisc.D}</span>
                                        <span class="disc-value i-value" title="I型平均">${avgDisc.I}</span>
                                        <span class="disc-value s-value" title="S型平均">${avgDisc.S}</span>
                                        <span class="disc-value c-value" title="C型平均">${avgDisc.C}</span>
                                        ${avgDisc.N > 0 ? `<span class="disc-value n-value" title="N型平均">${avgDisc.N}</span>` : ''}
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <small class="text-muted">主要プロファイル</small>
                                    <div class="mt-1">
                                        ${patterns.map(([pattern, count]) => 
                                            `<span class="badge bg-primary me-1" style="font-size: 0.7em">${pattern} (${count})</span>`
                                        ).join('')}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                teamStatsContainer.innerHTML = statsHtml;
            })
            .catch(error => {
                console.error('統計読み込みエラー:', error);
                teamStatsContainer.innerHTML = `<div class="alert alert-warning">統計データの読み込み中にエラーが発生しました: ${error.message}</div>`;
            });
    }
    
    // 初期表示
    filterTable();
    
    // 高度な統計を5秒後に読み込み（初期表示を早くするため）
    setTimeout(loadAdvancedTeamStats, 2000);
});