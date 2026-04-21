/**
 * MODULE: PSX5K Operational Terminal Controller
 * Dedicated logic for rendering PSX5K tasks with 7-column layout.
 */

// Global Configuration
const tableRecordsLimit = 8;
let psxData = [];
let filteredData = [];
let currentPage = 1;

/**
 * MOCK DATA GENERATOR (Operational Context)
 */
const mockPsxData = [
    { id: 'PSX-9421', operacion: 'add', estado: 'running', inicio: '2026-04-21 11:45:02', fin: '-', resultado: 'PROCESANDO' },
    { id: 'PSX-9388', operacion: 'delete', estado: 'finished', inicio: '2026-04-21 10:30:15', fin: '2026-04-21 10:35:42', resultado: 'EXITO' },
    { id: 'PSX-9210', operacion: 'add', estado: 'pending', inicio: '2026-04-21 12:00:00', fin: '-', resultado: 'EN COLA' },
    { id: 'PSX-9105', operacion: 'add', estado: 'finished', inicio: '2026-04-21 09:00:00', fin: '2026-04-21 09:12:10', resultado: 'EXITO' },
    { id: 'PSX-8992', operacion: 'delete', estado: 'finished', inicio: '2026-04-21 08:30:00', fin: '2026-04-21 08:35:00', resultado: 'FALLIDO' }
];

/**
 * GENERA UNA BARRA DE PROGRESO TERMINAL (Mainframe Style)
 */
function generateSegmentedBars() {
    const totalSegments = 15;
    const filledSegments = Math.floor(Math.random() * 8) + 5; // Simulación de carga
    let barsHtml = '';
    
    for (let i = 0; i < totalSegments; i++) {
        const isFilled = i < filledSegments;
        const color = isFilled ? 'rgb(var(--color-primary))' : 'rgb(var(--color-panel-border))';
        const opacity = isFilled ? '1' : '0.2';
        barsHtml += `<rect x="${i * 6}" y="0" width="4" height="12" rx="0.5" fill="${color}" fill-opacity="${opacity}" />`;
    }

    return `
        <div class="flex items-center justify-center font-mono text-label/40 gap-1 select-none">
            <span class="text-xs">[</span>
            <svg class="w-[90px] h-3" viewBox="0 0 90 12">
                ${barsHtml}
            </svg>
            <span class="text-xs">]</span>
        </div>
    `;
}

/**
 * Renders the table with exactly 10 rows (8 Columns Standard for PSX)
 */
function renderNexusTable() {
    const tbody = document.getElementById('auditTableBody');
    if (!tbody) return;

    const start = (currentPage - 1) * tableRecordsLimit;
    const end = start + tableRecordsLimit;
    const pageData = filteredData.slice(start, end);
    
    let html = '';

    // 1. Render Real Data Rows
    pageData.forEach(row => {
        const statusBadge = row.estado === 'running' ? 'badge-running' : 
                          row.estado === 'finished' ? 'badge-finished' : 'badge-pending';
        const opBadge = row.operacion === 'add' ? 'badge-op-add' : 'badge-op-delete';
        const opLabel = row.operacion === 'add' ? 'AGREGAR' : 'BORRAR';
        const statusLabel = row.estado === 'running' ? 'EJECUTANDO' : 
                           row.estado === 'finished' ? 'TERMINADO' : 'PENDIENTE';

        html += `
            <tr class="group hover:bg-primary/5 transition-all duration-300">
                <td class="px-5 py-0 h-[56px] text-[11px] font-black text-primary/80 bg-surface-container/30 border-y border-l border-panel-border rounded-l-2xl group-hover:border-primary/30 transition-colors">
                    <div class="flex items-center h-full">${row.id || 'N/A'}</div>
                </td>
                <td class="px-5 py-0 h-[56px] bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    <div class="flex items-center h-full"><div class="badge-nexus ${opBadge}">${row.action || opLabel}</div></div>
                </td>
                <td class="px-5 py-0 h-[56px] bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    <div class="flex items-center h-full"><div class="badge-nexus ${statusBadge}">${statusLabel}</div></div>
                </td>
                <td class="px-5 py-0 h-[56px] text-[10px] font-mono font-bold text-label/60 bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    <div class="flex items-center h-full">${row.inicio || row.time}</div>
                </td>
                <td class="px-5 py-0 h-[56px] text-[10px] font-mono font-bold text-label/60 bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    <div class="flex items-center h-full">${row.fin || '-'}</div>
                </td>
                <td class="px-5 py-0 h-[56px] text-[10px] font-black uppercase text-label/60 bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    <div class="flex items-center h-full">${row.resultado || row.status}</div>
                </td>
                <td class="px-5 py-0 h-[56px] bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors text-center">
                    <div class="flex items-center justify-center h-full">${generateSegmentedBars()}</div>
                </td>
                <td class="px-5 py-0 h-[56px] bg-surface-container/30 rounded-r-2xl border-y border-r border-panel-border text-center group-hover:border-primary/30 transition-colors">
                    <div class="flex items-center justify-center h-full">
                        <button class="p-2 hover:bg-primary/10 text-primary/40 hover:text-primary rounded-xl transition-all active:scale-90" title="Ver Detalles">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    // 2. Ghost Row Complementation (8 Columns)
    const ghostRowsCount = tableRecordsLimit - pageData.length;
    for (let i = 0; i < ghostRowsCount; i++) {
        html += `
            <tr class="animate-pulse pointer-events-none select-none opacity-40">
                <td class="px-5 py-0 h-[56px] bg-surface-container/5 border-y border-l border-panel-border/10 rounded-l-2xl">
                    <div class="flex items-center h-full mx-auto"><div class="h-2 w-12 bg-label/10 rounded-full"></div></div>
                </td>
                <td class="px-5 py-0 h-[56px] bg-surface-container/5 border-y border-panel-border/10">
                    <div class="flex items-center h-full"><div class="h-2 w-full bg-label/5 rounded-full"></div></div>
                </td>
                <td class="px-5 py-0 h-[56px] bg-surface-container/5 border-y border-panel-border/10">
                    <div class="flex items-center h-full"><div class="h-2 w-full bg-label/5 rounded-full"></div></div>
                </td>
                <td class="px-5 py-0 h-[56px] bg-surface-container/5 border-y border-panel-border/10">
                    <div class="flex items-center h-full"><div class="h-2 w-full bg-label/5 rounded-full"></div></div>
                </td>
                <td class="px-5 py-0 h-[56px] bg-surface-container/5 border-y border-panel-border/10">
                    <div class="flex items-center h-full"><div class="h-2 w-full bg-label/5 rounded-full"></div></div>
                </td>
                <td class="px-5 py-0 h-[56px] bg-surface-container/5 border-y border-panel-border/10">
                    <div class="flex items-center h-full"><div class="h-2 w-full bg-label/5 rounded-full"></div></div>
                </td>
                <td class="px-5 py-0 h-[56px] bg-surface-container/5 border-y border-panel-border/10">
                    <div class="flex items-center h-full"><div class="h-2 w-full bg-label/5 rounded-full"></div></div>
                </td>
                <td class="px-5 py-0 h-[56px] bg-surface-container/5 border-y border-r border-panel-border/10 rounded-r-2xl text-center">
                    <div class="flex items-center justify-center h-full"><div class="h-2 w-full bg-label/5 rounded-full mx-2"></div></div>
                </td>
            </tr>

        `;
    }

    tbody.innerHTML = html;
    updatePaginationUI();
}

/**
 * Pagination Controls UI Sync
 */
function updatePaginationUI() {
    const infoEl = document.getElementById('paginationInfo');
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');

    if (!infoEl || !prevBtn || !nextBtn) return;

    const total = filteredData.length;
    const start = total === 0 ? 0 : (currentPage - 1) * tableRecordsLimit + 1;
    const end = Math.min(currentPage * tableRecordsLimit, total);

    infoEl.innerText = `Mostrando ${start}-${end} de ${total} registros`;
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = end >= total;
}

/**
 * INITIALIZATION
 */
document.addEventListener('DOMContentLoaded', () => {
    psxData = [...mockPsxData];
    filteredData = [...psxData];

    // Search Integration
    const searchInput = document.getElementById('auditSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            filteredData = psxData.filter(item =>
                Object.values(item).some(val => String(val).toLowerCase().includes(term))
            );
            currentPage = 1;
            renderNexusTable();
        });
    }

    // Actions Listeners
    const refreshBtn = document.getElementById('refreshAudit');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => renderNexusTable());
    }

    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');

    if (prevBtn) prevBtn.addEventListener('click', () => { if (currentPage > 1) { currentPage--; renderNexusTable(); } });
    if (nextBtn) nextBtn.addEventListener('click', () => { if (currentPage * tableRecordsLimit < filteredData.length) { currentPage++; renderNexusTable(); } });

    renderNexusTable();
});
