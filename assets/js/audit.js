/**
 * MODULE: Audit Management
 * Logic for rendering and paginating the audit table with constant 8 items visualization.
 */

// Demo Database (Initial load or mock)
const auditData = [
    { time: '2026-04-17 16:45:12', user: 'dtovar', action: 'LOGIN_SUCCESS', ip: '192.168.1.105', status: 'success', detail: 'Acceso verificado vía token core' },
    { time: '2026-04-17 16:40:05', user: 'system', action: 'CONFIG_UPDATE', ip: 'local_host', status: 'info', detail: 'Sincronización de tokens finalizada' },
    { time: '2026-04-17 16:35:20', user: 'dtovar', action: 'DB_BACKUP', ip: '192.168.1.105', status: 'success', detail: 'Respaldo manual base nexus_prod' },
    { time: '2026-04-17 16:30:00', user: 'unknown', action: 'LOGIN_FAILED', ip: '45.12.8.22', status: 'error', detail: 'Fallo en credenciales: 3 intentos' },
    { time: '2026-04-17 16:25:15', user: 'dtovar', action: 'UI_MODERNIZATION', ip: '192.168.1.105', status: 'info', detail: 'Cambio de color header a celeste' },
    { time: '2026-04-17 16:15:40', user: 'system', action: 'LOG_PURGE', ip: 'local_host', status: 'success', detail: 'Limpieza automática de logs antiguos' },
    { time: '2026-04-17 16:10:22', user: 'root', action: 'PASS_CHANGE', ip: '127.0.0.1', status: 'warning', detail: 'Cambio de contraseña root detectado' },
    { time: '2026-04-17 16:05:01', user: 'dtovar', action: 'TAB_CLEANUP', ip: '192.168.1.105', status: 'info', detail: 'Remoción de token en tab container' },
    { time: '2026-04-17 15:55:30', user: 'guest_12', action: 'FILE_READ', ip: '10.0.0.5', status: 'success', detail: 'Acceso a documentación assets/docs' },
    { time: '2026-04-17 15:50:12', user: 'dtovar', action: 'SET_AUDIT', ip: '192.168.1.105', status: 'success', detail: 'Creación del módulo independiente audit' },
    { time: '2026-04-17 15:45:00', user: 'system', action: 'API_RESTART', ip: 'local_host', status: 'warning', detail: 'Reinicio automático del servicio API' },
    { time: '2026-04-17 15:30:15', user: 'dtovar', action: 'THEME_SYNC', ip: '192.168.1.105', status: 'info', detail: 'Sincronización con preferencias de usuario' },
    { time: '2026-04-17 15:20:44', user: 'bot_scanner', action: 'SQL_INJECTION_TRY', ip: '82.44.11.5', status: 'error', detail: 'Bloqueo automático de IP maliciosa' },
    { time: '2026-04-17 15:10:05', user: 'dtovar', action: 'BLUEPRINT_REG', ip: '192.168.1.105', status: 'success', detail: 'Registro de blueprints core y settings' },
    { time: '2026-04-17 15:00:22', user: 'root', action: 'DOCKER_BUILD', ip: '10.0.0.1', status: 'success', detail: 'Nueva imagen construida satisfactoriamente' },
    { time: '2026-04-17 14:50:11', user: 'system', action: 'SSL_REVOKE', ip: 'local_host', status: 'error', detail: 'Certificado SSL caducado en nodo B' },
    { time: '2026-04-17 14:40:00', user: 'dtovar', action: 'ASSET_COPY', ip: '192.168.1.105', status: 'info', detail: 'Copia de recursos estáticos a carpeta assets' },
    { time: '2026-04-17 14:30:55', user: 'developer_1', action: 'GIT_PUSH', ip: '192.168.1.50', status: 'success', detail: 'Push: Refactor de componentes UI' },
    { time: '2026-04-17 14:20:12', user: 'dtovar', action: 'ENV_INIT', ip: '192.168.1.105', status: 'success', detail: 'Inicialización de variables de entorno' },
    { time: '2026-04-17 14:10:05', user: 'dtovar', action: 'WORKSPACE_CREATE', ip: '192.168.1.105', status: 'success', detail: 'Apertura de nuevo espacio de trabajo' }
];

let currentPage = 1;
const recordsPerPage = 8;
let filteredData = [...auditData];

/**
 * Renders the audit table content
 */
function renderTable() {
    const tbody = document.getElementById('auditTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    const start = (currentPage - 1) * recordsPerPage;
    const end = start + recordsPerPage;
    const pageData = filteredData.slice(start, end);
    let rowsRendered = 0;

    // State Case: No Results
    if (filteredData.length === 0) {
        tbody.innerHTML += `
            <tr class="bg-surface-container/10 border border-dashed border-panel-border rounded-xl pointer-events-none">
                <td colspan="6" class="px-6 py-6 text-center">
                    <div class="flex items-center justify-center gap-3 opacity-30">
                        <svg class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 9.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        <span class="text-[10px] font-black uppercase tracking-[0.2em] text-label italic">No se encontraron registros activos</span>
                    </div>
                </td>
            </tr>
        `;
        rowsRendered = 1;
    } else {
        // Render Data Rows
        pageData.forEach(row => {
            const statusClass = {
                success: 'bg-green-500/10 text-green-500',
                info: 'bg-primary/10 text-primary',
                warning: 'bg-orange-500/10 text-orange-500',
                error: 'bg-red-500/10 text-red-500'
            }[row.status];

            tbody.innerHTML += `
                <tr class="bg-surface-container border border-surface-container-border rounded-xl hover:border-primary transition-all group active:scale-[0.995]">
                    <td class="px-4 py-3 text-[11px] font-bold text-label/60">
                        <div class="flex items-center gap-2">
                            <span class="w-1.5 h-1.5 rounded-full bg-primary/40"></span>
                            ${row.time}
                        </div>
                    </td>
                    <td class="px-4 py-3 text-[11px] font-black text-label uppercase tracking-tighter">${row.user}</td>
                    <td class="px-4 py-3 text-[11px] font-bold text-label">${row.action}</td>
                    <td class="px-4 py-3 text-[10px] font-mono text-label/40">${row.ip}</td>
                    <td class="px-4 py-3">
                        <span class="px-3 py-0.5 rounded-full text-[8px] font-black uppercase tracking-widest ${statusClass}">${row.status}</span>
                    </td>
                    <td class="px-4 py-3 text-right pr-4">
                        <button class="w-7 h-7 rounded-lg bg-label/5 text-label/40 hover:bg-primary/20 hover:text-primary transition-all flex items-center justify-center ml-auto">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        </button>
                    </td>
                </tr>
            `;
            rowsRendered++;
        });
    }

    const ghostRowsCount = recordsPerPage - rowsRendered;
    for (let i = 0; i < ghostRowsCount; i++) {
        tbody.innerHTML += `
            <tr class="bg-surface-container border border-surface-container-border rounded-xl pointer-events-none select-none">
                <td class="px-4 py-3 text-[11px] font-bold text-transparent">-</td>
                <td class="px-4 py-3 text-[11px] font-black text-transparent">-</td>
                <td class="px-4 py-3 text-[11px] font-bold text-transparent">-</td>
                <td class="px-4 py-3 text-[10px] font-mono text-transparent">-</td>
                <td class="px-4 py-3">
                    <div class="h-4 w-16 bg-label/10 rounded-full mx-auto opacity-30"></div>
                </td>
                <td class="px-4 py-3 text-right pr-4">
                    <div class="w-7 h-7 rounded-lg bg-label/5 ml-auto opacity-30"></div>
                </td>
            </tr>
        `;
    }

    updatePagination();
}

/**
 * Updates pagination text and buttons state
 */
function updatePagination() {
    const infoEl = document.getElementById('paginationInfo');
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    
    if (!infoEl || !prevBtn || !nextBtn) return;

    const total = filteredData.length;
    const start = total === 0 ? 0 : (currentPage - 1) * recordsPerPage + 1;
    const end = Math.min(currentPage * recordsPerPage, total);
    
    infoEl.innerText = `Mostrando ${start}-${end} de ${total} registros`;
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = end >= total;
}

// Initializing the module
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('auditSearch');
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            filteredData = auditData.filter(item => 
                item.user.toLowerCase().includes(term) || 
                item.action.toLowerCase().includes(term) || 
                item.detail.toLowerCase().includes(term) ||
                item.ip.includes(term)
            );
            currentPage = 1;
            renderTable();
        });
    }

    const refreshBtn = document.getElementById('refreshAudit');

    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            filteredData = [...auditData];
            currentPage = 1;
            renderTable();
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderTable();
            }
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (currentPage * recordsPerPage < filteredData.length) {
                currentPage++;
                renderTable();
            }
        });
    }

    renderTable();
});
