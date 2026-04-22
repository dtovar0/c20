/**
 * MODULE: Centralized Nexus Table Engine
 * Logic for rendering Audit and operational tables with 10 fixed rows.
 */

// Global Configuration
const tableRecordsLimit = 10;
let auditData = [];
let filteredData = [];
let currentPage = 1;

/**
 * MOCK DATA GENERATOR (Audit Context)
 */
const mockAuditData = [
    { id: 'AUD-001', user: 'admin', action: 'LOGIN', status: 'SUCCESS', time: '2026-04-21 11:45:02' },
    { id: 'AUD-002', user: 'dtovar', action: 'UPDATE_PLATFORM', status: 'SUCCESS', time: '2026-04-21 10:30:15' },
    { id: 'AUD-003', user: 'system', action: 'BACKUP', status: 'PENDING', time: '2026-04-21 12:00:00' }
];

/**
 * Renders the table with exactly 10 rows (8 Columns Standard)
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
        // Map status to visual styles
        const statusColors = {
            'success': 'text-emerald-400',
            'error': 'text-rose-400',
            'warning': 'text-amber-400',
            'info': 'text-primary'
        };

        const colorClass = statusColors[row.status] || statusColors['info'];

        // Map action type to visual styles
        const actionColors = {
            'tarea creada': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
            'tarea terminada': 'bg-violet-500/10 text-violet-400 border-violet-500/20',
            'tarea iniciada': 'bg-primary/10 text-primary border-primary/20',
            'LOGIN': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
            'LOGOUT': 'bg-slate-500/10 text-slate-400 border-slate-500/20',
            'SET_IDENTITY': 'bg-amber-500/10 text-amber-400 border-amber-500/20'
        };

        const actionClass = actionColors[row.action] || 'bg-primary/5 text-primary/70 border-primary/20';

        html += `
            <tr class="group hover:bg-primary/5 transition-all duration-300">
                <td class="px-5 py-0 h-[52px] text-[10px] font-black text-primary/60 bg-surface-container/30 border-y border-l border-panel-border rounded-l-2xl group-hover:border-primary/30 transition-colors">
                    #${String(row.id).padStart(5, '0')}
                </td>
                <td class="px-5 py-0 h-[52px] text-xs font-bold text-label/80 bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    ${row.user || 'SYSTEM'}
                </td>
                <td class="px-5 py-0 h-[52px] bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    <div class="inline-flex px-3 py-1 text-[9px] font-black tracking-widest uppercase border rounded-lg ${actionClass}">
                        ${row.action}
                    </div>
                </td>
                <td class="px-5 py-0 h-[52px] text-center bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    <span class="text-[9px] font-black tracking-widest uppercase ${colorClass}">${row.status}</span>
                </td>
                <td class="px-5 py-0 h-[52px] bg-surface-container/30 border-y border-panel-border group-hover:border-primary/30 transition-colors">
                    <div class="text-[10px] font-bold text-label/60 line-clamp-1 max-w-[300px]" title="${row.detail || ''}">
                        ${row.detail || '-'}
                    </div>
                </td>
                <td class="px-5 py-0 h-[52px] text-[10px] font-mono font-bold text-label/60 bg-surface-container/30 rounded-r-2xl border-y border-r border-panel-border group-hover:border-primary/30 transition-colors">
                    ${row.time}
                </td>
            </tr>
        `;
    });

    // 2. Ghost Row Complementation (6 Columns)
    const ghostRowsCount = tableRecordsLimit - pageData.length;
    for (let i = 0; i < ghostRowsCount; i++) {
        html += `
            <tr class="animate-pulse pointer-events-none select-none opacity-40">
                <td class="px-5 py-0 h-[52px] bg-surface-container/5 border-y border-l border-panel-border/10 rounded-l-2xl">
                    <div class="h-2 w-10 bg-label/10 rounded-full mx-auto"></div>
                </td>
                <td class="px-5 py-0 h-[52px] bg-surface-container/5 border-y border-panel-border/10" colspan="4">
                    <div class="h-2 w-full bg-label/5 rounded-full"></div>
                </td>
                <td class="px-5 py-0 h-[52px] bg-surface-container/5 border-y border-r border-panel-border/10 rounded-r-2xl">
                    <div class="h-2 w-full bg-label/5 rounded-full"></div>
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
 * FETCH DATA FROM BACKEND
 */
async function fetchAuditData() {
    try {
        const response = await fetch('/audit/api/list');
        const result = await response.json();
        
        if (result.status === 'success') {
            auditData = result.logs;
            filteredData = [...auditData];
            renderNexusTable();
        }
    } catch (error) {
        console.error('Error fetching Audit data:', error);
        if (typeof showToast === 'function') showToast('Error cargando auditoría', 'error');
    }
}

/**
 * INITIALIZATION
 */
document.addEventListener('DOMContentLoaded', () => {
    fetchAuditData();

    // Search Integration
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

    // Actions Listeners
    const refreshBtn = document.getElementById('refreshAudit');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => fetchAuditData());
    }

    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');

    if (prevBtn) prevBtn.addEventListener('click', () => { if (currentPage > 1) { currentPage--; renderNexusTable(); } });
    if (nextBtn) nextBtn.addEventListener('click', () => { if (currentPage * tableRecordsLimit < filteredData.length) { currentPage++; renderNexusTable(); } });

    renderNexusTable();
});
