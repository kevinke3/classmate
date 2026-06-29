document.addEventListener('DOMContentLoaded', () => {
    if (!auth.requireAuth()) return;

    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const cards = document.querySelectorAll('.student-card');
            cards.forEach(card => {
                const name = card.querySelector('.student-card-name').textContent.toLowerCase();
                card.style.display = name.includes(query) ? '' : 'none';
            });
        });
    }

    loadTeachers();
});

async function loadTeachers() {
    try {
        const response = await api.get('/teachers/?per_page=50');
        if (response && response.teachers && response.teachers.length > 0) {
            document.getElementById('teacherCount').textContent = response.total || response.teachers.length;
        }
    } catch (error) {
        // Use sample data
    }
}
