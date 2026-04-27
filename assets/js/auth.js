// Authentication Management Module
document.addEventListener('DOMContentLoaded', function() {
    const userData = [
        { id: 1, user: 'DTOVAR', email: 'david.tovar@nexus.ai', role: 'Superadmin', lastLogin: '2026-04-17 18:45:12', status: 'active' },
        { id: 2, user: 'SYSTEM', email: 'system@internal.ai', role: 'System', lastLogin: '2026-04-17 16:40:05', status: 'active' },
        { id: 3, user: 'JDIAZ', email: 'jorge.diaz@nexus.ai', role: 'Admin', lastLogin: '2026-04-16 12:35:20', status: 'active' },
        { id: 4, user: 'LPEREZ', email: 'laura.perez@nexus.ai', role: 'Editor', lastLogin: '2026-04-15 10:30:00', status: 'inactive' },
        { id: 5, user: 'MRODRIGUEZ', email: 'm.rodriguez@nexus.ai', role: 'Viewer', lastLogin: '2026-04-14 09:15:15', status: 'locked' },
        { id: 6, user: 'AGARCIA', email: 'ana.garcia@nexus.ai', role: 'Admin', lastLogin: '2026-04-13 14:10:22', status: 'active' },
        { id: 7, user: 'FSUAREZ', email: 'f.suarez@nexus.ai', role: 'Editor', lastLogin: '2026-04-12 11:05:01', status: 'active' },
        { id: 8, user: 'BCASTRO', email: 'betty@nexus.ai', role: 'Viewer', lastLogin: '2026-04-11 08:00:55', status: 'inactive' }
    ];

    let filteredData = [...userData];
    let currentPage = 1;
    const recordsPerPage = 8;

    const tbody = document.getElementById('authTableBody');
    const searchInput = document.getElementById('authSearch');
    const refreshBtn = document.getElementById('refreshAuth');
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    const paginationInfo = document.getElementById('paginationInfo');

    function renderTable() {
        if (!tbody) return;
        tbody.innerHTML = '';
        
        const start = (currentPage - 1) * recordsPerPage;
        const end = start + recordsPerPage;
        const pageData = filteredData.slice(start, end);

        let rowsRendered = 0;

        if (pageData.length === 0) {
            tbody.innerHTML = `
                <tr class="h-full">
                    <td colspan="6" class="text-center py-20">
                        <div class="flex flex-col items-center opacity-20">
                            <svg class="w-12 h-12 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
                            <p class="text-[12px] font-black uppercase tracking-widest text-label">Sin resultados encontrados</p>
                        </div>
                    </td>
                </tr>
            `;
            rowsRendered = 1;
        } else {
            pageData.forEach(row => {
                const statusClass = {
                    active: 'bg-green-500/10 text-green-500',
                    inactive: 'bg-label/10 text-label/40',
                    locked: 'bg-red-500/10 text-red-500'
                }[row.status];

                tbody.innerHTML += `
                    <tr class="bg-surface-container border border-surface-container-border rounded-xl hover:border-primary transition-all group active:scale-[0.995]">
                        <td class="px-4 py-3 text-[12px] font-bold text-label/80">
                            <div class="flex items-center gap-2">
                                <span class="w-1.5 h-1.5 rounded-full ${row.status === 'active' ? 'bg-green-500' : 'bg-red-500/40'}"></span>
                                ${row.user}
                            </div>
                        </td>
                        <td class="px-4 py-3 text-[12px] font-medium text-label/60 lowercase italic">${row.email}</td>
                        <td class="px-4 py-3 text-[12px] font-black text-label uppercase tracking-widest">${row.role}</td>
                        <td class="px-4 py-3 text-[12px] font-mono text-label/40">${row.lastLogin}</td>
                        <td class="px-4 py-3">
                            <span class="px-3 py-0.5 rounded-full text-[12px] font-black uppercase tracking-widest ${statusClass}">${row.status}</span>
                        </td>
                        <td class="px-4 py-3 text-right pr-4">
                            <div class="flex items-center justify-end gap-2">
                                <button class="w-7 h-7 rounded-lg bg-label/5 text-label/40 hover:bg-primary/20 hover:text-primary transition-all flex items-center justify-center">
                                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>
                                </button>
                                <button class="w-7 h-7 rounded-lg bg-label/5 text-label/40 hover:bg-red-500/20 hover:text-red-500 transition-all flex items-center justify-center">
                                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
                rowsRendered++;
            });
        }

        // Ghost Rows for structural stability
        const ghostRowsCount = recordsPerPage - rowsRendered;
        for (let i = 0; i < ghostRowsCount; i++) {
            tbody.innerHTML += `
                <tr class="opacity-20 pointer-events-none select-none border border-transparent">
                    <td class="px-4 py-3 text-transparent">-</td>
                    <td class="px-4 py-3 text-transparent">-</td>
                    <td class="px-4 py-3 text-transparent">-</td>
                    <td class="px-4 py-3 text-transparent">-</td>
                    <td class="px-4 py-3 text-transparent">-</td>
                    <td class="px-4 py-3 px-4 text-right pr-4"><div class="w-7 h-7 bg-label/5 rounded-lg ml-auto"></div></td>
                </tr>
            `;
        }

        updatePagination();
    }

    function updatePagination() {
        if (!paginationInfo) return;
        const total = filteredData.length;
        const start = total === 0 ? 0 : (currentPage - 1) * recordsPerPage + 1;
        const end = Math.min(currentPage * recordsPerPage, total);
        paginationInfo.innerText = `Mostrando ${start}-${end} de ${total} usuarios`;
        
        if (prevBtn) prevBtn.disabled = currentPage === 1;
        if (nextBtn) nextBtn.disabled = currentPage * recordsPerPage >= total;
    }

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            filteredData = userData.filter(u => 
                u.user.toLowerCase().includes(term) || 
                u.email.toLowerCase().includes(term) ||
                u.role.toLowerCase().includes(term)
            );
            currentPage = 1;
            renderTable();
        });
    }

    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            filteredData = [...userData];
            currentPage = 1;
            renderTable();
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderTable();
            }
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (currentPage * recordsPerPage < filteredData.length) {
                currentPage++;
                renderTable();
            }
        });
    }

    // Role Mapping Initialization
    initRoleMappings();
    renderTable();
});

/**
 * Initializes Dynamic Role Mappings from hidden input
 */
function initRoleMappings() {
    const list = document.getElementById('mappingList');
    const hiddenData = document.getElementById('ldap_role_mappings_data');
    if (!list || !hiddenData) return;

    try {
        const mappings = JSON.parse(hiddenData.value || '[]');
        list.innerHTML = '';
        
        if (mappings.length === 0) {
            document.getElementById('mappingEmptyState')?.classList.remove('hidden');
        } else {
            document.getElementById('mappingEmptyState')?.classList.add('hidden');
            mappings.forEach(m => addMappingRow(m.group, m.role));
        }
    } catch (e) {
        console.error('Error initializing mappings:', e);
        addMappingRow();
    }
}

/**
 * Adds a new row to the mapping list
 */
function addMappingRow(group = '', role = 'usuario') {
    const list = document.getElementById('mappingList');
    const emptyState = document.getElementById('mappingEmptyState');
    if (!list) return;

    if (emptyState) emptyState.classList.add('hidden');

    const row = document.createElement('div');
    row.className = 'mapping-row flex items-end gap-6 animate-in fade-in slide-in-from-left-2 duration-300';
    row.innerHTML = `
        <div class="flex-grow space-y-2 group">
            <label class="block text-[12px] font-black text-label/40 uppercase tracking-[0.2em] ml-1 group-focus-within:text-primary transition-colors">GRUPO LDAP (DN)</label>
            <div class="relative">
                <svg class="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-label/40 group-focus-within:text-primary transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
                <input type="text" class="mapping-group w-full bg-input-bg border-2 border-panel-border rounded-xl pl-12 pr-4 py-3 text-sm font-bold text-input outline-none focus:border-primary transition-all placeholder:text-label/20" 
                       placeholder="CN=AdminGroup,OU=Groups,DC=nexus,DC=local" value="${group}">
            </div>
        </div>
        <div class="w-60 shrink-0 space-y-2 group">
            <label class="block text-[12px] font-black text-label/40 uppercase tracking-[0.2em] ml-1 group-focus-within:text-primary transition-colors">ROL ASIGNADO</label>
            <div class="relative">
                <svg class="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-label/40 group-focus-within:text-primary transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                <select class="mapping-role w-full bg-input-bg border-2 border-panel-border rounded-xl pl-12 pr-10 py-3 text-[12px] font-black uppercase tracking-widest text-input outline-none focus:border-primary transition-all cursor-pointer appearance-none">
                    <option value="administrador" ${role === 'administrador' ? 'selected' : ''}>Administrador</option>
                    <option value="usuario" ${role === 'usuario' ? 'selected' : ''}>Usuario</option>
                </select>
                <svg class="w-4 h-4 absolute right-4 top-1/2 -translate-y-1/2 text-label/40 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
            </div>
        </div>
        <div class="pb-0.5">
            <button onclick="removeMappingRow(this)" class="w-12 h-12 flex items-center justify-center rounded-xl bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white transition-all active:scale-95 group/del shadow-lg shadow-red-500/5">
                <svg class="w-5 h-5 transition-transform group-hover/del:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
        </div>
    `;
    list.appendChild(row);
}

/**
 * Removes a row from the mapping list
 */
function removeMappingRow(button) {
    const row = button.closest('.mapping-row');
    row.classList.add('animate-out', 'fade-out', 'slide-out-to-right-4', 'duration-300');
    setTimeout(() => {
        row.remove();
        const list = document.getElementById('mappingList');
        if (list && list.children.length === 0) {
            document.getElementById('mappingEmptyState')?.classList.remove('hidden');
        }
    }, 280);
}

/**
 * Saves Auth Configuration to backend
 * @param {string} containerId 
 */
function saveAuthConfig(containerId) {
    // Collect role mappings
    const mappings = [];
    document.querySelectorAll('.mapping-row').forEach(row => {
        const group = row.querySelector('.mapping-group').value.trim();
        const role = row.querySelector('.mapping-role').value;
        if (group) {
            mappings.push({ group, role });
        }
    });

    const data = {
        ldap_host: document.getElementById('ldap_host')?.value,
        ldap_port: document.getElementById('ldap_port')?.value,
        ldap_ssl: document.getElementById('ldap_ssl')?.checked,
        ldap_user: document.getElementById('ntf_ldap_identity')?.value,
        ldap_pass: document.getElementById('ntf_ldap_credential')?.value,
        ldap_base_dn: document.getElementById('ldap_base_dn')?.value,
        ldap_user_attr: document.getElementById('ldap_user_attr')?.value,
        ldap_group_admin: document.getElementById('ldap_group_admin')?.value,
        ldap_group_user: document.getElementById('ldap_group_user')?.value,
        ldap_role_mappings: JSON.stringify(mappings)
    };

    showToast('Sincronizando Directorio...', 'info');

    fetch('/auth/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            showToast(result.message, 'success');
            // Update hidden data to reflect current state
            const hiddenData = document.getElementById('ldap_role_mappings_data');
            if (hiddenData) hiddenData.value = data.ldap_role_mappings;
        } else {
            showToast('Error: ' + result.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error de conexión', 'error');
    });
}


/**
 * Tests the LDAP connection with current parameters
 */
function testLdapConnection() {
    const data = {
        ldap_host: document.getElementById('ldap_host')?.value,
        ldap_port: document.getElementById('ldap_port')?.value,
        ldap_ssl: document.getElementById('ldap_ssl')?.checked,
        ldap_user: document.getElementById('ntf_ldap_identity')?.value,
        ldap_pass: document.getElementById('ntf_ldap_credential')?.value,
        ldap_base_dn: document.getElementById('ldap_base_dn')?.value,
        ldap_user_attr: document.getElementById('ldap_user_attr')?.value,
        ldap_group_admin: document.getElementById('ldap_group_admin')?.value,
        ldap_group_user: document.getElementById('ldap_group_user')?.value
    };

    if (!data.ldap_host || !data.ldap_port) {
        showToast('Host y Puerto son obligatorios', 'error');
        return;
    }

    showToast('Validando parámetros LDAP...', 'info');

    fetch('/auth/test_ldap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            showToast('Conexión LDAP Exitosa', 'success');
        } else {
            showToast('Error de Conexión: ' + result.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error al conectar con el servidor', 'error');
    });
}
