/**
 * Dashboard 1: ApexCharts High Fidelity Logic
 * Powered by Nexus Design Tokens
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Panel de Líneas: Volumen Operativo
    const optionsBooking = {
        series: [{
            name: 'Bookings',
            data: []
        }],
        chart: {
            height: 200,
            type: 'line',
            sparkline: { enabled: true },
            animations: { enabled: true, easing: 'easeinout', speed: 1000 }
        },
        dataLabels: { enabled: false },
        stroke: { 
            curve: 'smooth', 
            width: 4, 
            colors: ['#0ea5e9'],
            lineCap: 'round'
        },
        markers: {
            size: 0,
            hover: { size: 6 }
        },
        tooltip: { 
            theme: 'dark', 
            x: { show: false },
            y: { title: { formatter: () => 'Total:' } }
        },
        colors: ['#0ea5e9']
    };

    const chart1 = new ApexCharts(document.querySelector("#bookingSparkline"), optionsBooking);
    if (document.querySelector("#bookingSparkline")) chart1.render();

    // 2. Panel de Columnas: Cumplimiento (On Time)
    const optionsOnTime = {
        series: [{
            name: 'Eficiencia',
            data: []
        }],
        chart: {
            height: 200,
            type: 'bar',
            sparkline: { enabled: false },
            toolbar: { show: false }
        },
        plotOptions: {
            bar: {
                columnWidth: '45%',
                borderRadius: 8,
                colors: {
                    ranges: [{
                        from: 0,
                        to: 100,
                        color: 'rgb(var(--color-primary))'
                    }]
                }
            }
        },
        dataLabels: { enabled: false },
        xaxis: {
            labels: { show: false },
            axisBorder: { show: false },
            axisTicks: { show: false }
        },
        yaxis: {
            labels: {
                show: true,
                style: {
                    colors: 'rgb(var(--color-label-text))',
                    fontSize: '10px',
                    fontWeight: '900'
                }
            }
        },
        grid: {
            show: true,
            borderColor: 'rgba(var(--color-panel-border), 0.3)',
            strokeDashArray: 4
        },
        tooltip: { theme: 'dark' },
        colors: ['rgb(var(--color-primary))']
    };

    const chart2 = new ApexCharts(document.querySelector("#onTimeRadial"), optionsOnTime);
    if (document.querySelector("#onTimeRadial")) chart2.render();
});
