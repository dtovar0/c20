/**
 * DESIGN MODULE LOGIC
 */

async function saveDesign() {
    const data = {
        light_primary: document.getElementById('light_primary').value,
        light_secondary: document.getElementById('light_secondary').value,
        light_bg: document.getElementById('light_bg').value,
        light_panel: document.getElementById('light_panel').value,
        
        dark_primary: document.getElementById('dark_primary').value,
        dark_secondary: document.getElementById('dark_secondary').value,
        dark_bg: document.getElementById('dark_bg').value,
        dark_panel: document.getElementById('dark_panel').value
    };

    try {
        const response = await fetch('/design/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.status === 'success') {
            if (typeof showToast === 'function') {
                showToast(result.message, 'success');
            } else {
                alert(result.message);
            }
            // Reload styles after a short delay to apply changes
            setTimeout(() => window.location.reload(), 1000);
        } else {
            if (typeof showToast === 'function') {
                showToast(result.message, 'error');
            } else {
                alert(result.message);
            }
        }
    } catch (error) {
        if (typeof showToast === 'function') {
            showToast('Error al conectar con el servidor', 'error');
        } else {
            console.error('Error saving design:', error);
        }
    }
}

// Tab switcher is already global in global.js, but if design has local needs:
// (Currently design uses the global switchTab from global.js if available)
