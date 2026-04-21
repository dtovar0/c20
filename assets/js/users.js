/**
 * MODULE: Local User Management
 * Logic for rendering and paginating the local users table.
 */

// Demo User Database
const localUsersData = [
    { id: 1, name: 'dtovar', role: 'Super Admin', email: 'dtovar@nexus.core', activity: 'Hace 2 minutos', status: 'active' },
    { id: 2, name: 'admin_security', role: 'Security Ops', email: 'sec@nexus.core', activity: 'Hace 1 hora', status: 'active' },
    { id: 3, name: 'guest_observer', role: 'Viewer', email: 'guest@nexus.core', activity: 'Ayer, 14:20', status: 'inactive' },
    { id: 4, name: 'system_bot', role: 'Automation', email: 'bot@nexus.core', activity: 'En línea', status: 'active' },
    { id: 5, name: 'temp_user_01', role: 'External', email: 'ext@nexus.core', activity: 'Nunca', status: 'suspended' }
];

let currentUsersPage = 1;
const usersPerPage = 8;
let filteredUsers = [...localUsersData];

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
                <td colspan="4" class="px-6 py-6 bg-surface-container/10 border-y border-panel-border/20 text-center">
                    <span class="text-[10px] font-black uppercase tracking-[0.2em] text-label italic opacity-30">No se encontraron usuarios locales</span>
                </td>
                <td colspan="1" class="px-6 py-6 bg-surface-container/10 border-y border-r border-panel-border/20 rounded-r-2xl text-center"></td>
            </tr>
        `;
        rowsRendered = 1;
    } else {
        pageData.forEach(user => {
            const statusClass = {
                active: 'bg-green-500/10 text-green-500',
                inactive: 'bg-label/10 text-label/40',
                suspended: 'bg-red-500/10 text-red-500'
            }[user.status];

            const roleIcon = user.role.includes('Admin') 
                ? '<svg class="w-3 h-3 text-primary" fill="currentColor" viewBox="0 0 20 20"><path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/><path fill-rule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"/></svg>'
                : '<svg class="w-3 h-3 text-label/40" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/></svg>';

            html += `
                <tr class="transition-all group active:scale-[0.995] cursor-default">
                    <td class="px-6 py-3 bg-surface-container border-y border-l border-surface-container-border rounded-l-2xl group-hover:border-primary/30 transition-colors">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-[10px] font-black text-primary border border-primary/20">
                                ${user.name.charAt(0).toUpperCase()}
                            </div>
                            <span class="text-[11px] font-black text-label uppercase tracking-tighter">${user.name}</span>
                        </div>
                    </td>
                    <td class="px-4 py-3 bg-surface-container border-y border-surface-container-border group-hover:border-primary/30 transition-colors">
                        <div class="flex items-center gap-2">
                            ${roleIcon}
                            <span class="text-[10px] font-bold text-label/60 uppercase tracking-widest">${user.role}</span>
                        </div>
                    </td>
                    <td class="px-4 py-3 bg-surface-container border-y border-surface-container-border group-hover:border-primary/30 transition-colors">
                        <span class="text-[10px] font-mono text-label/40">${user.email}</span>
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
                <td class="px-6 py-3 bg-surface-container/5 border-y border-r border-surface-container-border/20 rounded-r-2xl text-right">
                    <div class="h-4 w-16 bg-label/10 rounded-full ml-auto opacity-10"></div>
                </td>
            </tr>
        `;
    }

    tbody.innerHTML = html;
    updateUsersPagination();
}

function updateUsersPagination() {
    const infoEl = document.getElementById('usersPaginationInfo');
    const total = filteredUsers.length;
    const start = total === 0 ? 0 : (currentUsersPage - 1) * usersPerPage + 1;
    const end = Math.min(currentUsersPage * usersPerPage, total);
    if (infoEl) infoEl.innerText = `Mostrando ${start}-${end} de ${total} usuarios locales`;
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
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
            renderUsersTable();
        });
    }
    renderUsersTable();
});
