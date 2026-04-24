/**
 * NEXUS PREMIUM GUIDED TOUR - PSX5K TERMINAL (V8)
 */
class PSXNexusTour {
    constructor(steps) {
        this.steps = steps;
        this.currentStep = -1;
        this.overlay = null;
        this.stepEl = null;
        this.spotlight = null;
        this._keyHandler = null;
    }

    init() {
        console.log('🏁 Initializing PSX Tour Elements...');
        // Cleanup existing tour elements to prevent duplication
        document.querySelectorAll('.nx-tour-overlay, .nx-tour-step, .nx-tour-spotlight').forEach(el => el.remove());

        this.overlay = document.createElement('div');
        this.overlay.className = 'nx-tour-overlay';
        this.overlay.onclick = () => this.end();
        document.body.appendChild(this.overlay);

        this.spotlight = document.createElement('div');
        this.spotlight.className = 'nx-tour-spotlight';
        document.body.appendChild(this.spotlight);

        this.stepEl = document.createElement('div');
        this.stepEl.className = 'nx-tour-step';
        document.body.appendChild(this.stepEl);
    }

    start() {
        console.log('🚀 Starting PSX5K Guided Tour');
        
        // Ensure UI elements are initialized before starting
        this.init();

        const modBtn = document.getElementById('modifyTaskBtn');
        if (modBtn) modBtn.classList.remove('opacity-30', 'pointer-events-none');

        this.currentStep = 0;
        this.overlay.classList.add('active');
        this.spotlight.classList.add('active');
        this.showStep();

        // Keyboard navigation
        this._keyHandler = (e) => {
            if (this.currentStep < 0) return;
            if (e.key === 'Enter' || e.key === 'ArrowRight') { e.preventDefault(); this.next(); }
            else if (e.key === 'Backspace' || e.key === 'ArrowLeft') { e.preventDefault(); this.prev(); }
            else if (e.key === 'Escape') { e.preventDefault(); this.end(); }
        };
        document.addEventListener('keydown', this._keyHandler);
    }

    next() {
        if (this.currentStep < this.steps.length - 1) {
            this.currentStep++;
            this.showStep();
        } else {
            this.end();
        }
    }

    prev() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep();
        }
    }

    end() {
        const modBtn = document.getElementById('modifyTaskBtn');
        if (modBtn) modBtn.classList.add('opacity-30', 'pointer-events-none');

        if (this.overlay) this.overlay.classList.remove('active');
        if (this.stepEl) this.stepEl.classList.remove('active');
        if (this.spotlight) this.spotlight.classList.remove('active');
        this.currentStep = -1;

        if (this._keyHandler) {
            document.removeEventListener('keydown', this._keyHandler);
            this._keyHandler = null;
        }
    }

    showStep() {
        const step = this.steps[this.currentStep];
        const target = document.querySelector(step.target);
        
        if (target) {
            const rect = target.getBoundingClientRect();
            const padding = 10;
            
            this.spotlight.style.top = `${rect.top - padding}px`;
            this.spotlight.style.left = `${rect.left - padding}px`;
            this.spotlight.style.width = `${rect.width + (padding * 2)}px`;
            this.spotlight.style.height = `${rect.height + (padding * 2)}px`;

            // Build pagination dots
            const dots = this.steps.map((_, i) => 
                `<div class="nx-tour-dot ${i === this.currentStep ? 'active' : ''}"></div>`
            ).join('');

            const arrowLeft = `<svg class="nx-tour-arrow ${this.currentStep === 0 ? 'disabled' : ''}" onclick="window.psxTour.prev()" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 19l-7-7 7-7"></path></svg>`;
            const arrowRight = `<svg class="nx-tour-arrow" onclick="window.psxTour.next()" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"></path></svg>`;

            // Build table if present in step
            let tableHTML = '';
            if (step.table) {
                const rows = step.table.map(row => `
                    <tr>
                        <td>${row.val}</td>
                        <td>${row.desc}</td>
                    </tr>
                `).join('');
                tableHTML = `
                    <table class="nx-tour-table">
                        <thead><tr><th>Elemento</th><th>Descripción</th></tr></thead>
                        <tbody>${rows}</tbody>
                    </table>`;
            }

            this.stepEl.innerHTML = `
                <div class="nx-tour-step-header">
                    <span class="nx-tour-type">${step.type}</span>
                    <h3>${step.title}</h3>
                </div>
                <div class="nx-tour-content">
                    <p>${step.content}</p>
                    ${tableHTML}
                </div>
                <div class="nx-tour-footer">
                    <div class="nx-tour-pagination">
                        ${arrowLeft}
                        <div class="nx-tour-dots">${dots}</div>
                        ${arrowRight}
                    </div>
                    <div class="nx-tour-counter">${this.currentStep + 1} / ${this.steps.length}</div>
                </div>
            `;

            const stepWidth = 420;
            let stepTop = rect.bottom + 30;
            let stepLeft = rect.left + (rect.width / 2) - (stepWidth / 2);

            // Screen bounds protection
            if (stepLeft < 20) stepLeft = 20;
            if (stepLeft + stepWidth > window.innerWidth - 20) stepLeft = window.innerWidth - stepWidth - 20;
            
            // If at bottom of screen, show above target
            if (stepTop + 400 > window.innerHeight) {
                stepTop = Math.max(20, rect.top - 420);
            }

            this.stepEl.style.width = `${stepWidth}px`;
            this.stepEl.style.top = `${stepTop}px`;
            this.stepEl.style.left = `${stepLeft}px`;
            this.stepEl.classList.add('active');
            
            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            console.warn(`[PSX-TOUR] Target not found: ${step.target}. Moving to next step.`);
            this.next();
        }
    }
}

// === INSTANCE & FLOW TRIGGER ===
(function() {
    // Inline Icon Helpers
    const ico = (svg, color) => `<svg class="w-4 h-4 inline-block align-middle mr-1" style="color:${color}" fill="none" stroke="currentColor" viewBox="0 0 24 24">${svg}</svg>`;
    const dot = (color) => `<div style="width:10px;height:10px;border-radius:50%;background:${color};box-shadow:0 0 6px ${color}40;display:inline-block;vertical-align:middle;"></div>`;
    
    // SVGs for tables
    const svgPlus = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>';
    const svgTrash = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>';
    const svgIn = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"></path>';
    const svgInOut = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path>';
    const svgSpin = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>';
    const svgCheck = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path>';
    const svgWarn = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>';
    const svgClock = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>';

    window.psxTour = new PSXNexusTour([
        {
            type: 'Botón',
            target: '#refreshAudit',
            title: 'Tarea Nueva',
            content: 'Inicia el proceso de creación de tareas. Permite cargar registros masivos de forma <b>manual</b> o mediante archivos <b>CSV / TXT</b>.'
        },
        {
            type: 'Botón',
            target: '#scheduleTaskBtn',
            title: 'Programar Tarea',
            content: 'Difiere la ejecución de la tarea para una ventana de tiempo específica. Útil para optimización de recursos en el nodo.'
        },
        {
            type: 'Botón',
            target: '#modifyTaskBtn',
            title: 'Modificar Tarea',
            content: 'Edita el <b>Routing Label</b> o el temporizador mientras la tarea aún no ha iniciado su ejecución.'
        },
        {
            type: 'Columna',
            target: '#colTicketHeader',
            title: 'Master Ticket ID',
            content: 'Identificador único global del lote de datos. Se usa para auditorías y seguimiento transaccional.'
        },
        {
            type: 'Columna',
            target: '#colUserHeader',
            title: 'Propietario',
            content: 'Muestra el usuario que generó la tarea. (Personalizado según tu rol administrativo o de usuario).'
        },
        {
            type: 'Columna',
            target: '#colOrigenHeader',
            title: 'Origen / Segmento',
            content: 'Nombre del archivo fuente o indicador manual, acompañado del índice del fragmento procesado.'
        },
        {
            type: 'Columna',
            target: '#colLabelHeader',
            title: 'Routing Label',
            content: 'Etiqueta lógica de destino enviada al PSX. Define el canal de salida de los datos procesados.'
        },
        {
            type: 'Columna + Iconos',
            target: '#colGraphHeader',
            title: 'Métricas de Avance',
            content: 'Barra de progreso que muestra los resultados por bloque según la respuesta del nodo.<br><br><b style="color:#2563eb">Porcentaje</b> = % de registros procesados &nbsp;|&nbsp; <b>OK</b> / <b style="color:#f43f5e">FAIL</b> + <b style="color:#f59e0b">DUP</b> + <b style="color:#8b5cf6">FORCE-OK</b>',
            table: [
                { val: `${dot('#2563eb')} Azul`, desc: '<b>OK</b> — Procesamiento exitoso' },
                { val: `${dot('#f43f5e')} Rojo`, desc: '<b>FAIL</b> — Error reportado por el nodo' },
                { val: `${dot('#8b5cf6')} Púrpura`, desc: '<b>FORCE</b> — Validación forzada' },
                { val: `${dot('#f59e0b')} Ámbar`, desc: '<b>DUP</b> — Registro duplicado ignorado' }
            ]
        },
        {
            type: 'Columna + Iconos',
            target: '#colStatusHeader',
            title: 'Estatus Operativo',
            content: 'Tríada de indicadores que resume el ciclo de vida del proceso.',
            table: [
                { val: 'Operación', desc: `${ico(svgPlus, '#2563eb')} Alta / ${ico(svgTrash, '#f43f5e')} Baja` },
                { val: 'Modo', desc: `${ico(svgIn, '#0ea5e9')} Call In / ${ico(svgInOut, '#6366f1')} Call In/Out` },
                { val: 'Estado', desc: `${ico(svgSpin, '#2563eb')} Ejecutando / ${ico(svgCheck, '#10b981')} Éxito / ${ico(svgWarn, '#f43f5e')} Error / ${ico(svgClock, '#f59e0b')} Espera` }
            ]
        },
        {
            type: 'Columna + Botón',
            target: '#colSearchHeader',
            title: 'Auditoría Profunda',
            content: 'Abre el log detallado de la tarea. Permite auditar la respuesta <b>(Success / Reject)</b> individual de cada registro enviado al nodo.'
        }
    ]);

    // Attachment Logic
    const helpBtn = document.getElementById('helpTourBtn');
    if (helpBtn) {
        console.log('✅ PSX Help Button Found. Attaching Listener.');
        helpBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            window.psxTour.start();
        });
    } else {
        console.warn('❌ PSX Help Button (#helpTourBtn) not found in DOM.');
    }
})();
