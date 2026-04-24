let currentWizardStep = 1;

/**
 * Cuenta registros reales expandiendo rangos (1000-1005 = 6)
 */
function countRealRecords(text) {
    if (!text) return 0;
    const items = text.replace(/;/g, '\n').replace(/,/g, '\n').replace(/ /g, '\n').split('\n');
    let total = 0;
    items.forEach(line => {
        const item = line.trim();
        if (!item) return;
        if (item.includes('-')) {
            const parts = item.split('-');
            if (parts.length === 2) {
                const s = parseInt(parts[0].replace(/\D/g, ''));
                const e = parseInt(parts[1].replace(/\D/g, ''));
                if (!isNaN(s) && !isNaN(e)) {
                    total += Math.abs(e - s) + 1;
                    return;
                }
            }
        }
        total += 1;
    });
    return total;
}

/**
 * Sincroniza los números de línea basándose en el contenido del textarea
 */
function syncLineNumbers(textareaId, lineNumsId) {
    const textarea = document.getElementById(textareaId);
    const lineNums = document.getElementById(lineNumsId);
    if (!textarea || !lineNums) return;

    const lines = textarea.value.split('\n');
    const count = Math.max(lines.length, 1);
    
    let html = '';
    for (let i = 1; i <= count; i++) {
        html += `<span>${i}</span>`;
    }
    lineNums.innerHTML = html;
}

/**
 * Sincroniza el scroll vertical entre el textarea y la columna de números
 */
function syncScroll(textareaId, lineNumsId) {
    const textarea = document.getElementById(textareaId);
    const lineNums = document.getElementById(lineNumsId);
    if (!textarea || !lineNums) return;

    lineNums.scrollTop = textarea.scrollTop;
}

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
        if (el.type === 'checkbox') el.checked = false;
        el.style.borderColor = 'var(--nx-border)';
    });

    const select = document.getElementById('clientModeSelect');
    if (select) select.value = 'call_in';

    const toggle = document.getElementById('dataEntryToggle');
    if (toggle) toggle.checked = false;

    const forceToggle = document.getElementById('psxForceToggle');
    if (forceToggle) forceToggle.checked = false;

    // Reset Op Buttons
    document.querySelectorAll('.op-select-btn').forEach(btn => {
        btn.style.borderColor = 'var(--nx-border)';
        btn.style.backgroundColor = 'var(--nx-surface)';
        btn.style.color = 'var(--nx-label)';
        btn.style.opacity = '0.6';
        btn.classList.remove('active');
    });

    // Reset File Area
    const display = document.getElementById('fileNameDisplay');
    const iconContainer = document.getElementById('fileIconContainer');
    const border = document.getElementById('psxFileInput') ? document.getElementById('psxFileInput').parentElement : null;
    
    if (display) {
        display.innerText = 'Cargar Archivo Operativo';
        display.style.color = 'var(--nx-label)';
    }
    if (iconContainer) {
        iconContainer.innerHTML = '<svg class="w-8 h-8 opacity-40 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>';
    }
    if (border) border.style.borderColor = 'var(--nx-border)';

    handleRoutingLabelState();
    toggleDataMethod();
    syncLineNumbers('wizardManualTextarea', 'wizardLineNums');
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
            const textarea = document.getElementById('wizardManualTextarea');
            const lines = textarea.value.trim().split('\n').filter(l => l.trim() !== '');
            
            if (lines.length === 0) {
                textarea.style.borderColor = ERROR_COLOR;
                isValid = false;
            } else {
                // regex: 10 dígitos O 10 dígitos - 10 dígitos
                const individualPattern = /^\d{7,15}$/;
                const rangePattern = /^\d{7,15}-\d{7,15}$/;
                
                const allValid = lines.every(line => {
                    const cleanLine = line.trim();
                    return individualPattern.test(cleanLine) || rangePattern.test(cleanLine);
                });

                if (!allValid) {
                    textarea.style.borderColor = ERROR_COLOR;
                    if (typeof showToast === 'function') {
                        showToast('Formato inválido: Use 10 dígitos o Rango (10-10)', 'error');
                    }
                    isValid = false;
                }
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
    document.getElementById(`wizardStep${currentWizardStep}`).style.display = 'flex';
    
    // Progress
    const progress = (currentWizardStep / 3) * 100;
    const progressBar = document.getElementById('stepProgress');
    const activeBtn = Array.from(document.querySelectorAll('.op-select-btn')).find(b => b.classList.contains('active'));
    const isEliminar = activeBtn && activeBtn.innerText.includes('Eliminar');
    
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        progressBar.style.backgroundColor = isEliminar ? 'rgb(239, 68, 68)' : 'var(--nx-primary)';
    }
    
    document.getElementById('currentStepNum').innerText = currentWizardStep;

    const forceContainer = document.getElementById('psxForceContainer');
    if (forceContainer) {
        forceContainer.style.display = isEliminar ? 'none' : 'flex';
    }
    
    // Step 2 Logic
    if (currentWizardStep === 2) {
        const configSection = document.getElementById('opConfigSection');
        if (configSection) {
            configSection.style.display = isEliminar ? 'none' : 'block';
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
    const isEliminar = activeBtn && activeBtn.innerText.includes('Eliminar');

    const modeRow = document.getElementById('summaryModeRow');
    const routingRow = document.getElementById('summaryRoutingRow');
    
    if (isEliminar) {
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
        const val = document.getElementById('wizardManualTextarea').value;
        const total = countRealRecords(val);
        document.getElementById('summaryFileName').innerText = `${total} registros`;
    } else {
        document.getElementById('summaryData').innerText = 'Archivo (XML/CSV)';
        document.getElementById('summaryFileLabel').innerText = 'Nombre Archivo:';
        document.getElementById('summaryFileName').innerText = document.getElementById('fileNameDisplay').innerText;
    }

    document.getElementById('summaryTaskType').innerText = taskType;
}

async function finalizeWizard() {
    const toggle = document.getElementById('dataEntryToggle');
    const isManual = toggle && toggle.checked;
    const fileInput = document.getElementById('psxFileInput');
    const activeBtn = Array.from(document.querySelectorAll('.op-select-btn')).find(b => b.classList.contains('active'));
    const isEliminar = activeBtn && activeBtn.innerText.includes('Eliminar');
    const clientMode = document.getElementById('clientModeSelect').value;
    const routingLabel = document.getElementById('routingLabelInput').value;
    const manualData = document.getElementById('wizardManualTextarea').value;
    const forceTask = document.getElementById('psxForceToggle').checked;

    // 1. Preparar Payload Base
    const taskPayload = {
        tarea: isEliminar ? 'delete' : 'add',
        estado: 'Pendiente',
        accion_tipo: isEliminar ? 'N/A' : clientMode,
        routing_label: isEliminar ? null : routingLabel,
        datos_tipo: isManual ? 'Manual' : 'Archivo',
        datos: isManual ? manualData : (fileInput.files[0] ? fileInput.files[0].name : ''),
        total_items: isManual ? countRealRecords(manualData) : 0,
        force: forceTask
    };

    closeWizard();
    
    const progressModal = document.getElementById('psxProgressModal');
    const progressBar = document.getElementById('uploadProgressBar');
    const statusText = document.getElementById('progressStatusText');
    const log1 = document.getElementById('logValidation');
    const log2 = document.getElementById('logIndexing');

    if (progressModal) {
        if (progressBar) {
            progressBar.style.backgroundColor = isEliminar ? 'rgb(239, 68, 68)' : 'var(--nx-primary)';
            progressBar.style.boxShadow = isEliminar ? '0 0 15px rgba(239, 68, 68, 0.5)' : '0 0 15px rgba(var(--color-primary), 0.5)';
        }
        
        progressModal.classList.remove('opacity-0', 'pointer-events-none');
        
        let progress = 0;
        const interval = setInterval(() => {
            if (progress < 85) progress += Math.floor(Math.random() * 5) + 2;
            if (progressBar) progressBar.style.width = `${progress}%`;
            
            if (progress >= 30 && log1) log1.classList.remove('opacity-0');
            if (progress >= 60 && log2) {
                log2.classList.remove('opacity-0');
                if (statusText) statusText.innerText = 'Sincronizando con Nodo...';
            }
        }, 200);

        try {
            // A. Si hay archivo, subirlo primero
            if (!isManual && fileInput && fileInput.files.length > 0) {
                const fileFormData = new FormData();
                fileFormData.append('file', fileInput.files[0]);
                const uploadRes = await fetch('/api/psx/upload', { method: 'POST', body: fileFormData });
                const uploadResult = await uploadRes.json();
                if (uploadResult.status !== 'success') throw new Error(uploadResult.message);
                
                // Actualizar datos con el nombre real guardado
                taskPayload.datos = uploadResult.filename;
            }

            // B. Crear la tarea en la DB
            const createRes = await fetch('/api/psx/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(taskPayload)
            });
            const createResult = await createRes.json();
            if (createResult.status !== 'success') throw new Error(createResult.message);

            const numTasks = createResult.task_ids ? createResult.task_ids.length : 1;

            // ÉXITO FINAL
            clearInterval(interval);
            if (progressBar) progressBar.style.width = '100%';
            if (statusText) statusText.innerText = 'OPERACIÓN REGISTRADA';
            
            setTimeout(() => {
                progressModal.classList.add('opacity-0', 'pointer-events-none');
                if (typeof showToast === 'function') {
                    showToast(`Se han creado ${numTasks} tareas correctamente`, 'success');
                }
                if (window.activeNexusTable) window.activeNexusTable.ajax.reload(null, false);
                
                setTimeout(() => {
                    if (progressBar) progressBar.style.width = '0%';
                    document.querySelectorAll('[id^="log"]').forEach(l => l.classList.add('opacity-0'));
                    if (statusText) statusText.innerText = 'Iniciando transferencia...';
                }, 500);
            }, 1000);

        } catch (error) {
            clearInterval(interval);
            if (statusText) statusText.innerText = 'ERROR EN OPERACIÓN';
            if (progressBar) progressBar.style.backgroundColor = 'rgb(239, 68, 68)';
            
            setTimeout(() => {
                progressModal.classList.add('opacity-0', 'pointer-events-none');
                if (typeof showToast === 'function') showToast(error.message || 'Error al procesar la tarea', 'error');
            }, 2000);
        }
    }
}

function handleRoutingLabelState() {
    const select = document.getElementById('clientModeSelect');
    const input = document.getElementById('routingLabelInput');
    const label = document.getElementById('routingLabelTag');
    if (!select || !input || !label) return;

    if (select.value === 'call_inout') {
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

function handleScheduleRoutingLabelState() {
    const select = document.getElementById('scheduleClientModeSelect');
    const input = document.getElementById('scheduleRoutingLabelInput');
    if (!select || !input) return;

    if (select.value === 'call_inout') {
        input.disabled = false;
        input.placeholder = 'Ingrese etiqueta de ruta...';
    } else {
        input.disabled = true;
        input.placeholder = 'Bloqueado...';
    }
}

function handleModRoutingLabelState() {
    const select = document.getElementById('modClientModeSelect');
    const input = document.getElementById('modRoutingInput');
    if (!select || !input) return;

    if (select.value === 'call_inout') {
        input.disabled = false;
        input.placeholder = 'Ingrese etiqueta de ruta...';
    } else {
        input.disabled = true;
        input.placeholder = 'N/A (Bloqueado)';
        input.value = '';
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
    const iconContainer = document.getElementById('fileIconContainer');
    const border = input.parentElement;
    
    if (!file || !display || !border || !iconContainer) return;

    const extension = file.name.split('.').pop().toLowerCase();
    
    if (['csv', 'xls', 'xlsx'].includes(extension)) {
        display.innerText = file.name;
        display.style.color = 'var(--nx-primary)';
        border.style.borderColor = 'var(--nx-primary)';
        
        // Change icon to Document/Check
        iconContainer.innerHTML = '<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>';
        iconContainer.style.opacity = '1';
    } else {
        input.value = '';
        display.innerText = 'Extension No Válida';
        display.style.color = 'rgb(var(--color-accent-violet))';
        border.style.borderColor = 'rgb(var(--color-accent-violet))';
        
        // Change icon to Warning
        iconContainer.innerHTML = '<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>';
        iconContainer.style.opacity = '1';
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
            if (modal && !modal.classList.contains('pointer-events-none')) closeWizard();
            
            const scheduleModal = document.getElementById('scheduleWizardModal');
            if (scheduleModal && !scheduleModal.classList.contains('pointer-events-none')) closeScheduleWizard();
        }
    });

    // Schedule Op Buttons Logic
    document.querySelectorAll('.schedule-op-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.schedule-op-btn').forEach(b => {
                b.classList.remove('active');
                b.style.borderColor = 'var(--nx-border)';
                b.style.backgroundColor = 'var(--nx-surface)';
                b.style.color = 'var(--nx-label)';
                b.style.opacity = '0.6';
            });
            btn.classList.add('active');
            const isAdd = btn.innerText.includes('Añadir');
            btn.style.borderColor = isAdd ? 'var(--nx-primary)' : 'rgb(var(--color-accent-violet))';
            btn.style.backgroundColor = isAdd ? 'rgba(var(--color-primary), 0.1)' : 'rgba(var(--color-accent-violet), 0.1)';
            btn.style.color = 'var(--nx-text)';
            btn.style.opacity = '1';
        });
    });

    const scheduleBtn = document.getElementById('scheduleTaskBtn');
    if (scheduleBtn) {
        scheduleBtn.addEventListener('click', (e) => {
            e.preventDefault();
            openScheduleWizard();
        });
    }
});

// === SCHEDULE WIZARD LOGIC ===
let currentScheduleStep = 1;

function openScheduleWizard() {
    const modal = document.getElementById('scheduleWizardModal');
    if (modal) {
        resetScheduleWizardForm();
        modal.classList.remove('opacity-0', 'pointer-events-none');
        currentScheduleStep = 1;
        updateScheduleUI();
    }
}

function resetScheduleWizardForm() {
    // Reset inputs
    document.querySelectorAll('#scheduleWizardModal input, #scheduleWizardModal textarea').forEach(el => {
        el.value = '';
        el.style.borderColor = 'var(--panel-border)';
        if (el.type === 'checkbox') el.checked = false;
    });
    
    const scheduleForceToggle = document.getElementById('schedulePsxForceToggle');
    if (scheduleForceToggle) scheduleForceToggle.checked = false;

    const select = document.getElementById('scheduleClientModeSelect');
    if (select) select.value = 'call_in';

    // Reset Buttons Selection
    document.querySelectorAll('.schedule-op-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.style.borderColor = 'var(--panel-border)';
        btn.style.backgroundColor = 'var(--surface-container)/40';
        btn.style.color = 'var(--nx-label)';
        btn.style.opacity = '0.6';
    });

    // Reset File Area
    const display = document.getElementById('scheduleFileNameDisplay');
    const iconContainer = document.getElementById('scheduleFileIconContainer');
    if (display) {
        display.innerText = 'Cargar Archivo Operativo';
        display.style.color = 'var(--nx-label)';
    }
    if (iconContainer) {
        iconContainer.innerHTML = '<svg class="w-8 h-8 opacity-40 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>';
    }

    handleScheduleRoutingLabelState();
    toggleScheduleDataMethod();
    syncLineNumbers('scheduleManualTextarea', 'scheduleLineNums');
}

function closeScheduleWizard() {
    const modal = document.getElementById('scheduleWizardModal');
    if (modal) {
        modal.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(resetScheduleWizardForm, 300);
    }
}

function changeScheduleStep(delta) {
    if (delta > 0 && !validateScheduleStep()) {
        triggerScheduleShake();
        return;
    }

    const nextStep = currentScheduleStep + delta;
    if (nextStep >= 1 && nextStep <= 4) {
        currentScheduleStep = nextStep;
        updateScheduleUI();
    }
}

function validateScheduleStep() {
    let isValid = true;
    const ERROR_COLOR = 'rgb(var(--color-accent-violet))';

    if (currentScheduleStep === 1) {
        const anyActive = Array.from(document.querySelectorAll('.schedule-op-btn')).some(btn => btn.classList.contains('active'));
        if (!anyActive) {
            if (typeof showToast === 'function') showToast('Seleccione un tipo de operación', 'error');
            isValid = false;
        }
    } 
    else if (currentScheduleStep === 2) {
        const activeBtn = Array.from(document.querySelectorAll('.schedule-op-btn')).find(b => b.classList.contains('active'));
        const isEliminar = activeBtn && activeBtn.innerText.includes('Eliminar');

        const mode = document.getElementById('scheduleClientModeSelect').value;
        const routing = document.getElementById('scheduleRoutingLabelInput');
        if (!isEliminar && mode === 'call_inout' && routing.value.trim() === '') {
            routing.style.borderColor = ERROR_COLOR;
            isValid = false;
        }

        const isManual = document.getElementById('scheduleDataEntryToggle').checked;
        if (isManual) {
            const textarea = document.getElementById('scheduleManualTextarea');
            const lines = textarea ? textarea.value.trim().split('\n').filter(l => l.trim() !== '') : [];
            
            if (lines.length === 0) {
                if (textarea) textarea.style.borderColor = ERROR_COLOR;
                isValid = false;
            } else {
                const individualPattern = /^\d{7,15}$/;
                const rangePattern = /^\d{7,15}-\d{7,15}$/;
                const allValid = lines.every(line => individualPattern.test(line.trim()) || rangePattern.test(line.trim()));

                if (!allValid) {
                    if (textarea) textarea.style.borderColor = ERROR_COLOR;
                    if (typeof showToast === 'function') showToast('Formato inválido en registros', 'error');
                    isValid = false;
                }
            }
        } else {
            const fileInput = document.getElementById('scheduleFileInput');
            if (!fileInput || fileInput.files.length === 0) {
                document.getElementById('scheduleMethodFileUpload').querySelector('label').style.borderColor = ERROR_COLOR;
                isValid = false;
            }
        }
    }
    else if (currentScheduleStep === 3) {
        const timeVal = document.getElementById('scheduleTimeInput').value;
        if (!timeVal) {
            if (typeof showToast === 'function') showToast('Ingrese la hora de inicio', 'error');
            isValid = false;
        } else {
            const [hours, minutes] = timeVal.split(':');
            const scheduledDateTime = new Date(selectedDate);
            scheduledDateTime.setHours(parseInt(hours), parseInt(minutes), 0, 0);
            const diffHours = (scheduledDateTime - new Date()) / (1000 * 60 * 60);

            if (diffHours < 1) {
                if (typeof showToast === 'function') showToast('Mínimo 1 hora de anticipación', 'error');
                isValid = false;
            }
        }
    }

    return isValid;
}

function triggerScheduleShake() {
    const box = document.querySelector('#scheduleWizardModal > div:last-child');
    if (box) {
        box.classList.add('animate-shake');
        setTimeout(() => box.classList.remove('animate-shake'), 500);
    }
}

function updateScheduleUI() {
    // Hide all steps
    document.querySelectorAll('#scheduleWizardModal .step-content').forEach(step => {
        step.style.display = 'none';
        step.classList.add('hidden');
    });

    const currentEl = document.getElementById(`scheduleStep${currentScheduleStep}`);
    if (currentEl) {
        currentEl.style.display = 'flex';
        currentEl.classList.remove('hidden');
    }

    const activeBtn = Array.from(document.querySelectorAll('.schedule-op-btn')).find(b => b.classList.contains('active'));
    const isEliminar = activeBtn && activeBtn.innerText.includes('Eliminar');

    // Progress Bar
    const progress = (currentScheduleStep / 4) * 100;
    const progressBar = document.getElementById('scheduleStepProgress');
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        progressBar.style.backgroundColor = isEliminar ? 'rgb(239, 68, 68)' : 'var(--nx-primary)';
        progressBar.style.boxShadow = isEliminar ? '0 0 15px rgba(239, 68, 68, 0.4)' : 'none';
    }

    // Visibility in Step 2
    if (currentScheduleStep === 2) {
        const configSection = document.getElementById('scheduleOpConfigSection');
        if (configSection) {
            configSection.style.display = isEliminar ? 'none' : 'block';
        }
    }

    // Step Num
    const stepNum = document.getElementById('scheduleStepNum');
    if (stepNum) stepNum.innerText = currentScheduleStep;

    const forceContainer = document.getElementById('scheduleForceContainer');
    if (forceContainer) {
        forceContainer.style.display = isEliminar ? 'none' : 'flex';
    }

    // Buttons
    const prevBtn = document.getElementById('schedulePrevStepBtn');
    const nextBtn = document.getElementById('scheduleNextStepBtn');
    const launchBtn = document.getElementById('scheduleLaunchBtn');

    if (prevBtn) prevBtn.style.display = (currentScheduleStep === 1) ? 'none' : 'flex';

    if (currentScheduleStep === 4) {
        if (nextBtn) nextBtn.style.display = 'none';
        if (launchBtn) {
            launchBtn.style.display = 'flex';
            launchBtn.classList.remove('hidden');
        }
    } else {
        if (nextBtn) nextBtn.style.display = 'flex';
        if (launchBtn) launchBtn.style.display = 'none';
    }
}

async function finalizeScheduleWizard() {
    const activeBtn = Array.from(document.querySelectorAll('.schedule-op-btn')).find(b => b.classList.contains('active'));
    const isEliminar = activeBtn && activeBtn.innerText.includes('Eliminar');
    const clientMode = document.getElementById('scheduleClientModeSelect').value;
    const routingLabel = document.getElementById('scheduleRoutingLabelInput').value;
    const isManual = document.getElementById('scheduleDataEntryToggle').checked;
    const fileInput = document.getElementById('scheduleFileInput');
    const manualData = document.getElementById('scheduleManualTextarea').value;
    const forceTask = document.getElementById('schedulePsxForceToggle').checked;

    const timeVal = document.getElementById('scheduleTimeInput').value;
    const [hours, minutes] = timeVal.split(':');
    const scheduledDateTime = new Date(selectedDate);
    scheduledDateTime.setHours(parseInt(hours), parseInt(minutes), 0, 0);

    const taskPayload = {
        tarea: isEliminar ? 'delete' : 'add',
        estado: 'Programada',
        accion_tipo: isManual ? 'Manual' : 'Archivo',
        routing_label: isEliminar ? null : routingLabel,
        datos_tipo: isEliminar ? 'N/A' : clientMode,
        datos: isManual ? manualData : (fileInput.files[0] ? fileInput.files[0].name : ''),
        total_items: isManual ? countRealRecords(manualData) : 0,
        fecha_inicio: scheduledDateTime.toISOString(),
        force: forceTask
    };

    closeScheduleWizard();
    
    const progressModal = document.getElementById('psxProgressModal');
    const statusText = document.getElementById('progressStatusText');
    const progressBar = document.getElementById('uploadProgressBar');

    if (progressModal) {
        progressModal.classList.remove('opacity-0', 'pointer-events-none');
        if (statusText) statusText.innerText = 'Programando Tarea...';
        
        let progress = 0;
        const interval = setInterval(() => {
            if (progress < 90) progress += 10;
            if (progressBar) progressBar.style.width = `${progress}%`;
        }, 100);

        try {
            if (!isManual && fileInput && fileInput.files.length > 0) {
                const fd = new FormData();
                fd.append('file', fileInput.files[0]);
                const up = await fetch('/api/psx/upload', { method: 'POST', body: fd });
                const ur = await up.json();
                if (ur.status === 'success') taskPayload.datos = ur.filename;
            }

            const res = await fetch('/api/psx/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(taskPayload)
            });
            const result = await res.json();
            if (result.status !== 'success') throw new Error(result.message);

            const numTasks = result.task_ids ? result.task_ids.length : 1;

            clearInterval(interval);
            if (progressBar) progressBar.style.width = '100%';
            if (statusText) statusText.innerText = 'TAREA PROGRAMADA';
            
            setTimeout(() => {
                progressModal.classList.add('opacity-0', 'pointer-events-none');
                if (typeof showToast === 'function') {
                    showToast(`Se han programado ${numTasks} tareas con éxito`, 'success');
                }
                if (window.activeNexusTable) window.activeNexusTable.ajax.reload(null, false);
            }, 1000);

        } catch (error) {
            clearInterval(interval);
            if (statusText) statusText.innerText = 'ERROR EN PROGRAMACIÓN';
            setTimeout(() => {
                progressModal.classList.add('opacity-0', 'pointer-events-none');
                if (typeof showToast === 'function') showToast(error.message, 'error');
            }, 2000);
        }
    }
}

function validateScheduleFile(input) {
    const file = input.files[0];
    const display = document.getElementById('scheduleFileNameDisplay');
    const iconContainer = document.getElementById('scheduleFileIconContainer');
    const border = input.parentElement;
    
    if (!file || !display || !border || !iconContainer) return;

    const extension = file.name.split('.').pop().toLowerCase();
    
    if (['csv', 'xls', 'xlsx'].includes(extension)) {
        display.innerText = file.name;
        display.style.color = 'var(--nx-primary)';
        border.style.borderColor = 'var(--nx-primary)';
        iconContainer.innerHTML = '<svg class="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>';
    } else {
        input.value = '';
        display.innerText = 'Extensión No Válida';
        display.style.color = 'rgb(var(--color-accent-violet))';
        border.style.borderColor = 'rgb(var(--color-accent-violet))';
        iconContainer.innerHTML = '<svg class="w-8 h-8 text-accent-violet" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>';
    }
}

// === CUSTOM CALENDAR LOGIC ===
let calendarDate = new Date();
let selectedDate = new Date();

function renderCalendar() {
    const monthLabel = document.getElementById('calendarMonthLabel');
    const grid = document.getElementById('calendarGrid');
    if (!monthLabel || !grid) return;

    const year = calendarDate.getFullYear();
    const month = calendarDate.getMonth();
    
    const months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
    monthLabel.innerText = `${months[month]} ${year}`;

    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    grid.innerHTML = '';

    // Empty spaces for first days
    for (let i = 0; i < firstDay; i++) {
        const span = document.createElement('span');
        grid.appendChild(span);
    }

    // Actual days
    const today = new Date();
    today.setHours(0,0,0,0);

    for (let day = 1; day <= daysInMonth; day++) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.innerText = day;
        btn.className = "h-9 w-full rounded-xl text-[12px] font-bold flex items-center justify-center transition-all";
        
        const currentIterDate = new Date(year, month, day);
        const isPast = currentIterDate < today;
        const isToday = today.toDateString() === currentIterDate.toDateString();
        const isSelected = selectedDate.toDateString() === currentIterDate.toDateString();

        if (isPast) {
            btn.classList.add('opacity-10', 'cursor-not-allowed', 'pointer-events-none');
        } else {
            btn.classList.add('hover:bg-primary/20', 'hover:text-primary');
            if (isToday) btn.classList.add('text-primary', 'bg-primary/5');
            if (isSelected) {
                btn.classList.add('bg-primary', 'text-white', 'shadow-[0_0_15px_rgba(var(--color-primary),0.4)]');
                btn.classList.remove('hover:bg-primary/20', 'hover:text-primary');
            }

            btn.onclick = () => {
                selectedDate = new Date(year, month, day);
                renderCalendar();
            };
        }

        grid.appendChild(btn);
    }
}

function changeCalendarMonth(delta) {
    calendarDate.setMonth(calendarDate.getMonth() + delta);
    renderCalendar();
}

// Trigger render when opening wizard or switching to step 3
const originalUpdateScheduleUI = updateScheduleUI;
updateScheduleUI = function() {
    originalUpdateScheduleUI();
    if (currentScheduleStep === 3) {
        renderCalendar();
    }
    if (currentScheduleStep === 4) {
        collectScheduleData();
    }
}

function collectScheduleData() {
    const activeBtn = Array.from(document.querySelectorAll('.schedule-op-btn')).find(b => b.classList.contains('active'));
    const taskType = activeBtn ? activeBtn.innerText.trim() : 'N/A';
    const isEliminar = activeBtn && activeBtn.innerText.includes('Eliminar');

    const modeSelect = document.getElementById('scheduleClientModeSelect');
    const routingInput = document.getElementById('scheduleRoutingLabelInput');
    const timeInput = document.getElementById('scheduleTimeInput');

    // Fill Summary
    document.getElementById('scheduleSummaryTaskType').innerText = taskType;
    
    const modeRow = document.getElementById('scheduleSummaryModeRow');
    const routingRow = document.getElementById('scheduleSummaryRoutingRow');

    if (isEliminar) {
        if (modeRow) modeRow.style.display = 'none';
        if (routingRow) routingRow.style.display = 'none';
    } else {
        if (modeRow) modeRow.style.display = 'grid';
        if (routingRow) routingRow.style.display = 'grid';
        
        document.getElementById('scheduleSummaryMode').innerText = (modeSelect) ? modeSelect.options[modeSelect.selectedIndex].text : 'N/A';
        document.getElementById('scheduleSummaryRouting').innerText = (routingInput && routingInput.value.trim() !== '') ? routingInput.value : 'N/A';
    }
    
    // Schedule Data
    document.getElementById('scheduleSummaryDate').innerText = selectedDate.toLocaleDateString('es-ES', { day: '2-digit', month: 'long', year: 'numeric' });
    document.getElementById('scheduleSummaryTime').innerText = (timeInput && timeInput.value) ? timeInput.value + ' hrs' : 'No definida';

    const toggle = document.getElementById('scheduleDataEntryToggle');
    const isManual = toggle && toggle.checked;

    if (isManual) {
        document.getElementById('scheduleSummaryData').innerText = 'Ingreso Manual';
        const textarea = document.getElementById('scheduleManualTextarea');
        const total = countRealRecords(textarea ? textarea.value : '');
        document.getElementById('scheduleSummaryFileName').innerText = `${total} registros`;
    } else {
        document.getElementById('scheduleSummaryData').innerText = 'Archivo (XML/CSV)';
        const fileName = document.getElementById('scheduleFileNameDisplay');
        document.getElementById('scheduleSummaryFileName').innerText = fileName ? fileName.innerText : '-';
    }
}

function toggleScheduleDataMethod() {
    const toggle = document.getElementById('scheduleDataEntryToggle');
    const fileArea = document.getElementById('scheduleMethodFileUpload');
    const manualArea = document.getElementById('scheduleMethodManualEntry');
    const labelFile = document.getElementById('scheduleLabelFileMode');
    const labelManual = document.getElementById('scheduleLabelManualMode');
    if (!toggle || !fileArea || !manualArea) return;

    if (toggle.checked) {
        fileArea.classList.add('hidden');
        manualArea.classList.remove('hidden');
        manualArea.style.display = 'block';
        fileArea.style.display = 'none';
        labelManual.style.opacity = '1';
        labelFile.style.opacity = '0.4';
    } else {
        fileArea.classList.remove('hidden');
        manualArea.classList.add('hidden');
        fileArea.style.display = 'block';
        manualArea.style.display = 'none';
        labelFile.style.opacity = '1';
        labelManual.style.opacity = '0.4';
    }
}

function handleScheduleRoutingLabelState() {
    const select = document.getElementById('scheduleClientModeSelect');
    const input = document.getElementById('scheduleRoutingLabelInput');
    const label = document.getElementById('scheduleRoutingLabelTag');
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
// === MODIFY WIZARD LOGIC (Dynamic Flow) ===

let currentModifyStep = 1;
let currentModifyJobId = null;
let currentModifyTaskData = null;
let modifyAction = 'modify'; // 'modify' or 'cancel'
let modifyTaskType = 'add'; 
let modifyTiming = 'now';

async function openModifyModal(taskId) {
    const modal = document.getElementById('modifyTaskModal');
    if (!modal) return;

    try {
        // Obtener datos del Job
        const res = await fetch(`/api/psx/list`);
        const json = await res.json();
        const task = json.tasks.find(t => t.id === taskId);
        if (!task) throw new Error("Tarea no encontrada");

        currentModifyJobId = task.job_id;
        currentModifyTaskData = task;

        // Reset UI
        resetModifyForm();
        currentModifyStep = 1;
        document.getElementById('modifyTicketNum').innerText = String(taskId).padStart(5, '0');
        
        // 1. Mostrar botones según estado
        const btnCancel = document.getElementById('btnActionCancel');
        const btnActivate = document.getElementById('btnActionActivate');
        const btnModify = document.getElementById('btnActionModify');
        const grid = document.getElementById('modifyDecisionGrid');

        // Reset
        btnCancel.classList.add('hidden');
        btnCancel.classList.remove('col-span-2');
        btnActivate.classList.add('hidden');
        btnModify.classList.remove('hidden', 'col-span-2');
        grid.classList.replace('grid-cols-1', 'grid-cols-2');

        const stateLower = task.estado.toLowerCase();
        
        if (stateLower === 'ejecutando') {
            // Solo se puede cancelar si está ejecutando
            btnCancel.classList.remove('hidden');
            btnCancel.classList.add('col-span-2');
            btnModify.classList.add('hidden');
            grid.classList.replace('grid-cols-2', 'grid-cols-1');
        } else if (['activa', 'programada', 'pendiente'].includes(stateLower)) {
            btnCancel.classList.remove('hidden');
            btnModify.classList.remove('hidden');
        } else if (['terminada', 'error', 'cancelada'].includes(stateLower)) {
            btnActivate.classList.remove('hidden');
            btnModify.classList.remove('hidden');
        } else {
            // Unificamos el resto de estados para que al menos se pueda cancelar si no es un estado terminal
            btnCancel.classList.remove('hidden');
            btnModify.classList.remove('hidden');
        }

        // Pre-cargar valores
        modifyTaskType = task.tarea;
        setModifyTaskType(task.tarea);
        
        document.getElementById('modRoutingInput').value = task.routing_label || '';
        document.getElementById('modForceToggle').checked = task.force || false;
        document.getElementById('modSourceDisplay').innerText = task.archivo_origen || 'INGRESO MANUAL';

        // Timing
        if (task.estado === 'Programada' && task.fecha_inicio) {
            setModifyTiming('schedule');
            const d = new Date(task.fecha_inicio);
            selectedModDate = d;
            currentModMonth = d.getMonth();
            currentModYear = d.getFullYear();
            const time = task.fecha_inicio.split('T')[1].split('.')[0].substring(0, 5);
            document.getElementById('modTimeInput').value = time;
            renderModCalendar();
        } else {
            setModifyTiming('now');
            selectedModDate = new Date();
            currentModMonth = selectedModDate.getMonth();
            currentModYear = selectedModDate.getFullYear();
            renderModCalendar();
        }

        modal.classList.remove('opacity-0', 'pointer-events-none');
        updateModifyUI();

    } catch (e) {
        if (typeof showToast === 'function') showToast(e.message, 'error');
    }
}

function closeModifyModal() {
    const modal = document.getElementById('modifyTaskModal');
    if (modal) {
        modal.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(resetModifyForm, 300);
    }
}

function resetModifyForm() {
    modifyAction = 'modify';
    modifyTaskType = 'add';
    modifyTiming = 'now';
    currentModifyStep = 1;

    const modal = document.getElementById('modifyTaskModal');
    if (!modal) return;

    modal.querySelectorAll('input, select').forEach(el => {
        if (el.type === 'checkbox') el.checked = false;
        else if (el.tagName === 'SELECT') el.value = 'call_in';
        else el.value = '';
    });

    const routingInput = document.getElementById('modRoutingInput');
    if (routingInput) {
        routingInput.disabled = false;
        routingInput.placeholder = 'N/A';
    }

    const forceToggle = document.getElementById('modForceToggle');
    if (forceToggle) forceToggle.checked = false;

    // Reset button groups
    selectModifyAction('modify');
    setModifyTiming('now');
    
    const step4 = document.getElementById('modifyStep4');
    if (step4) step4.classList.remove('hidden');
    
    const totalStepsLabel = document.getElementById('modifyTotalSteps');
    if (totalStepsLabel) totalStepsLabel.innerText = '5';
}

function selectModifyAction(action) {
    modifyAction = action;
    const btns = [
        { id: 'btnActionCancel', color: 'rose-500' },
        { id: 'btnActionActivate', color: 'emerald-500' },
        { id: 'btnActionModify', color: 'primary' }
    ];

    btns.forEach(item => {
        const btn = document.getElementById(item.id);
        if (!btn) return;
        
        // Reset to default
        btn.classList.remove(`border-${item.color}`, `bg-${item.color}/10`, 'text-label');
        btn.classList.add('border-panel-border', 'bg-surface-container/40', 'text-label/60');
        btn.style.boxShadow = 'none';
        
        if (modifyAction === item.id.replace('btnAction', '').toLowerCase()) {
            btn.classList.remove('border-panel-border', 'bg-surface-container/40', 'text-label/60');
            btn.classList.add(`border-${item.color}`, `bg-${item.color}/10`, 'text-label');
            if (item.color === 'primary') {
                btn.style.boxShadow = '0 0 50px rgba(var(--color-primary), 0.2)';
            } else {
                const hex = item.color === 'rose-500' ? '244,63,94' : '16,185,129';
                btn.style.boxShadow = `0 0 50px rgba(${hex}, 0.2)`;
            }
        }
    });
}

function setModifyTaskType(type) {
    modifyTaskType = type;
    const btnAdd = document.getElementById('modTypeAdd');
    const btnDel = document.getElementById('modTypeDel');
    if (!btnAdd || !btnDel) return;

    // Reset
    [btnAdd, btnDel].forEach(b => {
        b.classList.remove('border-primary', 'bg-primary/10', 'border-rose-500', 'bg-rose-500/10', 'text-label');
        b.classList.add('border-panel-border', 'bg-surface-container/40', 'text-label/60');
        b.style.boxShadow = 'none';
    });

    if (type === 'add') {
        btnAdd.classList.remove('border-panel-border', 'bg-surface-container/40', 'text-label/60');
        btnAdd.classList.add('border-primary', 'bg-primary/10', 'text-label');
        btnAdd.style.boxShadow = '0 0 50px rgba(var(--color-primary), 0.2)';
    } else {
        btnDel.classList.remove('border-panel-border', 'bg-surface-container/40', 'text-label/60');
        btnDel.classList.add('border-rose-500', 'bg-rose-500/10', 'text-label');
        btnDel.style.boxShadow = '0 0 50px rgba(244,63,94,0.2)';
    }
}

function setModifyTiming(timing) {
    modifyTiming = timing;
    const btnNow = document.getElementById('modTimingNow');
    const btnLate = document.getElementById('modTimingLate');
    const calendar = document.getElementById('modCalendarContainer');

    btnNow.classList.remove('bg-primary', 'text-white');
    btnLate.classList.remove('bg-primary', 'text-white');
    calendar.classList.add('hidden');

    if (timing === 'now') {
        btnNow.classList.add('bg-primary', 'text-white');
    } else {
        btnLate.classList.add('bg-primary', 'text-white');
        calendar.classList.remove('hidden');
        renderModCalendar();
    }
}

function changeModifyStep(delta) {
    // Decisiones en Paso 1 (Saltos directos para Cancelar/Activar)
    const isQuickAction = (modifyAction === 'cancel' || modifyAction === 'activate');
    
    if (currentModifyStep === 1 && isQuickAction && delta > 0) {
        currentModifyStep = 5;
    } 
    else if (currentModifyStep === 5 && isQuickAction && delta < 0) {
        currentModifyStep = 1;
    }
    else {
        // Validación de Calendario si es programada
        if (currentModifyStep === 3 && modifyTiming === 'schedule' && delta > 0) {
            const timeVal = document.getElementById('modTimeInput').value;
            if (!timeVal || !selectedModDate) {
                if (typeof showToast === 'function') showToast("Complete fecha y hora", "error");
                return;
            }

            const [hours, minutes] = timeVal.split(':');
            const scheduledDateTime = new Date(selectedModDate);
            scheduledDateTime.setHours(parseInt(hours), parseInt(minutes), 0, 0);
            const diffHours = (scheduledDateTime - new Date()) / (1000 * 60 * 60);

            if (diffHours < 1) {
                if (typeof showToast === 'function') showToast('Mínimo 1 hora de anticipación', 'error');
                return;
            }
        }
        
        currentModifyStep += delta;

        // Skip Step 4 if it's a delete operation
        const isEliminar = (modifyTaskType === 'delete' || modifyTaskType === 'del');
        if (isEliminar && currentModifyStep === 4) {
            currentModifyStep += delta;
        }
    }

    if (currentModifyStep < 1) currentModifyStep = 1;
    if (currentModifyStep > 5) currentModifyStep = 5;

    updateModifyUI();
}

function updateModifyUI() {
    const isQuickAction = (modifyAction === 'cancel' || modifyAction === 'activate');
    const isEliminar = (modifyTaskType === 'delete' || modifyTaskType === 'del');
    
    // Calculate effective total steps and visual current step
    let totalSteps = 5;
    let visualStep = currentModifyStep;

    if (isQuickAction) {
        totalSteps = 2;
        visualStep = (currentModifyStep === 5) ? 2 : 1;
    } else if (isEliminar) {
        totalSteps = 4;
        if (currentModifyStep === 5) visualStep = 4;
    }

    document.querySelectorAll('.modify-step-content').forEach(s => s.classList.add('hidden'));
    document.getElementById(`modifyStep${currentModifyStep}`).classList.remove('hidden');

    const stepNumLabel = document.getElementById('modifyStepNum');
    const totalStepsLabel = document.getElementById('modifyTotalSteps');
    const progressBar = document.getElementById('modifyStepProgress');

    if (stepNumLabel) stepNumLabel.innerText = visualStep;
    if (totalStepsLabel) totalStepsLabel.innerText = totalSteps;
    if (progressBar) progressBar.style.width = `${(visualStep / totalSteps) * 100}%`;

    const prevBtn = document.getElementById('modPrevBtn');
    const nextBtn = document.getElementById('modNextBtn');
    const submitBtn = document.getElementById('modSubmitBtn');

    prevBtn.classList.toggle('hidden', currentModifyStep === 1);
    nextBtn.classList.toggle('hidden', currentModifyStep === 5);
    submitBtn.classList.toggle('hidden', currentModifyStep !== 5);

    // Ocultar forzado en eliminación
    const forceContainer = document.getElementById('modForceContainer');
    if (forceContainer) {
        forceContainer.style.display = (modifyTaskType === 'delete' || modifyTaskType === 'del') ? 'none' : 'flex';
    }

    if (currentModifyStep === 5) collectModifySummary();
}

function collectModifySummary() {
    const title = document.getElementById('modFinalTitle');
    const desc = document.getElementById('modFinalDesc');
    
    if (modifyAction === 'cancel') {
        title.innerText = "Confirmar Cancelación";
        desc.innerText = "Se detendrán los fragmentos pendientes de esta tarea.";
        document.getElementById('summaryModAction').innerText = "CANCELAR TAREA";
    } else if (modifyAction === 'activate') {
        title.innerText = "Confirmar Activación";
        desc.innerText = "Se procederá a poner en cola nuevamente el fragmento seleccionado.";
        document.getElementById('summaryModAction').innerText = "ACTIVAR TAREA";
    } else {
        title.innerText = "Confirmar Modificaciones";
        desc.innerText = "Se aplicarán los parámetros a los fragmentos o se creará una nueva tarea de reproceso.";
        document.getElementById('summaryModAction').innerText = modifyTaskType.toUpperCase();
    }

    const dateStr = selectedModDate ? selectedModDate.toISOString().split('T')[0] : 'HOY';
    const modTimeInput = document.getElementById('modTimeInput');
    const modRoutingInput = document.getElementById('modRoutingInput');
    
    const timeVal = modTimeInput ? modTimeInput.value : '00:00';
    document.getElementById('summaryModTime').innerText = modifyTiming === 'now' ? 'INMEDIATO' : `${dateStr} ${timeVal}`;
    document.getElementById('summaryModLabel').innerText = (modRoutingInput ? modRoutingInput.value : '') || 'N/A';
}

async function confirmModifyAction() {
    let schedTime = null;
    if (modifyTiming === 'schedule' && selectedModDate) {
        const timeVal = document.getElementById('modTimeInput').value;
        schedTime = `${selectedModDate.toISOString().split('T')[0]}T${timeVal}:00`;
    }

    const modClientMode = document.getElementById('modClientModeSelect');
    const modRouting = document.getElementById('modRoutingInput');
    const modForce = document.getElementById('modForceToggle');

    const payload = {
        action: modifyAction,
        tarea: modifyTaskType,
        origin_task_id: currentModifyTaskData ? currentModifyTaskData.id : null,
        routing_label: modRouting ? modRouting.value : null,
        accion_tipo: modifyTaskType === 'delete' ? 'N/A' : (modClientMode ? modClientMode.value : 'call_in'),
        datos_tipo: currentModifyTaskData.datos_tipo, 
        force: modForce ? modForce.checked : false,
        is_scheduled: modifyTiming === 'schedule',
        scheduled_time: schedTime
    };

    try {
        const res = await fetch(`/api/psx/job/update/${currentModifyJobId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await res.json();
        if (result.status === 'success') {
            if (typeof showToast === 'function') showToast(result.message, 'success');
            closeModifyModal();
            if (typeof fetchPSXData === 'function') fetchPSXData();
            if (psxDataTable) psxDataTable.ajax.reload();
        } else {
            throw new Error(result.message);
        }
    } catch (e) {
        if (typeof showToast === 'function') showToast(e.message, 'error');
    }
}

// === MODIFY CALENDAR ENGINE ===
let selectedModDate = new Date();
let currentModMonth = selectedModDate.getMonth();
let currentModYear = selectedModDate.getFullYear();

function renderModCalendar() {
    const grid = document.getElementById('modCalendarGrid');
    const label = document.getElementById('modCalendarMonthLabel');
    if (!grid || !label) return;

    grid.innerHTML = '';
    const months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
    label.innerText = `${months[currentModMonth]} ${currentModYear}`;

    const firstDay = new Date(currentModYear, currentModMonth, 1).getDay();
    const daysInMonth = new Date(currentModYear, currentModMonth + 1, 0).getDate();
    const today = new Date();
    today.setHours(0,0,0,0);

    for (let i = 0; i < firstDay; i++) {
        grid.innerHTML += '<div></div>';
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(currentModYear, currentModMonth, day);
        const isPast = date < today;
        const isSelected = selectedModDate && date.getTime() === selectedModDate.getTime();
        
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.innerText = day;
        btn.className = `h-8 w-8 text-[12px] font-bold rounded-lg transition-all ${isPast ? 'opacity-20 cursor-not-allowed' : 'hover:bg-primary/20 cursor-pointer'}`;
        if (isSelected) btn.className += ' bg-primary text-white shadow-lg shadow-primary/40 scale-110';
        
        if (!isPast) {
            btn.onclick = () => {
                selectedModDate = date;
                renderModCalendar();
            };
        }
        grid.appendChild(btn);
    }
}

function changeModCalendarMonth(delta) {
    currentModMonth += delta;
    if (currentModMonth < 0) { currentModMonth = 11; currentModYear--; }
    if (currentModMonth > 11) { currentModMonth = 0; currentModYear++; }
    renderModCalendar();
}

// Global KeyDown listener for ESC key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        if (typeof closeModifyModal === 'function') closeModifyModal();
        if (typeof closeWizard === 'function') closeWizard();
        if (typeof closeScheduleWizard === 'function') closeScheduleWizard();
    }
});
