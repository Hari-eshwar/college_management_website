document.addEventListener('DOMContentLoaded', function() {
    loadAnalytics();
});

function loadAnalytics() {
    fetch('/admin/analytics')
        .then(r => r.json())
        .then(data => {
            document.getElementById('totalStudents').textContent = data.total_students || 0;
            document.getElementById('totalFaculty').textContent = data.total_faculty || 0;
            document.getElementById('totalAttendance').textContent = data.total_attendance || 0;

            renderPieChart(data);
        })
        .catch(() => {
            document.getElementById('totalStudents').textContent = '--';
            document.getElementById('totalFaculty').textContent = '--';
            document.getElementById('totalAttendance').textContent = '--';

        });
}

function renderPieChart(data) {
    const canvas = document.getElementById('analyticsPieChart');
    if (!canvas) return;
    const present = data.present_today || 0;
    const total = data.today_attendance || 0;
    const absent = total - present;
    new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: ['Present', 'Absent'],
            datasets: [{
                data: [present, Math.max(0, absent)],
                backgroundColor: ['#2ecc71', '#e74c3c'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' },
                title: { display: true, text: 'Today: ' + present + '/' + total, color: '#636e72' }
            }
        }
    });
}
