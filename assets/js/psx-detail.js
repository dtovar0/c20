/* PSX DETAIL MODULE - LOGIC DECOUPLING */

let historyDataTable;

$(document).ready(function() {
    initHistoryDataTable();

    // Custom tab switching logic
    // We don't use ready for switchTab as it is called from onclick
});

/**
 * Tab switching logic for Dashboard, Technical History, and CMD History.
 */
function switchTab(tabId) {
    const panes = document.querySelectorAll('.tab-panel');
    panes.forEach(p => {
        p.classList.add('hidden');
        p.style.opacity = '0';
        p.style.transform = 'translateY(10px)';
    });

    document.querySelectorAll('.tab-trigger').forEach(b => {
        b.classList.remove('nav-item-active');
    });

    const activePane = document.getElementById('tab-panel-' + tabId);
    if (activePane) {
        activePane.classList.remove('hidden');
        
        // Trigger animation
        setTimeout(() => {
            activePane.style.opacity = '1';
            activePane.style.transform = 'translateY(0)';
            activePane.style.transition = 'all 0.4s cubic-bezier(0.22, 1, 0.36, 1)';
        }, 50);

        if (tabId === 'logs' && historyDataTable) {
            historyDataTable.columns.adjust().draw(false);
        }
    }

    const btn = document.getElementById('tab-trigger-' + tabId);
    if (btn) {
        btn.classList.add('nav-item-active');
    }
}

/**
 * DATATABLES INTEGRATION
 */
function initHistoryDataTable() {
    const tableEl = $('#historyTable');
    if (!tableEl.length) return;

    historyDataTable = tableEl.DataTable({
        autoWidth: false,
        pageLength: 10,
        pagingType: 'simple',
        order: [[3, 'desc']], // Order by time by default
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
            renderGhostRows(settings, 4);
        }
    });

    // Sync custom search input
    $('#logSearch').on('input', function() {
        historyDataTable.search(this.value).draw();
    });

    // Custom quick filters
    window.quickFilter = function(type) {
        if (type === 'all') {
            historyDataTable.search('').column(2).search('').draw();
        } else {
            // Search in column 2 (Event) using regex
            historyDataTable.column(2).search(type).draw();
        }

        // Update UI of buttons
        updateFilterUI(type);
    };

    // Register for global search
    window.activeNexusTable = historyDataTable;
}

function updateFilterUI(type) {
    const container = document.getElementById('logFiltersContainer');
    if (!container) return;
    
    const buttons = container.querySelectorAll('button');
    buttons.forEach(btn => {
        const btnOnclick = btn.getAttribute('onclick') || '';
        const isTarget = btnOnclick.includes(`'${type}'`);
        const isAll = btnOnclick.includes("'all'");
        const base = "p-3 rounded-2xl transition-all active:scale-95 border ";
        
        if (isAll) {
            btn.className = base + "bg-panel-fill/20 hover:bg-panel-fill/40 border-panel-border/30 text-label";
            return;
        }

        if (btnOnclick.toLowerCase().includes("'ok'")) {
            btn.className = base + (isTarget ? "bg-emerald-500 text-white border-emerald-500 shadow-lg shadow-emerald-500/20" : "bg-emerald-500/10 hover:bg-emerald-500/20 border-emerald-500/30 text-emerald-500");
        } else if (btnOnclick.toLowerCase().includes("'force_ok'")) {
            btn.className = base + (isTarget ? "bg-sky-500 text-white border-sky-500 shadow-lg shadow-sky-500/20" : "bg-sky-500/10 hover:bg-sky-500/20 border-sky-500/30 text-sky-400");
        } else if (btnOnclick.toLowerCase().includes("'fail'")) {
            btn.className = base + (isTarget ? "bg-rose-500 text-white border-rose-500 shadow-lg shadow-rose-500/20" : "bg-rose-500/10 hover:bg-rose-500/20 border-rose-500/30 text-rose-500");
        } else if (btnOnclick.toLowerCase().includes("'dup'")) {
            btn.className = base + (isTarget ? "bg-amber-500 text-white border-amber-500 shadow-lg shadow-amber-500/20" : "bg-amber-500/10 hover:bg-amber-500/20 border-amber-500/30 text-amber-500");
        }
    });
}

function renderGhostRows(settings, columns) {
    const api = new $.fn.dataTable.Api(settings);
    const info = api.page.info();
    const tbody = $(settings.nTBody);
    
    tbody.find('.dataTables_empty').closest('tr').remove();
    const rowsOnPage = info.end - info.start;
    const targetTotal = 10;
    const ghostCount = targetTotal - rowsOnPage;

    if (ghostCount <= 0) return;

    let ghostHtml = '';
    for (let i = 0; i < ghostCount; i++) {
        ghostHtml += `
            <tr class="animate-pulse pointer-events-none select-none opacity-20">
                <td class="bg-panel-fill/5 border-y border-l border-panel-border/10 rounded-l-2xl py-6 px-5">
                    <div class="h-2 w-24 bg-label/10 rounded-full"></div>
                </td>
                <td class="bg-panel-fill/5 border-y border-panel-border/10 py-6 px-5">
                    <div class="h-1.5 w-full bg-label/5 rounded-full"></div>
                </td>
                <td class="bg-panel-fill/5 border-y border-panel-border/10 py-6 px-5">
                    <div class="h-8 w-8 bg-label/5 rounded-lg mx-auto"></div>
                </td>
                <td class="bg-panel-fill/5 border-y border-r border-panel-border/10 rounded-r-2xl py-6 px-5">
                    <div class="h-1.5 w-12 bg-label/5 rounded-full ml-auto"></div>
                </td>
            </tr>
        `;
    }
    
    setTimeout(() => {
        tbody.append(ghostHtml);
    }, 0);
}

function reprocessDuplicates(taskId) {
    const modal = document.getElementById('reprocessModal');
    if (modal) {
        modal.classList.remove('opacity-0', 'pointer-events-none');
        modal.classList.add('opacity-100');
    }
}

function closeReprocessModal() {
    const modal = document.getElementById('reprocessModal');
    if (modal) {
        modal.classList.add('opacity-0', 'pointer-events-none');
        modal.classList.remove('opacity-100');
    }
}

// Cerrar modal con tecla ESC
window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeReprocessModal();
});

async function executeReprocess(taskId) {
    const btn = document.getElementById('confirmReprocessBtn');
    if (!btn) return;
    
    const originalContent = btn.innerHTML;
    btn.innerHTML = `
        <svg class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>Procesando...</span>
    `;
    btn.disabled = true;

    try {
        const res = await fetch(`/api/psx/reprocess_duplicates/${taskId}`, { method: 'POST' });
        const data = await res.json();
        
        if (data.status === 'success') {
            closeReprocessModal();
            // Notificamos éxito con el estilo de la plataforma (puedes usar un toast si tienes, si no alert por ahora)
            location.href = `/psx/view/${data.task_id}?tour=true`;
        } else {
            alert(`Error: ${data.message}`);
            btn.innerHTML = originalContent;
            btn.disabled = false;
        }
    } catch (err) {
        alert('Fallo de conexión con el servidor.');
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }
}
