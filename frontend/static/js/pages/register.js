document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('registerForm');
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

            const data = {
                first_name: document.getElementById('firstName').value,
                last_name: document.getElementById('lastName').value,
                email: document.getElementById('email').value,
                phone: document.getElementById('phone').value,
                role: document.getElementById('role').value,
                password: document.getElementById('password').value
            };

            if (!data.role) {
                showAlert('Please select an account type', 'error');
                return;
            }

            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating account...';

            try {
                const response = await api.post('/auth/register', data);

                if (response.user) {
                    showAlert('Account created successfully! Redirecting...', 'success');
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 1500);
                } else {
                    showAlert(response.error || 'Registration failed', 'error');
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Create Account';
                }
            } catch (error) {
                showAlert('An error occurred. Please try again.', 'error');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Create Account';
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
