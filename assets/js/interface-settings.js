/**
 * INTERFACE SETTINGS MODULE
 * Manages global UI preferences stored in localStorage.
 */

window.nexusSettings = {
    notifications: true,
    emailNotifications: true,
    refreshInterval: 60, // seconds
    tourEnabled: true,
    initialized: false
};

document.addEventListener('DOMContentLoaded', () => {
    loadInterfaceSettings();
    initSettingsUI();
});

/**
 * Loads settings from localStorage or defaults
 */
function loadInterfaceSettings() {
    // 1. Recover from Database (injected in body)
    const body = document.body;
    if (body.dataset.prefNotifications) {
        window.nexusSettings.notifications = body.dataset.prefNotifications === 'true';
        window.nexusSettings.emailNotifications = body.dataset.prefEmail === 'true';
        window.nexusSettings.refreshInterval = parseInt(body.dataset.prefRefresh) || 60;
        window.nexusSettings.tourEnabled = body.dataset.prefTour === 'true';
    }

    // 2. Fallback to localStorage (legacy support or local session overrides)
    const saved = localStorage.getItem('nexus_interface_settings');
    if (saved) {
        try {
            const parsed = JSON.parse(saved);
            // We prioritize the localStorage if it exists, as it might have local session changes
            window.nexusSettings = { ...window.nexusSettings, ...parsed };
        } catch (e) {
            console.error('Error parsing settings:', e);
        }
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
        // Sync UI with current settings
        if (refreshRange) refreshRange.value = window.nexusSettings.refreshInterval;
        if (refreshDisplay) refreshDisplay.textContent = window.nexusSettings.refreshInterval + 's';
        if (notifyToggle) notifyToggle.checked = window.nexusSettings.notifications;
        if (emailNotifyToggle) emailNotifyToggle.checked = window.nexusSettings.emailNotifications;
        if (tourToggle) tourToggle.checked = window.nexusSettings.tourEnabled;
        
        if (typeof openModal === 'function') openModal('settingsModal');
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
                tourEnabled: tourToggle ? tourToggle.checked : true
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
                    tour_enabled: newSettings.tourEnabled
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    if (typeof showToast === 'function') {
                        showToast('Configuración sincronizada con el servidor', 'success');
                    }
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
    const psxTable = $('#auditTableBody').closest('table').DataTable();
    if (psxTable) {
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
