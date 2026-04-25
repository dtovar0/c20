/**
 * Dashboard 1: ApexCharts High Fidelity Logic
 * Powered by Nexus Design Tokens
 */

document.addEventListener('DOMContentLoaded', () => {
    const getColors = () => {
        const c = window.nexusSettings.statusColors;
        return [c.ok, c.fail, c.force, c.dup];
    };

    // 1. Panel de Líneas: Volumen Operativo
    const optionsVolume = {
        series: [{
            name: 'Registros',
            data: [0, 0, 0, 0]
        }],
        chart: {
            height: 200,
            type: 'bar',
            sparkline: { enabled: false },
            toolbar: { show: false },
            animations: { enabled: true, easing: 'easeinout', speed: 1000 }
        },
        plotOptions: {
            bar: {
                columnWidth: '60%',
                borderRadius: 4,
                distributed: true,
                dataLabels: { position: 'top' }
            }
        },
        dataLabels: {
            enabled: true,
            formatter: (val) => val > 0 ? val : '',
            offsetY: -20,
            style: {
                fontSize: '11px',
                colors: ["rgb(var(--color-label-text))"],
                fontWeight: '900'
            }
        },
        xaxis: {
            categories: ['OK', 'FAIL', 'FORCE', 'Duplicados'],
            labels: {
                style: {
                    colors: 'rgb(var(--color-label-text))',
                    fontSize: '10px',
                    fontWeight: '900'
                }
            },
            axisBorder: { show: true, color: 'rgba(var(--color-panel-border), 0.5)' },
            axisTicks: { show: true, color: 'rgba(var(--color-panel-border), 0.5)' }
        },
        yaxis: { 
            show: true,
            labels: {
                style: {
                    colors: 'rgb(var(--color-label-text))',
                    fontSize: '10px',
                    fontWeight: '900'
                }
            },
            axisBorder: { show: true, color: 'rgba(var(--color-panel-border), 0.5)' }
        },
        grid: { 
            show: true,
            borderColor: 'rgba(var(--color-panel-border), 0.2)',
            strokeDashArray: 4
        },
        legend: { show: false },
        tooltip: { theme: 'dark' },
        colors: getColors()
    };

    const volumeChart = new ApexCharts(document.querySelector("#bookingSparkline"), optionsVolume);
    if (document.querySelector("#bookingSparkline")) volumeChart.render();

    // 2. Panel de Columnas: Detalle de Tareas (Últimas 7)
    const optionsHistory = {
        series: [
            { name: 'OK', data: [0, 0, 0, 0, 0, 0, 0] },
            { name: 'FAIL', data: [0, 0, 0, 0, 0, 0, 0] },
            { name: 'FORCE', data: [0, 0, 0, 0, 0, 0, 0] },
            { name: 'DUP', data: [0, 0, 0, 0, 0, 0, 0] }
        ],
        chart: {
            height: 200,
            type: 'bar',
            stacked: true,
            toolbar: { show: false }
        },
        plotOptions: {
            bar: {
                columnWidth: '40%',
                borderRadius: 4
            }
        },
        dataLabels: { enabled: false },
        stroke: { show: true, width: 2, colors: ['transparent'] },
        xaxis: {
            categories: ['-', '-', '-', '-', '-', '-', '-'],
            labels: {
                style: {
                    colors: 'rgb(var(--color-label-text))',
                    fontSize: '9px',
                    fontWeight: '900'
                }
            },
            axisBorder: { show: true, color: 'rgba(var(--color-panel-border), 0.5)' },
            axisTicks: { show: false }
        },
        yaxis: {
            labels: {
                style: {
                    colors: 'rgb(var(--color-label-text))',
                    fontSize: '10px',
                    fontWeight: '900'
                }
            }
        },
        grid: {
            show: true,
            borderColor: 'rgba(var(--color-panel-border), 0.1)',
            strokeDashArray: 4
        },
        legend: { show: false },
        tooltip: { theme: 'dark' },
        colors: getColors()
    };

    const historyChart = new ApexCharts(document.querySelector("#onTimeRadial"), optionsHistory);
    if (document.querySelector("#onTimeRadial")) historyChart.render();

    // 3. PSX5K Stats Integration
    async function loadPSXStats() {
        try {
            const response = await fetch('/api/psx/stats');
            const data = await response.json();
            
            if (data.status === 'success') {
                const s = data.stats;
                const totalEl = document.getElementById('kpiTotalTasks');
                const pendingEl = document.getElementById('kpiPendingTasks');
                const scheduledEl = document.getElementById('kpiScheduledTasks');
                const activeEl = document.getElementById('kpiActiveTask');
                const volumeEl = document.getElementById('kpiOperationalVolume');
                const efficiencyEl = document.getElementById('kpiEfficiency');

                if (totalEl) totalEl.textContent = s.total.toLocaleString();
                if (pendingEl) pendingEl.textContent = s.pending.toLocaleString();
                if (scheduledEl) scheduledEl.textContent = s.scheduled.toLocaleString();
                if (volumeEl) volumeEl.textContent = s.volume_today.toLocaleString();
                if (efficiencyEl) efficiencyEl.textContent = s.processed_total.toLocaleString();

                // Update Volume Chart Breakdown
                if (volumeChart) {
                    const hasData = s.volume_today > 0;
                    const volumeContent = document.getElementById('volumeContent');
                    const emptyMessage = document.getElementById('noDataVolume');

                    if (hasData) {
                        if (volumeContent) volumeContent.classList.remove('opacity-0', 'pointer-events-none');
                        if (emptyMessage) emptyMessage.classList.add('hidden');
                        volumeChart.updateSeries([{
                            name: 'Registros',
                            data: [s.breakdown.ok, s.breakdown.fail, s.breakdown.force, s.breakdown.dup]
                        }]);
                    } else {
                        if (volumeContent) volumeContent.classList.add('opacity-0', 'pointer-events-none');
                        if (emptyMessage) emptyMessage.classList.remove('hidden');
                    }
                }

                // Update History Chart (Last 7 Tasks)
                if (historyChart) {
                    const hasHistory = s.last_7_tasks && s.last_7_tasks.length > 0;
                    const historyContent = document.getElementById('historyContent');
                    const emptyHistory = document.getElementById('noDataHistory');

                    if (hasHistory) {
                        if (historyContent) historyContent.classList.remove('opacity-0', 'pointer-events-none');
                        if (emptyHistory) emptyHistory.classList.add('hidden');

                        const okData = s.last_7_tasks.map(t => t.ok);
                        const failData = s.last_7_tasks.map(t => t.fail);
                        const forceData = s.last_7_tasks.map(t => t.force);
                        const dupData = s.last_7_tasks.map(t => t.dup);
                        const categories = s.last_7_tasks.map(t => `#${t.id.toString().padStart(4, '0')}`);

                        historyChart.updateOptions({
                            xaxis: { categories: categories }
                        });
                        historyChart.updateSeries([
                            { name: 'OK', data: okData },
                            { name: 'FAIL', data: failData },
                            { name: 'FORCE', data: forceData },
                            { name: 'DUP', data: dupData }
                        ]);
                    } else {
                        if (historyContent) historyContent.classList.add('opacity-0', 'pointer-events-none');
                        if (emptyHistory) emptyHistory.classList.remove('hidden');
                    }
                }

                if (activeEl) {
                    activeEl.textContent = s.active_task !== "NINGUNA" ? `PSX-${s.active_task}` : "NINGUNA";
                    if (s.active_task !== "NINGUNA") {
                        activeEl.classList.add('text-emerald-500');
                    } else {
                        activeEl.classList.remove('text-emerald-500');
                    }
                }
            }
        } catch (error) {
            console.error('Error loading PSX stats:', error);
        }
    }

    // React to settings changes
    document.addEventListener('nexus:settingsUpdated', (e) => {
        const newColors = getColors();
        if (volumeChart) {
            volumeChart.updateOptions({ colors: newColors });
        }
        if (historyChart) {
            historyChart.updateOptions({ colors: newColors });
        }
    });

    loadPSXStats();
    // Auto-refresh stats every 60 seconds
    setInterval(loadPSXStats, 60000);
});
