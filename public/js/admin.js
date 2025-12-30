document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const API_URL = '/api/v1/admin';

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const errorDiv = document.getElementById('login-error');
            errorDiv.style.display = 'none';
            errorDiv.textContent = '';

            const formData = new FormData(loginForm);
            
            try {
                const response = await fetch(`${API_URL}/login`, {
                    method: 'POST',
                    body: formData // sending as form-data for OAuth2PasswordRequestForm
                });

                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('access_token', data.access_token);
                    window.location.href = '/admin/dashboard.html';
                } else {
                    const error = await response.json();
                    errorDiv.textContent = error.detail || 'Login failed';
                    errorDiv.style.display = 'block';
                }
            } catch (err) {
                errorDiv.textContent = 'Network error occurred';
                errorDiv.style.display = 'block';
            }
        });
    }

    // Auth Guard for admin pages
    if (window.location.pathname.includes('/admin/') && !window.location.pathname.includes('login.html')) {
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/login.html';
        } else {
            // Setup logout button if it exists
            const logoutBtn = document.getElementById('logout-btn');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    localStorage.removeItem('access_token');
                    window.location.href = '/login.html';
                });
            }
            // Load dashboard data if on dashboard
            if (window.location.pathname.includes('dashboard.html')) {
                loadDashboardData();
            }
        }
    }

    async function loadDashboardData() {
        const token = localStorage.getItem('access_token');
        try {
            const response = await fetch(`${API_URL}/dashboard`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const messages = await response.json();
                renderMessages(messages);
            } else if (response.status === 401) {
                // Token expired or invalid
                localStorage.removeItem('access_token');
                window.location.href = '/login.html';
            }
        } catch (error) {
            console.error('Error fetching dashboard:', error);
        }
    }

    function renderMessages(messages) {
        const tbody = document.querySelector('tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        messages.forEach(msg => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${new Date(msg.timestamp).toLocaleString()}</td>
                <td>${escapeHtml(msg.name)}</td>
                <td>${escapeHtml(msg.email)}</td>
                <td>${escapeHtml(msg.phone || '')}</td>
                <td>
                    <button class="btn-view" onclick="viewMessage('${escapeHtml(msg.message)}', '${escapeHtml(msg.name)}')">View</button>
                    <button class="btn-delete" onclick="deleteMessage(${msg.id})">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    window.viewMessage = (message, name) => {
        alert(`Message from ${name}:\n\n${message}`);
    }

    window.deleteMessage = async (id) => {
        if (!confirm('Are you sure you want to delete this message?')) return;
        
        const token = localStorage.getItem('access_token');
        try {
            const response = await fetch(`${API_URL}/messages/${id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                loadDashboardData(); // Reload table
            } else {
                alert('Failed to delete message');
            }
        } catch (error) {
            console.error('Error deleting:', error);
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
