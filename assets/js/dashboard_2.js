/**
 * Dashboard 2: ApexCharts Unification Engine
 * High-Density Interactive Monitoring
 */

async function changeActivityPage(page) {
    const container = document.getElementById('activityLogsContainer');
    if (!container) return;

    container.style.opacity = '0.5';
    container.style.pointerEvents = 'none';

    try {
        const response = await fetch(`/dashboard-2?page=${page}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        
        if (response.ok) {
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            const newLogs = doc.getElementById('activityLogsContainer');
            const newFooter = doc.getElementById('activityPaginationFooter');
            
            if (newLogs) container.innerHTML = newLogs.innerHTML;
            const footer = document.getElementById('activityPaginationFooter');
            if (footer && newFooter) footer.innerHTML = newFooter.innerHTML;
        }
    } catch (err) {
        console.error("Error updating activity:", err);
    } finally {
        container.style.opacity = '1';
        container.style.pointerEvents = 'auto';
    }
}

document.addEventListener('DOMContentLoaded', () => {

    // 1. Tareas por Usuario (Top 5 Stacked Columns)
    const optionsMirror = {
        series: [
            { name: 'Completadas', data: [] },
            { name: 'Con Errores', data: [] },
            { name: 'Pendiente', data: [] },
            { name: 'Programada', data: [] },
            { name: 'Activa', data: [] }
        ],
        chart: {
            type: 'bar',
            height: '100%',
            stacked: true,
            toolbar: { show: false },
            sparkline: { enabled: false }
        },
        plotOptions: {
            bar: {
                borderRadius: 4,
                columnWidth: '40%',
                horizontal: false,
            }
        },
        colors: [
            window.nexusSettings?.statusColors?.ok || '#22c55e', // Green
            window.nexusSettings?.statusColors?.fail || '#ef4444', // Red
            window.nexusSettings?.statusColors?.dup || '#f59e0b', // Amber
            '#6366f1', // Indigo
            window.nexusSettings?.statusColors?.force || '#3b82f6' // Blue
        ],
        dataLabels: { enabled: false },
        xaxis: {
            categories: [],
            labels: { 
                show: true,
                style: { colors: '#94a3b8', fontSize: '9px', fontWeight: 700 } 
            },
            axisBorder: { show: false },
            axisTicks: { show: false }
        },
        yaxis: { 
            show: true,
            forceNiceScale: true,
            labels: { 
                show: true,
                style: { colors: '#94a3b8', fontSize: '9px', fontWeight: 700 },
                formatter: (val) => Math.round(val)
            },
            axisBorder: { show: false }
        },
        grid: { 
            show: true,
            borderColor: 'rgba(148, 163, 184, 0.1)',
            strokeDashArray: 4,
            xaxis: { lines: { show: false } },
            yaxis: { lines: { show: true } }
        },
        legend: { show: false },
        tooltip: { 
            theme: 'dark', 
            shared: true,
            intersect: false,
            followCursor: true,
            custom: function({ series, seriesIndex, dataPointIndex, w }) {
                const colors = w.config.colors;
                const cat = w.globals.labels[dataPointIndex];
                
                let html = `<div class="bg-panel-fill/95 backdrop-blur-xl border border-white/10 p-4 rounded-xl shadow-2xl min-w-[180px]">`;
                html += `<div class="text-[10px] font-black uppercase tracking-wider text-label/40 mb-3 border-b border-white/5 pb-2">${cat}</div>`;
                html += `<div class="space-y-2">`;
                
                series.forEach((s, idx) => {
                    const val = s[dataPointIndex];
                    const name = w.globals.seriesNames[idx];
                    const color = colors[idx];
                    html += `
                        <div class="flex items-center justify-between gap-4">
                            <div class="flex items-center gap-2">
                                <div class="w-2.5 h-2.5 rounded-full" style="background-color: ${color}; box-shadow: 0 0 10px ${color}88"></div>
                                <span class="text-[11px] font-bold text-label/70">${name}</span>
                            </div>
                            <span class="text-[12px] font-black text-label">${val}</span>
                        </div>
                    `;
                });
                
                html += `</div></div>`;
                return html;
            }
        }
    };
    mirrorChartApex = new ApexCharts(document.querySelector("#mirrorChartApex"), optionsMirror);
    mirrorChartApex.render();

    // 2. Tareas Diarias (Line/Point Chart por día)
    const optionsDemand = {
        series: [{
            name: 'Tareas',
            data: []
        }],
        chart: { 
            type: 'line', 
            height: '100%', 
            toolbar: { show: false }, 
            sparkline: { enabled: false },
            zoom: { enabled: false }
        },
        stroke: { curve: 'smooth', width: 4 },
        markers: {
            size: 5,
            colors: ['#fff'],
            strokeColors: window.nexusSettings?.statusColors?.force || '#8b5cf6',
            strokeWidth: 3,
            hover: { size: 7 }
        },
        colors: [window.nexusSettings?.statusColors?.force || '#8b5cf6'],
        xaxis: {
            categories: [],
            labels: { 
                show: true,
                style: { colors: '#94a3b8', fontSize: '9px', fontWeight: 700 } 
            },
            axisBorder: { show: false },
            axisTicks: { show: false }
        },
        yaxis: { 
            show: true,
            forceNiceScale: true,
            labels: { 
                show: true,
                style: { colors: '#94a3b8', fontSize: '9px', fontWeight: 700 },
                formatter: (val) => Math.round(val)
            }
        },
        grid: { 
            show: true,
            borderColor: 'rgba(148, 163, 184, 0.1)',
            strokeDashArray: 4,
            yaxis: { lines: { show: true } }
        },
        tooltip: { 
            theme: 'dark', 
            shared: true,
            intersect: false,
            followCursor: true,
            custom: function({ series, seriesIndex, dataPointIndex, w }) {
                const color = (w.config.colors && w.config.colors[0]) ? w.config.colors[0] : '#6366f1';
                const cat = (w.globals.categoryLabels && w.globals.categoryLabels[dataPointIndex]) ? w.globals.categoryLabels[dataPointIndex] : (w.globals.labels ? w.globals.labels[dataPointIndex] : dataPointIndex);
                const val = (series[0] && series[0][dataPointIndex] !== undefined) ? series[0][dataPointIndex] : 0;
                
                return `
                    <div class="bg-panel-fill/95 backdrop-blur-xl border border-white/10 p-4 rounded-xl shadow-2xl min-w-[150px]">
                        <div class="text-[10px] font-black uppercase tracking-wider text-label/40 mb-2 border-b border-white/5 pb-1">${cat}</div>
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <div class="w-2.5 h-2.5 rounded-full" style="background-color: ${color}; box-shadow: 0 0 10px ${color}88"></div>
                                <span class="text-[11px] font-bold text-label/70">Tareas</span>
                            </div>
                            <span class="text-[12px] font-black text-label">${val}</span>
                        </div>
                    </div>
                `;
            }
        }
    };
    demandChartApex = new ApexCharts(document.querySelector("#demandChartApex"), optionsDemand);
    demandChartApex.render();

    // 4. Análisis Diario (Stacked Columns por día)
    const optionsAi = {
        series: [
            { name: 'OK', data: [] },
            { name: 'Fail', data: [] },
            { name: 'Force', data: [] },
            { name: 'Dup', data: [] }
        ],
        chart: { 
            type: 'bar', 
            height: '100%', 
            stacked: true,
            toolbar: { show: false }, 
            sparkline: { enabled: false } 
        },
        plotOptions: {
            bar: {
                borderRadius: 4,
                columnWidth: '50%',
                horizontal: false
            }
        },
        colors: [
            window.nexusSettings?.statusColors?.ok || '#22c55e', 
            window.nexusSettings?.statusColors?.fail || '#ef4444', 
            window.nexusSettings?.statusColors?.force || '#8b5cf6', 
            window.nexusSettings?.statusColors?.dup || '#f59e0b'
        ],
        dataLabels: { enabled: false },
        xaxis: {
            categories: [],
            labels: { 
                show: true,
                style: { colors: '#94a3b8', fontSize: '9px', fontWeight: 700 } 
            },
            axisBorder: { show: false },
            axisTicks: { show: false }
        },
        yaxis: { 
            show: true,
            forceNiceScale: true,
            labels: { 
                show: true,
                style: { colors: '#94a3b8', fontSize: '9px', fontWeight: 700 },
                formatter: (val) => Math.round(val)
            }
        },
        grid: { 
            show: true,
            borderColor: 'rgba(148, 163, 184, 0.1)',
            strokeDashArray: 4,
            yaxis: { lines: { show: true } }
        },
        tooltip: { 
            theme: 'dark', 
            shared: true,
            intersect: false,
            followCursor: true,
            custom: function({ series, seriesIndex, dataPointIndex, w }) {
                const colors = w.config.colors;
                const categories = w.globals.labels;
                const cat = categories[dataPointIndex];
                
                let html = `<div class="bg-panel-fill/95 backdrop-blur-xl border border-white/10 p-4 rounded-xl shadow-2xl min-w-[180px]">`;
                html += `<div class="text-[10px] font-black uppercase tracking-wider text-label/40 mb-3 border-b border-white/5 pb-2">${cat}</div>`;
                html += `<div class="space-y-2">`;
                
                series.forEach((s, idx) => {
                    const val = s[dataPointIndex];
                    const name = w.globals.seriesNames[idx];
                    const color = colors[idx];
                    html += `
                        <div class="flex items-center justify-between gap-4">
                            <div class="flex items-center gap-2">
                                <div class="w-2 h-2 rounded-full shadow-[0_0_8px]" style="background-color: ${color}; box-shadow: 0 0 8px ${color}66"></div>
                                <span class="text-[11px] font-bold text-label/70">${name}</span>
                            </div>
                            <span class="text-[12px] font-black text-label">${val}</span>
                        </div>
                    `;
                });
                
                html += `</div></div>`;
                return html;
            }
        },
        legend: { show: false }
    };
    aiPulseChartApex = new ApexCharts(document.querySelector("#aiPulseChartApex"), optionsAi);
    aiPulseChartApex.render();

    // 5. Monitoreo de tareas (Donut por Hoy)
    const optionsCpu = {
        series: [0, 0, 0, 0],
        chart: { 
            type: 'donut', 
            height: '100%', 
            sparkline: { enabled: true } 
        },
        labels: ['Completadas', 'Activas', 'Pendientes', 'Error'],
        plotOptions: {
            pie: { 
                donut: { 
                    size: '75%',
                    labels: {
                        show: true,
                        total: {
                            show: true,
                            label: 'HOY',
                            fontSize: '10px',
                            fontWeight: 900,
                            color: '#94a3b8'
                        }
                    }
                } 
            }
        },
        colors: [
            window.nexusSettings?.statusColors?.ok || '#22c55e', 
            window.nexusSettings?.statusColors?.force || '#3b82f6', 
            window.nexusSettings?.statusColors?.dup || '#f59e0b', 
            window.nexusSettings?.statusColors?.fail || '#ef4444'
        ],
        stroke: { show: false },
        dataLabels: { enabled: false },
        tooltip: { theme: 'dark' },
        legend: { show: false }
    };
    cpuEngineChartApex = new ApexCharts(document.querySelector("#cpuEngineChartApex"), optionsCpu);
    cpuEngineChartApex.render();

    // 7. Global Admin Stats Integration
    async function loadGlobalStats() {
        try {
            const response = await fetch('/api/psx/stats/global');
            const data = await response.json();
            
            if (data.status === 'success') {
                const s = data.stats;
                const usersEl = document.getElementById('globalKpiUsers');
                const tasksEl = document.getElementById('globalKpiTasks');
                const pendingEl = document.getElementById('globalKpiPending');
                const scheduledEl = document.getElementById('globalKpiScheduled');
                const queueEl = document.getElementById('globalKpiQueue');
                const activeEl = document.getElementById('globalKpiActive');
                
                if (usersEl) usersEl.textContent = s.users.toLocaleString();
                if (tasksEl) tasksEl.textContent = s.tasks.toLocaleString();
                if (pendingEl) pendingEl.textContent = s.pending.toLocaleString();
                if (scheduledEl) scheduledEl.textContent = s.scheduled.toLocaleString();
                if (queueEl) queueEl.textContent = s.queue.toLocaleString();
                
                // Sync Top Users Chart (Stacked Breakdown)
                if (data.stats.top_users && mirrorChartApex) {
                    const u = data.stats.top_users;
                    mirrorChartApex.updateSeries([
                        { name: 'Completadas', data: u.ok },
                        { name: 'Con Errores', data: u.fail },
                        { name: 'Pendiente', data: u.pending },
                        { name: 'Programada', data: u.scheduled },
                        { name: 'Activa', data: u.active }
                    ], true);
                    mirrorChartApex.updateOptions({
                        xaxis: { categories: u.users },
                        yaxis: { show: true, forceNiceScale: true }
                    });
                }

                // Sync Daily Operations Trend
                if (data.stats.daily_tasks && demandChartApex) {
                    const days = data.stats.daily_tasks.map(d => d.day);
                    const counts = data.stats.daily_tasks.map(d => d.count);
                    demandChartApex.updateOptions({
                        series: [{
                            name: 'Operaciones',
                            data: counts
                        }],
                        xaxis: { categories: days },
                        yaxis: { show: true, forceNiceScale: true }
                    }, false, true); // true to redraw
                }

                // Sync Daily Analysis (Stacked Status)
                if (data.stats.analysis_daily && aiPulseChartApex) {
                    const an = data.stats.analysis_daily;
                    aiPulseChartApex.updateOptions({
                        series: [
                            { name: 'OK', data: an.ok },
                            { name: 'Error', data: an.fail },
                            { name: 'Force', data: an.force },
                            { name: 'Dup', data: an.dup }
                        ],
                        xaxis: { categories: an.days },
                        yaxis: { show: true, forceNiceScale: true }
                    }, false, true);
                }

                // Sync Today Status Distribution (Donut)
                if (data.stats.today_stats && cpuEngineChartApex) {
                    const totalToday = data.stats.today_stats.reduce((a, b) => a + b, 0);
                    const emptyEl = document.getElementById('cpuEmptyState');
                    const chartEl = document.getElementById('cpuEngineChartApex');
                    
                    if (totalToday === 0) {
                        if (emptyEl) emptyEl.classList.remove('hidden');
                        if (chartEl) chartEl.style.opacity = '0';
                    } else {
                        if (emptyEl) emptyEl.classList.add('hidden');
                        if (chartEl) chartEl.style.opacity = '1';
                        cpuEngineChartApex.updateSeries(data.stats.today_stats, true);
                    }
                }

                if (activeEl) {
                    if (s.active_id) {
                        activeEl.textContent = `${s.active_name}: PSX-${s.active_id}`;
                        activeEl.classList.add('text-emerald-500');
                    } else {
                        activeEl.textContent = "NINGUNA";
                        activeEl.classList.remove('text-emerald-500');
                    }
                }
            }
        } catch (error) {
            console.error('Error loading global stats:', error);
        }
    }

    loadGlobalStats();
    // Refresh every 60 seconds
    setInterval(loadGlobalStats, 60000);
});
