// Main JavaScript file for Smart Travel Assistant

document.addEventListener('DOMContentLoaded', function() {
    // Initialize date picker with default date (today)
    const dateInput = document.getElementById('date');
    if (dateInput) {
        const today = new Date();
        const formattedDate = today.toISOString().substr(0, 10);
        dateInput.value = formattedDate;
        dateInput.min = formattedDate; // Prevent selecting past dates
    }
    
    // City selection validation - prevent same source and destination
    const sourceSelect = document.getElementById('source');
    const destSelect = document.getElementById('destination');
    
    if (sourceSelect && destSelect) {
        sourceSelect.addEventListener('change', function() {
            validateSelections();
        });
        
        destSelect.addEventListener('change', function() {
            validateSelections();
        });
        
        function validateSelections() {
            const sourceValue = sourceSelect.value;
            const destValue = destSelect.value;
            
            if (sourceValue && destValue && sourceValue === destValue) {
                alert('Source and destination cannot be the same');
                // Reset the one that was just changed
                if (document.activeElement === sourceSelect) {
                    sourceSelect.value = '';
                } else {
                    destSelect.value = '';
                }
            }
        }
    }
    
    // Enable tooltips everywhere
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });
    
    // Form validation for search form
    const searchForm = document.querySelector('form[action="/search"]');
    if (searchForm) {
        searchForm.addEventListener('submit', function(event) {
            const source = document.getElementById('source').value;
            const destination = document.getElementById('destination').value;
            const date = document.getElementById('date').value;
            
            if (!source || !destination || !date) {
                event.preventDefault();
                alert('Please fill in all required fields');
            } else if (source === destination) {
                event.preventDefault();
                alert('Source and destination cannot be the same');
            }
        });
    }
});

// Price trends chart setup (if element exists)
function setupPriceChart(elementId, data) {
    const chartElement = document.getElementById(elementId);
    if (!chartElement) return;
    
    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: 'Flight',
                    data: data.flight,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    tension: 0.1
                },
                {
                    label: 'Train',
                    data: data.train,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.1
                },
                {
                    label: 'Bus',
                    data: data.bus,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Price Trends'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Price (₹)'
                    },
                    beginAtZero: false
                }
            }
        }
    });
}

// Filter results functionality
function filterResults(filters) {
    fetch('/api/filter', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(filters),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload the page or update DOM with filtered results
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error applying filters:', error);
    });
}
