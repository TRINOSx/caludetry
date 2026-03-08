/* ================================
   Animation Engine
   ================================ */

const AnimationEngine = {
    // Parcel map canvas animation
    drawParcelMap(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;

        // Background - field
        const fieldGrad = ctx.createLinearGradient(0, 0, w, h);
        fieldGrad.addColorStop(0, '#2d5016');
        fieldGrad.addColorStop(0.5, '#3a6b1e');
        fieldGrad.addColorStop(1, '#4a7c2e');
        ctx.fillStyle = fieldGrad;
        ctx.fillRect(0, 0, w, h);

        // Draw field patterns (crop rows)
        ctx.strokeStyle = 'rgba(100,180,50,0.3)';
        ctx.lineWidth = 1;
        for (let i = 0; i < h; i += 8) {
            ctx.beginPath();
            ctx.moveTo(0, i);
            for (let x = 0; x < w; x += 4) {
                ctx.lineTo(x, i + Math.sin(x * 0.05 + i * 0.1) * 2);
            }
            ctx.stroke();
        }

        // Draw parcel boundary
        ctx.strokeStyle = '#06b6d4';
        ctx.lineWidth = 2;
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.moveTo(40, 30);
        ctx.lineTo(240, 20);
        ctx.lineTo(260, 170);
        ctx.lineTo(30, 180);
        ctx.closePath();
        ctx.stroke();

        // Draw yield zones
        // High zone
        ctx.fillStyle = 'rgba(255,255,0,0.15)';
        ctx.beginPath();
        ctx.ellipse(180, 60, 60, 40, 0.2, 0, Math.PI * 2);
        ctx.fill();

        // Low zone
        ctx.fillStyle = 'rgba(0,150,255,0.15)';
        ctx.beginPath();
        ctx.ellipse(100, 130, 70, 45, -0.3, 0, Math.PI * 2);
        ctx.fill();

        // Sensor dots (animated)
        this.animateSensorDots(canvas, ctx);
    },

    // Animate sensor dots on parcel map
    animateSensorDots(canvas, ctx) {
        const sensors = [
            { x: 70, y: 50 },
            { x: 200, y: 45 },
            { x: 140, y: 100 },
            { x: 60, y: 150 },
            { x: 220, y: 140 },
        ];

        let frame = 0;
        const animate = () => {
            // Clear only sensor area (redraw dots)
            sensors.forEach(s => {
                ctx.clearRect(s.x - 10, s.y - 10, 20, 20);

                // Redraw field background for cleared area
                ctx.fillStyle = '#3a6b1e';
                ctx.fillRect(s.x - 10, s.y - 10, 20, 20);

                // Pulse ring
                const pulseSize = 3 + Math.sin(frame * 0.05) * 2;
                ctx.beginPath();
                ctx.arc(s.x, s.y, pulseSize + 3, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(6,182,212,${0.2 + Math.sin(frame * 0.05) * 0.1})`;
                ctx.fill();

                // Sensor dot
                ctx.beginPath();
                ctx.arc(s.x, s.y, 3, 0, Math.PI * 2);
                ctx.fillStyle = '#06b6d4';
                ctx.fill();
            });

            frame++;
            requestAnimationFrame(animate);
        };
        animate();
    },

    // AlphaEarth Map visualization
    drawAlphaEarthMap(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;

        let frame = 0;

        const drawFrame = () => {
            ctx.clearRect(0, 0, w, h);

            // Background grid
            ctx.strokeStyle = 'rgba(6,182,212,0.08)';
            ctx.lineWidth = 0.5;
            const gridSize = 30;
            for (let x = 0; x < w; x += gridSize) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, h);
                ctx.stroke();
            }
            for (let y = 0; y < h; y += gridSize) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(w, y);
                ctx.stroke();
            }

            // Heatmap zones
            const zones = [
                { x: 200, y: 150, r: 120, color: [16, 185, 129] },
                { x: 400, y: 200, r: 100, color: [59, 130, 246] },
                { x: 600, y: 300, r: 80, color: [245, 158, 11] },
                { x: 350, y: 350, r: 90, color: [139, 92, 246] },
                { x: 150, y: 350, r: 70, color: [6, 182, 212] },
            ];

            zones.forEach(zone => {
                const grad = ctx.createRadialGradient(zone.x, zone.y, 0, zone.x, zone.y, zone.r);
                const [r, g, b] = zone.color;
                const pulse = 0.15 + Math.sin(frame * 0.02 + zone.x * 0.01) * 0.05;
                grad.addColorStop(0, `rgba(${r},${g},${b},${pulse})`);
                grad.addColorStop(1, 'transparent');
                ctx.fillStyle = grad;
                ctx.fillRect(0, 0, w, h);
            });

            // Parcel outline
            ctx.strokeStyle = '#06b6d4';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.strokeRect(150, 100, 500, 300);
            ctx.setLineDash([]);

            // Sensor mesh lines
            const meshPoints = [
                [200, 150], [400, 180], [600, 200],
                [180, 300], [350, 280], [550, 320],
                [250, 380], [450, 400], [620, 370],
            ];

            ctx.strokeStyle = 'rgba(6,182,212,0.2)';
            ctx.lineWidth = 0.5;
            meshPoints.forEach((p1, i) => {
                meshPoints.forEach((p2, j) => {
                    if (j > i) {
                        const dist = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
                        if (dist < 250) {
                            ctx.beginPath();
                            ctx.moveTo(p1[0], p1[1]);
                            ctx.lineTo(p2[0], p2[1]);
                            ctx.stroke();
                        }
                    }
                });
            });

            // Sensor nodes
            meshPoints.forEach((p, i) => {
                const pulseR = 4 + Math.sin(frame * 0.04 + i) * 2;
                ctx.beginPath();
                ctx.arc(p[0], p[1], pulseR + 4, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(6,182,212,0.15)';
                ctx.fill();

                ctx.beginPath();
                ctx.arc(p[0], p[1], 4, 0, Math.PI * 2);
                ctx.fillStyle = '#06b6d4';
                ctx.fill();
            });

            // Title
            ctx.fillStyle = '#94a3b8';
            ctx.font = '12px Inter';
            ctx.fillText('AlphaEarth Geospatial Analysis - VOC Heatmap', 160, 90);

            // NDVI colorbar
            const barX = w - 40;
            const barY = 120;
            const barH = 260;
            const colorbar = ctx.createLinearGradient(barX, barY, barX, barY + barH);
            colorbar.addColorStop(0, '#10b981');
            colorbar.addColorStop(0.5, '#f59e0b');
            colorbar.addColorStop(1, '#ef4444');
            ctx.fillStyle = colorbar;
            ctx.fillRect(barX, barY, 15, barH);
            ctx.fillStyle = '#94a3b8';
            ctx.font = '9px JetBrains Mono';
            ctx.fillText('High', barX - 5, barY - 5);
            ctx.fillText('Low', barX - 5, barY + barH + 12);

            frame++;
            requestAnimationFrame(drawFrame);
        };

        drawFrame();
    },

    // Timeline prediction thumbnails
    drawTimelineThumbnail(canvas, type, index) {
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;

        // Field base color with variation
        const greenShift = type === 'past' ? -10 : (type === 'future' ? index * 3 : 0);
        const baseGreen = Math.max(80, Math.min(180, 120 + greenShift));

        ctx.fillStyle = `rgb(40, ${baseGreen}, 30)`;
        ctx.fillRect(0, 0, w, h);

        // Field texture
        ctx.strokeStyle = `rgba(100, ${baseGreen + 40}, 50, 0.3)`;
        ctx.lineWidth = 0.5;
        for (let y = 0; y < h; y += 6) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            for (let x = 0; x < w; x += 3) {
                ctx.lineTo(x, y + Math.sin(x * 0.1 + index) * 1.5);
            }
            ctx.stroke();
        }

        // Stress zones for future predictions
        if (type === 'future') {
            const stressIntensity = Math.min(0.3, index * 0.05);
            ctx.fillStyle = `rgba(245, 158, 11, ${stressIntensity})`;
            ctx.beginPath();
            ctx.ellipse(w * 0.6, h * 0.4, 20 + index * 3, 15 + index * 2, 0, 0, Math.PI * 2);
            ctx.fill();
        }
    },

    // Animate value counter
    animateCounter(element, targetValue, duration = 1000) {
        const start = parseFloat(element.textContent) || 0;
        const startTime = performance.now();
        const isPercent = element.textContent.includes('%');

        const update = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
            const current = start + (targetValue - start) * eased;

            element.textContent = Math.round(current) + (isPercent ? '%' : '');

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        };

        requestAnimationFrame(update);
    },

    // Intersection observer for card entrance animations
    setupScrollAnimations() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.card-enter').forEach(el => {
            observer.observe(el);
        });
    },

    // Data update flash animation
    flashUpdate(element) {
        element.classList.remove('value-update');
        void element.offsetWidth; // force reflow
        element.classList.add('value-update');
    },
};
