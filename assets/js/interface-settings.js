/**
 * INTERFACE SETTINGS MODULE
 * Manages global UI preferences stored in localStorage.
 */

window.nexusSettings = {
    notifications: true,
    emailNotifications: true,
    refreshInterval: 60, // seconds
    tourEnabled: true,
    statusColors: {
        ok: '#2563eb',
        fail: '#f43f5e',
        force: '#8b5cf6',
        dup: '#f59e0b'
    },
    initialized: false
};

/**
 * Tab Switcher for Settings Modal
 */
window.switchSettingsTab = function(tab) {
    const tabs = ['general', 'colors'];
    tabs.forEach(t => {
        const btn = document.getElementById(`tabBtn${t.charAt(0).toUpperCase() + t.slice(1)}`);
        const content = document.getElementById(`tabContent${t.charAt(0).toUpperCase() + t.slice(1)}`);
        
        if (t === tab) {
            btn.classList.add('border-2', 'border-primary', 'bg-primary/5', 'text-primary');
            btn.classList.remove('bg-transparent', 'border-transparent', 'text-label/40', 'hover:bg-surface-container/30');
            content.classList.remove('hidden');
        } else {
            btn.classList.remove('border-2', 'border-primary', 'bg-primary/5', 'text-primary');
            btn.classList.add('bg-transparent', 'border-transparent', 'text-label/40', 'hover:bg-surface-container/30');
            content.classList.add('hidden');
        }
    });
};

document.addEventListener('DOMContentLoaded', () => {
    loadInterfaceSettings();
    initSettingsUI();
});

/**
 * Loads settings from localStorage or defaults
 */
function loadInterfaceSettings() {
    // 1. Fallback initial: localStorage (legacy support or local session overrides)
    const saved = localStorage.getItem('nexus_interface_settings');
    if (saved) {
        try {
            const parsed = JSON.parse(saved);
            // Ensure refreshInterval is a valid number if present
            if (parsed.refreshInterval) {
                parsed.refreshInterval = parseInt(parsed.refreshInterval);
            }
            window.nexusSettings = { ...window.nexusSettings, ...parsed };
        } catch (e) {
            console.error('Error parsing settings:', e);
        }
    }

    // 2. Recover from Database (SSoT - Single Source of Truth)
    // We overwrite localStorage with DB values if they exist
    const body = document.body;
    if (body.dataset.prefNotifications !== undefined) {
        window.nexusSettings.notifications = body.dataset.prefNotifications === 'true';
        window.nexusSettings.emailNotifications = body.dataset.prefEmail === 'true';
        window.nexusSettings.refreshInterval = parseInt(body.dataset.prefRefresh) || 60;
        window.nexusSettings.tourEnabled = body.dataset.prefTour === 'true';
        
        // Recover Colors
        if (body.dataset.prefColors) {
            try {
                window.nexusSettings.statusColors = JSON.parse(body.dataset.prefColors);
            } catch(e) { console.error("Error parsing DB colors", e); }
        }
        
        // Sync back to localStorage to keep it fresh
        localStorage.setItem('nexus_interface_settings', JSON.stringify(window.nexusSettings));
    }
    
    window.nexusSettings.initialized = true;
    
    // Apply initial state if needed (e.g. starting pollers)
    startGlobalPolling();
}

/**
 * Initializes the Modal UI interaction
 */
function initSettingsUI() {
    const settingsBtn = document.getElementById('settingsBtn');
    const saveBtn = document.getElementById('saveSettingsBtn');
    const refreshRange = document.getElementById('settingRefreshRange');
    const refreshDisplay = document.getElementById('refreshValueDisplay');
    const notifyToggle = document.getElementById('settingNotifyToggle');
    const emailNotifyToggle = document.getElementById('settingEmailNotifyToggle');
    const tourToggle = document.getElementById('settingTourToggle');

    if (!settingsBtn) return;

    // Open Modal
    settingsBtn.addEventListener('click', () => {
        const val = window.nexusSettings.refreshInterval;
        const $range = $('#settingRefreshRange');
        const $display = $('#refreshValueDisplay');
        const $notif = $('#settingNotifyToggle');
        const $email = $('#settingEmailNotifyToggle');
        const $tour = $('#settingTourToggle');

        console.log('💎 Current Settings SSoT:', window.nexusSettings);

        if (typeof openModal === 'function') {
            openModal('settingsModal');
            
            // Sync UI *after* modal is visible (crucial for some browsers/range-inputs)
            setTimeout(() => {
                const $range = $('#settingRefreshRange');
                const $display = $('#refreshValueDisplay');
                const $notif = $('#settingNotifyToggle');
                const $email = $('#settingEmailNotifyToggle');
                const $tour = $('#settingTourToggle');
                const val = window.nexusSettings.refreshInterval;

                console.log('🔄 DEFERRED SYNC:', val);
                
                if ($range.length) {
                    $range.val(val).attr('value', val);
                    $range.trigger('input').trigger('change');
                }
                if ($display.length) $display.text(val + 's');
                if ($notif.length) $notif.prop('checked', window.nexusSettings.notifications);
                if ($email.length) $email.prop('checked', window.nexusSettings.emailNotifications);
                if ($tour.length) $tour.prop('checked', window.nexusSettings.tourEnabled);

                // Sync Colors
                const colors = window.nexusSettings.statusColors;
                if ($('#colorOk').length) $('#colorOk').val(colors.ok);
                if ($('#colorFail').length) $('#colorFail').val(colors.fail);
                if ($('#colorForce').length) $('#colorForce').val(colors.force);
                if ($('#colorDup').length) $('#colorDup').val(colors.dup);

                // Initial preview sync
                updateIconPreview('previewIconOk', colors.ok);
                updateIconPreview('previewIconFail', colors.fail);
                updateIconPreview('previewIconForce', colors.force);
                updateIconPreview('previewIconDup', colors.dup);
            }, 50);
        }
    });

    // Real-time Preview Listeners
    ['Ok', 'Fail', 'Force', 'Dup'].forEach(status => {
        const picker = document.getElementById(`color${status}`);
        if (picker) {
            picker.addEventListener('input', (e) => {
                updateIconPreview(`previewIcon${status}`, e.target.value);
            });
        }
    });

    // Range Input Feedback
    if (refreshRange && refreshDisplay) {
        refreshRange.addEventListener('input', (e) => {
            refreshDisplay.textContent = e.target.value + 's';
        });
    }

    // Save Logic
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            const newSettings = {
                notifications: notifyToggle ? notifyToggle.checked : true,
                emailNotifications: emailNotifyToggle ? emailNotifyToggle.checked : true,
                refreshInterval: refreshRange ? parseInt(refreshRange.value) : 60,
                tourEnabled: tourToggle ? tourToggle.checked : true,
                statusColors: {
                    ok: document.getElementById('colorOk').value,
                    fail: document.getElementById('colorFail').value,
                    force: document.getElementById('colorForce').value,
                    dup: document.getElementById('colorDup').value
                }
            };

            const changedInterval = newSettings.refreshInterval !== window.nexusSettings.refreshInterval;
            
            window.nexusSettings = { ...window.nexusSettings, ...newSettings };
            
            // Local persistence
            localStorage.setItem('nexus_interface_settings', JSON.stringify(window.nexusSettings));

            // DB Persistence
            fetch('/auth/preferences/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    notifications: newSettings.notifications,
                    email_notifications: newSettings.emailNotifications,
                    refresh_interval: newSettings.refreshInterval,
                    tour_enabled: newSettings.tourEnabled,
                    status_colors: newSettings.statusColors
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    if (typeof showToast === 'function') {
                        showToast('Configuración sincronizada con el servidor', 'success');
                    }
                    // Inform other modules about the change
                    document.dispatchEvent(new CustomEvent('nexus:settingsUpdated', { detail: window.nexusSettings }));
                }
            })
            .catch(err => console.error('Error syncing preferences:', err));

            // If interval changed, we need to restart pollers
            if (changedInterval) {
                startGlobalPolling();
            }

            if (typeof closeModal === 'function') closeModal('settingsModal');
        });
    }
}

/**
 * Global Polking Orchestrator
 * Clears existing intervals and sets up new ones based on current settings.
 */
window.nexusPollers = window.nexusPollers || [];

function startGlobalPolling() {
    // 1. Clear existing pollers
    window.nexusPollers.forEach(p => clearInterval(p.id));
    window.nexusPollers = [];

    const intervalMs = window.nexusSettings.refreshInterval * 1000;

    // 2. Register Poller: PSX Task Table (if present)
    const tableTarget = $('#psxDataTable'); // Usar ID directo del elemento
    if (tableTarget.length && $.fn.dataTable.isDataTable('#psxDataTable')) {
        const psxTable = tableTarget.DataTable();
        const id = setInterval(() => {
            console.log('🔄 Polling: DataTables Reload');
            psxTable.ajax.reload(null, false); // Reload without resetting pagination
        }, intervalMs);
        window.nexusPollers.push({ name: 'psx_table', id });
    }

    // 3. Register Poller: Dashboard Charts (if present)
    // Add logic here if dashboard charts need refresh
}

/**
 * Notification Helper
 * Usage: if (window.canNotify()) { ... }
 */
window.canNotify = function() {
    return window.nexusSettings.notifications;
};

// Re-run polling start when custom events or navigation happen
document.addEventListener('nexus:viewChanged', startGlobalPolling);

/**
 * Updates a specific icon preview with a given hex color
 */
function updateIconPreview(id, hex) {
    const el = document.getElementById(id);
    if (!el) return;
    
    // Apply as background with transparency and solid text/border
    el.style.backgroundColor = `${hex}4D`; // 30% alpha in hex
    el.style.color = hex;
    el.style.boxShadow = `inset 0 0 0 1px ${hex}66`; // 40% alpha for the ring
}
