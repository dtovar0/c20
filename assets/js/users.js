/**
 * Returns optimal pageLength based on viewport height.
 *   < 900px → 8 rows   >= 900px → 10 rows
 */
function getPageLength() {
    const h = window.innerHeight;
    if (h < 900) return 8;
    return 10;
}

/**
 * MODULE: Local User Management (DataTables Powered)
 * Logic for fetching, rendering, and managing users from the real database.
 */

let usersDataTable;
let selectedUsers = new Set();

/**
 * INITIALIZATION
 */
$(document).ready(function() {
    initUsersDataTable();

    // Universal Search Integration with Debounce
    let searchTimeout;
    $('#userSearch').on('input', function() {
        clearTimeout(searchTimeout);
        const term = this.value;
        searchTimeout = setTimeout(() => {
            if (usersDataTable) {
                usersDataTable.search(term).draw();
            }
        }, 300);
    });

    // Select All logic
    $('#selectAllUsers').on('change', function() {
        const isChecked = this.checked;
        const nodes = usersDataTable.rows({ page: 'current' }).nodes().to$();
        const data = usersDataTable.rows({ page: 'current' }).data();

        nodes.each(function(index) {
            const userId = data[index].id;
            if (isChecked) {
                selectedUsers.add(userId);
                $(this).addClass('bg-primary/5');
                $(this).find('.nexus-checkbox').prop('checked', true);
            } else {
                selectedUsers.delete(userId);
                $(this).removeClass('bg-primary/5');
                $(this).find('.nexus-checkbox').prop('checked', false);
            }
        });

        updateUserActions();
    });

    updateUserActions();
});

/**
 * Initializes DataTables for Users
 */
function initUsersDataTable() {
    const tableEl = $('#usersTableBody').closest('table');
    if (!tableEl.length) return;

    usersDataTable = tableEl.DataTable({
        ajax: {
            url: '/auth/users/list', // El backend ya soporta ?search= pero DataTables lo hace client-side por defecto si cargamos todo
            dataSrc: ''
        },
        columns: [
            { 
                data: 'id', 
                orderable: false,
                width: '60px',
                render: (data, type, row) => {
                    const isSelected = selectedUsers.has(row.id);
                    return `<div class="flex items-center h-full justify-center">
                                <input type="checkbox" ${isSelected ? 'checked' : ''} class="nexus-checkbox pointer-events-none">
                            </div>`;
                }
            },
            { 
                data: 'nombre', 
                width: 'auto',
                render: (data) => `
                    <div class="flex items-center gap-3 overflow-hidden">
                        <div class="w-8 h-8 rounded-full bg-primary/10 flex-shrink-0 flex items-center justify-center text-[12px] font-black text-primary border border-primary/20">
                            ${(data || '?').charAt(0).toUpperCase()}
                        </div>
                        <span class="text-[12px] font-black text-label uppercase tracking-tighter truncate">${data || '-'}</span>
                    </div>`
            },
            { data: 'name', width: '220px', render: (data) => `<div class="flex items-center h-full text-[12px] font-mono text-label/40 truncate">${data}</div>` },
            { 
                data: 'source', 
                width: '100px',
                render: (data) => {
                    const isLdap = data.toLowerCase() === 'ldap';
                    const sourceClass = isLdap ? 'bg-primary/10 text-primary border-primary/20' : 'bg-label/5 text-label/40 border-panel-border';
                    return `
                        <div class="flex items-center h-full">
                            <span class="px-2 py-0.5 rounded-lg border text-[12px] font-black uppercase tracking-widest ${sourceClass}">${data}</span>
                        </div>`;
                }
            },
            { 
                data: 'role', 
                width: '140px',
                render: (data) => {
                    const isAdmin = data.toLowerCase().includes('admin');
                    const roleIcon = isAdmin 
                        ? '<svg class="w-3 h-3 text-primary flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/><path fill-rule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"/></svg>'
                        : '<svg class="w-3 h-3 text-label/40 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/></svg>';
                    return `
                        <div class="flex items-center h-full gap-2 overflow-hidden">
                            ${roleIcon}
                            <span class="text-[12px] font-bold text-label/60 uppercase tracking-widest truncate">${data}</span>
                        </div>`;
                }
            },
            { 
                data: 'status', 
                width: '100px',
                className: 'text-right',
                render: (data) => {
                    const statusClass = {
                        active: 'bg-green-500/10 text-green-500',
                        inactive: 'bg-label/10 text-label/40',
                        suspended: 'bg-red-500/10 text-red-500'
                    }[data.toLowerCase()] || 'bg-label/10 text-label/40';
                    return `<div class="flex items-center justify-end h-full"><span class="px-3 py-0.5 rounded-full text-[12px] font-black uppercase tracking-widest ${statusClass}">${data}</span></div>`;
                }
            }
        ],
        autoWidth: false,
        pageLength: getPageLength(),
        pagingType: 'simple',
        order: [[1, 'asc']], // Sort by Name by default to avoid arrow on checkbox column
        layout: {
            topStart: null,
            topEnd: null,
            bottomStart: 'info',
            bottomEnd: 'paging'
        },
        language: {
            zeroRecords: "No se encontraron usuarios",
            info: "Mostrando _START_-_END_ de _TOTAL_ registros",
            infoEmpty: "Mostrando 0-0 de 0 registros",
            infoFiltered: "(filtrado de _MAX_ registros totales)",
            paginate: {
                previous: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>',
                next: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>'
            }
        },
        drawCallback: function(settings) {
            const api = new $.fn.dataTable.Api(settings);
            const visibleCols = api.columns(':visible').count();
            renderGhostRows(settings, visibleCols);
            updateUserActions();
        },
        initComplete: function() {
            // Wrap table in .nx-table-scroll for height measurement
            const cell = $(this.api().table().container()).find('.dt-layout-row.dt-layout-table .dt-layout-cell');
            const tbl  = cell.children('table');
            if (tbl.length && !cell.children('.nx-table-scroll').length) {
                tbl.wrap('<div class="nx-table-scroll"></div>');
            }
            // Resize: recalculate pageLength and row heights
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
        },
        createdRow: function(row, data) {
            $(row).addClass('transition-colors duration-200 group cursor-pointer');
            if (selectedUsers.has(data.id)) {
                $(row).addClass('bg-primary/5');
            }
            $(row).on('click', function(e) {
                // Prevent toggle if clicking a button inside the row
                if ($(e.target).closest('button, a').length) return;
                toggleUserSelection(data.id, this);
            });
        }
    });

    // Register globally for top bar search
    window.activeNexusTable = usersDataTable;
}

function toggleUserSelection(userId, rowEl) {
    // If we don't have rowEl, let's try to find it in the current page
    if (!rowEl) {
        rowEl = usersDataTable.rows().nodes().to$().filter(function() {
            return usersDataTable.row(this).data().id === userId;
        });
    }

    if (selectedUsers.has(userId)) {
        selectedUsers.delete(userId);
        $(rowEl).removeClass('bg-primary/5');
        $(rowEl).find('.nexus-checkbox').prop('checked', false);
    } else {
        selectedUsers.add(userId);
        $(rowEl).addClass('bg-primary/5');
        $(rowEl).find('.nexus-checkbox').prop('checked', true);
    }
    
    // Sync Select All checkbox state
    const totalOnPage = usersDataTable.rows({ page: 'current' }).data().length;
    const selectedOnPage = usersDataTable.rows({ page: 'current' }).nodes().to$().find('.nexus-checkbox:checked').length;
    $('#selectAllUsers').prop('checked', selectedOnPage > 0 && selectedOnPage === totalOnPage);

    updateUserActions();
}

/**
 * Updates the state of action buttons based on selection
 */
function updateUserActions() {
    const btnModify = document.getElementById('btn-modify-user');
    const btnDelete = document.getElementById('btn-delete-user');
    const count = selectedUsers.size;

    if (!btnModify || !btnDelete) return;

    btnModify.disabled = (count !== 1);
    btnDelete.disabled = (count < 1);
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
    if (usersDataTable) usersDataTable.draw(false);
});

// Global actions
function addUserModal() {
    openModal('modal-add-user');
}

function modifyUser() {
    const targetId = Array.from(selectedUsers)[0];
    const user = usersDataTable.rows().data().toArray().find(u => u.id === targetId);
    if (user) {
        openModal('modal-modify-user');
        const form = document.getElementById('form-modify-user');
        if (form) {
            form.elements['user_id'].value = user.id;
            form.elements['username'].value = user.name;
            form.elements['nombre'].value = user.nombre;
            
            const isAdmin = user.role.toLowerCase() === 'admin';
            form.elements['is_admin'].checked = isAdmin;
            
            const textEl = document.getElementById('admin_role_text_modify');
            if (textEl) textEl.textContent = isAdmin ? 'Rol: Administrador Total' : 'Rol: Usuario Estándar';
        }
    }
}

function deleteUser() {
    const count = selectedUsers.size;
    const displayEl = document.getElementById('delete-user-display');
    const msgEl = document.getElementById('delete-modal-msg');
    
    if (displayEl) {
        if (count === 1) {
            const targetId = Array.from(selectedUsers)[0];
            const user = usersDataTable.rows().data().toArray().find(u => u.id === targetId);
            displayEl.textContent = user ? user.name : 'Identidad Seleccionada';
            displayEl.classList.add('text-white/90');
        } else {
            displayEl.textContent = `${count} Usuarios`;
            displayEl.classList.add('text-red-500');
        }
    }

    if (msgEl) {
        msgEl.innerText = count === 1 
            ? `Estás a punto de eliminar permanentemente este usuario. Esta acción no se puede deshacer.`
            : `Estás a punto de eliminar permanentemente ${count} usuarios de la matriz. Esta acción es irreversible.`;
    }
    openModal('modal-delete-confirm');
}

// FORM: Add User
$(document).on('submit', '#form-add-user', async function(e) {
    e.preventDefault();
    if (!validateNexusForm('modal-add-user')) return;

    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());
    data.role = data.is_admin ? 'admin' : 'user';
    delete data.is_admin;

    try {
        const response = await fetch('/auth/users/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const res = await response.json();
        
        if (res.status === 'success') {
            closeModal('modal-add-user');
            this.reset();
            document.getElementById('admin_role_text_add').textContent = 'Rol: Usuario Estándar';
            usersDataTable.ajax.reload(null, false);
            if(typeof showToast === 'function') showToast('Usuario creado correctamente', 'success');
        } else {
            showToast(res.message, 'error');
        }
    } catch (error) {
        console.error('Error creating user:', error);
    }
});

// ACTION: Confirm Delete
$(document).on('click', '#confirm-delete-action', async function() {
    const ids = Array.from(selectedUsers);
    try {
        const response = await fetch('/auth/users/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids })
        });
        const res = await response.json();
        
        if (res.status === 'success') {
            closeModal('modal-delete-confirm');
            selectedUsers.clear();
            usersDataTable.ajax.reload(null, false);
            if(typeof showToast === 'function') showToast(`${ids.length} usuarios eliminados`, 'success');
        }
    } catch (error) {
        console.error('Error deleting users:', error);
    }
});

// FORM: Modify User
$(document).on('submit', '#form-modify-user', async function(e) {
    e.preventDefault();
    if (!validateNexusForm('modal-modify-user')) return;

    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());
    data.role = data.is_admin ? 'admin' : 'user';
    delete data.is_admin;

    try {
        const response = await fetch('/auth/users/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const res = await response.json();
        
        if (res.status === 'success') {
            closeModal('modal-modify-user');
            selectedUsers.clear();
            usersDataTable.ajax.reload(null, false);
            if(typeof showToast === 'function') showToast('Usuario actualizado', 'success');
        } else {
            showToast(res.message, 'error');
        }
    } catch (error) {
        console.error('Error updating user:', error);
    }
});
