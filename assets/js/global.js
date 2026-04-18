// 1. DOM Interaction Logic
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.classList.add('dark');
    }

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            const isMobile = window.innerWidth < 1024;
            
            if (isMobile) {
                sidebar.classList.toggle('-translate-x-full');
            } else {
                // Toggle collapsed state
                sidebar.classList.toggle('w-64');
                sidebar.classList.toggle('w-20');
                sidebar.classList.toggle('is-collapsed'); // New helper class
                
                document.querySelectorAll('.sidebar-text').forEach(el => {
                    el.classList.toggle('hidden');
                });
                
                const brandText = document.querySelector('.brand-text');
                if (brandText) brandText.classList.toggle('hidden');
            }
        });
    }

    // 3. Theme Toggle Logic
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;
    
    // Set initial theme based on localStorage or system preference
    const storedTheme = localStorage.getItem('theme');
    if (storedTheme) {
        if (storedTheme === 'dark') html.classList.add('dark');
        else html.classList.remove('dark');
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        html.classList.add('dark');
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            html.classList.toggle('dark');
            const newTheme = html.classList.contains('dark') ? 'dark' : 'light';
            localStorage.setItem('theme', newTheme);
        });
    }
});

/**
 * PREMIUM TOAST SYSTEM
 * Usage: showToast('Message', 'success' | 'error' | 'info' | 'warning')
 */
function showToast(message, type = 'info') {
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
        
        // check email format if type is email
        else if (input.type === 'email') {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                inputError = true;
                showToast('Formato Inválido: La dirección de correo no es correcta.', 'warning');
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
 */
function showPremiumModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    // Clear all inputs inside the modal before opening
    const allInputs = modal.querySelectorAll('input, select, textarea');
    allInputs.forEach(input => {
        if (input.type === 'checkbox' || input.type === 'radio') {
            input.checked = false;
        } else {
            input.value = '';
        }
        input.classList.remove('border-error', 'animate-shake');
    });

    modal.classList.add('show');
    
    // Focus first input if any
    const firstInput = modal.querySelector('input');
    if (firstInput) setTimeout(() => firstInput.focus(), 300);
}

function closePremiumModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    modal.classList.remove('show');
}

// Global Listener for ESC key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const openModal = document.querySelector('.modal-backdrop.show');
        if (openModal) {
            closePremiumModal(openModal.id);
        }
    }
});
