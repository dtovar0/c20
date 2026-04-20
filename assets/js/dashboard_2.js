/**
 * Dashboard 2: ApexCharts Unification Engine
 * High-Density Interactive Monitoring
 */

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

    // 6. Network Throughput (Stepline/Area Pulse)
    const optionsNet = {
        series: [{
            name: 'Traffic',
            data: [10, 41, 35, 51, 49, 62, 69, 91, 148]
        }],
        chart: { type: 'line', height: '100%', toolbar: { show: false }, sparkline: { enabled: true }, animations: { speed: 800 } },
        stroke: { curve: 'stepline', width: 3 },
        colors: ['#3b82f6'],
        markers: { size: 0 },
        tooltip: { theme: 'dark' }
    };
    new ApexCharts(document.querySelector("#networkPulseChartApex"), optionsNet).render();
});
