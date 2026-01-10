// API Base URL
const API_BASE_URL = 'http://localhost:8000';

// Show alert
function showAlert(message, type = 'success') {
    const alertContainer = document.getElementById('alert-container');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} show`;
    alert.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i> ${message}`;
    alertContainer.innerHTML = '';
    alertContainer.appendChild(alert);

    setTimeout(() => {
        alert.classList.remove('show');
    }, 5000);
}

// Navigation between main sections
document.addEventListener('DOMContentLoaded', function() {
    // Section navigation
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();

            // Remove active from all nav items
            navItems.forEach(nav => nav.classList.remove('active'));

            // Add active to clicked item
            this.classList.add('active');

            // Hide all sections
            document.querySelectorAll('.section').forEach(section => {
                section.classList.remove('active');
            });

            // Show selected section
            const sectionId = this.getAttribute('data-section') + '-section';
            const section = document.getElementById(sectionId);
            if (section) {
                section.classList.add('active');

                // Update page title
                const pageTitle = this.querySelector('span').textContent;
                document.getElementById('page-title').textContent = pageTitle;

                // Load data for specific sections
                if (sectionId === 'agents-section') {
                    loadAgents();
                } else if (sectionId === 'tasks-section') {
                    loadTasks();
                } else if (sectionId === 'sessions-section') {
                    loadSessions();
                } else if (sectionId === 'dashboard-section') {
                    loadDashboard();
                }
            }
        });
    });

    // Initialize with dashboard data
    loadDashboard();
    checkAPIStatus();
    setInterval(checkAPIStatus, 30000);
});

// Check API status
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        const statusEl = document.getElementById('api-status');
        if (data.status === 'healthy') {
            statusEl.className = 'status-badge healthy';
            statusEl.innerHTML = '<i class="fas fa-circle"></i> Healthy';
        } else {
            statusEl.className = 'status-badge degraded';
            statusEl.innerHTML = '<i class="fas fa-circle"></i> Degraded';
        }
    } catch (error) {
        const statusEl = document.getElementById('api-status');
        statusEl.className = 'status-badge degraded';
        statusEl.innerHTML = '<i class="fas fa-circle"></i> Offline';
    }
}

// Show/hide risk scoring tabs
function showRiskTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });

    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabName).classList.add('active');

    // Add active class to clicked tab button
    event.target.classList.add('active');

    // Load data if needed
    if (tabName === 'applications') {
        loadApplications();
    }
}

// ===== DASHBOARD SECTION =====
async function loadDashboard() {
    try {
        // Load stats
        const [agentsRes, tasksRes, sessionsRes, scoresRes] = await Promise.all([
            fetch(`${API_BASE_URL}/agents`),
            fetch(`${API_BASE_URL}/tasks`),
            fetch(`${API_BASE_URL}/sessions`),
            fetch(`${API_BASE_URL}/risk-scores`)
        ]);

        const agents = await agentsRes.json();
        const tasks = await tasksRes.json();
        const sessions = await sessionsRes.json();
        const scores = await scoresRes.json();

        document.getElementById('total-agents').textContent = agents.length || 0;
        document.getElementById('total-tasks').textContent = tasks.length || 0;
        document.getElementById('total-sessions').textContent = sessions.length || 0;
        document.getElementById('total-risk-scores').textContent = scores.length || 0;
    } catch (error) {
        console.error('Dashboard loading error:', error);
    }
}

// Quick Execute Form
document.getElementById('quick-execute-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const model = document.getElementById('quick-model').value;
    const task = document.getElementById('quick-task').value;

    try {
        const response = await fetch(`${API_BASE_URL}/execute`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({model, task})
        });

        const data = await response.json();

        if (response.ok) {
            const resultBox = document.getElementById('quick-result');
            resultBox.style.display = 'block';
            resultBox.innerHTML = `<pre>${data.result || 'Task completed successfully!'}</pre>`;
            showAlert('✅ Task executed successfully!', 'success');
        } else {
            showAlert(`❌ Error: ${data.detail || 'Execution failed'}`, 'error');
        }
    } catch (error) {
        showAlert(`❌ Connection error: ${error.message}`, 'error');
    }
});

// ===== AGENTS SECTION =====
function showCreateAgentForm() {
    document.getElementById('create-agent-form').style.display = 'block';
}

function hideCreateAgentForm() {
    document.getElementById('create-agent-form').style.display = 'none';
}

async function loadAgents() {
    try {
        const response = await fetch(`${API_BASE_URL}/agents`);
        const agents = await response.json();

        const listEl = document.getElementById('agents-list');

        if (agents.length === 0) {
            listEl.innerHTML = '<div class="empty-state"><i class="fas fa-robot"></i><h3>No Agents Yet</h3><p>Create your first agent to get started</p></div>';
            return;
        }

        let html = '<table><thead><tr><th>Name</th><th>Model</th><th>Role</th><th>Actions</th></tr></thead><tbody>';
        agents.forEach(agent => {
            html += `
                <tr>
                    <td><strong>${agent.name}</strong></td>
                    <td>${agent.model}</td>
                    <td>${agent.role || '-'}</td>
                    <td>
                        <button class="btn btn-danger" onclick="deleteAgent('${agent.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        html += '</tbody></table>';
        listEl.innerHTML = html;
    } catch (error) {
        showAlert('❌ Failed to load agents', 'error');
    }
}

document.getElementById('agent-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const agentData = {
        name: document.getElementById('agent-name').value,
        model: document.getElementById('agent-model').value,
        role: document.getElementById('agent-role').value,
        goal: document.getElementById('agent-goal').value,
        instructions: document.getElementById('agent-instructions').value
    };

    try {
        const response = await fetch(`${API_BASE_URL}/agents`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(agentData)
        });

        if (response.ok) {
            showAlert('✅ Agent created successfully!', 'success');
            hideCreateAgentForm();
            document.getElementById('agent-form').reset();
            loadAgents();
        } else {
            const data = await response.json();
            showAlert(`❌ Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showAlert(`❌ Connection error: ${error.message}`, 'error');
    }
});

async function deleteAgent(agentId) {
    if (!confirm('Are you sure you want to delete this agent?')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/agents/${agentId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showAlert('✅ Agent deleted successfully!', 'success');
            loadAgents();
        } else {
            showAlert('❌ Failed to delete agent', 'error');
        }
    } catch (error) {
        showAlert(`❌ Connection error: ${error.message}`, 'error');
    }
}

// ===== TASKS SECTION =====
function showExecuteTaskForm() {
    document.getElementById('execute-task-form').style.display = 'block';
    loadAgentsForTask();
}

function hideExecuteTaskForm() {
    document.getElementById('execute-task-form').style.display = 'none';
}

async function loadAgentsForTask() {
    try {
        const response = await fetch(`${API_BASE_URL}/agents`);
        const agents = await response.json();

        const select = document.getElementById('task-agent');
        select.innerHTML = '<option value="">Select an agent...</option>';

        agents.forEach(agent => {
            select.innerHTML += `<option value="${agent.id}">${agent.name}</option>`;
        });
    } catch (error) {
        console.error('Failed to load agents for task');
    }
}

async function loadTasks() {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks`);
        const tasks = await response.json();

        const listEl = document.getElementById('tasks-list');

        if (tasks.length === 0) {
            listEl.innerHTML = '<div class="empty-state"><i class="fas fa-tasks"></i><h3>No Tasks Yet</h3><p>Execute your first task to get started</p></div>';
            return;
        }

        let html = '<table><thead><tr><th>Task</th><th>Agent</th><th>Status</th><th>Created</th></tr></thead><tbody>';
        tasks.forEach(task => {
            html += `
                <tr>
                    <td>${task.description?.substring(0, 50)}...</td>
                    <td>${task.agent_name || '-'}</td>
                    <td><span class="badge badge-${task.status}">${task.status}</span></td>
                    <td>${new Date(task.created_at).toLocaleString()}</td>
                </tr>
            `;
        });
        html += '</tbody></table>';
        listEl.innerHTML = html;
    } catch (error) {
        showAlert('❌ Failed to load tasks', 'error');
    }
}

document.getElementById('task-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const taskData = {
        agent_id: document.getElementById('task-agent').value,
        description: document.getElementById('task-description').value
    };

    try {
        const response = await fetch(`${API_BASE_URL}/tasks`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(taskData)
        });

        if (response.ok) {
            showAlert('✅ Task executed successfully!', 'success');
            hideExecuteTaskForm();
            document.getElementById('task-form').reset();
            loadTasks();
        } else {
            const data = await response.json();
            showAlert(`❌ Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showAlert(`❌ Connection error: ${error.message}`, 'error');
    }
});

// ===== SESSIONS SECTION =====
function showCreateSessionForm() {
    document.getElementById('create-session-form').style.display = 'block';
}

function hideCreateSessionForm() {
    document.getElementById('create-session-form').style.display = 'none';
}

async function loadSessions() {
    try {
        const response = await fetch(`${API_BASE_URL}/sessions`);
        const sessions = await response.json();

        const listEl = document.getElementById('sessions-list');

        if (sessions.length === 0) {
            listEl.innerHTML = '<div class="empty-state"><i class="fas fa-history"></i><h3>No Sessions Yet</h3><p>Create your first session to get started</p></div>';
            return;
        }

        let html = '<table><thead><tr><th>Session ID</th><th>Storage</th><th>Created</th><th>Actions</th></tr></thead><tbody>';
        sessions.forEach(session => {
            html += `
                <tr>
                    <td><strong>${session.session_id}</strong></td>
                    <td>${session.storage_type}</td>
                    <td>${new Date(session.created_at).toLocaleString()}</td>
                    <td>
                        <button class="btn btn-danger" onclick="deleteSession('${session.session_id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        html += '</tbody></table>';
        listEl.innerHTML = html;
    } catch (error) {
        showAlert('❌ Failed to load sessions', 'error');
    }
}

document.getElementById('session-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const sessionData = {
        session_id: document.getElementById('session-id').value,
        storage_type: document.getElementById('storage-type').value
    };

    try {
        const response = await fetch(`${API_BASE_URL}/sessions`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(sessionData)
        });

        if (response.ok) {
            showAlert('✅ Session created successfully!', 'success');
            hideCreateSessionForm();
            document.getElementById('session-form').reset();
            loadSessions();
        } else {
            const data = await response.json();
            showAlert(`❌ Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showAlert(`❌ Connection error: ${error.message}`, 'error');
    }
});

async function deleteSession(sessionId) {
    if (!confirm('Are you sure you want to delete this session?')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showAlert('✅ Session deleted successfully!', 'success');
            loadSessions();
        } else {
            showAlert('❌ Failed to delete session', 'error');
        }
    } catch (error) {
        showAlert(`❌ Connection error: ${error.message}`, 'error');
    }
}

// ===== RISK SCORING SECTION =====

// Submit new risk application
document.getElementById('risk-application-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = {
        application: {
            company_info: {
                company_type: document.getElementById('company_type').value,
                merchant_name: document.getElementById('merchant_name').value,
                trade_name: document.getElementById('trade_name').value,
                mersis_number: document.getElementById('mersis_number').value || null,
                monthly_revenue: parseFloat(document.getElementById('monthly_revenue').value) || null,
                hosting_vkn: document.getElementById('hosting_vkn').value || null,
                hosting_url: document.getElementById('hosting_url').value || null,
                city: document.getElementById('city').value,
                district: document.getElementById('district').value,
                address: document.getElementById('address').value,
                bkm_number: document.getElementById('bkm_number').value || null,
                language: "TR",
                country: "TR"
            },
            authorized_person: {
                tc_number: document.getElementById('tc_number').value,
                first_name: document.getElementById('first_name').value,
                last_name: document.getElementById('last_name').value,
                email: document.getElementById('email').value,
                company_email: document.getElementById('company_email').value || null,
                mobile_phone: document.getElementById('mobile_phone').value
            },
            documents: {}
        }
    };

    try {
        const response = await fetch(`${API_BASE_URL}/risk-score`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(`✅ Başvuru oluşturuldu! ID: ${data.application_id}. Risk analizi başlatıldı.`, 'success');
            document.getElementById('risk-application-form').reset();

            // Switch to applications tab after 2 seconds
            setTimeout(() => {
                showRiskTab('applications');
                document.querySelectorAll('.tab-btn')[1].click();
            }, 2000);
        } else {
            showAlert(`❌ Hata: ${data.detail || 'Başvuru oluşturulamadı'}`, 'error');
        }
    } catch (error) {
        showAlert(`❌ Bağlantı hatası: ${error.message}`, 'error');
    }
});

// Load applications
async function loadApplications() {
    const contentEl = document.getElementById('applications-content');
    contentEl.innerHTML = '<div class="loading"><i class="fas fa-spinner"></i><p>Yükleniyor...</p></div>';

    try {
        const response = await fetch(`${API_BASE_URL}/risk-scores`);
        const applications = await response.json();

        if (applications.length === 0) {
            contentEl.innerHTML = '<div class="empty-state"><i class="fas fa-clipboard-list"></i><h3>Henüz Başvuru Yok</h3><p>İlk başvurunuzu oluşturun</p></div>';
            return;
        }

        let html = `
            <table>
                <thead>
                    <tr>
                        <th>Merchant</th>
                        <th>Skor</th>
                        <th>Risk Kategorisi</th>
                        <th>Durum</th>
                        <th>Tarih</th>
                        <th>İşlem</th>
                    </tr>
                </thead>
                <tbody>
        `;

        applications.forEach(app => {
            const riskBadge = getRiskBadge(app.risk_category);
            const statusBadge = getStatusBadge(app.status);
            const scoreColor = getScoreColor(app.risk_score);

            html += `
                <tr>
                    <td><strong>${app.merchant_name}</strong></td>
                    <td style="color: ${scoreColor}; font-weight: bold;">${app.risk_score ? app.risk_score.toFixed(1) : '-'}/100</td>
                    <td>${riskBadge}</td>
                    <td>${statusBadge}</td>
                    <td>${new Date(app.created_at).toLocaleString('tr-TR')}</td>
                    <td>
                        <button class="btn btn-primary" style="padding: 6px 12px; font-size: 12px;" onclick="viewDetail('${app.application_id}')">
                            <i class="fas fa-eye"></i> Detay
                        </button>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        contentEl.innerHTML = html;
    } catch (error) {
        showAlert(`❌ Başvurular yüklenemedi: ${error.message}`, 'error');
        contentEl.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-circle"></i><h3>Yüklenemedi</h3><p>Hata oluştu</p></div>';
    }
}

// View application detail
async function viewDetail(applicationId) {
    try {
        const response = await fetch(`${API_BASE_URL}/risk-score/${applicationId}`);
        const data = await response.json();

        const modal = document.getElementById('detailModal');
        const content = document.getElementById('detailContent');

        const scoreColor = getScoreColor(data.risk_score);

        let html = `
            <div class="score-display" style="background: ${scoreColor}; color: white;">
                ${data.risk_score ? data.risk_score.toFixed(1) : '-'} / 100
                <div style="font-size: 20px; margin-top: 10px;">${data.risk_category}</div>
                <div style="font-size: 16px; margin-top: 5px;">${data.merchant_name}</div>
            </div>

            <h3 style="margin-top: 30px;"><i class="fas fa-info-circle"></i> Analiz Özeti</h3>
            <p style="background: var(--light); padding: 15px; border-radius: 8px;">${data.summary || 'Analiz devam ediyor...'}</p>
        `;

        if (data.sources && data.sources.length > 0) {
            html += '<h3 style="margin-top: 30px;"><i class="fas fa-database"></i> Veri Kaynakları</h3>';
            data.sources.forEach(source => {
                html += `
                    <div class="source-card">
                        <strong>${source.source_name}</strong>
                        <div style="margin-top: 8px; font-size: 13px;">
                            <div><strong>Kaynak:</strong> ${source.source_url || 'N/A'}</div>
                            <div><strong>Bulunan:</strong> ${source.data_found}</div>
                            <div><strong>Etki:</strong> ${source.risk_impact}</div>
                            <div><strong>Skor Katkısı:</strong> <strong style="color: var(--primary);">${source.score_contribution} puan</strong></div>
                        </div>
                    </div>
                `;
            });
        }

        if (data.recommendations && data.recommendations.length > 0) {
            html += '<h3 style="margin-top: 30px;"><i class="fas fa-lightbulb"></i> Öneriler</h3>';
            data.recommendations.forEach(rec => {
                html += `<div class="recommendation-item">${rec}</div>`;
            });
        }

        html += `
            <div style="margin-top: 30px; padding: 15px; background: var(--light); border-radius: 8px;">
                <strong>Başvuru ID:</strong> ${data.application_id}<br>
                <strong>Durum:</strong> ${getStatusBadge(data.status)}<br>
                <strong>Oluşturma:</strong> ${new Date(data.created_at).toLocaleString('tr-TR')}<br>
                <strong>İşlenme:</strong> ${data.processed_at ? new Date(data.processed_at).toLocaleString('tr-TR') : 'Devam ediyor'}
            </div>
        `;

        content.innerHTML = html;
        modal.style.display = 'block';

        // Scroll to modal
        modal.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        showAlert(`❌ Detay yüklenemedi: ${error.message}`, 'error');
    }
}

function closeDetail() {
    document.getElementById('detailModal').style.display = 'none';
}

// Send report
document.getElementById('send-report-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const applicationId = document.getElementById('report_application_id').value;
    const emails = document.querySelectorAll('.recipient-email');

    const recipients = [
        { department: "Risk ve Uyum", email: emails[0].value },
        { department: "Operasyon", email: emails[1].value },
        { department: "Fraud", email: emails[2].value },
        { department: "Product", email: emails[3].value }
    ].filter(r => r.email);

    try {
        const response = await fetch(`${API_BASE_URL}/send-report`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                risk_score_id: applicationId,
                recipients: recipients
            })
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(`✅ Rapor ${data.recipients.length} alıcıya gönderildi!`, 'success');
            document.getElementById('send-report-form').reset();
        } else {
            showAlert(`❌ Hata: ${data.detail || 'Rapor gönderilemedi'}`, 'error');
        }
    } catch (error) {
        showAlert(`❌ Bağlantı hatası: ${error.message}`, 'error');
    }
});

// Helper functions
function getRiskBadge(category) {
    const badges = {
        'EXCELLENT': '<span class="badge badge-excellent">EXCELLENT</span>',
        'LOW': '<span class="badge badge-low">LOW RISK</span>',
        'MEDIUM': '<span class="badge badge-medium">MEDIUM RISK</span>',
        'HIGH': '<span class="badge badge-high">HIGH RISK</span>',
        'CRITICAL': '<span class="badge badge-critical">CRITICAL</span>',
        'PENDING': '<span class="badge badge-pending">PENDING</span>'
    };
    return badges[category] || badges['PENDING'];
}

function getStatusBadge(status) {
    const badges = {
        'pending': '<span class="badge badge-pending">Beklemede</span>',
        'processing': '<span class="badge badge-processing">İşleniyor</span>',
        'completed': '<span class="badge badge-completed">Tamamlandı</span>',
        'failed': '<span class="badge badge-failed">Hatalı</span>'
    };
    return badges[status] || badges['pending'];
}

function getScoreColor(score) {
    if (score >= 80) return '#10b981';
    if (score >= 60) return '#3b82f6';
    if (score >= 40) return '#f59e0b';
    if (score >= 20) return '#ef4444';
    return '#dc2626';
}
