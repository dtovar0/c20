/**
 * PSX5K STEP WIZARD CONTROLLER
 * Fixed Visibility & Token Alignment
 */

let currentWizardStep = 1;

function openWizard() {
    const modal = document.getElementById('psxWizardModal');
    if (modal) {
        resetWizardForm();
        modal.classList.remove('opacity-0', 'pointer-events-none');
        currentWizardStep = 1;
        updateWizardUI();
    }
}

function closeWizard() {
    const modal = document.getElementById('psxWizardModal');
    if (modal) {
        modal.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(resetWizardForm, 300);
    }
}

function resetWizardForm() {
    document.querySelectorAll('#psxWizardModal input, #psxWizardModal textarea').forEach(el => {
        el.value = '';
        el.style.borderColor = 'var(--nx-border)';
    });

    const select = document.getElementById('clientModeSelect');
    if (select) select.value = 'calls_only';

    const toggle = document.getElementById('dataEntryToggle');
    if (toggle) toggle.checked = false;

    // Reset Op Buttons
    document.querySelectorAll('.op-select-btn').forEach(btn => {
        btn.style.borderColor = 'var(--nx-border)';
        btn.style.backgroundColor = 'var(--nx-surface)';
        btn.style.color = 'var(--nx-label)';
        btn.style.opacity = '0.6';
        btn.classList.remove('active');
    });

    handleRoutingLabelState();
    toggleDataMethod();
}

function changeStep(delta) {
    if (delta > 0 && !validateCurrentStep()) {
        triggerShakeEffect();
        return;
    }

    const nextStep = currentWizardStep + delta;
    if (nextStep >= 1 && nextStep <= 3) {
        currentWizardStep = nextStep;
        updateWizardUI();
    }
}

function validateCurrentStep() {
    let isValid = true;
    const ERROR_COLOR = 'rgb(var(--color-accent-violet))';

    if (currentWizardStep === 1) {
        const anyActive = Array.from(document.querySelectorAll('.op-select-btn')).some(btn => btn.classList.contains('active'));
        if (!anyActive) isValid = false;
    } 
    else if (currentWizardStep === 2) {
        const mode = document.getElementById('clientModeSelect').value;
        const routing = document.getElementById('routingLabelInput');
        if (mode === 'both' && routing.value.trim() === '') {
            routing.style.borderColor = ERROR_COLOR;
            isValid = false;
        }

        const isManual = document.getElementById('dataEntryToggle').checked;
        if (isManual) {
            const textarea = document.querySelector('#methodManualEntry textarea');
            if (textarea.value.trim() === '') {
                textarea.style.borderColor = ERROR_COLOR;
                isValid = false;
            }
        } else {
            const fileInput = document.getElementById('psxFileInput');
            if (fileInput.files.length === 0) {
                document.getElementById('methodFileUpload').querySelector('label').style.borderColor = ERROR_COLOR;
                isValid = false;
            }
        }
    }

    return isValid;
}

function triggerShakeEffect() {
    const wizardBox = document.querySelector('#psxWizardModal > div:last-child');
    wizardBox.classList.add('animate-shake');
    setTimeout(() => wizardBox.classList.remove('animate-shake'), 500);
}

function updateWizardUI() {
    // Hide all steps
    document.querySelectorAll('.step-content').forEach(step => step.style.display = 'none');
    document.getElementById(`wizardStep${currentWizardStep}`).style.display = 'block';
    
    // Progress
    const progress = (currentWizardStep / 3) * 100;
    document.getElementById('stepProgress').style.width = `${progress}%`;
    document.getElementById('currentStepNum').innerText = currentWizardStep;
    
    // Step 2 Logic
    if (currentWizardStep === 2) {
        const activeBtn = Array.from(document.querySelectorAll('.op-select-btn')).find(b => b.classList.contains('active'));
        const isBorrar = activeBtn && activeBtn.innerText.includes('Borrar');
        const configSection = document.getElementById('opConfigSection');
        if (configSection) {
            configSection.style.display = isBorrar ? 'none' : 'block';
        }
    }

    if (currentWizardStep === 3) collectWizardData();

    // Footer Buttons Logic (HARD VISIBILITY)
    const prevBtn = document.getElementById('prevStepBtn');
    const nextBtn = document.getElementById('nextStepBtn');
    const launchBtn = document.getElementById('launchBtn');
    
    // Reset displays
    prevBtn.style.display = (currentWizardStep === 1) ? 'none' : 'flex';
    
    if (currentWizardStep === 3) {
        nextBtn.style.display = 'none';
        launchBtn.style.display = 'flex';
    } else {
        nextBtn.style.display = 'flex';
        launchBtn.style.display = 'none';
    }
}

function collectWizardData() {
    const activeBtn = Array.from(document.querySelectorAll('.op-select-btn')).find(b => b.classList.contains('active'));
    const taskType = activeBtn ? activeBtn.innerText.trim() : 'N/A';
    const isBorrar = activeBtn && activeBtn.innerText.includes('Borrar');

    const modeRow = document.getElementById('summaryModeRow');
    const routingRow = document.getElementById('summaryRoutingRow');
    
    if (isBorrar) {
        if (modeRow) modeRow.style.display = 'none';
        if (routingRow) routingRow.style.display = 'none';
    } else {
        if (modeRow) modeRow.style.display = 'grid';
        if (routingRow) routingRow.style.display = 'grid';
        
        const modeSelect = document.getElementById('clientModeSelect');
        document.getElementById('summaryMode').innerText = modeSelect ? modeSelect.options[modeSelect.selectedIndex].text : '-';
        
        const routingInput = document.getElementById('routingLabelInput');
        document.getElementById('summaryRouting').innerText = (routingInput && routingInput.value.trim() !== '') ? routingInput.value : 'SIN ETIQUETA';
    }

    const toggle = document.getElementById('dataEntryToggle');
    const isManual = toggle && toggle.checked;

    if (isManual) {
        document.getElementById('summaryData').innerText = 'Ingreso Manual';
        document.getElementById('summaryFileLabel').innerText = 'Total registros:';
        const lines = document.querySelector('#methodManualEntry textarea').value.split('\n').filter(l => l.trim() !== '').length;
        document.getElementById('summaryFileName').innerText = `${lines} registros`;
    } else {
        document.getElementById('summaryData').innerText = 'Archivo (XML/CSV)';
        document.getElementById('summaryFileLabel').innerText = 'Nombre Archivo:';
        document.getElementById('summaryFileName').innerText = document.getElementById('fileNameDisplay').innerText;
    }

    document.getElementById('summaryTaskType').innerText = taskType;
}

async function finalizeWizard() {
    const launchBtn = document.getElementById('launchBtn');
    const toggle = document.getElementById('dataEntryToggle');
    const isManual = toggle && toggle.checked;
    
    launchBtn.innerHTML = '<svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Procesando...';
    launchBtn.disabled = true;

    try {
        if (!isManual) {
            const fileInput = document.getElementById('psxFileInput');
            if (fileInput.files.length > 0) {
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                const response = await fetch('/api/psx/upload', { method: 'POST', body: formData });
                const result = await response.json();
                if (result.status !== 'success') throw new Error(result.message);
            }
        }
        
        setTimeout(() => {
            if (typeof showToast === 'function') {
                showToast('Tarea guardada con éxito', 'success');
            }
            closeWizard();
            launchBtn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg><span>Guardar</span>';
            launchBtn.disabled = false;
            if (typeof renderNexusTable === 'function') renderNexusTable();
        }, 800);

    } catch (error) {
        launchBtn.innerHTML = 'Error en Carga';
        launchBtn.style.backgroundColor = 'rgb(var(--color-accent-violet))';
        triggerShakeEffect();
        setTimeout(() => {
            launchBtn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg><span>Volver a Guardar</span>';
            launchBtn.style.backgroundColor = 'var(--nx-primary)';
            launchBtn.disabled = false;
        }, 2000);
    }
}

function handleRoutingLabelState() {
    const select = document.getElementById('clientModeSelect');
    const input = document.getElementById('routingLabelInput');
    const label = document.getElementById('routingLabelTag');
    if (!select || !input || !label) return;

    if (select.value === 'both') {
        input.disabled = false;
        input.placeholder = 'Ingrese etiqueta de ruta...';
        label.innerText = 'Routing Label (Activo)';
        label.style.color = 'var(--nx-primary)';
        label.style.opacity = '1';
    } else {
        input.disabled = true;
        input.placeholder = 'Bloqueado...';
        label.innerText = 'Routing Label (Bloqueado)';
        label.style.color = 'var(--nx-label)';
        label.style.opacity = '0.4';
    }
}

function toggleDataMethod() {
    const toggle = document.getElementById('dataEntryToggle');
    const fileArea = document.getElementById('methodFileUpload');
    const manualArea = document.getElementById('methodManualEntry');
    const labelFile = document.getElementById('labelFileMode');
    const labelManual = document.getElementById('labelManualMode');
    if (!toggle || !fileArea || !manualArea) return;

    if (toggle.checked) {
        fileArea.style.display = 'none';
        manualArea.style.display = 'block';
        labelManual.style.opacity = '1';
        labelFile.style.opacity = '0.4';
    } else {
        fileArea.style.display = 'block';
        manualArea.style.display = 'none';
        labelFile.style.opacity = '1';
        labelManual.style.opacity = '0.4';
    }
}

function validateFile(input) {
    const file = input.files[0];
    const display = document.getElementById('fileNameDisplay');
    const border = input.parentElement;
    if (!file || !display || !border) return;

    const extension = file.name.split('.').pop().toLowerCase();
    if (['xml', 'csv'].includes(extension)) {
        display.innerText = file.name;
        display.style.color = 'var(--nx-primary)';
        border.style.borderColor = 'var(--nx-primary)';
    } else {
        input.value = '';
        display.innerText = 'Extension No Válida';
        display.style.color = 'rgb(var(--color-accent-violet))';
        border.style.borderColor = 'rgb(var(--color-accent-violet))';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const mainBtn = document.getElementById('refreshAudit');
    if (mainBtn && document.getElementById('psx-view-marker')) {
        mainBtn.addEventListener('click', (e) => { e.preventDefault(); openWizard(); });
    }

    document.querySelectorAll('.op-select-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.op-select-btn').forEach(b => {
                b.classList.remove('active');
                b.style.borderColor = 'var(--nx-border)';
                b.style.backgroundColor = 'var(--nx-surface)';
                b.style.color = 'var(--nx-label)';
                b.style.opacity = '0.6';
            });
            btn.classList.add('active');
            const isAdd = btn.innerText.includes('Agregar');
            btn.style.borderColor = isAdd ? 'var(--nx-primary)' : 'rgb(var(--color-accent-violet))';
            btn.style.backgroundColor = isAdd ? 'rgba(var(--color-primary), 0.1)' : 'rgba(var(--color-accent-violet), 0.1)';
            btn.style.color = 'var(--nx-text)';
            btn.style.opacity = '1';
        });
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const modal = document.getElementById('psxWizardModal');
            if (modal && modal.style.opacity !== '0') closeWizard();
        }
    });
});
