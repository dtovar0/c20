/**
 * MODULE: PSX5K Operational Terminal Controller (DataTables Powered)
 * Dedicated logic for rendering PSX5K tasks with DataTables integration.
 */

let psxDataTable;

/**
 * GENERA UNA GRÁFICA DE SEGMENTOS REAL
 */
function generateTaskGraphic(resumen) {
    if (!resumen || resumen.total === 0) {
        return `<div class="h-1.5 w-24 bg-panel-border/20 rounded-full"></div>`;
    }

    const processed = resumen.ok + resumen.fail + resumen.force_ok + resumen.dup;
    const rawPct = (processed / resumen.total) * 100;
    const totalPct = Math.min(rawPct, 100);

    // Normalize segments proportionally within 100%
    const scale = processed > 0 ? totalPct / rawPct : 0;
    const okPct = ((resumen.ok / resumen.total) * 100) * scale;
    const failPct = ((resumen.fail / resumen.total) * 100) * scale;
    const forcePct = ((resumen.force_ok / resumen.total) * 100) * scale;
    const dupPct = ((resumen.dup / resumen.total) * 100) * scale;
    const pendingPct = Math.max(0, 100 - (okPct + failPct + forcePct + dupPct));

    return `
        <div class="flex flex-col gap-1.5 w-full max-w-[130px] mx-auto">
            <div class="h-4 w-full rounded-lg overflow-hidden flex shadow-inner border border-white/5" style="background:rgba(148,163,184,0.15)">
                <div class="h-full transition-all duration-700 ease-out" style="width:${okPct}%;background:#2563eb" title="OK: ${resumen.ok}"></div>
                <div class="h-full transition-all duration-700 ease-out" style="width:${failPct}%;background:#f43f5e" title="FAIL: ${resumen.fail}"></div>
                <div class="h-full transition-all duration-700 ease-out" style="width:${forcePct}%;background:#8b5cf6" title="FORCED: ${resumen.force_ok}"></div>
                <div class="h-full transition-all duration-700 ease-out" style="width:${dupPct}%;background:#f59e0b" title="DUP: ${resumen.dup}"></div>
                <div class="h-full bg-transparent" style="width:${pendingPct}%"></div>
            </div>
            <div class="flex justify-between items-center px-0.5">
                <span class="text-[12px] font-black" style="color:#2563eb">${Math.round(totalPct)}%</span>
                <span class="text-[12px] font-bold text-label/30">${processed}/${resumen.total}</span>
            </div>
        </div>
    `;
}

/**
 * INITIALIZATION
 */$(document).ready(function() {
    initPSXDataTable();

    // Universal Search Integration
    $('#auditSearch').on('input', function() {
        if (psxDataTable) {
            psxDataTable.search(this.value).draw();
        }
    });

    // Refresh Action
    $('#refreshAudit').on('click', function() {
        if (psxDataTable) {
            psxDataTable.ajax.reload();
        }
    });

    // Select All logic for PSX
    $(document).on('change', '#selectAllPSX', function() {
        const isChecked = this.checked;
        if (!psxDataTable) return;
        const nodes = psxDataTable.rows({ page: 'current' }).nodes().to$();
        
        nodes.each(function() {
            if (isChecked) {
                $(this).addClass('nexus-row-selected');
                $(this).find('.nexus-checkbox').prop('checked', true);
            } else {
                $(this).removeClass('nexus-row-selected');
                $(this).find('.nexus-checkbox').prop('checked', false);
            }
        });
        updatePSXActions();
    });
});

/**
 * Initializes DataTables for PSX5K
 */
function initPSXDataTable() {
    const tableEl = $('#auditTableBody').closest('table');
    if (!tableEl.length) return;

    psxDataTable = tableEl.DataTable({
        retrieve: true,
        ajax: {
            url: '/api/psx/list',
            dataSrc: (json) => {
                const isAdmin = json.is_admin || false;
                const api = tableEl.DataTable();
                if (api) { 
                    api.column(2).visible(isAdmin); // Columna Usuario (Admin Only)
                } 
                return json.tasks;
            }
        },
        columns: [
            {
                data: null,
                defaultContent: '',
                orderable: false,
                className: 'nexus-check-trigger',
                width: '60px',
                render: (data, type, row) => {
                    return `<div class="flex items-center justify-center h-full">
                                <input type="checkbox" class="nexus-checkbox pointer-events-none">
                            </div>`;
                }
            },
            { 
                data: 'id', 
                width: '80px', 
                render: (data) => `<div class="flex items-center justify-start h-full px-2 text-[12px] font-black text-primary/80 tracking-widest">#${String(data).padStart(5, '0')}</div>` 
            },
            { 
                data: 'usuario', 
                width: '180px', 
                render: (data) => `<div class="flex items-center justify-start h-full px-2 text-[12px] font-bold text-label/80 uppercase tracking-tighter truncate" data-nx-tooltip="Propietario: ${data}">${data}</div>` 
            },
            { 
                data: 'archivo_origen', 
                width: '280px', 
                render: (data, type, row) => `
                    <div class="flex items-center h-full gap-3">
                        <span class="text-[12px] font-bold text-label/60 truncate max-w-[180px]" data-nx-tooltip="${data}">
                            ${data && data.length > 25 ? '...' + data.slice(-22) : (data || 'MANUAL')}
                        </span>
                        <span class="px-2 py-0.5 rounded-md bg-white/[0.07] border border-white/10 text-[12px] font-black text-label/60 uppercase tracking-tighter whitespace-nowrap shadow-sm shadow-black/20">
                            ${row.chunk_index}/${row.chunk_total}
                        </span>
                    </div>` 
            },
            { 
                data: 'routing_label', 
                width: '140px', 
                render: (data) => `<div class="flex items-center justify-start h-full px-2 text-[12px] font-bold text-label/60 uppercase tracking-tight truncate" data-nx-tooltip="${data || 'N/A'}">${data || 'N/A'}</div>` 
            },
            { 
                data: 'resumen', 
                width: '120px', 
                orderable: false, 
                render: (data, type, row) => {
                    const state = (row.estado || '').toLowerCase();
                    if (state === 'programada' || state === 'pendiente') {
                        return `<div class="flex items-center justify-center gap-1.5 opacity-30 italic py-2">
                                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                    <span class="text-[11px] font-black uppercase tracking-[0.15em]">En Cola</span>
                                </div>`;
                    }
                    if (state === 'cancelada') {
                        return `<div class="flex items-center justify-center gap-1.5 opacity-40 text-rose-500/60 py-2">
                                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"></path></svg>
                                    <span class="text-[11px] font-black uppercase tracking-[0.15em]">Descartada</span>
                                </div>`;
                    }
                    return `<div class="flex items-center justify-center h-full min-w-0 overflow-hidden">${generateTaskGraphic(data)}</div>`;
                } 
            },
            { 
                data: null, 
                width: '120px',
                orderable: false,
                render: (data, type, row) => {
                    const isAdd = row.tarea === 'add';
                    const actionStyle = isAdd 
                        ? 'color:#2563eb;background:rgba(37,99,235,0.1);border-color:rgba(37,99,235,0.2)' 
                        : 'color:#f43f5e;background:rgba(244,63,94,0.1);border-color:rgba(244,63,94,0.2)';
                    const actionIcon = isAdd 
                        ? `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"></path></svg>`
                        : `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>`;
                    
                    let modeIcon = '';
                    let modeStyle = 'color:rgba(148,163,184,0.5);background:rgba(148,163,184,0.05);border-color:rgba(148,163,184,0.15)';
                    
                    // Normalización de Título de Modo
                    let modeTitle = row.accion_tipo || 'N/A';
                    if (modeTitle.toLowerCase() === 'eliminar') modeTitle = 'N/A';
                    
                    if (row.accion_tipo === 'call_in') {
                        modeIcon = `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"></path></svg>`;
                        modeStyle = 'color:#0ea5e9;background:rgba(14,165,233,0.1);border-color:rgba(14,165,233,0.2)';
                    } else if (row.accion_tipo === 'call_inout') {
                        modeIcon = `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path></svg>`;
                        modeStyle = 'color:#6366f1;background:rgba(99,102,241,0.1);border-color:rgba(99,102,241,0.2)';
                    } else {
                        modeIcon = `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M20 12H4"></path></svg>`;
                    }

                    let statusIcon = '';
                    let statusStyle = '';
                    const state = row.estado.toLowerCase();
                    if (state === 'ejecutando') {
                        statusIcon = `<svg class="w-3.5 h-3.5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>`;
                        statusStyle = 'color:#2563eb;background:rgba(37,99,235,0.15);border-color:rgba(37,99,235,0.3)';
                    } else if (state === 'terminada') {
                        statusIcon = `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>`;
                        statusStyle = 'color:#10b981;background:rgba(16,185,129,0.15);border-color:rgba(16,185,129,0.3)';
                    } else if (state === 'error') {
                        statusIcon = `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>`;
                        statusStyle = 'color:#f43f5e;background:rgba(244,63,94,0.15);border-color:rgba(244,63,94,0.3)';
                    } else {
                        statusIcon = `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`;
                        statusStyle = 'color:#f59e0b;background:rgba(245,158,11,0.15);border-color:rgba(245,158,11,0.3)';
                    }

                    return `
                        <div class="flex items-center justify-center gap-2 h-full">
                            <div class="flex items-center justify-center w-8 h-8 rounded-lg border transition-all hover:scale-110" style="${actionStyle}" data-nx-tooltip="${row.tarea.toUpperCase()}">
                                ${actionIcon}
                            </div>
                            <div class="flex items-center justify-center w-8 h-8 rounded-lg border transition-all hover:scale-110" style="${modeStyle}" data-nx-tooltip="MODO: ${modeTitle.toUpperCase()}">
                                ${modeIcon}
                            </div>
                            <div class="flex items-center justify-center w-8 h-8 rounded-lg border transition-all hover:scale-110" style="${statusStyle}" data-nx-tooltip="${row.estado.toUpperCase()}">
                                ${statusIcon}
                            </div>
                        </div>`;
                }
            },
            { 
                data: 'id', 
                width: '50px',
                orderable: false,
                render: (data) => `
                    <div class="flex items-center justify-center h-full">
                        <a href="/api/psx/detail/${data}" target="_blank" class="p-2 hover:bg-primary/10 text-primary/40 hover:text-primary rounded-xl transition-all" data-nx-tooltip="Ver Detalles">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                        </a>
                    </div>`
            }
        ],
        autoWidth: false,
        pageLength: 10,
        pagingType: 'simple',
        order: [[1, 'desc']], 
        layout: {
            topStart: null,
            topEnd: null,
            bottomStart: 'info',
            bottomEnd: 'paging'
        },
        language: {
            zeroRecords: "No se encontraron tareas",
            info: "Mostrando _START_-_END_ de _TOTAL_ registros",
            paginate: {
                previous: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>',
                next: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>'
            }
        },
        drawCallback: function(settings) {
            const api = new $.fn.dataTable.Api(settings);
            const visibleCols = api.columns(':visible').count();
            if (typeof renderGhostRows === 'function') {
                renderGhostRows(settings, visibleCols);
            }
            updatePSXActions();
        },
        initComplete: function() {
            if (typeof startGlobalPolling === 'function') startGlobalPolling();
        }
    });

    // LÓGICA DE SELECCIÓN CUSTOM (Manual - Solo Checkbox)
    tableEl.on('click', '.nexus-check-trigger', function(e) {
        e.stopPropagation();
        const tr = $(this).closest('tr');
        const checkbox = tr.find('.nexus-checkbox');

        if (tr.hasClass('nexus-row-selected')) {
            tr.removeClass('nexus-row-selected');
            checkbox.prop('checked', false);
        } else {
            // Deseleccionar otros (Lógica de selección única)
            tableEl.find('tr.nexus-row-selected').removeClass('nexus-row-selected').find('.nexus-checkbox').prop('checked', false);
            tr.addClass('nexus-row-selected');
            checkbox.prop('checked', true);
        }

        // Sync Select All state
        const totalOnPage = psxDataTable.rows({ page: 'current' }).data().length;
        const selectedOnPage = psxDataTable.rows({ page: 'current' }).nodes().to$().filter('.nexus-row-selected').length;
        $('#selectAllPSX').prop('checked', selectedOnPage === totalOnPage && totalOnPage > 0);

        updatePSXActions();
    });

    window.activeNexusTable = psxDataTable;
}

function updatePSXActions() {
    const tr = $('#auditTableBody tr.nexus-row-selected');
    const modifyBtn = $('#modifyTaskBtn');
    
    if (tr.length === 1) {
        const data = psxDataTable.row(tr).data();
        const isRunning = data.estado.toLowerCase() === 'ejecutando';

        if (isRunning) {
            modifyBtn.addClass('opacity-30 pointer-events-none');
            modifyBtn.off('click');
        } else {
            modifyBtn.removeClass('opacity-30 pointer-events-none');
            modifyBtn.off('click').on('click', () => {
                if (typeof openModifyModal === 'function') openModifyModal(data.id);
            });
        }
    } else {
        modifyBtn.addClass('opacity-30 pointer-events-none');
        modifyBtn.off('click');
    }
}

/**
 * Renders ghost (skeleton) rows to fill the table container dynamically
 */
function renderGhostRows(settings, columns) {
    const api = new $.fn.dataTable.Api(settings);
    const info = api.page.info();
    const tbody = $(settings.nTBody);
    
    // Remove default empty message if present
    tbody.find('.dataTables_empty').closest('tr').remove();

    const rowsOnPage = info.end - info.start;
    
    // Adaptive Logic: Calculate how many rows fit in the current viewport
    const container = tbody.closest('.overflow-x-auto');
    const containerHeight = container.innerHeight() || 500;
    const rowHeight = 56; // High density row height including spacing (52px + 4px)
    const headerHeight = tbody.closest('table').find('thead').outerHeight() || 50;
    
    // STRICT LIMIT: Always target 10 rows to match pagination exactly
    const targetTotal = 10;
    const ghostCount = targetTotal - rowsOnPage;

    if (ghostCount <= 0) return;

    let ghostHtml = '';
    for (let i = 0; i < ghostCount; i++) {
        ghostHtml += `
            <tr class="animate-pulse pointer-events-none select-none opacity-40">
                <td class="bg-surface-container/5 border-y border-l border-panel-border/10 rounded-l-2xl">
                    <div class="h-1.5 w-10 bg-label/10 rounded-full mx-auto"></div>
                </td>
                ${Array(columns - 2).fill(0).map(() => `
                    <td class="bg-surface-container/5 border-y border-panel-border/10">
                        <div class="h-1 w-full bg-label/5 rounded-full"></div>
                    </td>
                `).join('')}
                <td class="bg-surface-container/5 border-y border-r border-panel-border/10 rounded-r-2xl">
                    <div class="h-1 w-full bg-label/5 rounded-full"></div>
                </td>
            </tr>
        `;
    }
    
    setTimeout(() => {
        tbody.append(ghostHtml);
    }, 0);
}

// Adaptive Redraw on Resize
$(window).on('resize', () => {
    if (psxDataTable) psxDataTable.draw(false);
});
