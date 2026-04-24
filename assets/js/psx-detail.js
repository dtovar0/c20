/* PSX DETAIL MODULE - LOGIC DECOUPLING */

/**
 * Tab switching logic for Dashboard, Technical History, and CMD History.
 */
function switchTab(tabId) {
    const panes = document.querySelectorAll('.tab-pane');
    panes.forEach(p => {
        p.classList.remove('active');
        p.style.opacity = '0';
        p.style.transform = 'translateY(10px)';
        p.style.transition = 'all 0.4s ease-out';
    });

    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('active');
        const dot = b.querySelector('div');
        if (dot) dot.className = 'w-1.5 h-1.5 rounded-full bg-label/20 transition-colors';
    });

    const activePane = document.getElementById('tab-' + tabId);
    activePane.classList.add('active');
    
    // Trigger animation
    setTimeout(() => {
        activePane.style.opacity = '1';
        activePane.style.transform = 'translateY(0)';
    }, 50);

    const btn = document.getElementById('btn-' + tabId);
    if (btn) {
        btn.classList.add('active');
        const dot = btn.querySelector('div');
        if(dot) {
            if(tabId === 'dashboard') dot.className = 'w-1.5 h-1.5 rounded-full bg-sky-500 shadow-[0_0_8px_rgba(14,165,233,1)]';
            else if(tabId === 'logs') dot.className = 'w-1.5 h-1.5 rounded-full bg-violet-500 shadow-[0_0_8px_rgba(139,92,246,1)]';
            else if(tabId === 'cmd') dot.className = 'w-1.5 h-1.5 rounded-full bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,1)]';
        }
    }
}

// Pagination & Search Logic
let currentPage = 1;
const rowsPerPage = 10;
let filteredRows = [];
let sortDirections = [true, true, true, true]; // Ascending by default

function initPagination() {
    const table = document.getElementById('historyTable');
    if (!table) return;
    const rows = Array.from(table.getElementsByClassName('history-row'));
    filteredRows = rows;
    renderTable();
}

function sortHistory(colIndex) {
    const table = document.getElementById('historyTable');
    if (!table) return;
    
    const rows = Array.from(table.getElementsByClassName('history-row'));
    const asc = sortDirections[colIndex];
    
    rows.sort((a, b) => {
        const valA = a.cells[colIndex].textContent.trim();
        const valB = b.cells[colIndex].textContent.trim();
        return asc ? valA.localeCompare(valB) : valB.localeCompare(valA);
    });

    // Update direction
    sortDirections[colIndex] = !asc;

    // Clear icons and set active one
    for(let i=0; i<4; i++) {
        const sortIcon = document.getElementById('sort-'+i);
        if(sortIcon) sortIcon.innerHTML = '';
    }
    const currentSortIcon = document.getElementById('sort-'+colIndex);
    if(currentSortIcon) currentSortIcon.innerHTML = asc ? '↑' : '↓';

    filteredRows = rows; 
    renderTable();
}

let currentQuickFilter = 'all';

function quickFilter(type) {
    const table = document.getElementById('historyTable');
    if (!table) return;
    
    const rows = Array.from(table.getElementsByClassName('history-row'));
    
    // LOGIC: Toggle off if clicking the same active filter
    if (type === currentQuickFilter && type !== 'all') {
        type = 'all';
    }
    
    currentQuickFilter = type;
    
    // Apply Filtering
    if (type === 'all') {
        filteredRows = rows;
    } else {
        filteredRows = rows.filter(row => {
            const statusCell = row.querySelector('.status-badge');
            return statusCell && statusCell.textContent.includes(type);
        });
    }

    // UPDATE UI STYLES (Dinamically)
    const container = document.getElementById('logFiltersContainer');
    if (container) {
        const buttons = container.querySelectorAll('button');
        buttons.forEach(btn => {
            const btnOnclick = btn.getAttribute('onclick') || '';
            const isTarget = btnOnclick.includes(`'${type}'`);
            const isAll = btnOnclick.includes("'all'");

            // Base classes (Common)
            const base = "p-3 rounded-2xl transition-all active:scale-95 border ";
            
            if (isAll) {
                // Return to neutral
                btn.className = base + "bg-panel-fill/20 hover:bg-panel-fill/40 border-panel-border/30 text-label";
                return;
            }

            if (btnOnclick.includes("'OK'")) {
                btn.className = base + (isTarget ? "bg-emerald-500 text-white border-emerald-500 shadow-lg shadow-emerald-500/20" : "bg-emerald-500/10 hover:bg-emerald-500/20 border-emerald-500/30 text-emerald-500");
            } else if (btnOnclick.includes("'FAIL'")) {
                btn.className = base + (isTarget ? "bg-rose-500 text-white border-rose-500 shadow-lg shadow-rose-500/20" : "bg-rose-500/10 hover:bg-rose-500/20 border-rose-500/30 text-rose-500");
            } else if (btnOnclick.includes("'DUP'")) {
                btn.className = base + (isTarget ? "bg-amber-500 text-white border-amber-500 shadow-lg shadow-amber-500/20" : "bg-amber-500/10 hover:bg-amber-500/20 border-amber-500/30 text-amber-500");
            }
        });
    }

    currentPage = 1;
    renderTable();
}

function filterHistory() {
    const input = document.getElementById('logSearch');
    if (!input) return;
    
    const filter = input.value.toUpperCase();
    const table = document.getElementById('historyTable');
    if (!table) return;
    
    const rows = Array.from(table.getElementsByClassName('history-row'));

    filteredRows = rows.filter(row => {
        const text = row.innerText.toUpperCase();
        return text.includes(filter);
    });

    currentPage = 1;
    renderTable();
}

function renderTable() {
    const total = filteredRows.length;
    const table = document.getElementById('historyTable');
    if (!table) return;
    
    const allRows = Array.from(table.getElementsByClassName('history-row'));
    
    // Hide everything first
    allRows.forEach(row => row.style.display = 'none');

    // Show slice
    const start = (currentPage - 1) * rowsPerPage;
    const end = Math.min(start + rowsPerPage, total);
    
    for(let i = start; i < end; i++) {
        filteredRows[i].style.display = '';
    }

    // Update info
    const totalCountEl = document.getElementById('totalCount');
    const rangeStartEl = document.getElementById('rangeStart');
    const rangeEndEl = document.getElementById('rangeEnd');
    
    if(totalCountEl) totalCountEl.innerText = total;
    if(rangeStartEl) rangeStartEl.innerText = total === 0 ? 0 : start + 1;
    if(rangeEndEl) rangeEndEl.innerText = end;

    // Update buttons
    const totalPages = Math.ceil(total / rowsPerPage);
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    
    if(prevBtn) prevBtn.disabled = currentPage === 1;
    if(nextBtn) nextBtn.disabled = currentPage === totalPages || totalPages === 0;

    renderPageNumbers(totalPages);
}

function renderPageNumbers(total) {
    const container = document.getElementById('pageNumbers');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (total <= 1) return;

    for(let i = 1; i <= total; i++) {
        if(i == 1 || i == total || (i >= currentPage - 1 && i <= currentPage + 1)) {
            const btn = document.createElement('button');
            btn.innerText = i;
            btn.className = `w-9 h-9 rounded-xl text-[12px] font-black transition-all flex items-center justify-center ${i === currentPage ? 'bg-primary text-panel-fill shadow-lg shadow-primary/20 border border-primary' : 'bg-panel-fill/30 text-label border border-panel-border/20 hover:bg-panel-fill/50 hover:border-primary/20'}`;
            btn.onclick = () => { currentPage = i; renderTable(); };
            container.appendChild(btn);
        } else if (i == currentPage - 2 || i == currentPage + 2) {
            const span = document.createElement('span');
            span.innerText = '...';
            span.className = 'text-label/40 text-[10px] px-0.5 font-black';
            container.appendChild(span);
        }
    }
}

function changePage(dir) {
    currentPage += dir;
    renderTable();
}

async function reprocessDuplicates(taskId) {
    if(!confirm('¿Desea crear una nueva tarea utilizando únicamente los registros duplicados?')) return;
    
    const btn = document.getElementById('reprocessBtn');
    if (!btn) return;
    
    const originalText = btn.innerText;
    btn.innerText = 'PROCESANDO...';
    btn.disabled = true;

    try {
        const res = await fetch(`/api/psx/reprocess_duplicates/${taskId}`, { method: 'POST' });
        const data = await res.json();
        
        if (data.status === 'success') {
            alert(`Éxito: Se ha creado la Tarea #${data.task_id}`);
            window.location.href = `/psx/view/${data.task_id}`;
        } else {
            alert(`Error: ${data.message}`);
            btn.innerText = originalText;
            btn.disabled = false;
        }
    } catch (err) {
        alert('Fallo de conexión con el servidor.');
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

// Initialize on load
window.onload = initPagination;
