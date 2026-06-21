document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('loginForm');
    const alert = document.getElementById('authAlert');
    const toggleBtn = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const type = passwordInput.type === 'password' ? 'text' : 'password';
            passwordInput.type = type;
            toggleBtn.innerHTML = type === 'password'
                ? '<i class="lucide-eye"></i>'
                : '<i class="lucide-eye-off"></i>';
        });
    }

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Signing in...';

            try {
                const response = await api.post('/auth/login', { email, password });

                if (response.access_token) {
                    localStorage.setItem('access_token', response.access_token);
                    localStorage.setItem('refresh_token', response.refresh_token);
                    localStorage.setItem('user', JSON.stringify(response.user));

                    const role = response.user.role;
                    const redirectMap = {
                        'admin': '/dashboard',
                        'teacher': '/teacher-portal',
                        'student': '/student-portal',
                        'parent': '/parent-portal'
                    };

                    window.location.href = redirectMap[role] || '/dashboard';
                } else {
                    showAlert(response.error || 'Invalid credentials', 'error');
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Sign In';
                }
            } catch (error) {
                showAlert('An error occurred. Please try again.', 'error');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Sign In';
            }
        });
    }

    function showAlert(message, type) {
        if (alert) {
            alert.textContent = message;
            alert.className = `auth-alert ${type}`;
        }
    }
});
