/**
 * Returns optimal pageLength based on viewport height.
 *   < 900px → 9 rows   >= 900px → 10 rows
 */
function getPageLength() {
    const h = window.innerHeight;
    if (h < 900) return 9;
    return 10;
}

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
                    const action = String(data).toLowerCase();
                    let cls = 'nx-badge-primary';
                    let label = String(data).toUpperCase();

                    if (action.includes('login')) cls = 'nx-badge-cyan';
                    else if (action.includes('logout')) cls = 'nx-badge-slate';
                    else if (action.includes('creada')) cls = 'nx-badge-success';
                    else if (action.includes('terminada')) cls = 'nx-badge-violet';
                    else if (action.includes('iniciada')) cls = 'nx-badge-primary';
                    else if (action.includes('identity')) cls = 'nx-badge-warning';

                    return `<div class="flex items-center h-full"><span class="nx-badge ${cls}">${label}</span></div>`;
                }
            },
            { 
                data: 'status', 
                width: '100px',
                render: (data) => {
                    const status = String(data).toLowerCase();
                    let cls = 'nx-badge-primary';
                    if (status.includes('success')) cls = 'nx-badge-success';
                    else if (status.includes('error')) cls = 'nx-badge-error';
                    else if (status.includes('warning')) cls = 'nx-badge-warning';
                    
                    return `<div class="flex items-center justify-center h-full"><span class="nx-badge ${cls}">${data.toUpperCase()}</span></div>`;
                }
            },
            { data: 'detail', width: 'auto', render: (data) => `<div class="flex items-center h-full text-[12px] font-bold text-label/60 line-clamp-1 min-w-0 overflow-hidden text-ellipsis" title="${data || ''}">${data || '-'}</div>` },
            { data: 'time', width: '180px', render: (data) => `<div class="flex items-center h-full font-mono text-[12px] font-bold text-label/60 justify-end">${data}</div>` }
        ],
        autoWidth: false,
        pageLength: getPageLength(),
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
        },
        initComplete: function() {
            const cell = $(this.api().table().container()).find('.dt-layout-row.dt-layout-table .dt-layout-cell');
            const tbl  = cell.children('table');
            if (tbl.length && !cell.children('.nx-table-scroll').length) {
                tbl.wrap('<div class="nx-table-scroll"></div>');
            }
            const api = this.api();
            let resizeTimer;
            $(window).on('resize.dtPageLen', function() {
                clearTimeout(resizeTimer);
                resizeTimer = setTimeout(function() {
                    const newLen = getPageLength();
                    if (api.page.len() !== newLen) api.page.len(newLen).draw();
                    else api.draw(false);
                }, 200);
            });
        }
    });

    // Register globally for top bar search
    window.activeNexusTable = auditDataTable;
}

/**
 * Sizes all rows equally to fill the table wrapper, then adds ghost rows.
 * rowH = floor( (wrapperHeight - borderGaps) / (pageLen + 1) )
 */
function renderGhostRows(settings, columns) {
    const api     = new $.fn.dataTable.Api(settings);
    const info    = api.page.info();
    const tbody   = $(settings.nTBody);
    const pageLen = api.page.len();

    // 1. Cleanup
    tbody.find('.ghost-row').remove();
    tbody.find('.dataTables_empty').closest('tr').remove();

    // 2. Calculate row height based on the GRID SCOPE
    const container = api.table().container();
    const gridH = $(container).height(); 
    let rowH = 50;
    
    if (gridH > 0) {
        const totalRows  = pageLen;
        // Restamos el footer y aplicamos un offset de -1px para compensar bordes
        rowH = Math.max(40, Math.floor((gridH - 52) / (totalRows + 1)) - 1);
    }
    
    // Set the variable for CSS (Matches Header, Body and Pagination)
    $(container).css('--row-h', rowH + 'px');

    // 3. Ghost Row injection (simplified)
    const realRows   = info.end - info.start;
    const ghostCount = pageLen - realRows;
    if (ghostCount <= 0) return;

    let ghostHtml = '';
    for (let i = 0; i < ghostCount; i++) {
        ghostHtml += `
            <tr class="ghost-row pointer-events-none select-none">
                <td><div></div></td>
                ${Array(columns - 1).fill(0).map(() => `
                    <td><div></div></td>
                `).join('')}
            </tr>`;
    }
    tbody.append(ghostHtml);
}


// Adaptive Redraw on Resize
$(window).on('resize', () => {
    if (auditDataTable) auditDataTable.draw(false);
});
