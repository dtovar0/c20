/**
 * SETTINGS MODULE LOGIC
 * Manages identity mode toggling, live preview synchronization, and state recovery.
 */

let currentIdentityMode = 'icon'; // Global track for save logic

document.addEventListener('DOMContentLoaded', () => {
    initLivePreview();
    recoverState();
});

/**
 * Recovers state from the 'settings-state' data attributes
 */
function recoverState() {
    const stateEl = document.getElementById('settings-state');
    if (!stateEl) return;

    if (stateEl.dataset.configExists === 'true') {
        const identityType = stateEl.dataset.identityType;
        const savedIconPath = stateEl.dataset.portalIconPath;
        
        toggleIdentityMode(identityType);

        if (identityType === 'icon' && savedIconPath) {
            // INFALLIBLE FINGERPRINT HIGHLIGHTING
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = savedIconPath;
            const targetD = tempDiv.querySelector('path')?.getAttribute('d');
            
            if (targetD) {
                const iconButtons = document.querySelectorAll('#group-icon-picker button');
                iconButtons.forEach(btn => {
                    const btnPath = btn.querySelector('path')?.getAttribute('d');
                    if (btnPath === targetD) {
                        btn.classList.add('bg-primary/20', 'text-primary', 'shadow-lg', 'shadow-primary/20', 'z-10');
                        btn.classList.remove('text-primary/60');
                        btn.scrollIntoView({ behavior: 'auto', block: 'center' });
                    }
                });
            }
        }
    }
}

/**
 * Initializes all live preview listeners
 */
function initLivePreview() {
    const portalNameInput = document.getElementById('portal-name-input');
    const previewPortalName = document.getElementById('preview-portal-name');
    const previewPortalIcon = document.getElementById('preview-portal-icon');
    const imageInput = document.getElementById('portal-image-input');
    const iconButtons = document.querySelectorAll('#group-icon-picker button');

    if (!portalNameInput || !previewPortalName || !previewPortalIcon) return;

    // 1. Live Sync: Portal Name
    portalNameInput.addEventListener('input', (e) => {
        previewPortalName.textContent = e.target.value || 'Nexus Core AI';
        previewPortalName.classList.add('scale-105', 'text-primary');
        setTimeout(() => previewPortalName.classList.remove('scale-105', 'text-primary'), 200);
    });

    // 2. Live Sync: Icon Picker
    iconButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active state from all
            iconButtons.forEach(b => {
                b.classList.remove('bg-primary/20', 'text-primary', 'shadow-lg', 'shadow-primary/20', 'z-10');
                b.classList.add('text-primary/60');
            });

            // Add active state to selected
            btn.classList.add('bg-primary/20', 'text-primary', 'shadow-lg', 'shadow-primary/20', 'z-10');
            btn.classList.remove('text-primary/60');

            // Get the SVG from the button
            const svg = btn.querySelector('svg').outerHTML;
            previewPortalIcon.innerHTML = svg;
            
            animatePreviewBoard();
        });
    });

    // 3. Live Sync: Image Upload
    if (imageInput) {
        imageInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    previewPortalIcon.innerHTML = `<img src="${event.target.result}" class="w-full h-full object-cover">`;
                    animatePreviewBoard();
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // 4. Live Sync: Color Pickers
    const bgColorInput = document.getElementById('portal-bg-color');
    const textColorInput = document.getElementById('portal-text-color');

    if (bgColorInput) {
        bgColorInput.addEventListener('input', (e) => {
            previewPortalIcon.style.backgroundColor = e.target.value;
            const sidebarLogo = document.querySelector('#sidebar div.brand-text > div');
            if (sidebarLogo) sidebarLogo.style.backgroundColor = e.target.value;
        });
    }

    if (textColorInput) {
        textColorInput.addEventListener('input', (e) => {
            previewPortalIcon.style.color = e.target.value;
            const sidebarLogo = document.querySelector('#sidebar div.brand-text > div');
            if (sidebarLogo) sidebarLogo.style.color = e.target.value;
        });
    }
}

/**
 * Toggles between Icon selection and Image upload modes
 */
function toggleIdentityMode(mode) {
    currentIdentityMode = mode;
    const iconGroup = document.getElementById('group-icon-picker');
    const imageGroup = document.getElementById('group-image-upload');
    const btnIcon = document.getElementById('btn-toggle-icon');
    const btnImage = document.getElementById('btn-toggle-image');
    const imageInput = document.getElementById('portal-image-input');

    if (!iconGroup || !imageGroup || !btnIcon || !btnImage) return;

    if (mode === 'icon') {
        iconGroup.classList.remove('hidden');
        imageGroup.classList.add('hidden');
        if (imageInput) imageInput.disabled = true;
        btnIcon.className = "flex-grow py-4 bg-button-bg text-button-text shadow-lg shadow-button-bg/20 rounded-2xl text-xs font-black uppercase tracking-widest hover:opacity-90 transition-all active:scale-95 flex items-center justify-center gap-2";
        btnImage.className = "flex-grow py-4 bg-panel-fill border-2 border-button-bg/20 text-label rounded-2xl text-xs font-black uppercase tracking-widest hover:border-button-bg transition-all active:scale-95 flex items-center justify-center gap-2";
    } else {
        iconGroup.classList.add('hidden');
        imageGroup.classList.remove('hidden');
        if (imageInput) imageInput.disabled = false;
        btnImage.className = "flex-grow py-4 bg-button-bg text-button-text shadow-lg shadow-button-bg/20 rounded-2xl text-xs font-black uppercase tracking-widest hover:opacity-90 transition-all active:scale-95 flex items-center justify-center gap-2";
        btnIcon.className = "flex-grow py-4 bg-panel-fill border-2 border-button-bg/20 text-label rounded-2xl text-xs font-black uppercase tracking-widest hover:border-button-bg transition-all active:scale-95 flex items-center justify-center gap-2";
    }

    animatePreviewBoard();
}

/**
 * Kinetic feedback to the preview board
 */
function animatePreviewBoard() {
    const previewIconContainer = document.getElementById('preview-portal-icon')?.parentElement;
    if (previewIconContainer) {
        previewIconContainer.classList.add('animate-in', 'fade-in', 'zoom-in-95', 'duration-300');
        setTimeout(() => previewIconContainer.classList.remove('animate-in', 'fade-in', 'zoom-in-95', 'duration-300'), 300);
    }
}

/**
 * Updates default port based on engine selection
 */
function updateDefaultPort(engine) {
    const portInput = document.getElementById('db-port');
    if (!portInput) return;
    
    if (engine === 'mysql') {
        portInput.value = '3306';
        portInput.placeholder = '3306';
    } else if (engine === 'postgres') {
        portInput.value = '5432';
        portInput.placeholder = '5432';
    }
    
    portInput.parentElement.classList.add('scale-[1.02]');
    setTimeout(() => portInput.parentElement.classList.remove('scale-[1.02]'), 200);
}

/**
 * Saves settings to the backend
 */
function saveSettings(containerId) {
    const portalName = document.getElementById('portal-name-input')?.value;
    const previewBoard = document.getElementById('preview-portal-icon');
    
    let portalIconValue = '';
    if (currentIdentityMode === 'icon') {
        portalIconValue = previewBoard?.innerHTML; 
    } else {
        const img = previewBoard?.querySelector('img');
        portalIconValue = img ? img.src : ''; 
    }

    const data = {
        portal_name: portalName,
        portal_identity_type: currentIdentityMode,
        portal_icon: portalIconValue,
        bg_color: document.getElementById('portal-bg-color')?.value,
        text_color: document.getElementById('portal-text-color')?.value
    };

    if (containerId === 'tab-panel-database') {
        showToast('Sincronizando...', 'info');
    }

    fetch('/settings/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        setTimeout(() => {
            if (result.status === 'success') {
                showToast(result.message, 'success', true);
            } else {
                showToast('Error: ' + result.message, 'error', true);
            }
        }, 500);
    })
    .catch(error => {
        console.error('Error saving settings:', error);
        showToast('Error de Conexión', 'error');
    });
}
