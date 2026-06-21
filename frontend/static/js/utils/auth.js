class AuthManager {
    constructor() {
        this.user = null;
        this.init();
    }

    init() {
        const userData = localStorage.getItem('user');
        if (userData) {
            this.user = JSON.parse(userData);
            this.updateUI();
        }
    }

    isAuthenticated() {
        return !!localStorage.getItem('access_token');
    }

    getUser() {
        return this.user;
    }

    getRole() {
        return this.user ? this.user.role : null;
    }

    async login(email, password) {
        const response = await api.post('/auth/login', { email, password });

        if (response.access_token) {
            localStorage.setItem('access_token', response.access_token);
            localStorage.setItem('refresh_token', response.refresh_token);
            localStorage.setItem('user', JSON.stringify(response.user));
            this.user = response.user;
            return { success: true, user: response.user };
        }

        return { success: false, error: response.error };
    }

    async register(data) {
        const response = await api.post('/auth/register', data);

        if (response.user) {
            return { success: true, user: response.user };
        }

        return { success: false, error: response.error };
    }

    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        this.user = null;
        window.location.href = '/login';
    }

    updateUI() {
        if (!this.user) return;

        const userNameEl = document.getElementById('userName');
        const userRoleEl = document.getElementById('userRole');
        const userAvatarEl = document.getElementById('userAvatar');

        if (userNameEl) userNameEl.textContent = this.user.full_name;
        if (userRoleEl) userRoleEl.textContent = this.capitalizeRole(this.user.role);
        if (userAvatarEl) userAvatarEl.textContent = this.user.first_name.charAt(0);
    }

    capitalizeRole(role) {
        return role.charAt(0).toUpperCase() + role.slice(1);
    }

    requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = '/login';
            return false;
        }
        return true;
    }

    requireRole(roles) {
        if (!this.requireAuth()) return false;
        if (!roles.includes(this.getRole())) {
            window.location.href = '/dashboard';
            return false;
        }
        return true;
    }
}

const auth = new AuthManager();

document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => auth.logout());
    }
});
