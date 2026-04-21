/**
 * MODULE: Local User Management
 * Logic for fetching, rendering, and managing users from the real database.
 */

let currentUsersPage = 1;
const usersPerPage = 6;
let fetchedUsers = [];
let selectedUsers = new Set();
let isFetching = false;

/**
 * Fetches users from the API with optional search term
 */
async function fetchUsers(searchTerm = '') {
    if (isFetching) return;
    isFetching = true;

    try {
        const response = await fetch(`/auth/users/list?search=${encodeURIComponent(searchTerm)}`);
        if (!response.ok) throw new Error('Error al conectar con la base de datos');
        
        fetchedUsers = await response.json();
        renderUsersTable();
    } catch (error) {
        console.error('Fetch Error:', error);
        showUsersError();
    } finally {
        isFetching = false;
    }
}

/**
 * Renders the users table content
 */
function renderUsersTable() {
    const tbody = document.getElementById('usersTableBody');
    if (!tbody) return;

    let html = '';
    const start = (currentUsersPage - 1) * usersPerPage;
    const end = start + usersPerPage;
    const pageData = fetchedUsers.slice(start, end);
    let rowsRendered = 0;

    if (fetchedUsers.length === 0) {
        html += `
            <tr class="group transition-all duration-300">
                <td colspan="1" class="px-6 py-6 bg-surface-container/10 border-y border-l border-panel-border/20 rounded-l-2xl text-center">
                    <div class="flex items-center justify-center gap-3 opacity-30">
                        <svg class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
                    </div>
                </td>
                <td colspan="3" class="px-6 py-6 bg-surface-container/10 border-y border-panel-border/20 text-center">
                    <span class="text-[10px] font-black uppercase tracking-[0.2em] text-label italic opacity-30">No se encontraron registros en la base de datos</span>
                </td>
                <td colspan="1" class="px-6 py-6 bg-surface-container/10 border-y border-r border-panel-border/20 rounded-r-2xl text-center"></td>
            </tr>
        `;
        rowsRendered = 1;
    } else {
        pageData.forEach(user => {
            const isSelected = selectedUsers.has(user.id);
            const statusClass = {
                active: 'bg-green-500/10 text-green-500',
                inactive: 'bg-label/10 text-label/40',
                suspended: 'bg-red-500/10 text-red-500'
            }[user.status];

            const roleIcon = user.role.toLowerCase().includes('admin') 
                ? '<svg class="w-3 h-3 text-primary" fill="currentColor" viewBox="0 0 20 20"><path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/><path fill-rule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"/></svg>'
                : '<svg class="w-3 h-3 text-label/40" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/></svg>';

            html += `
                <tr onclick="toggleUserSelection(${user.id})" class="transition-all group active:scale-[0.995] cursor-pointer ${isSelected ? 'bg-primary/5' : ''}">
                    <td class="px-6 py-3 bg-surface-container border-y border-l border-surface-container-border rounded-l-2xl group-hover:border-primary/30 transition-colors w-12">
                        <input type="checkbox" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation(); toggleUserSelection(${user.id})" class="nexus-checkbox">
                    </td>
                    <td class="px-4 py-3 bg-surface-container border-y border-surface-container-border group-hover:border-primary/30 transition-colors">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-[10px] font-black text-primary border border-primary/20">
                                ${user.name.charAt(0).toUpperCase()}
                            </div>
                            <span class="text-[11px] font-black text-label uppercase tracking-tighter">${user.name}</span>
                        </div>
                    </td>
                    <td class="px-4 py-3 bg-surface-container border-y border-surface-container-border group-hover:border-primary/30 transition-colors">
                        <span class="text-[10px] font-mono text-label/40">${user.email}</span>
                    </td>
                    <td class="px-4 py-3 bg-surface-container border-y border-surface-container-border group-hover:border-primary/30 transition-colors">
                        <div class="flex items-center gap-2">
                            ${roleIcon}
                            <span class="text-[10px] font-bold text-label/60 uppercase tracking-widest">${user.role}</span>
                        </div>
                    </td>
                    <td class="px-6 py-3 text-right bg-surface-container border-y border-r border-surface-container-border rounded-r-2xl group-hover:border-primary/30 transition-colors">
                        <span class="px-3 py-0.5 rounded-full text-[8px] font-black uppercase tracking-widest ${statusClass}">${user.status}</span>
                    </td>
                </tr>
            `;
            rowsRendered++;
        });
    }

    // Ghost rows for stable layout (Standardized with Audit table)
    const ghostRowsCount = usersPerPage - rowsRendered;
    for (let i = 0; i < ghostRowsCount; i++) {
        html += `
            <tr class="group transition-all duration-300 pointer-events-none select-none">
                <td class="py-8 bg-surface-container/10 rounded-l-2xl border-y border-l border-panel-border/20" colspan="1"></td>
                <td class="py-8 bg-surface-container/10 border-y border-panel-border/20 text-center" colspan="3">
                    <div class="h-1.5 w-32 bg-label/20 dark:bg-white/10 rounded-full mx-auto"></div>
                </td>
                <td class="py-8 bg-surface-container/10 rounded-r-2xl border-y border-r border-panel-border/20" colspan="1"></td>
            </tr>
        `;
    }

    tbody.innerHTML = html;
    updateUsersPagination();
    updateUserActions();
}

function showUsersError() {
    const tbody = document.getElementById('usersTableBody');
    if (tbody) {
        tbody.innerHTML = `<tr><td colspan="5" class="py-12 text-center text-red-500 font-bold uppercase text-[9px] tracking-widest opacity-60">Falla de enlace con servicio de datos</td></tr>`;
    }
}

/**
 * Toggles a single user selection
 */
function toggleUserSelection(userId) {
    if (selectedUsers.has(userId)) {
        selectedUsers.delete(userId);
    } else {
        selectedUsers.add(userId);
    }
    renderUsersTable();
}

/**
 * Toggles all users on current page
 */
function toggleAllUsers(checked) {
    const start = (currentUsersPage - 1) * usersPerPage;
    const end = start + usersPerPage;
    const pageData = fetchedUsers.slice(start, end);

    pageData.forEach(user => {
        if (checked) {
            selectedUsers.add(user.id);
        } else {
            selectedUsers.delete(user.id);
        }
    });

    renderUsersTable();
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

function updateUsersPagination() {
    const infoEl = document.getElementById('usersPaginationInfo');
    const btnPrev = document.getElementById('prevUsersPage');
    const btnNext = document.getElementById('nextUsersPage');

    const total = fetchedUsers.length;
    const totalPages = Math.ceil(total / usersPerPage);
    const start = total === 0 ? 0 : (currentUsersPage - 1) * usersPerPage + 1;
    const end = Math.min(currentUsersPage * usersPerPage, total);

    if (infoEl) infoEl.innerText = `Mostrando ${start}-${end} de ${total} registros reales`;
    
    // Update button states
    if (btnPrev) btnPrev.disabled = (currentUsersPage <= 1);
    if (btnNext) btnNext.disabled = (currentUsersPage >= totalPages || total === 0);
}

// Modal Controls
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden'; // Prevent scroll
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = ''; // Restore scroll
    }
}

// Global actions
function addUserModal() {
    openModal('modal-add-user');
}

function modifyUser() {
    const targetId = Array.from(selectedUsers)[0];
    const user = fetchedUsers.find(u => u.id === targetId);
    if (user) {
        console.log(`📡 Solicitud de edición para: ${user.name}`);
        // Logica para cargar datos en modal de edicion
    }
}

function deleteUser() {
    const count = selectedUsers.size;
    const msgEl = document.getElementById('delete-modal-msg');
    if (msgEl) {
        msgEl.innerText = `Estás a punto de eliminar permanentemente ${count} usuario(s) de la base de datos. Esta acción no se puede deshacer.`;
    }
    openModal('modal-delete-confirm');
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Search logic with Debounce
    let searchTimeout;
    const searchInput = document.getElementById('userSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const term = e.target.value;
                selectedUsers.clear();
                fetchUsers(term);
            }, 300);
        });
    }

    // Select All logic
    const selectAll = document.getElementById('selectAllUsers');
    if (selectAll) {
        selectAll.addEventListener('change', (e) => {
            toggleAllUsers(e.target.checked);
        });
    }

    // Pagination Listeners
    const btnPrev = document.getElementById('prevUsersPage');
    const btnNext = document.getElementById('nextUsersPage');

    if (btnPrev) {
        btnPrev.addEventListener('click', () => {
            if (currentUsersPage > 1) {
                currentUsersPage--;
                selectedUsers.clear();
                renderUsersTable();
            }
        });
    }

    if (btnNext) {
        btnNext.addEventListener('click', () => {
            const totalPages = Math.ceil(fetchedUsers.length / usersPerPage);
            if (currentUsersPage < totalPages) {
                currentUsersPage++;
                selectedUsers.clear();
                renderUsersTable();
            }
        });
    }

    // FORM: Add User
    const formAdd = document.getElementById('form-add-user');
    if (formAdd) {
        formAdd.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(formAdd);
            const data = Object.fromEntries(formData.entries());

            try {
                const response = await fetch('/auth/users/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const res = await response.json();
                
                if (res.status === 'success') {
                    closeModal('modal-add-user');
                    formAdd.reset();
                    fetchUsers();
                    if(typeof showToast === 'function') showToast('Usuario creado correctamente', 'success');
                } else {
                    alert(res.message);
                }
            } catch (error) {
                console.error('Error creating user:', error);
            }
        });
    }

    // ACTION: Confirm Delete
    const btnConfirmDelete = document.getElementById('confirm-delete-action');
    if (btnConfirmDelete) {
        btnConfirmDelete.addEventListener('click', async () => {
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
                    fetchUsers();
                    if(typeof showToast === 'function') showToast(`${ids.length} usuarios eliminados`, 'success');
                }
            } catch (error) {
                console.error('Error deleting users:', error);
            }
        });
    }

    // Initial Load
    fetchUsers();
});
