/* Admin dashboard charts (Chart.js). Data comes from window.FC_CHART. */
(function () {
  var data = window.FC_CHART;
  if (!data || typeof Chart === 'undefined') return;

  var green = '#2e7d47', greenSoft = 'rgba(46,125,71,.18)';
  var base = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,.06)' } },
              x: { grid: { display: false } } }
  };

  new Chart(document.getElementById('revenueChart'), {
    type: 'line',
    data: { labels: data.labels,
      datasets: [{ data: data.revenue, borderColor: green, backgroundColor: greenSoft,
                   fill: true, tension: .35, pointRadius: 3 }] },
    options: base
  });

  new Chart(document.getElementById('ordersChart'), {
    type: 'bar',
    data: { labels: data.labels,
      datasets: [{ data: data.orders, backgroundColor: green, borderRadius: 6 }] },
    options: base
  });

  new Chart(document.getElementById('statusChart'), {
    type: 'doughnut',
    data: { labels: ['Approved', 'Pending', 'Rejected'],
      datasets: [{ data: data.product_status,
                   backgroundColor: ['#2e7d47', '#e0a63c', '#c0483c'] }] },
    options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
  });

  new Chart(document.getElementById('usersChart'), {
    type: 'doughnut',
    data: { labels: ['Farmers', 'Customers'],
      datasets: [{ data: data.users, backgroundColor: ['#2e7d47', '#7cb08a'] }] },
    options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
  });
})();
