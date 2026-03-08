/* ================================
   VOC Field Intelligence - Main App
   Plant Metabolism Platform
   ================================ */

const VOCApp = {
    currentParcel: 'P1',
    refreshTimers: {},
    sensorData: [],

    // Initialize application
    async init() {
        console.log('[VOCField] Initializing Plant Metabolism Platform...');

        this.setupNavigation();
        this.setupSidebar();
        this.updateDateTime();
        setInterval(() => this.updateDateTime(), 1000);

        // Initial data load
        await this.loadDashboard();

        // Start refresh cycles
        this.startRefreshCycles();

        // Setup animations
        AnimationEngine.setupScrollAnimations();

        console.log('[VOCField] Platform ready.');
    },

    // === Navigation ===
    setupNavigation() {
        document.querySelectorAll('.menu-item').forEach(item => {
            item.addEventListener('click', () => {
                const section = item.dataset.section;
                this.navigateTo(section);
            });
        });
    },

    navigateTo(section) {
        // Update menu
        document.querySelectorAll('.menu-item').forEach(mi => mi.classList.remove('active'));
        document.querySelector(`[data-section="${section}"]`)?.classList.add('active');

        // Update sections
        document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
        const target = document.getElementById(`section-${section}`);
        if (target) {
            target.classList.add('active');
        }

        // Update breadcrumb
        const label = document.querySelector(`[data-section="${section}"] span`)?.textContent || section;
        document.getElementById('current-section').textContent = label;

        // Load section-specific data
        this.loadSection(section);
    },

    async loadSection(section) {
        switch (section) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'voc-monitor':
                this.loadVOCMonitor();
                break;
            case 'sensors':
                this.loadSensors();
                break;
            case 'predictions':
                this.loadPredictions();
                break;
            case 'alerts':
                this.loadAlerts();
                break;
            case 'alphaearth':
                this.loadAlphaEarth();
                break;
            case 'parcels':
                this.loadParcels();
                break;
        }
    },

    // === Sidebar ===
    setupSidebar() {
        const toggle = document.getElementById('sidebar-toggle');
        toggle?.addEventListener('click', () => {
            const sidebar = document.getElementById('sidebar');
            const main = document.getElementById('main-content');
            sidebar.classList.toggle('collapsed');
            main.classList.toggle('sidebar-collapsed');
        });
    },

    // === DateTime ===
    updateDateTime() {
        const now = new Date();
        const dtEl = document.getElementById('datetime');
        if (dtEl) {
            dtEl.textContent = now.toLocaleString('en-US', {
                year: 'numeric', month: 'short', day: 'numeric',
                hour: '2-digit', minute: '2-digit', second: '2-digit',
            });
        }
        const nowTime = document.getElementById('now-time');
        if (nowTime) {
            nowTime.textContent = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        }
    },

    // === Dashboard ===
    async loadDashboard() {
        // Fetch data
        const sensorResult = await APIClient.getSensorData(this.currentParcel);
        this.sensorData = sensorResult.data || [];

        // Render VOC readings
        this.renderVOCReadings();

        // Render charts
        if (this.sensorData.length > 0) {
            ChartManager.createVOCTimeChart('vocTimeChart', this.sensorData);
            ChartManager.createSoilClimateChart('soilClimateChart', this.sensorData);
        }

        // Render timeline
        this.renderTimeline();

        // Render parcel map
        AnimationEngine.drawParcelMap('parcelMapCanvas');

        // Update plant status with animation
        this.updatePlantStatus();
    },

    // Render VOC gas readings grid
    renderVOCReadings() {
        const grid = document.getElementById('voc-readings-grid');
        if (!grid) return;

        grid.innerHTML = VOC_COMPOUNDS.primary.map(voc => {
            const level = getVOCLevel(voc.value, voc.id);
            return `
                <div class="voc-reading-item">
                    <span class="voc-name">${voc.name}:</span>
                    <span class="voc-value ${level}">${voc.value}${voc.unit}</span>
                </div>
            `;
        }).join('');
    },

    // Update plant status values
    updatePlantStatus() {
        const status = APIClient.simulateParcelStatus();

        const updates = [
            { id: 'stress-value', value: Math.round(status.stress), suffix: '%' },
            { id: 'floration-value', value: Math.round(status.floration), suffix: '%' },
            { id: 'plagues-value', value: Math.round(status.plagues), suffix: '%' },
            { id: 'metabolism-value', value: Math.round(status.metabolism), suffix: '%' },
        ];

        updates.forEach(u => {
            const el = document.getElementById(u.id);
            if (el) {
                el.textContent = u.value + u.suffix;
            }
        });

        // Update status bars
        document.querySelectorAll('.status-fill').forEach(bar => {
            const targetWidth = bar.style.width;
            bar.style.setProperty('--target-width', targetWidth);
        });
    },

    // Render prediction timeline
    renderTimeline() {
        const track = document.getElementById('timeline-track');
        if (!track) return;

        const items = [];

        // Past items (5)
        for (let i = 4; i >= 0; i--) {
            const t = new Date(Date.now() - (i + 1) * 3600000);
            items.push({
                type: 'past',
                label: t.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
                index: 4 - i,
            });
        }

        // Now
        items.push({ type: 'now', label: 'NOW', index: 5 });

        // Future items (5)
        for (let i = 0; i < 5; i++) {
            const t = new Date(Date.now() + (i + 1) * 3600000);
            items.push({
                type: 'future',
                label: t.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
                index: i,
            });
        }

        track.innerHTML = items.map((item, idx) => `
            <div class="timeline-item ${item.type}" style="animation-delay: ${idx * 0.05}s">
                <div class="timeline-thumb">
                    <canvas id="thumb-${idx}" width="120" height="80"></canvas>
                </div>
                <div class="timeline-label">${item.label}</div>
            </div>
        `).join('');

        // Draw thumbnails
        items.forEach((item, idx) => {
            const canvas = document.getElementById(`thumb-${idx}`);
            if (canvas) {
                AnimationEngine.drawTimelineThumbnail(canvas, item.type, item.index);
            }
        });
    },

    // === VOC Monitor ===
    loadVOCMonitor() {
        const grid = document.getElementById('voc-full-grid');
        if (!grid) return;

        const allCompounds = [
            ...VOC_COMPOUNDS.boschNose,
            ...VOC_COMPOUNDS.extended,
            ...VOC_COMPOUNDS.agricultural,
        ];

        grid.innerHTML = allCompounds.map(compound => {
            const value = Math.round(Math.random() * 500 + 10);
            const level = value > 400 ? 'high' : (value > 250 ? 'elevated' : '');
            return `
                <div class="voc-full-item ${level}">
                    <div>
                        <div class="vf-name" title="${compound.name}">${compound.name}</div>
                        <div class="vf-formula">${compound.formula || ''}</div>
                    </div>
                    <div class="vf-value">${value} ppb</div>
                </div>
            `;
        }).join('');

        // Full chart
        ChartManager.createVOCFullChart('vocFullChart');
    },

    // === Sensors ===
    loadSensors() {
        const grid = document.getElementById('sensor-grid');
        if (!grid) return;

        grid.innerHTML = CONFIG.SENSOR_NODES.map(sensor => `
            <div class="sensor-card">
                <div class="sensor-card-header">
                    <h4>${sensor.id}</h4>
                    <div class="sensor-status-dot ${sensor.status === 'online' ? '' : 'offline'}"></div>
                </div>
                <div class="sensor-card-body">
                    <div class="sensor-metric">
                        <span class="s-label">Type</span>
                        <span class="s-value" style="color: var(--accent-cyan); font-size: 0.8rem">${sensor.type}</span>
                    </div>
                    <div class="sensor-metric">
                        <span class="s-label">Location</span>
                        <span class="s-value" style="color: var(--text-secondary); font-size: 0.8rem">${sensor.location}</span>
                    </div>
                    <div class="sensor-metric">
                        <span class="s-label">Status</span>
                        <span class="s-value" style="color: ${sensor.status === 'online' ? 'var(--accent-green)' : 'var(--accent-red)'}">
                            ${sensor.status.toUpperCase()}
                        </span>
                    </div>
                    <div class="sensor-metric">
                        <span class="s-label">Last Read</span>
                        <span class="s-value" style="font-size: 0.75rem">${new Date().toLocaleTimeString()}</span>
                    </div>
                </div>
            </div>
        `).join('');
    },

    // === Predictions ===
    loadPredictions() {
        ChartManager.createPredictionRadar('predictionRadar');
        ChartManager.createMetabolismChart('metabolismChart');
    },

    // === Alerts ===
    async loadAlerts() {
        const result = await APIClient.getAlerts();
        const list = document.getElementById('alerts-list');
        if (!list || !result.alerts) return;

        list.innerHTML = result.alerts.map(alert => `
            <div class="alert-item ${alert.type}">
                <div class="alert-icon">
                    <i class="fas fa-${alert.type === 'danger' ? 'exclamation-triangle' : (alert.type === 'warning' ? 'exclamation-circle' : 'info-circle')}"></i>
                </div>
                <div class="alert-content">
                    <div class="alert-title">${alert.title}</div>
                    <div class="alert-desc">${alert.description}</div>
                </div>
                <div class="alert-time">${new Date(alert.timestamp).toLocaleTimeString()}</div>
            </div>
        `).join('');
    },

    // === AlphaEarth ===
    async loadAlphaEarth() {
        AnimationEngine.drawAlphaEarthMap('alphaEarthMap');
        ChartManager.createRegionalChart('regionalChart');

        // AlphaEarth embedding vector display
        const vectorEl = document.getElementById('ae-vector');
        if (vectorEl) {
            const data = await APIClient.getAlphaEarthData(20.6597, -103.3496);
            vectorEl.textContent = `[${data.embedding.join(', ')}]`;
        }
    },

    // === Parcels ===
    loadParcels() {
        const grid = document.getElementById('parcels-grid');
        if (!grid) return;

        grid.innerHTML = CONFIG.PARCELS.map(parcel => {
            const stress = Math.round(Math.random() * 20 + 5);
            const metabolism = Math.round(70 + Math.random() * 15);
            const plagues = Math.round(Math.random() * 5);
            return `
                <div class="parcel-card" onclick="VOCApp.selectParcel('${parcel.id}')">
                    <h3>${parcel.name}</h3>
                    <p class="parcel-crop">${parcel.crop} - ${parcel.area}</p>
                    <div class="parcel-stats">
                        <div class="parcel-mini-stat">
                            <span class="pms-label">Stress</span>
                            <span class="pms-value ${stress > 20 ? 'warning' : 'good'}">${stress}%</span>
                        </div>
                        <div class="parcel-mini-stat">
                            <span class="pms-label">Metabolism</span>
                            <span class="pms-value good">${metabolism}%</span>
                        </div>
                        <div class="parcel-mini-stat">
                            <span class="pms-label">Plagues</span>
                            <span class="pms-value ${plagues > 3 ? 'warning' : 'good'}">${plagues}%</span>
                        </div>
                        <div class="parcel-mini-stat">
                            <span class="pms-label">Sensors</span>
                            <span class="pms-value good">${Math.floor(Math.random() * 6 + 4)}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    },

    selectParcel(parcelId) {
        this.currentParcel = parcelId;
        const parcel = CONFIG.PARCELS.find(p => p.id === parcelId);
        if (parcel) {
            document.getElementById('parcel-number').textContent = parcel.name.split(' ')[1];
            document.getElementById('crop-name').textContent = parcel.crop.toUpperCase();
        }
        this.navigateTo('dashboard');
    },

    // === Refresh Cycles ===
    startRefreshCycles() {
        // VOC data refresh
        this.refreshTimers.voc = setInterval(async () => {
            const result = await APIClient.getSensorData(this.currentParcel);
            if (result.data && result.data.length > 0) {
                this.sensorData = result.data;
                const activeSection = document.querySelector('.content-section.active');
                if (activeSection?.id === 'section-dashboard') {
                    ChartManager.createVOCTimeChart('vocTimeChart', this.sensorData);
                    ChartManager.createSoilClimateChart('soilClimateChart', this.sensorData);
                    this.renderVOCReadings();
                    this.updatePlantStatus();
                }
            }
        }, CONFIG.REFRESH.vocData);

        // Alerts refresh
        this.refreshTimers.alerts = setInterval(async () => {
            const result = await APIClient.getAlerts();
            if (result.alerts) {
                const badge = document.getElementById('alert-count');
                if (badge) badge.textContent = result.alerts.length;
            }
        }, CONFIG.REFRESH.alerts);
    },

    // === Utilities ===
    async testConnection() {
        const url = document.getElementById('api-url')?.value;
        if (!url) return;
        try {
            const response = await fetch(url + '/health');
            if (response.ok) {
                alert('Connection successful!');
            } else {
                alert('Connection failed: ' + response.status);
            }
        } catch {
            alert('Cannot reach backend. Using simulated data.');
        }
    },
};

// Boot
document.addEventListener('DOMContentLoaded', () => {
    VOCApp.init();
});
