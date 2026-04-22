/**
 * MODULE: PSX5K Operational Terminal Controller
 * Dedicated logic for rendering PSX5K tasks with 7-column layout.
 */

// Global Configuration
const tableRecordsLimit = 7;
let psxData = [];
let filteredData = [];
let currentPage = 1;

/**
 * MOCK DATA GENERATOR (Operational Context)
 */
const mockPsxData = [];

/**
 * GENERA UNA GRÁFICA DE SEGMENTOS REAL (Basada en psx5k_details)
 */
function generateTaskGraphic(resumen) {
    if (!resumen || resumen.total === 0) {
        return `<div class="h-1.5 w-24 bg-panel-border/20 rounded-full"></div>`;
    }

    const okPct = (resumen.ok / resumen.total) * 100;
    const failPct = (resumen.fail / resumen.total) * 100;
    const forcePct = (resumen.force_ok / resumen.total) * 100;
    const pendingPct = Math.max(0, 100 - (okPct + failPct + forcePct));

    return `
        <div class="flex flex-col gap-1 w-full max-w-[120px] mx-auto">
            <div class="h-2 w-full bg-panel-border/20 rounded-full overflow-hidden flex shadow-inner">
                <div class="h-full bg-primary transition-all duration-500" style="width: ${okPct}%" title="OK: ${resumen.ok}"></div>
                <div class="h-full bg-rose-500 transition-all duration-500" style="width: ${failPct}%" title="FAIL: ${resumen.fail}"></div>
                <div class="h-full bg-violet-500 transition-all duration-500" style="width: ${forcePct}%" title="FORCED: ${resumen.force_ok}"></div>
                <div class="h-full bg-transparent" style="width: ${pendingPct}%"></div>
            </div>
            <div class="flex justify-between items-center px-0.5">
                <span class="text-[8px] font-black text-primary/60">${Math.round(okPct + failPct + forcePct)}%</span>
                <span class="text-[8px] font-bold text-label/30">${resumen.ok + resumen.fail + resumen.force_ok}/${resumen.total}</span>
            </div>
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
        // Mapping backend states to frontend badges
        const statusBadge = row.estado === 'Ejecutando' ? 'badge-running' : 
                          row.estado === 'Terminada' ? 'badge-finished' : 
                          row.estado === 'Programada' ? 'badge-scheduled' : 'badge-pending';
        
        const opBadge = row.tarea === 'add' ? 'badge-op-add' : 'badge-op-delete';
        const opLabel = row.tarea === 'add' ? 'AGREGAR' : 'BORRAR';
        const statusLabel = row.estado.toUpperCase();

        html += `
            <tr class="group hover:bg-primary/5 transition-all duration-300">
                <td class="px-5 py-0 h-[56px] text-[11px] font-black text-primary/80 bg-surface-container/30 border-y border-l border-panel-border rounded-l-2xl group-hover:border-primary/30 transition-colors">
                    <div class="flex items-center h-full">#${String(row.id).padStart(5, '0')}</div>
                </td>
                <td class="px-5 py-0 h-[56px] bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    <div class="flex items-center h-full"><div class="badge-nexus ${opBadge}">${opLabel}</div></div>
                </td>
                <td class="px-5 py-0 h-[56px] bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    <div class="flex items-center h-full"><div class="badge-nexus ${statusBadge}">${statusLabel}</div></div>
                </td>
                <td class="px-5 py-0 h-[56px] text-[10px] font-mono font-bold text-label/60 bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    <div class="flex items-center h-full text-primary/70">${row.fecha_inicio ? row.fecha_inicio.replace('T', ' ') : 'PENDIENTE'}</div>
                </td>
                <td class="px-5 py-0 h-[56px] text-[10px] font-mono font-bold text-label/60 bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    <div class="flex items-center h-full">${row.fecha_fin ? row.fecha_fin.replace('T', ' ') : '-'}</div>
                </td>
                <td class="px-5 py-0 h-[56px] text-[10px] font-black uppercase text-label/40 bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    <div class="flex items-center h-full tracking-[0.1em]">${row.datos_tipo || 'MANUAL'}</div>
                </td>
                <td class="px-5 py-0 h-[56px] bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors text-center">
                    <div class="flex items-center justify-center h-full">${generateTaskGraphic(row.resumen)}</div>
                </td>
                <td class="px-5 py-0 h-[56px] bg-surface-container/30 rounded-r-2xl border-y border-r border-panel-border text-center group-hover:border-primary/30 transition-colors">
                    <div class="flex items-center justify-center h-full">
                        <a href="/api/psx/detail/${row.id}" target="_blank" class="p-2 hover:bg-primary/10 text-primary/40 hover:text-primary rounded-xl transition-all active:scale-90" title="Ver Detalles">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                        </a>
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
 * FETCH DATA FROM BACKEND
 */
async function fetchPSXData() {
    try {
        const response = await fetch('/api/psx/list');
        const result = await response.json();
        
        if (result.status === 'success') {
            psxData = result.tasks;
            filteredData = [...psxData];
            renderNexusTable();
        }
    } catch (error) {
        console.error('Error fetching PSX data:', error);
    }
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
    fetchPSXData(); // Load real data on start

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
        refreshBtn.addEventListener('click', () => fetchPSXData());
    }

    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');

    if (prevBtn) prevBtn.addEventListener('click', () => { if (currentPage > 1) { currentPage--; renderNexusTable(); } });
    if (nextBtn) nextBtn.addEventListener('click', () => { if (currentPage * tableRecordsLimit < filteredData.length) { currentPage++; renderNexusTable(); } });

    renderNexusTable();
});
