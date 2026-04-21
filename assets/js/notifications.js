/**
 * NOTIFICATIONS MODULE LOGIC
 * Manages SMTP configuration persistence
 */

function saveNotifications(containerId) {
    if (!validateNexusForm(containerId)) return;

    const data = {
        server: document.querySelector('#tab-panel-config input[data-validation-type="server"]')?.value,
        port: document.querySelector('#tab-panel-config input[data-validation-type="port"]')?.value,
        encryption: document.querySelector('#tab-panel-config select')?.value,
        auth_enabled: document.getElementById('smtpAuthToggle')?.checked,
        sender_name: document.getElementById('smtpName')?.value,
        sender_email: document.getElementById('smtpUser')?.value,
        password: document.getElementById('smtpPass')?.value
    };

    showToast('Guardando configuración...', 'info');

    fetch('/notifications/save', {
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
