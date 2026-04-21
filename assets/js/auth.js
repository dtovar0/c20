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
                            <p class="text-[10px] font-black uppercase tracking-widest text-label">Sin resultados encontrados</p>
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
                        <td class="px-4 py-3 text-[11px] font-bold text-label/80">
                            <div class="flex items-center gap-2">
                                <span class="w-1.5 h-1.5 rounded-full ${row.status === 'active' ? 'bg-green-500' : 'bg-red-500/40'}"></span>
                                ${row.user}
                            </div>
                        </td>
                        <td class="px-4 py-3 text-[11px] font-medium text-label/60 lowercase italic">${row.email}</td>
                        <td class="px-4 py-3 text-[10px] font-black text-label uppercase tracking-widest">${row.role}</td>
                        <td class="px-4 py-3 text-[10px] font-mono text-label/40">${row.lastLogin}</td>
                        <td class="px-4 py-3">
                            <span class="px-3 py-0.5 rounded-full text-[8px] font-black uppercase tracking-widest ${statusClass}">${row.status}</span>
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

    renderTable();
});

/**
 * Saves Auth Configuration to backend
 * @param {string} containerId 
 */
function saveAuthConfig(containerId) {
    if (!validateNexusForm(containerId)) return;

    const data = {
        ldap_host: document.getElementById('ldap_host')?.value,
        ldap_port: document.getElementById('ldap_port')?.value,
        ldap_ssl: document.getElementById('ldap_ssl')?.checked,
        ldap_user: document.getElementById('ldap_user')?.value,
        ldap_pass: document.getElementById('ldap_pass')?.value,
        ldap_base_dn: document.getElementById('ldap_base_dn')?.value,
        ldap_user_attr: document.getElementById('ldap_user_attr')?.value,
        ldap_group_admin: document.getElementById('ldap_group_admin')?.value,
        ldap_group_user: document.getElementById('ldap_group_user')?.value
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
        ldap_user: document.getElementById('ldap_user')?.value,
        ldap_pass: document.getElementById('ldap_pass')?.value,
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
