/**
 * MODULE: Centralized Nexus Table Engine
 * Logic for rendering Audit and operational tables with 10 fixed rows.
 */

// Global Configuration
const tableRecordsLimit = 10;
let auditData = []; // Can be filled externally or via mock
let filteredData = [];
let currentPage = 1;

/**
 * MOCK DATA GENERATOR (Fallback)
 */
const mockAuditData = [
    { id: 'PSX-9421', nombre: 'Mainframe Sync', operacion: 'add', estado: 'running', inicio: '2026-04-21 11:45:02', fin: '-', resultado: 'PROCESANDO' },
    { id: 'PSX-9388', nombre: 'Legacy Node Clean', operacion: 'delete', estado: 'finished', inicio: '2026-04-21 10:30:15', fin: '2026-04-21 10:35:42', resultado: 'EXITO' },
    { id: 'PSX-9210', nombre: 'Buffer Calibration', operacion: 'add', estado: 'pending', inicio: '2026-04-21 12:00:00', fin: '-', resultado: 'EN COLA' },
    { id: 'PSX-9105', nombre: 'Security Patch v5.2', operacion: 'add', estado: 'finished', inicio: '2026-04-21 09:00:00', fin: '2026-04-21 09:12:10', resultado: 'EXITO' },
    { id: 'PSX-8992', nombre: 'Database Purge', operacion: 'delete', estado: 'finished', inicio: '2026-04-21 08:30:00', fin: '2026-04-21 08:35:00', resultado: 'FALLIDO' }
];

/**
 * Renders the table with exactly 10 rows (Real Data + Ghost Rows)
 */
function renderNexusTable() {
    const tbody = document.getElementById('auditTableBody');
    if (!tbody) return;

    const isPsx = !!document.getElementById('psx-view-marker');
    const start = (currentPage - 1) * tableRecordsLimit;
    const end = start + tableRecordsLimit;
    const pageData = filteredData.slice(start, end);
    
    let html = '';

    // 1. Render Real Data Rows
    pageData.forEach(row => {
        // Map states to badges
        const statusBadge = row.estado === 'running' ? 'badge-running' : 
                          row.estado === 'finished' ? 'badge-finished' : 'badge-pending';
        const opBadge = row.operacion === 'add' ? 'badge-op-add' : 'badge-op-delete';
        const opLabel = row.operacion === 'add' ? 'AGREGAR' : 'BORRAR';
        const statusLabel = row.estado === 'running' ? 'EJECUTANDO' : 
                           row.estado === 'finished' ? 'TERMINADO' : 'PENDIENTE';

        html += `
            <tr class="group hover:bg-primary/5 transition-all duration-300">
                <td class="px-5 py-3 text-[11px] font-black text-primary/80 bg-surface-container/30 border-y border-l border-panel-border rounded-l-2xl group-hover:border-primary/30 transition-colors">
                    ${row.id || 'N/A'}
                </td>
                <td class="px-5 py-3 text-xs font-bold text-text bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    ${row.nombre || row.user || 'N/A'}
                </td>
                <td class="px-5 py-3 bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    <div class="badge-nexus ${opBadge}">${row.action || opLabel}</div>
                </td>
                <td class="px-5 py-3 bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    <div class="badge-nexus ${statusBadge}">${statusLabel}</div>
                </td>
                <td class="px-5 py-3 text-[10px] font-mono font-bold text-label/60 bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    ${row.inicio || row.time}
                </td>
                <td class="px-5 py-3 text-[10px] font-mono font-bold text-label/60 bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    ${row.fin || '-'}
                </td>
                <td class="px-5 py-3 text-[10px] font-black uppercase text-label/60 bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    ${row.resultado || row.status}
                </td>
                <td class="px-5 py-3 bg-surface-container/30 rounded-r-2xl border-y border-r border-panel-border text-center group-hover:border-primary/30 transition-colors">
                    <button class="p-2 hover:bg-primary/10 text-primary/40 hover:text-primary rounded-xl transition-all active:scale-90" title="Ver Detalles">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                    </button>
                </td>
            </tr>
        `;
    });

    // 2. Ghost Row Complementation (Always fill up to 10 rows)
    const ghostRowsCount = tableRecordsLimit - pageData.length;
    for (let i = 0; i < ghostRowsCount; i++) {
        html += `
            <tr class="animate-pulse pointer-events-none select-none opacity-40">
                <td class="px-5 py-3 bg-surface-container/5 border-y border-l border-panel-border/10 rounded-l-2xl">
                    <div class="h-2 w-12 bg-label/10 rounded-full"></div>
                </td>
                <td class="px-5 py-3 bg-surface-container/5 border-y border-panel-border/10" colspan="6">
                    <div class="h-2 w-full bg-label/5 rounded-full"></div>
                </td>
                <td class="px-5 py-3 bg-surface-container/5 border-y border-r border-panel-border/10 rounded-r-2xl"></td>
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
    // 1. Determine which data to load
    const isPsxPage = !!document.getElementById('psx-view-marker');
    auditData = isPsxPage ? mockAuditData : mockAuditData; // Both use same for now, can be swapped for AJAX
    filteredData = [...auditData];

    // 2. Search Integration
    const searchInput = document.getElementById('auditSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            filteredData = auditData.filter(item =>
                Object.values(item).some(val => String(val).toLowerCase().includes(term))
            );
            currentPage = 1;
            renderNexusTable();
        });
    }

    // 3. Actions Listeners
    const refreshBtn = document.getElementById('refreshAudit');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => renderNexusTable());
    }

    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');

    if (prevBtn) prevBtn.addEventListener('click', () => { if (currentPage > 1) { currentPage--; renderNexusTable(); } });
    if (nextBtn) nextBtn.addEventListener('click', () => { if (currentPage * tableRecordsLimit < filteredData.length) { currentPage++; renderNexusTable(); } });

    // Initial Trigger
    renderNexusTable();
});
