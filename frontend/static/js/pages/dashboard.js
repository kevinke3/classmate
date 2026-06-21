document.addEventListener('DOMContentLoaded', () => {
    if (!auth.requireAuth()) return;

    animateCounters();
    initAttendanceChart();
    initRevenueChart();
    loadDashboardData();
});

function animateCounters() {
    const counters = document.querySelectorAll('[data-target]');
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-target'));
        const prefix = counter.getAttribute('data-prefix') || '';
        const duration = 1500;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(eased * target);

            if (target > 10000) {
                counter.textContent = prefix + current.toLocaleString();
            } else {
                counter.textContent = prefix + current;
            }

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    });
}

function initAttendanceChart() {
    const ctx = document.getElementById('attendanceChart');
    if (!ctx) return;

    const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Mon', 'Tue'];
    const data = {
        labels,
        datasets: [{
            label: 'Present',
            data: [92, 94, 91, 95, 93, 96, 94],
            borderColor: '#10B981',
            backgroundColor: 'rgba(16, 185, 129, 0.08)',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointBackgroundColor: '#10B981'
        }, {
            label: 'Absent',
            data: [8, 6, 9, 5, 7, 4, 6],
            borderColor: '#E63946',
            backgroundColor: 'rgba(230, 57, 70, 0.05)',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointBackgroundColor: '#E63946'
        }]
    };

    new Chart(ctx, {
        type: 'line',
        data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: {
                        boxWidth: 8,
                        boxHeight: 8,
                        borderRadius: 4,
                        useBorderRadius: true,
                        font: { family: 'Outfit', size: 12 }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Outfit', size: 12 } }
                },
                y: {
                    grid: { color: 'rgba(0,0,0,0.04)' },
                    ticks: {
                        font: { family: 'Outfit', size: 12 },
                        callback: value => value + '%'
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

function initRevenueChart() {
    const ctx = document.getElementById('revenueChart');
    if (!ctx) return;

    const data = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
            label: 'Revenue (KES)',
            data: [380000, 420000, 510000, 460000, 520000, 580000],
            backgroundColor: [
                'rgba(230, 57, 70, 0.8)',
                'rgba(230, 57, 70, 0.65)',
                'rgba(230, 57, 70, 0.8)',
                'rgba(230, 57, 70, 0.55)',
                'rgba(230, 57, 70, 0.7)',
                'rgba(230, 57, 70, 0.9)'
            ],
            borderRadius: 8,
            borderSkipped: false
        }]
    };

    new Chart(ctx, {
        type: 'bar',
        data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Outfit', size: 12 } }
                },
                y: {
                    grid: { color: 'rgba(0,0,0,0.04)' },
                    ticks: {
                        font: { family: 'Outfit', size: 11 },
                        callback: value => (value / 1000) + 'K'
                    }
                }
            }
        }
    });
}

async function loadDashboardData() {
    try {
        const overview = await api.get('/analytics/overview');
        if (overview) {
            updateStatCards(overview);
        }
    } catch (error) {
        // Use default sample data
    }
}

function updateStatCards(data) {
    const counters = document.querySelectorAll('[data-target]');
    if (data.total_students) {
        counters[0].setAttribute('data-target', data.total_students);
    }
    if (data.total_teachers) {
        counters[1].setAttribute('data-target', data.total_teachers);
    }
}
