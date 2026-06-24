document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const body = document.body;

    const savedState = localStorage.getItem('sidebar_collapsed');
    if (savedState === 'true') {
        body.classList.add('sidebar-collapsed');
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            body.classList.toggle('sidebar-collapsed');
            localStorage.setItem('sidebar_collapsed', body.classList.contains('sidebar-collapsed'));
        });
    }

    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('mobile-open');
        });
    }

    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768) {
            if (!sidebar.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                sidebar.classList.remove('mobile-open');
            }
        }
    });

    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
    navItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href === currentPath) {
            item.classList.add('active');
        }
    });

    const userData = localStorage.getItem('user');
    if (userData) {
        const user = JSON.parse(userData);
        if (user.role === 'finance') {
            navItems.forEach(item => {
                const href = item.getAttribute('href');
                const allowed = ['/finance-portal', '/settings'];
                if (!allowed.includes(href)) {
                    item.style.display = 'none';
                }
            });
            const financeLink = document.querySelector('.sidebar-nav .nav-item[href="/finance"]');
            if (financeLink) {
                financeLink.setAttribute('href', '/finance-portal');
                financeLink.style.display = '';
            }
        }
    }
});
