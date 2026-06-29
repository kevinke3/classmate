document.addEventListener('DOMContentLoaded', () => {
    if (!auth.requireAuth()) return;

    const user = auth.getUser();
    if (user) {
        document.getElementById('settingsFirstName').value = user.first_name || '';
        document.getElementById('settingsLastName').value = user.last_name || '';
        document.getElementById('settingsEmail').value = user.email || '';
        document.getElementById('settingsPhone').value = user.phone || '';
        document.getElementById('settingsRole').value = user.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : '';
        document.getElementById('profileAvatar').textContent = user.first_name ? user.first_name.charAt(0) : 'U';

        if (user.role === 'admin') {
            document.getElementById('schoolNavItem').style.display = 'flex';
            loadSchoolSettings();
        }
    }

    initSettingsNav();
    initProfileForm(user);
    initPasswordForm();
    initSchoolForm();
});

function initSettingsNav() {
    const navItems = document.querySelectorAll('.settings-nav-item');
    const sections = document.querySelectorAll('.settings-section');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navItems.forEach(n => n.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            item.classList.add('active');
            document.getElementById(`section-${item.dataset.section}`).classList.add('active');
        });
    });
}

function initProfileForm(user) {
    document.getElementById('profileForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            first_name: document.getElementById('settingsFirstName').value,
            last_name: document.getElementById('settingsLastName').value,
            phone: document.getElementById('settingsPhone').value
        };
        try {
            await api.put('/settings/profile', data);
            localStorage.setItem('user', JSON.stringify({ ...user, ...data }));
            alert('Profile updated successfully');
        } catch (err) {
            console.error(err);
            alert('Failed to update profile');
        }
    });
}

function initPasswordForm() {
    const form = document.getElementById('passwordForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const alert = document.getElementById('passwordAlert');
        const newPass = document.getElementById('newPassword').value;
        const confirmPass = document.getElementById('confirmPassword').value;

        if (newPass !== confirmPass) {
            alert.style.display = 'block';
            alert.style.background = 'rgba(239, 68, 68, 0.06)';
            alert.style.color = 'var(--color-error)';
            alert.style.border = '1px solid rgba(239, 68, 68, 0.15)';
            alert.textContent = 'Passwords do not match';
            return;
        }

        try {
            await api.post('/settings/change-password', {
                current_password: document.getElementById('currentPassword').value,
                new_password: newPass
            });
            alert.style.display = 'block';
            alert.style.background = 'rgba(34, 197, 94, 0.06)';
            alert.style.color = 'var(--color-success)';
            alert.style.border = '1px solid rgba(34, 197, 94, 0.15)';
            alert.textContent = 'Password updated successfully';
            form.reset();
        } catch (err) {
            alert.style.display = 'block';
            alert.style.background = 'rgba(239, 68, 68, 0.06)';
            alert.style.color = 'var(--color-error)';
            alert.style.border = '1px solid rgba(239, 68, 68, 0.15)';
            alert.textContent = 'Failed to update password. Check your current password.';
        }
    });
}

async function loadSchoolSettings() {
    try {
        const data = await api.get('/settings/school');
        const school = data.school;
        if (school) {
            document.getElementById('schoolName').value = school.school_name || '';
            document.getElementById('schoolMotto').value = school.motto || '';
            document.getElementById('schoolLogo').value = school.logo_url || '';
            document.getElementById('schoolEmail').value = school.email || '';
            document.getElementById('schoolPhone').value = school.phone || '';
            document.getElementById('schoolAddress').value = school.address || '';
            document.getElementById('schoolWebsite').value = school.website || '';
            document.getElementById('schoolYear').value = school.academic_year || '';
            document.getElementById('schoolTerm').value = school.current_term || 'Term 1';
        }
    } catch (err) {
        console.error('Failed to load school settings:', err);
    }
}

function initSchoolForm() {
    const form = document.getElementById('schoolForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const alert = document.getElementById('schoolAlert');
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Saving...';

        try {
            await api.put('/settings/school', {
                school_name: document.getElementById('schoolName').value,
                motto: document.getElementById('schoolMotto').value,
                logo_url: document.getElementById('schoolLogo').value,
                email: document.getElementById('schoolEmail').value,
                phone: document.getElementById('schoolPhone').value,
                address: document.getElementById('schoolAddress').value,
                website: document.getElementById('schoolWebsite').value,
                academic_year: document.getElementById('schoolYear').value,
                current_term: document.getElementById('schoolTerm').value
            });
            alert.style.display = 'block';
            alert.style.background = 'rgba(34, 197, 94, 0.06)';
            alert.style.color = 'var(--color-success)';
            alert.style.border = '1px solid rgba(34, 197, 94, 0.15)';
            alert.textContent = 'School settings saved successfully';
        } catch (err) {
            console.error(err);
            alert.style.display = 'block';
            alert.style.background = 'rgba(239, 68, 68, 0.06)';
            alert.style.color = 'var(--color-error)';
            alert.style.border = '1px solid rgba(239, 68, 68, 0.15)';
            alert.textContent = 'Failed to save school settings';
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Save School Settings';
        }
    });
}
