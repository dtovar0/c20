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
 * INITIALIZATION
 */
$(document).ready(function() {
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
});

/**
 * Initializes DataTables for PSX5K
 */
function initPSXDataTable() {
    const tableEl = $('#auditTableBody').closest('table');
    if (!tableEl.length) return;

    psxDataTable = tableEl.DataTable({
        ajax: {
            url: '/api/psx/list',
            dataSrc: (json) => {
                // Toggling Usuario column visibility based on admin status
                const isAdmin = json.is_admin || false;
                const api = tableEl.DataTable();
                if (api) {
                    api.column(5).visible(isAdmin);
                }
                return json.tasks;
            }
        },
        columns: [
            { 
                data: 'id', 
                width: '100px', 
                render: (data) => `<div class="flex items-center justify-center h-full text-[11px] font-black text-primary/80">#${String(data).padStart(5, '0')}</div>` 
            },
            { 
                data: 'tarea', 
                width: '120px',
                render: (data) => {
                    const opBadge = data === 'add' ? 'badge-op-add' : 'badge-op-delete';
                    const opLabel = data === 'add' ? 'AGREGAR' : 'BORRAR';
                    return `<div class="flex items-center h-full"><div class="badge-nexus ${opBadge} w-fit">${opLabel}</div></div>`;
                }
            },
            { 
                data: 'estado', 
                width: '130px',
                render: (data) => {
                    const statusBadge = data === 'Ejecutando' ? 'badge-running' : 
                                      data === 'Terminada' ? 'badge-finished' : 
                                      data === 'Programada' ? 'badge-scheduled' : 'badge-pending';
                    return `<div class="flex items-center h-full"><div class="badge-nexus ${statusBadge}">${data.toUpperCase()}</div></div>`;
                }
            },
            { 
                data: 'fecha_inicio', 
                width: '120px', 
                render: (data) => `<div class="flex items-center h-full text-[10px] font-mono font-bold text-primary/70">${data ? data.replace('T', ' ').split('.')[0].split(' ')[1] || data.replace('T', ' ').split('.')[0] : 'PENDIENTE'}</div>` 
            },
            { 
                data: 'fecha_fin', 
                width: '120px', 
                render: (data) => `<div class="flex items-center h-full text-[10px] font-mono font-bold text-violet-400/70">${data ? data.replace('T', ' ').split('.')[0].split(' ')[1] || data.replace('T', ' ').split('.')[0] : '--:--:--'}</div>` 
            },
            { 
                data: 'usuario', 
                width: '100px', 
                visible: false,
                render: (data) => `<div class="flex items-center h-full text-[10px] font-black text-label/50 uppercase tracking-wider">${data}</div>` 
            },
            { 
                data: 'archivo_origen', 
                width: '180px', 
                render: (data) => `
                    <div class="flex items-center h-full text-[10px] font-bold text-label/40 truncate max-w-[170px]" title="${data}">
                        ${data && data.length > 25 ? '...' + data.slice(-22) : (data || 'MANUAL')}
                    </div>` 
            },
            { 
                data: 'chunk_index',
                width: '100px',
                render: (data, type, row) => `
                    <div class="flex items-center h-full">
                        <span class="px-3 py-1 bg-label/5 rounded-lg text-[9px] font-black text-label/40 uppercase tracking-widest border border-panel-border/20">
                            ${row.chunk_index} / ${row.chunk_total}
                        </span>
                    </div>`
            },
            { data: 'resumen', width: '120px', orderable: false, render: (data) => `<div class="flex items-center justify-center h-full min-w-0 overflow-hidden">${generateTaskGraphic(data)}</div>` },
            { 
                data: 'id', 
                width: '60px',
                orderable: false,
                render: (data) => `
                    <div class="flex items-center justify-center h-full">
                        <a href="/api/psx/detail/${data}" target="_blank" class="p-2 hover:bg-primary/10 text-primary/40 hover:text-primary rounded-xl transition-all" title="Ver Detalles">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                        </a>
                    </div>`
            }
        ],
        autoWidth: false,
        pageLength: 10,
        pagingType: 'simple',
        order: [[0, 'desc']],
        layout: {
            topStart: null,
            topEnd: null,
            bottomStart: 'info',
            bottomEnd: 'paging'
        },
        language: {
            zeroRecords: "No se encontraron tareas",
            info: "Mostrando _START_-_END_ de _TOTAL_ registros"
        },
        renderer: {
            pagingButton: function (settings, button, content, active, disabled) {
                if (button === 'previous') {
                    return $('<button/>').addClass('p-2 bg-surface-container border border-surface-container-border rounded-lg text-label hover:border-primary disabled:opacity-30 disabled:pointer-events-none transition-all active:scale-90')
                        .append('<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>')
                        .prop('disabled', disabled);
                }
                if (button === 'next') {
                    return $('<button/>').addClass('p-2 bg-surface-container border border-surface-container-border rounded-lg text-label hover:border-primary disabled:opacity-30 disabled:pointer-events-none transition-all active:scale-90')
                        .append('<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>')
                        .prop('disabled', disabled);
                }
                return null;
            }
        },
        drawCallback: function(settings) {
            // Count visible columns for correct ghost row rendering
            const api = new $.fn.dataTable.Api(settings);
            const visibleCols = api.columns(':visible').count();
            renderGhostRows(settings, visibleCols);
        }
    });
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
                <td class="bg-surface-container/5 border-y border-l border-panel-border/10 rounded-l-2xl h-[52px]">
                    <div class="h-1.5 w-10 bg-label/10 rounded-full mx-auto"></div>
                </td>
                ${Array(columns - 2).fill(0).map(() => `
                    <td class="bg-surface-container/5 border-y border-panel-border/10 h-[52px]">
                        <div class="h-1 w-full bg-label/5 rounded-full"></div>
                    </td>
                `).join('')}
                <td class="bg-surface-container/5 border-y border-r border-panel-border/10 rounded-r-2xl h-[52px]">
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
