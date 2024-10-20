document.addEventListener('DOMContentLoaded', function() {
    const revenueSlider = document.getElementById('revenue');
    const revenueValue = document.getElementById('revenueValue');
    const transactionsSlider = document.getElementById('transactions');
    const transactionsValue = document.getElementById('transactionsValue');
    const transactionValueSlider = document.getElementById('transactionValue');
    const transactionValueValue = document.getElementById('transactionValueValue');
    const resultsDiv = document.getElementById('results');
    let chart;

    function formatCurrency(value, currency = 'USD') {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: currency }).format(value);
    }

    function calculateResults() {
        const revenue = parseFloat(revenueSlider.value);
        const transactions = parseInt(transactionsSlider.value);
        const transactionAmount = parseFloat(transactionValueSlider.value);
        const skoolFee = revenue * 0.029 + (transactions * 0.3);
        const revenueAfterSkool = revenue - skoolFee;
        const tax = revenueAfterSkool * 0.3;
        const profitAfterTax = revenueAfterSkool - tax;
        const aryanShare = profitAfterTax / 2;
        const deepanshuShare = profitAfterTax / 2;
        const aryanTax = aryanShare * 0.3;
        const deepanshuTax = deepanshuShare * 0.3;
        const aryanTakeHome = aryanShare - aryanTax;
        const deepanshuTakeHome = deepanshuShare - deepanshuTax;

        return {
            revenue: revenue,
            transactions: transactions,
            transactionAmount: transactionAmount,
            skoolFee: skoolFee,
            revenueAfterSkool: revenueAfterSkool,
            tax: tax,
            profitAfterTax: profitAfterTax,
            aryanShare: aryanShare,
            deepanshuShare: deepanshuShare,
            aryanTax: aryanTax,
            deepanshuTax: deepanshuTax,
            aryanTakeHome: aryanTakeHome,
            deepanshuTakeHome: deepanshuTakeHome
        };
    }

    function updateResults() {
        const data = calculateResults();
        updateTable(data);
        updateChart(data);
        resultsDiv.classList.remove('hidden');
    }

    function updateTable(data) {
        const table = document.getElementById('resultsTable');
        table.innerHTML = `
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Revenue</td><td>${formatCurrency(data.revenue)}</td></tr>
            <tr><td>Number of Transactions</td><td>${data.transactions}</td></tr>
            <tr><td>Transaction Value</td><td>${formatCurrency(data.transactionAmount)}</td></tr>
            <tr><td>Skool Fee</td><td>${formatCurrency(data.skoolFee)}</td></tr>
            <tr><td>Revenue After Skool</td><td>${formatCurrency(data.revenueAfterSkool)}</td></tr>
            <tr><td>Tax (30%)</td><td>${formatCurrency(data.tax)}</td></tr>
            <tr><td>Profit After Tax</td><td>${formatCurrency(data.profitAfterTax)}</td></tr>
            <tr><td>Aryan's Share</td><td>${formatCurrency(data.aryanShare)}</td></tr>
            <tr><td>Deepanshu's Share</td><td>${formatCurrency(data.deepanshuShare)}</td></tr>
            <tr><td>Aryan's Tax (30%)</td><td>${formatCurrency(data.aryanTax)}</td></tr>
            <tr><td>Deepanshu's Tax (30%)</td><td>${formatCurrency(data.deepanshuTax)}</td></tr>
            <tr><td>Aryan's Take Home</td><td>${formatCurrency(data.aryanTakeHome)}</td></tr>
            <tr><td>Deepanshu's Take Home</td><td>${formatCurrency(data.deepanshuTakeHome)}</td></tr>
        `;
    }

    function updateChart(data) {
        const ctx = document.getElementById('revenueChart').getContext('2d');
        
        const chartData = {
            labels: ['Total Revenue', 'Skool Fee', 'Tax', 'Aryan Take Home', 'Deepanshu Take Home'],
            datasets: [{
                label: 'Amount ($)',
                data: [
                    data.totalRevenue,
                    data.skoolFee,
                    data.tax,
                    data.aryanTakeHome,
                    data.deepanshuTakeHome
                ],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.5)',
                    'rgba(54, 162, 235, 0.5)',
                    'rgba(255, 206, 86, 0.5)',
                    'rgba(75, 192, 192, 0.5)',
                    'rgba(153, 102, 255, 0.5)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)'
                ],
                borderWidth: 1
            }]
        };

        const options = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return '$' + context.parsed.y.toLocaleString();
                        }
                    }
                }
            }
        };

        if (chart) {
            chart.data = chartData;
            chart.options = options;
            chart.update();
        } else {
            chart = new Chart(ctx, {
                type: 'bar',
                data: chartData,
                options: options
            });
        }
    }

    function addZoomFeature(slider) {
        // ... (keep the existing zoom feature code)
    }

    // Add zoom feature to all sliders with data-zoom attribute
    document.querySelectorAll('input[type="range"][data-zoom="true"]').forEach(addZoomFeature);

    function updateRevenue() {
        const transactions = parseInt(transactionsSlider.value);
        const transactionValue = parseFloat(transactionValueSlider.value);
        const newRevenue = transactions * transactionValue;
        revenueSlider.value = newRevenue.toFixed(2);
        revenueValue.textContent = formatCurrency(newRevenue);
    }

    revenueSlider.addEventListener('input', function() {
        revenueValue.textContent = formatCurrency(this.value);
        updateResults();
    });

    transactionsSlider.addEventListener('input', function() {
        transactionsValue.textContent = this.value;
        updateRevenue();
        updateResults();
    });

    transactionValueSlider.addEventListener('input', function() {
        transactionValueValue.textContent = formatCurrency(this.value);
        updateRevenue();
        updateResults();
    });

    // Set initial values and update
    revenueSlider.value = 100000;
    transactionsSlider.value = 1010;
    transactionValueSlider.value = 99;
    
    revenueValue.textContent = formatCurrency(revenueSlider.value);
    transactionsValue.textContent = transactionsSlider.value;
    transactionValueValue.textContent = formatCurrency(transactionValueSlider.value);

    // Initial update
    updateResults();
});
