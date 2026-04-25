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
            
            window.history.pushState({page: page}, `Page ${page}`, `?page=${page}`);
        }
    } catch (err) {
        console.error("Error updating activity:", err);
    } finally {
        container.style.opacity = '1';
        container.style.pointerEvents = 'auto';
    }
}

document.addEventListener('DOMContentLoaded', () => {

    // 1. Mirror Status (Stacked Horizontal Bars)
    const optionsMirror = {
        series: [
            { name: 'Sync', data: [44, 55, 41, 37] },
            { name: 'Queue', data: [53, 32, 33, 52] },
            { name: 'Error', data: [12, 17, 11, 9] }
        ],
        chart: {
            type: 'bar',
            height: '100%',
            stacked: true,
            stackType: '100%',
            toolbar: { show: false },
            sparkline: { enabled: true }
        },
        plotOptions: {
            bar: { horizontal: true, barHeight: '60%', borderRadius: 2 }
        },
        colors: ['#3b82f6', '#8b5cf6', '#fba772'],
        tooltip: { theme: 'dark', y: { formatter: (val) => val + "%" } },
        xaxis: { categories: ['West', 'East', 'Cent', 'South'] }
    };
    new ApexCharts(document.querySelector("#mirrorChartApex"), optionsMirror).render();

    // 2. Predictive Demand (Vertical Bars)
    const optionsDemand = {
        series: [{
            name: 'Demand',
            data: [400, 430, 448, 470, 540, 580, 690]
        }],
        chart: { type: 'bar', height: '100%', toolbar: { show: false }, sparkline: { enabled: true } },
        plotOptions: {
            bar: { borderRadius: 4, columnWidth: '60%', distributed: true }
        },
        colors: ['#3b82f620', '#3b82f620', '#3b82f620', '#3b82f620', '#3b82f620', '#3b82f620', '#3b82f6'],
        dataLabels: { enabled: false },
        tooltip: { theme: 'dark' }
    };
    new ApexCharts(document.querySelector("#demandChartApex"), optionsDemand).render();

    // 4. AI Activity Pulse (Spline Area)
    const optionsAi = {
        series: [{
            name: 'Activity',
            data: [31, 40, 28, 51, 42, 109, 100]
        }],
        chart: { type: 'area', height: '100%', toolbar: { show: false }, sparkline: { enabled: true } },
        stroke: { curve: 'smooth', width: 3 },
        fill: {
            type: 'gradient',
            gradient: { shadeIntensity: 1, opacityFrom: 0.5, opacityTo: 0.1 }
        },
        colors: ['#10b981'],
        tooltip: { theme: 'dark' }
    };
    new ApexCharts(document.querySelector("#aiPulseChartApex"), optionsAi).render();

    // 5. CPU Engine Load (Donut)
    const optionsCpu = {
        series: [44, 55, 41, 17],
        chart: { type: 'donut', height: '100%', sparkline: { enabled: true } },
        plotOptions: {
            pie: {
                donut: { size: '75%' },
                expandOnClick: true,
            }
        },
        colors: ['#a78bfa', '#7c3aed', '#4c1d95', '#2e1065'],
        stroke: { show: false },
        tooltip: { theme: 'dark' },
        legend: { show: false }
    };
    new ApexCharts(document.querySelector("#cpuEngineChartApex"), optionsCpu).render();

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
                const queueEl = document.getElementById('globalKpiQueue');
                const activeEl = document.getElementById('globalKpiActive');
                
                if (usersEl) usersEl.textContent = s.users.toLocaleString();
                if (tasksEl) tasksEl.textContent = s.tasks.toLocaleString();
                if (pendingEl) pendingEl.textContent = s.pending.toLocaleString();
                if (queueEl) queueEl.textContent = s.queue.toLocaleString();
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
