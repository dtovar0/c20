document.addEventListener('DOMContentLoaded', function() {
    const authToggle = document.getElementById('smtpAuthToggle');
    const authInputs = ['smtpName', 'smtpUser', 'smtpPass'];
    const authStatusText = document.getElementById('authStatusText');

    function updateAuthFields() {
        const isEnabled = authToggle.checked;
        authInputs.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.disabled = !isEnabled;
                // Visual feedback correction
                if (!isEnabled) {
                    el.classList.add('opacity-30', 'cursor-not-allowed');
                } else {
                    el.classList.remove('opacity-30', 'cursor-not-allowed');
                }
            }
        });
        if (authStatusText) {
            authStatusText.innerText = isEnabled ? 'Activo' : 'Inactivo';
            authStatusText.className = isEnabled 
                ? 'text-[9px] text-primary/60 font-bold uppercase tracking-widest' 
                : 'text-[9px] text-label/40 font-bold uppercase tracking-widest';
        }
    }

    if (authToggle) {
        authToggle.addEventListener('change', updateAuthFields);
        updateAuthFields(); // Initialize state
    }
    
    // Password Visibility Toggle
    const togglePassBtn = document.getElementById('togglePassVisibility');
    if (togglePassBtn) {
        togglePassBtn.addEventListener('click', function() {
            const passInput = document.getElementById('smtpPass');
            if (passInput) {
                passInput.type = passInput.type === 'password' ? 'text' : 'password';
            }
        });
    }
});

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
