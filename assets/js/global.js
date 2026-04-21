// 1. Immediate Persistence Logic (Prevent Flickering)
(() => {
    const html = document.documentElement;
    const storedTheme = localStorage.getItem('theme');
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    const isMobile = window.innerWidth < 1024;
    
    // Immediate Theme Apply
    if (storedTheme === 'dark' || (!storedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        html.classList.add('dark');
    } else {
        html.classList.remove('dark');
    }

    // Immediate Sidebar State Apply (Global Class)
    if (isCollapsed && !isMobile) {
        html.classList.add('sidebar-is-collapsed');
    }
})();

// 2. DOM Interaction Logic
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const html = document.documentElement;
    
    // Sidebar State Sync (Apply local styling if global class is present)
    if (sidebar && html.classList.contains('sidebar-is-collapsed')) {
        sidebar.classList.remove('w-64', 'min-w-64');
        sidebar.classList.add('w-16', 'min-w-16', 'is-collapsed');
        document.querySelectorAll('.sidebar-text').forEach(el => el.classList.add('hidden'));
    }

    // Dynamic Brand Color Injection (Sync with DB)
    const brandBg = document.body.getAttribute('data-brand-bg');
    const brandText = document.body.getAttribute('data-brand-text');
    if (brandBg) html.style.setProperty('--color-brand-identity-bg', brandBg);
    if (brandText) html.style.setProperty('--color-brand-identity-text', brandText);

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            const isMobile = window.innerWidth < 1024;
            
            if (isMobile) {
                sidebar.classList.toggle('-translate-x-full');
            } else {
                sidebar.classList.toggle('w-64');
                sidebar.classList.toggle('min-w-64');
                sidebar.classList.toggle('w-16');
                sidebar.classList.toggle('min-w-16');
                sidebar.classList.toggle('is-collapsed');
                
                document.querySelectorAll('.sidebar-text').forEach(el => {
                    el.classList.toggle('hidden');
                });

                const isCollapsed = sidebar.classList.contains('is-collapsed');
                localStorage.setItem('sidebarCollapsed', isCollapsed);
                
                // Keep HTML class in sync
                if (isCollapsed) html.classList.add('sidebar-is-collapsed');
                else html.classList.remove('sidebar-is-collapsed');
            }
        });
    }

    // 3. Theme Toggle Listener
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            html.classList.toggle('dark');
            localStorage.setItem('theme', html.classList.contains('dark') ? 'dark' : 'light');
        });
    }
});

/**
 * PREMIUM TOAST SYSTEM
 * Usage: showToast('Message', 'success' | 'error' | 'info' | 'warning', clearAll = false)
 */
function showToast(message, type = 'info', clearAll = false) {
    if (clearAll) {
        document.querySelectorAll('.toast').forEach(t => {
            t.classList.remove('show');
            setTimeout(() => t.remove(), 300);
        });
    }

    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast`;
    
    const icons = {
        success: `<div class="toast-icon w-12 h-12 bg-emerald-500/20 text-emerald-500 shadow-lg shadow-emerald-500/10"><svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg></div>`,
        error: `<div class="toast-icon w-12 h-12 bg-rose-500/20 text-rose-500 shadow-lg shadow-rose-500/10"><svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg></div>`,
        warning: `<div class="toast-icon w-12 h-12 bg-amber-500/20 text-amber-500 shadow-lg shadow-amber-500/10"><svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg></div>`,
        info: `<div class="toast-icon w-12 h-12 bg-sky-500/20 text-sky-500 shadow-lg shadow-sky-500/10"><svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg></div>`
    };

    toast.innerHTML = `
        ${icons[type] || icons.info}
        <div class="toast-content py-1">
            <h4 class="text-[10px] font-black uppercase text-primary/60 tracking-[0.2em] mb-0.5">${type === 'success' ? 'Nexus Success' : type === 'error' ? 'nexus error' : 'nexus system'}</h4>
            <p class="toast-message leading-tight">${message}</p>
        </div>
        <div class="toast-progress" style="background-color: ${type === 'success' ? '#10b981' : type === 'error' ? '#f43f5e' : type === 'warning' ? '#f59e0b' : '#0ea5e9'}"></div>
    `;

    container.appendChild(toast);

    // Initial Trigger
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);

    // Auto Close
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 500);
    }, 3000);
}

/**
 * PREMIUM FORM VALIDATION
 * Returns true if all visible inputs in container are filled
 */
function validateNexusForm(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return true;

    const inputs = container.querySelectorAll('input:not([type="hidden"]), select, textarea');
    let isValid = true;

    inputs.forEach(input => {
        // Skip disabled inputs
        if (input.disabled) return;

        // Clean previous states
        input.classList.remove('border-error', 'animate-shake');

        const value = input.value ? input.value.trim() : '';
        let inputError = false;

        // check empty
        if (value === '') {
            inputError = true;
        } 
        
        // check password rules
        else if (input.dataset.validationType === 'password') {
            const hasLetters = /[a-zA-Z]/.test(value);
            const hasNumbers = /\d/.test(value);
            const hasSpecial = /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(value);
            
            if (value.length < 12) {
                inputError = true;
                showToast('Seguridad: La contraseña debe tener al menos 12 caracteres', 'warning');
            } else if (!hasLetters || !hasNumbers || !hasSpecial) {
                inputError = true;
                showToast('Seguridad: Usa letras, números y al menos 1 carácter especial', 'warning');
            }
        }
        
        // check match (passwords)
        else if (input.dataset.validationType === 'match') {
            const targetId = input.dataset.matchTarget;
            const targetEl = document.getElementById(targetId);
            if (!targetEl || value !== targetEl.value) {
                inputError = true;
                showToast('Las contraseñas no coinciden', 'error');
            }
        }

        if (inputError) {
            isValid = false;
            
            // Apply error styles
            input.classList.add('border-error', 'animate-shake');
            
            // Remove shake after animation to allow repeat
            setTimeout(() => {
                input.classList.remove('animate-shake');
            }, 600);
        }
    });

    if (!isValid && !container.querySelector('.border-error[type="email"]')) {
        showToast('Campos Requeridos: Por favor completa la información resaltada.', 'error');
    }

    return isValid;
}

/**
 * PREMIUM MODAL CONTROLLER
 * Optimized for nexus-modal architecture with smooth transitions.
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        // Clear previous state
        const allInputs = modal.querySelectorAll('input, select, textarea');
        allInputs.forEach(input => {
            if (input.type === 'checkbox' || input.type === 'radio') {
                input.checked = false;
            } else if (!input.getAttribute('name')?.includes('user_id')) {
                input.value = '';
            }
            
            // Clean visual validation state
            input.classList.remove('border-error', 'animate-shake');
            input.style.borderColor = '';
        });

        modal.classList.remove('hidden');
        modal.classList.add('flex');
        // Force reflow
        modal.offsetWidth;
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Focus first input
        const firstInput = modal.querySelector('input:not([type="hidden"])');
        if (firstInput) setTimeout(() => firstInput.focus(), 400);
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) {
        // If no ID, attempt to close the currently open modal
        const openModal = document.querySelector('.nexus-modal.show');
        if (openModal) modalId = openModal.id;
        else return;
    }
    
    const targetModal = document.getElementById(modalId);
    if (targetModal) {
        targetModal.classList.remove('show');
        document.body.style.overflow = '';
        setTimeout(() => {
            targetModal.classList.remove('flex');
            targetModal.classList.add('hidden');
        }, 300);
    }
}

// Global Listener for ESC key (Close Modals, Dropdowns, and Clear Search)
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const activeEl = document.activeElement;
        
        // 1. Logic for Search Inputs (If focused and has content)
        if (activeEl && activeEl.tagName === 'INPUT' && (activeEl.id.toLowerCase().includes('search') || activeEl.placeholder.toLowerCase().includes('buscar'))) {
            if (activeEl.value !== '') {
                activeEl.value = '';
                activeEl.dispatchEvent(new Event('input', { bubbles: true }));
                return; // Consume the event if we cleared a search
            }
        }

        // 2. Logic for Modals
        const activeModal = document.querySelector('.nexus-modal.show');
        if (activeModal) {
            closeModal(activeModal.id);
        }
    }
});

/**
 * PREMIUM LIVE VALIDATION
 * Actively monitors .premium-validate fields to provide real-time kinetic feedback.
 */
document.addEventListener('input', (e) => {
    if (e.target.classList.contains('premium-validate')) {
        const input = e.target;
        const type = input.dataset.validationType;
        const val = input.value.trim();
        
        let isValid = val.length > 0; // Baseline check
        
        // Context-aware deep validation
        if (type === 'email' && val.length > 0) {
            isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
        } else if (type === 'password' && val.length > 0) {
            // Enterprise rules: min 12 chars, alphanumeric, 1 special char
            const hasLetters = /[a-zA-Z]/.test(val);
            const hasNumbers = /\d/.test(val);
            const hasSpecial = /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(val);
            isValid = val.length >= 12 && hasLetters && hasNumbers && hasSpecial;
        } else if (type === 'server' && val.length > 0) {
            isValid = /^([a-zA-Z0-9.-]+)\.([a-zA-Z]{2,})$/.test(val) || /^localhost$/.test(val);
        } else if (type === 'port' && val.length > 0) {
            const portNum = parseInt(val, 10);
            isValid = /^\d+$/.test(val) && portNum > 0 && portNum <= 65535;
        } else if (type === 'match' && val.length > 0) {
            const targetId = input.dataset.matchTarget;
            const targetEl = document.getElementById(targetId);
            isValid = targetEl && val === targetEl.value && val.length >= 12;
        }

        // Apply visual premium token feedback
        if (isValid) {
            input.classList.remove('border-error');
            input.style.borderColor = '#10b981'; // Emerald 500
            input.style.boxShadow = '0 0 0 4px rgba(16, 185, 129, 0.1)';
        } else {
            // Only show error if there is content or it's a required mismatch
            if (val.length > 0 || input.required) {
                input.classList.add('border-error');
                input.style.borderColor = ''; 
                input.style.boxShadow = '';
            }
        }
    }
});

/**
 * TAB NAVIGATION LOGIC (Global)
 */
function switchTab(tabId) {
    const activeClasses = ['text-tab-active-text', 'bg-tab-active', 'shadow-xl', 'shadow-tab-active/20'];
    const standbyClasses = ['text-tab-inactive-text', 'bg-tab-inactive', 'border', 'border-panel-border'];

    document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.add('hidden'));
    document.querySelectorAll('.tab-trigger').forEach(trigger => {
        trigger.classList.remove(...activeClasses);
        trigger.classList.add(...standbyClasses);
    });
    
    const targetPanel = document.getElementById('tab-panel-' + tabId);
    if (targetPanel) targetPanel.classList.remove('hidden');
    
    const activeTrigger = document.getElementById('tab-trigger-' + tabId);
    if (activeTrigger) {
        activeTrigger.classList.remove(...standbyClasses);
        activeTrigger.classList.add(...activeClasses);
    }
}

/**
 * AUTH CONTROLLER
 * Toggles disabled state of password inputs based on their authentication toggle.
 */
document.addEventListener('change', (e) => {
    if (e.target.id === 'smtpAuthToggle') {
        const isAuth = e.target.checked;
        const smtpPass = document.getElementById('smtpPass');
        const authStatusText = document.getElementById('authStatusText');
        
        if (authStatusText) {
            authStatusText.textContent = isAuth ? 'Activo' : 'Inactivo';
        }
        
            if (smtpPass) {
                smtpPass.disabled = !isAuth;
                if (!isAuth) {
                    // Clear validation tokens when disabling
                    smtpPass.classList.remove('border-error');
                    smtpPass.style.borderColor = '';
                    smtpPass.style.boxShadow = '';
                } else {
                    // Re-evaluate validity instantly when enabling
                    smtpPass.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }
    }
});

// 4. Notification Dropdown Logic (Encapsulated)
document.addEventListener('DOMContentLoaded', () => {
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationDropdown = document.getElementById('notificationDropdown');
    const notificationBadge = document.getElementById('notificationBadge');

    if (notificationBtn && notificationDropdown) {
        notificationBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isHidden = notificationDropdown.classList.contains('opacity-0');
            
            if (isHidden) {
                // Open
                notificationDropdown.classList.remove('opacity-0', 'translate-y-4', 'pointer-events-none');
                // Hide badge on open
                if (notificationBadge) {
                    notificationBadge.style.opacity = '0';
                    notificationBadge.style.transform = 'scale(0)';
                    setTimeout(() => notificationBadge.classList.add('hidden'), 300);
                }
            } else {
                // Close
                notificationDropdown.classList.add('opacity-0', 'translate-y-4', 'pointer-events-none');
            }
        });

        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !notificationDropdown.classList.contains('opacity-0')) {
                notificationDropdown.classList.add('opacity-0', 'translate-y-4', 'pointer-events-none');
            }
        });

        // Close on click outside
        document.addEventListener('click', (e) => {
            if (!notificationDropdown.contains(e.target) && !notificationBtn.contains(e.target)) {
                notificationDropdown.classList.add('opacity-0', 'translate-y-4', 'pointer-events-none');
            }
        });
    }
});

// 5. Sidebar User Dropdown Logic
document.addEventListener('DOMContentLoaded', () => {
    const userProfileBtn = document.getElementById('userProfileBtn');
    const userDropdown = document.getElementById('userDropdown');

    if (userProfileBtn && userDropdown) {
        userProfileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isHidden = userDropdown.classList.contains('opacity-0');
            
            if (isHidden) {
                // Open
                userDropdown.classList.remove('opacity-0', 'translate-y-4', 'pointer-events-none');
            } else {
                // Close
                userDropdown.classList.add('opacity-0', 'translate-y-4', 'pointer-events-none');
            }
        });

        // Close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !userDropdown.classList.contains('opacity-0')) {
                userDropdown.classList.add('opacity-0', 'translate-y-4', 'pointer-events-none');
            }
        });

        // Close on click away
        document.addEventListener('click', (e) => {
            if (!userDropdown.contains(e.target) && !userProfileBtn.contains(e.target)) {
                userDropdown.classList.add('opacity-0', 'translate-y-4', 'pointer-events-none');
            }
        });
    }
});
