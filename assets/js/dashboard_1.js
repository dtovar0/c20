/**
 * Dashboard 1: ApexCharts High Fidelity Logic
 * Powered by Nexus Design Tokens
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Booking Count Sparkline (Area Chart)
    const optionsBooking = {
        series: [{
            name: 'Bookings',
            data: [31, 40, 28, 51, 42, 109, 100]
        }],
        chart: {
            height: 160,
            type: 'area',
            sparkline: { enabled: true },
            animations: { enabled: true, easing: 'easeinout', speed: 800 }
        },
        dataLabels: { enabled: false },
        stroke: { curve: 'smooth', width: 3, colors: ['#ffffff'] },
        fill: {
            type: 'gradient',
            gradient: {
                shadeIntensity: 1,
                opacityFrom: 0.4,
                opacityTo: 0,
                stops: [0, 90, 100]
            }
        },
        tooltip: { theme: 'dark', x: { show: false } },
        colors: ['#ffffff']
    };

    new ApexCharts(document.querySelector("#bookingSparkline"), optionsBooking).render();

    // 2. On Time Radial Bar (Performance A)
    const optionsOnTime = {
        series: [39],
        chart: {
            height: 240,
            type: 'radialBar',
            sparkline: { enabled: true }
        },
        plotOptions: {
            radialBar: {
                hollow: { size: '65%' },
                track: { background: 'rgba(59, 130, 246, 0.1)' },
                dataLabels: {
                    name: { show: false },
                    value: {
                        offsetY: 10,
                        fontSize: '28px',
                        fontWeight: '900',
                        color: '#1e293b',
                        formatter: function (val) { return val + "%" }
                    }
                }
            }
        },
        colors: ['#3b82f6'], // Primary
        labels: ['On Time'],
    };

    new ApexCharts(document.querySelector("#onTimeRadial"), optionsOnTime).render();

    // 3. Late Delivery Radial Bar (Performance B)
    const optionsLate = {
        series: [61],
        chart: {
            height: 240,
            type: 'radialBar',
            sparkline: { enabled: true }
        },
        plotOptions: {
            radialBar: {
                hollow: { size: '65%' },
                track: { background: 'rgba(251, 167, 114, 0.1)' },
                dataLabels: {
                    name: { show: false },
                    value: {
                        offsetY: 10,
                        fontSize: '28px',
                        fontWeight: '900',
                        color: '#1e293b',
                        formatter: function (val) { return val + "%" }
                    }
                }
            }
        },
        colors: ['#fba772'], // Peach Accent
        labels: ['Late Delivery'],
    };

    new ApexCharts(document.querySelector("#lateDeliveryRadial"), optionsLate).render();
});
