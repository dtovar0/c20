/**
 * MODULE: Local User Management
 * Logic for rendering, selecting and managing local users.
 */

// Professional Demo User Database
const localUsersData = [
    { id: 1, name: 'Daniel Tovar', role: 'Administrator', email: 'dtovar@nexus-infra.com', status: 'active' },
    { id: 2, name: 'Sarah Chen', role: 'Security Architect', email: 'schen@nexus-infra.com', status: 'active' },
    { id: 3, name: 'Marco Rosso', role: 'Network Operator', email: 'mrosso@nexus-infra.com', status: 'active' },
    { id: 4, name: 'Alex Novak', role: 'Audit Compliance', email: 'anovak@nexus-infra.com', status: 'inactive' },
    { id: 5, name: 'Service Engine', role: 'System', email: 'engine@nexus-internal.svc', status: 'active' },
    { id: 6, name: 'External Auditor', role: 'Guest', email: 'auditor@external.com', status: 'suspended' }
];

let currentUsersPage = 1;
const usersPerPage = 8;
let filteredUsers = [...localUsersData];
let selectedUsers = new Set();

/**
 * Renders the users table content
 */
function renderUsersTable() {
    const tbody = document.getElementById('usersTableBody');
    if (!tbody) return;

    let html = '';
    const start = (currentUsersPage - 1) * usersPerPage;
    const end = start + usersPerPage;
    const pageData = filteredUsers.slice(start, end);
    let rowsRendered = 0;

    if (filteredUsers.length === 0) {
        html += `
            <tr class="group transition-all duration-300">
                <td colspan="1" class="px-6 py-6 bg-surface-container/10 border-y border-l border-panel-border/20 rounded-l-2xl text-center">
                    <div class="flex items-center justify-center gap-3 opacity-30">
                        <svg class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
                    </div>
                </td>
                <td colspan="3" class="px-6 py-6 bg-surface-container/10 border-y border-panel-border/20 text-center">
                    <span class="text-[10px] font-black uppercase tracking-[0.2em] text-label italic opacity-30">No se encontraron usuarios locales</span>
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

            const roleIcon = user.role.includes('Admin') 
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

    // Ghost rows for stable layout
    const ghostRowsCount = usersPerPage - rowsRendered;
    for (let i = 0; i < ghostRowsCount; i++) {
        html += `
            <tr class="pointer-events-none select-none">
                <td class="px-6 py-3 bg-surface-container/5 border-y border-l border-surface-container-border/20 rounded-l-2xl text-transparent">-</td>
                <td class="px-4 py-3 bg-surface-container/5 border-y border-surface-container-border/20 text-transparent">-</td>
                <td class="px-4 py-3 bg-surface-container/5 border-y border-surface-container-border/20 text-transparent">-</td>
                <td class="px-4 py-3 bg-surface-container/5 border-y border-surface-container-border/20 text-transparent">-</td>
                <td class="px-6 py-3 bg-surface-container/5 border-y border-r border-surface-container-border/20 rounded-r-2xl text-right">
                    <div class="h-4 w-16 bg-label/10 rounded-full ml-auto opacity-10"></div>
                </td>
            </tr>
        `;
    }

    tbody.innerHTML = html;
    updateUsersPagination();
    updateUserActions();
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
    const pageData = filteredUsers.slice(start, end);

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

    // Default: both disabled
    btnModify.disabled = true;
    btnDelete.disabled = true;

    if (count === 1) {
        btnModify.disabled = false;
        btnDelete.disabled = false;
    } else if (count >= 2) {
        btnModify.disabled = true;
        btnDelete.disabled = false;
    }
}

function updateUsersPagination() {
    const infoEl = document.getElementById('usersPaginationInfo');
    const total = filteredUsers.length;
    const start = total === 0 ? 0 : (currentUsersPage - 1) * usersPerPage + 1;
    const end = Math.min(currentUsersPage * usersPerPage, total);
    if (infoEl) infoEl.innerText = `Mostrando ${start}-${end} de ${total} usuarios locales`;
}

// Global actions placeholders
function modifyUser() {
    const targetId = Array.from(selectedUsers)[0];
    const user = localUsersData.find(u => u.id === targetId);
    if (user) {
        console.log(`Modificando usuario: ${user.name} (ID: ${user.id})`);
        // showToast(`Editando a ${user.name}`, 'info');
    }
}

function deleteUser() {
    const count = selectedUsers.size;
    console.log(`Eliminando ${count} usuarios: ${Array.from(selectedUsers).join(', ')}`);
    // showToast(`${count} usuarios eliminados permanentemente`, 'success');
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Search logic
    const searchInput = document.getElementById('userSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            filteredUsers = localUsersData.filter(user => 
                user.name.toLowerCase().includes(term) ||
                user.role.toLowerCase().includes(term) ||
                user.email.toLowerCase().includes(term)
            );
            currentUsersPage = 1;
            selectedUsers.clear(); // Clear selection on search
            renderUsersTable();
        });
    }

    // Select All logic
    const selectAll = document.getElementById('selectAllUsers');
    if (selectAll) {
        selectAll.addEventListener('change', (e) => {
            toggleAllUsers(e.target.checked);
        });
    }

    renderUsersTable();
});
