/* PSX DETAIL MODULE - LOGIC DECOUPLING */

/**
 * Tab switching logic for Dashboard, Technical History, and CMD History.
 */
function switchTab(tabId) {
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('active', 'text-white');
        b.classList.add('text-slate-500');
        const dot = b.querySelector('div');
        dot.className = 'w-1.5 h-1.5 rounded-full bg-slate-600 transition-colors';
    });

    document.getElementById('tab-' + tabId).classList.add('active');
    const btn = document.getElementById('btn-' + tabId);
    btn.classList.add('active', 'text-white');
    btn.classList.remove('text-slate-500');
    
    const dot = btn.querySelector('div');
    if(tabId === 'dashboard') {
        dot.className = 'w-1.5 h-1.5 rounded-full bg-sky-500 shadow-[0_0_8px_rgba(14,165,233,1)]';
    } else if(tabId === 'logs') {
        dot.className = 'w-1.5 h-1.5 rounded-full bg-violet-500 shadow-[0_0_8px_rgba(139,92,246,1)]';
    } else if(tabId === 'cmd') {
        dot.className = 'w-1.5 h-1.5 rounded-full bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,1)]';
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

function filterHistory() {
    const input = document.getElementById('logSearch');
    if (!input) return;
    
    const filter = input.value.toUpperCase();
    const table = document.getElementById('historyTable');
    if (!table) return;
    
    const rows = Array.from(table.getElementsByClassName('history-row'));

    filteredRows = rows.filter(row => {
        const text = row.textContent || row.innerText;
        return text.toUpperCase().indexOf(filter) > -1;
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
            btn.className = `w-8 h-8 rounded-lg text-[10px] font-black transition-all ${i === currentPage ? 'bg-sky-500 text-white shadow-lg shadow-sky-500/20' : 'bg-white/5 text-slate-500 hover:bg-white/10'}`;
            btn.onclick = () => { currentPage = i; renderTable(); };
            container.appendChild(btn);
        } else if (i == currentPage - 2 || i == currentPage + 2) {
            const span = document.createElement('span');
            span.innerText = '...';
            span.className = 'text-slate-700 text-xs px-1';
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
