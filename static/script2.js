document.addEventListener('DOMContentLoaded', function() {
    const revenueSlider = document.getElementById('revenue');
    const revenueValue = document.getElementById('revenueValue');
    const adSpendSlider = document.getElementById('adSpend');
    const adSpendValue = document.getElementById('adSpendValue');
    const roasSlider = document.getElementById('roas');
    const roasValue = document.getElementById('roasValue');
    const marketerFeeSlider = document.getElementById('marketerFee');
    const marketerFeeValue = document.getElementById('marketerFeeValue');
    const resultsDiv = document.getElementById('results');
    let chart;

    function formatCurrency(value) {
        return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);
    }

    function calculateResults() {
        const revenue = parseFloat(revenueSlider.value);
        const adSpend = parseFloat(adSpendSlider.value);
        const roas = parseFloat(roasSlider.value);
        const marketerFeePercentage = parseFloat(marketerFeeSlider.value);

        // Calculations
        const paymentGatewayFee = revenue * 0.02;
        const adRebate = adSpend * 0.18;
        const profitBeforeTax = revenue - paymentGatewayFee - adSpend + adRebate;
        const tax = profitBeforeTax * 0.30;
        const profitAfterTax = profitBeforeTax - tax;
        const performanceMarketerFee = profitAfterTax * (marketerFeePercentage / 100);
        const finalProfit = profitAfterTax - performanceMarketerFee;

        // Divide profit between Aryan and Deepanshu
        const aryanShare = finalProfit / 2;
        const deepanshuShare = finalProfit / 2;

        // Calculate individual taxes (30% on their share)
        const aryanTax = aryanShare * 0.30;
        const deepanshuTax = deepanshuShare * 0.30;

        // Calculate final take-home amounts
        const aryanTakeHome = aryanShare - aryanTax;
        const deepanshuTakeHome = deepanshuShare - deepanshuTax;

        return {
            revenue: revenue,
            paymentGatewayFee: paymentGatewayFee,
            adSpend: adSpend,
            adRebate: adRebate,
            profitBeforeTax: profitBeforeTax,
            tax: tax,
            profitAfterTax: profitAfterTax,
            performanceMarketerFee: performanceMarketerFee,
            finalProfit: finalProfit,
            roas: adSpend > 0 ? revenue / adSpend : Infinity,
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
            <tr><td>Revenue</td><td>${formatCurrency(data.revenue)}</td></tr>
            <tr><td>Payment Gateway Fee (2%)</td><td>${formatCurrency(data.paymentGatewayFee)}</td></tr>
            <tr><td>Ad Spend</td><td>${formatCurrency(data.adSpend)}</td></tr>
            <tr><td>Ad Rebate (18% of Ad Spend)</td><td>${formatCurrency(data.adRebate)}</td></tr>
            <tr><td>Profit Before Tax</td><td>${formatCurrency(data.profitBeforeTax)}</td></tr>
            <tr><td>Tax (30%)</td><td>${formatCurrency(data.tax)}</td></tr>
            <tr><td>Profit After Tax</td><td>${formatCurrency(data.profitAfterTax)}</td></tr>
            <tr><td>Performance Marketer Fee</td><td>${formatCurrency(data.performanceMarketerFee)}</td></tr>
            <tr><td>Final Profit</td><td>${formatCurrency(data.finalProfit)}</td></tr>
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
            labels: ['Revenue', 'Ad Spend', 'Profit', 'Aryan Take Home', 'Deepanshu Take Home'],
            datasets: [{
                label: 'Amount (₹)',
                data: [
                    data.revenue,
                    data.adSpend,
                    data.finalProfit,
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
                            return '₹' + value.toLocaleString();
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return '₹' + context.parsed.y.toLocaleString();
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

    function updateAdSpend() {
        const revenue = parseFloat(revenueSlider.value);
        const roas = parseFloat(roasSlider.value);
        const newAdSpend = revenue === 0 ? 0 : Math.min(revenue / roas, 10000000);
        adSpendSlider.value = newAdSpend;
        adSpendValue.textContent = formatCurrency(newAdSpend);
    }

    function updateROAS() {
        const revenue = parseFloat(revenueSlider.value);
        const adSpend = parseFloat(adSpendSlider.value);
        let newROAS = 0;
        if (adSpend > 0 && revenue > 0) {
            newROAS = revenue / adSpend;
        } else if (revenue > 0) {
            newROAS = 10; // Max ROAS when ad spend is 0
        }
        roasSlider.value = Math.min(Math.max(newROAS, 0.1), 10);
        roasValue.textContent = parseFloat(roasSlider.value).toFixed(1);
    }

    function addZoomFeature(slider) {
        let touchStartX, touchStartY, touchEndX, touchEndY;
        let originalMin, originalMax, originalValue;

        slider.addEventListener('touchstart', function(e) {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
            originalMin = parseFloat(slider.min);
            originalMax = parseFloat(slider.max);
            originalValue = parseFloat(slider.value);
        });

        slider.addEventListener('touchmove', function(e) {
            e.preventDefault();
            touchEndX = e.touches[0].clientX;
            touchEndY = e.touches[0].clientY;

            const deltaX = touchEndX - touchStartX;
            const deltaY = touchEndY - touchStartY;

            if (Math.abs(deltaX) > Math.abs(deltaY)) {
                const zoomFactor = 1 + Math.abs(deltaX) / slider.offsetWidth;
                const newMin = Math.max(0, originalValue - (originalValue - originalMin) * zoomFactor);
                const newMax = Math.min(parseFloat(slider.getAttribute('max')), originalValue + (originalMax - originalValue) * zoomFactor);

                slider.min = newMin;
                slider.max = newMax;
            }
        });

        slider.addEventListener('touchend', function() {
            slider.min = originalMin;
            slider.max = originalMax;
        });
    }

    // Add zoom feature to all sliders with data-zoom attribute
    document.querySelectorAll('input[type="range"][data-zoom="true"]').forEach(addZoomFeature);

    revenueSlider.addEventListener('input', function() {
        revenueValue.textContent = formatCurrency(this.value);
        updateAdSpend();
        updateROAS();
        updateResults();
    });

    adSpendSlider.addEventListener('input', function() {
        adSpendValue.textContent = formatCurrency(this.value);
        updateROAS();
        updateResults();
    });

    roasSlider.addEventListener('input', function() {
        roasValue.textContent = parseFloat(this.value).toFixed(1);
        updateAdSpend();
        updateResults();
    });

    marketerFeeSlider.addEventListener('input', function() {
        marketerFeeValue.textContent = this.value;
        updateResults();
    });

    // Set initial values and update
    revenueSlider.value = 100000; // 1L
    roasSlider.value = 2.0;
    marketerFeeSlider.value = 10;
    
    // Calculate initial ad spend based on revenue and ROAS
    const initialAdSpend = 100000 / 2.0;
    adSpendSlider.value = initialAdSpend;

    revenueValue.textContent = formatCurrency(revenueSlider.value);
    adSpendValue.textContent = formatCurrency(adSpendSlider.value);
    roasValue.textContent = parseFloat(roasSlider.value).toFixed(1);
    marketerFeeValue.textContent = marketerFeeSlider.value;

    // Initial update
    updateResults();
});
