/**
 * MODULE: Centralized Nexus Table Engine (DataTables Powered)
 * Logic for rendering Audit tables with DataTables integration.
 */

let auditDataTable;

/**
 * INITIALIZATION
 */
$(document).ready(function() {
    initAuditDataTable();

    // Universal Search Integration
    $('#auditSearch').on('input', function() {
        if (auditDataTable) {
            auditDataTable.search(this.value).draw();
        }
    });

    // Refresh Action
    $('#refreshAudit').on('click', function() {
        if (auditDataTable) {
            auditDataTable.ajax.reload();
        }
    });
});

/**
 * Initializes DataTables for Audit
 */
function initAuditDataTable() {
    const tableEl = $('table');
    if (!tableEl.length) return;

    auditDataTable = tableEl.DataTable({
        ajax: {
            url: '/audit/api/list',
            dataSrc: 'logs'
        },
        columns: [
            { data: 'id', width: '80px', render: (data) => `<div class="flex items-center h-full text-primary/60 font-black">#${String(data).padStart(5, '0')}</div>` },
            { data: 'user', width: '130px', render: (data) => `<div class="flex items-center h-full font-bold text-label/80 truncate">${data || 'SYSTEM'}</div>` },
            { 
                data: 'action', 
                width: '170px',
                render: (data) => {
                    const actionColors = {
                        'tarea creada': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
                        'tarea terminada': 'bg-violet-500/10 text-violet-400 border-violet-500/20',
                        'tarea iniciada': 'bg-primary/10 text-primary border-primary/20',
                        'LOGIN': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
                        'LOGOUT': 'bg-slate-500/10 text-slate-400 border-slate-500/20',
                        'SET_IDENTITY': 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                    };
                    const actionClass = actionColors[data] || 'bg-primary/5 text-primary/70 border-primary/20';
                    return `<div class="flex items-center h-full"><div class="inline-flex px-3 py-1 text-[9px] font-black tracking-widest uppercase border rounded-lg ${actionClass} truncate">${data}</div></div>`;
                }
            },
            { 
                data: 'status', 
                width: '100px',
                render: (data) => {
                    const statusColors = {
                        'success': 'text-emerald-400',
                        'error': 'text-rose-400',
                        'warning': 'text-amber-400',
                        'info': 'text-primary'
                    };
                    const colorClass = statusColors[data.toLowerCase()] || statusColors['info'];
                    return `<div class="flex items-center justify-center h-full"><span class="text-[9px] font-black tracking-widest uppercase ${colorClass}">${data}</span></div>`;
                }
            },
            { data: 'detail', width: 'auto', render: (data) => `<div class="flex items-center h-full text-[10px] font-bold text-label/60 line-clamp-1 min-w-0 overflow-hidden text-ellipsis" title="${data || ''}">${data || '-'}</div>` },
            { data: 'time', width: '180px', render: (data) => `<div class="flex items-center h-full font-mono text-[10px] font-bold text-label/60 justify-end">${data}</div>` }
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
            zeroRecords: "No se encontraron registros",
            info: "Mostrando _START_-_END_ de _TOTAL_ registros",
            infoEmpty: "Mostrando 0-0 de 0 registros",
            infoFiltered: "(filtrado de _MAX_ registros totales)",
            paginate: {
                previous: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>',
                next: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>'
            }
        },
        drawCallback: function(settings) {
            renderGhostRows(settings, 6);
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
    
    // Calculate available space for rows
    const availableHeight = containerHeight - headerHeight;
    
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
    
    // Use setTimeout to ensure we don't conflict with DataTables internal draw timing
    setTimeout(() => {
        tbody.append(ghostHtml);
    }, 0);
}

// Adaptive Redraw on Resize
$(window).on('resize', () => {
    if (auditDataTable) auditDataTable.draw(false);
});
