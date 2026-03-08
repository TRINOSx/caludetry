/* ================================
   Chart Manager
   ================================ */

const ChartManager = {
    charts: {},

    // Default chart styling
    defaultOptions: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 800,
            easing: 'easeInOutQuart',
        },
        plugins: {
            legend: {
                labels: {
                    color: '#94a3b8',
                    font: { family: 'Inter', size: 11 },
                    boxWidth: 12,
                    padding: 12,
                },
            },
            tooltip: {
                backgroundColor: 'rgba(17,24,39,0.95)',
                titleColor: '#e2e8f0',
                bodyColor: '#94a3b8',
                borderColor: '#2a3a4a',
                borderWidth: 1,
                cornerRadius: 8,
                titleFont: { family: 'Inter', weight: '600' },
                bodyFont: { family: 'JetBrains Mono', size: 12 },
                padding: 10,
            },
        },
        scales: {
            x: {
                grid: { color: 'rgba(42,58,74,0.4)', lineWidth: 0.5 },
                ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 9 } },
            },
            y: {
                grid: { color: 'rgba(42,58,74,0.4)', lineWidth: 0.5 },
                ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 10 } },
            },
        },
    },

    // Create VOC Time Series Chart
    createVOCTimeChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        const labels = data.map(d => {
            const t = new Date(d.timestamp);
            return t.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        });

        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    this.makeDataset('TVOC', data.map(d => d.tvoc), CONFIG.CHART_COLORS.tvoc),
                    this.makeDataset('VOC', data.map(d => d.voc), CONFIG.CHART_COLORS.voc),
                    this.makeDataset('CO', data.map(d => d.co), CONFIG.CHART_COLORS.co),
                    this.makeDataset('H2', data.map(d => d.h2), CONFIG.CHART_COLORS.h2),
                    this.makeDataset('CH4', data.map(d => d.ch4), CONFIG.CHART_COLORS.ch4),
                    this.makeDataset('Smoke', data.map(d => d.smoke), CONFIG.CHART_COLORS.smoke),
                    this.makeDataset('Odor', data.map(d => d.odor), CONFIG.CHART_COLORS.odor),
                    this.makeDataset('SPO40', data.map(d => d.spo40), CONFIG.CHART_COLORS.spo40),
                ],
            },
            options: {
                ...this.defaultOptions,
                plugins: {
                    ...this.defaultOptions.plugins,
                    legend: {
                        ...this.defaultOptions.plugins.legend,
                        position: 'bottom',
                    },
                },
            },
        });
    },

    // Create Soil & Climate Chart
    createSoilClimateChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        const labels = data.map(d => {
            const t = new Date(d.timestamp);
            return t.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        });

        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    this.makeDataset('CO2 (ppm)', data.map(d => d.co2), CONFIG.CHART_COLORS.co2),
                    this.makeDataset('NH3 (ppb)', data.map(d => d.nh3), CONFIG.CHART_COLORS.nh3),
                    this.makeDataset('Temp (C)', data.map(d => d.temperature * 10), CONFIG.CHART_COLORS.temperature),
                    this.makeDataset('Humidity (%)', data.map(d => d.humidity), CONFIG.CHART_COLORS.humidity),
                ],
            },
            options: {
                ...this.defaultOptions,
                plugins: {
                    ...this.defaultOptions.plugins,
                    legend: {
                        ...this.defaultOptions.plugins.legend,
                        position: 'bottom',
                    },
                },
            },
        });
    },

    // Create Prediction Radar Chart
    createPredictionRadar(canvasId) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        this.charts[canvasId] = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Stress', 'Plagues', 'Metabolism', 'Flowering', 'Nutrition', 'Hydration'],
                datasets: [
                    {
                        label: 'Current',
                        data: [10, 2, 80, 1, 75, 68],
                        backgroundColor: 'rgba(6,182,212,0.15)',
                        borderColor: '#06b6d4',
                        borderWidth: 2,
                        pointBackgroundColor: '#06b6d4',
                        pointRadius: 4,
                    },
                    {
                        label: 'Predicted +24h',
                        data: [12, 3, 78, 2, 73, 65],
                        backgroundColor: 'rgba(139,92,246,0.15)',
                        borderColor: '#8b5cf6',
                        borderWidth: 2,
                        pointBackgroundColor: '#8b5cf6',
                        pointRadius: 4,
                        borderDash: [5, 5],
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 1000 },
                plugins: {
                    legend: {
                        labels: { color: '#94a3b8', font: { family: 'Inter' } },
                    },
                },
                scales: {
                    r: {
                        grid: { color: 'rgba(42,58,74,0.5)' },
                        angleLines: { color: 'rgba(42,58,74,0.5)' },
                        ticks: { color: '#64748b', backdropColor: 'transparent', font: { size: 9 } },
                        pointLabels: { color: '#94a3b8', font: { size: 11, family: 'Inter' } },
                    },
                },
            },
        });
    },

    // Create Metabolism Trend Chart
    createMetabolismChart(canvasId) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        const labels = [];
        const metabolismData = [];
        const stressData = [];
        const now = Date.now();

        for (let i = -24; i <= 24; i++) {
            const t = new Date(now + i * 3600000);
            labels.push(t.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
            if (i <= 0) {
                metabolismData.push(78 + Math.sin(i * 0.3) * 5 + Math.random() * 3);
                stressData.push(10 + Math.cos(i * 0.2) * 3 + Math.random() * 2);
            } else {
                metabolismData.push(78 - i * 0.25 + Math.random() * 2);
                stressData.push(10 + i * 0.35 + Math.random() * 2);
            }
        }

        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Metabolism %',
                        data: metabolismData,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16,185,129,0.1)',
                        fill: true,
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                    },
                    {
                        label: 'Stress %',
                        data: stressData,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245,158,11,0.1)',
                        fill: true,
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                    },
                ],
            },
            options: {
                ...this.defaultOptions,
                plugins: {
                    ...this.defaultOptions.plugins,
                    annotation: {
                        annotations: {
                            nowLine: {
                                type: 'line',
                                xMin: 24,
                                xMax: 24,
                                borderColor: '#06b6d4',
                                borderWidth: 2,
                                borderDash: [5, 5],
                                label: {
                                    content: 'NOW',
                                    enabled: true,
                                    position: 'start',
                                },
                            },
                        },
                    },
                },
            },
        });
    },

    // Create Regional Comparison Chart (AlphaEarth)
    createRegionalChart(canvasId) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Your Parcel', 'Region Avg', 'Top 10%', 'Bottom 10%'],
                datasets: [
                    {
                        label: 'NDVI',
                        data: [0.82, 0.71, 0.89, 0.52],
                        backgroundColor: ['#10b981', '#3b82f6', '#8b5cf6', '#ef4444'],
                        borderRadius: 6,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8', font: { size: 10 } },
                    },
                    y: {
                        grid: { color: 'rgba(42,58,74,0.4)' },
                        ticks: { color: '#64748b' },
                        max: 1,
                    },
                },
            },
        });
    },

    // VOC Full Chart
    createVOCFullChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        const compounds = VOC_COMPOUNDS.boschNose.slice(0, 20);
        const labels = compounds.map(c => c.name);
        const values = compounds.map(() => Math.round(Math.random() * 400 + 50));

        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Concentration (ppb)',
                    data: values,
                    backgroundColor: values.map(v => {
                        if (v < 150) return 'rgba(16,185,129,0.7)';
                        if (v < 300) return 'rgba(6,182,212,0.7)';
                        if (v < 400) return 'rgba(245,158,11,0.7)';
                        return 'rgba(239,68,68,0.7)';
                    }),
                    borderRadius: 4,
                }],
            },
            options: {
                ...this.defaultOptions,
                indexAxis: 'y',
                plugins: { legend: { display: false } },
            },
        });
    },

    // Helper: create line dataset
    makeDataset(label, data, color) {
        return {
            label,
            data,
            borderColor: color,
            backgroundColor: color + '15',
            borderWidth: 1.5,
            tension: 0.3,
            pointRadius: 0,
            pointHoverRadius: 3,
            fill: false,
        };
    },

    // Update chart data with animation
    updateChart(chartId, newData) {
        const chart = this.charts[chartId];
        if (!chart) return;

        newData.datasets.forEach((ds, i) => {
            if (chart.data.datasets[i]) {
                chart.data.datasets[i].data = ds.data;
            }
        });
        if (newData.labels) {
            chart.data.labels = newData.labels;
        }
        chart.update('active');
    },
};
