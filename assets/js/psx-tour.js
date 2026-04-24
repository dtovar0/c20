/**
 * NEXUS PREMIUM GUIDED TOUR - PSX5K TERMINAL (ICON-RICH V6)
 */
class NexusTour {
    constructor(steps) {
        this.steps = steps;
        this.currentStep = -1;
        this.overlay = null;
        this.stepEl = null;
        this.spotlight = null;
        
        this.init();
    }

    init() {
        const oldOverlay = document.querySelector('.nx-tour-overlay');
        if (oldOverlay) oldOverlay.remove();
        const oldStep = document.querySelector('.nx-tour-step');
        if (oldStep) oldStep.remove();
        const oldSpot = document.querySelector('.nx-tour-spotlight');
        if (oldSpot) oldSpot.remove();

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
        // Force enable modify button for tour visibility
        const modBtn = document.getElementById('modifyTaskBtn');
        if (modBtn) modBtn.classList.remove('opacity-30', 'pointer-events-none');

        this.currentStep = 0;
        this.overlay.classList.add('active');
        this.spotlight.classList.add('active');
        this.showStep();
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
        // Restore modify button state
        const modBtn = document.getElementById('modifyTaskBtn');
        if (modBtn) modBtn.classList.add('opacity-30', 'pointer-events-none');

        this.overlay.classList.remove('active');
        this.stepEl.classList.remove('active');
        this.spotlight.classList.remove('active');
        this.currentStep = -1;
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

            this.stepEl.innerHTML = `
                <div class="nx-tour-step-header">
                    <span class="text-[10px] font-black text-primary uppercase tracking-[0.3em] block mb-2">${step.type}</span>
                    <h3 class="text-xl font-black text-white italic leading-tight">${step.title}</h3>
                </div>
                <div class="py-4 nx-tour-content max-h-[400px] overflow-y-auto custom-scrollbar pr-2">
                    <p class="text-[13px] text-slate-400 font-bold leading-relaxed mb-4">${step.content}</p>
                    ${step.table ? `
                        <div class="mt-4 rounded-xl border border-white/5 overflow-hidden bg-black/20">
                            <table class="w-full text-[10px] text-left border-separate border-spacing-0">
                                <thead class="bg-white/5">
                                    <tr>
                                        <th class="p-3 font-black uppercase tracking-widest text-primary/80 border-b border-white/5">Elemento</th>
                                        <th class="p-3 font-black uppercase tracking-widest text-primary/80 border-b border-white/5">Descripción</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${step.table.map(row => `
                                        <tr class="border-b border-white/5 last:border-0 hover:bg-white/5">
                                            <td class="p-3 border-b border-white/5">${row.val}</td>
                                            <td class="p-3 border-b border-white/5 text-slate-300 font-bold">${row.desc}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    ` : ''}
                </div>
                <div class="flex justify-between items-center mt-6 border-t border-white/5 pt-5">
                    <div class="flex gap-1.5">
                        ${this.steps.map((_, i) => `<div class="w-2 h-2 rounded-full ${i === this.currentStep ? 'bg-primary shadow-[0_0_10px_rgba(37,99,235,1)] scale-125' : 'bg-white/10'} transition-all duration-300"></div>`).join('')}
                    </div>
                    <div class="flex gap-3">
                        <button class="px-4 py-2 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-white transition-colors" onclick="window.nexusTour.prev()" ${this.currentStep === 0 ? 'style="display:none"' : ''}>Atrás</button>
                        <button id="nx-tour-next-btn" class="px-7 py-3 bg-primary text-white text-[11px] font-black uppercase tracking-widest rounded-xl shadow-xl shadow-primary/20 hover:scale-105 active:scale-95 transition-all">
                            ${this.currentStep === this.steps.length - 1 ? 'Finalizar' : 'Siguiente'}
                        </button>
                    </div>
                </div>
            `;

            this.stepEl.querySelector('#nx-tour-next-btn').onclick = () => this.next();

            const stepWidth = 460; 
            let stepTop = rect.bottom + 40;
            let stepLeft = rect.left + (rect.width/2) - (stepWidth/2);

            if (stepLeft < 20) stepLeft = 20;
            if (stepLeft + stepWidth > window.innerWidth - 20) stepLeft = window.innerWidth - stepWidth - 20;
            
            if (stepTop + 500 > window.innerHeight) {
                stepTop = Math.max(20, rect.top - 520);
            }

            this.stepEl.style.width = `${stepWidth}px`;
            this.stepEl.style.top = `${stepTop}px`;
            this.stepEl.style.left = `${stepLeft}px`;
            this.stepEl.classList.add('active');
            
            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            this.next();
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Icons for tables
    const iconPlus = `<svg class="w-4 h-4 text-primary inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg>`;
    const iconTrash = `<svg class="w-4 h-4 text-rose-500 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>`;
    const iconIn = `<svg class="w-4 h-4 text-sky-500 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"></path></svg>`;
    const iconInOut = `<svg class="w-4 h-4 text-indigo-500 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path></svg>`;
    const iconSpinner = `<svg class="w-4 h-4 text-primary animate-spin inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>`;
    const iconCheck = `<svg class="w-4 h-4 text-emerald-500 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>`;
    const iconWarning = `<svg class="w-4 h-4 text-rose-500 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>`;
    const iconClock = `<svg class="w-4 h-4 text-amber-500 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`;

    window.nexusTour = new NexusTour([
        {
            type: 'BOTÓN',
            target: '#refreshAudit',
            title: 'Tarea Nueva',
            content: 'Inicia el proceso de creación de tareas. Permite cargar registros masivos de forma manual o mediante archivos CSV/TXT.'
        },
        {
            type: 'BOTÓN',
            target: '#scheduleTaskBtn',
            title: 'Programar Tarea',
            content: 'Difiere la ejecución de la tarea para una ventana de tiempo específica. Útil para optimización de recursos en el nodo.'
        },
        {
            type: 'BOTÓN',
            target: '#modifyTaskBtn',
            title: 'Modificar Tarea',
            content: 'Edita el <b>Routing Label</b> o el temporizador mientras la tarea aún no ha iniciado su ejecución.'
        },
        {
            type: 'COLUMNA',
            target: '#psxDataTable thead th:nth-child(2)',
            title: 'Master Ticket ID',
            content: 'Identificador único global para el seguimiento transaccional de un lote de datos procesados.'
        },
        {
            type: 'COLUMNA',
            target: '#psxDataTable thead th:nth-child(3)',
            title: 'Origen del Segmento',
            content: 'Nombre del archivo fuente o registro manual, acompañado del índice del fragmento procesado.'
        },
        {
            type: 'COLUMNA',
            target: '#psxDataTable thead th:nth-child(4)',
            title: 'Routing Label',
            content: 'Configuración lógica de destino enviada al PSX. Determina el canal de salida de los datos.'
        },
        {
            type: 'ICONO / COLUMNA',
            target: '#psxDataTable thead th:nth-child(5)',
            title: 'Métricas de Avance',
            content: 'Visualización cromática de los estados finales por bloque según la respuesta del Nodo.',
            table: [
                { val: '<div class="w-3 h-3 rounded-full bg-primary shadow-[0_0_5px_rgba(37,99,235,0.5)]"></div>', desc: '<b>OK</b>: Procesamiento exitoso.' },
                { val: '<div class="w-3 h-3 rounded-full bg-rose-500 shadow-[0_0_5px_rgba(244,63,94,0.5)]"></div>', desc: '<b>FAIL</b>: Error reportado por el nodo.' },
                { val: '<div class="w-3 h-3 rounded-full bg-violet-500 shadow-[0_0_5px_rgba(139,92,246,0.5)]"></div>', desc: '<b>FORCE</b>: Validación forzada por sistema.' },
                { val: '<div class="w-3 h-3 rounded-full bg-amber-500 shadow-[0_0_5px_rgba(245,158,11,0.5)]"></div>', desc: '<b>DUP</b>: Registro duplicado ignorado.' }
            ]
        },
        {
            type: 'ICONO / COLUMNA',
            target: '#psxDataTable thead th:nth-child(6)',
            title: 'Estatus Operativo',
            content: 'Control de ciclo de vida del proceso desglosado en tres indicadores visuales.',
            table: [
                { val: 'Operación', desc: `${iconPlus} Alta / ${iconTrash} Baja` },
                { val: 'Modo', desc: `${iconIn} Call In / ${iconInOut} Call In/Out` },
                { val: 'Estado', desc: `${iconSpinner} Ejecutando / ${iconCheck} Éxito / ${iconWarning} Error / ${iconClock} En Espera` }
            ]
        },
        {
            type: 'ICONO / BOTÓN',
            target: '#psxDataTable thead th:nth-child(7)',
            title: 'Auditoría Profunda',
            content: 'Abre el log detallado. Aquí puedes ver la respuesta <b>(Success/Reject)</b> individual de cada registro enviado.'
        }
    ]);

    const helpBtn = document.getElementById('helpTourBtn');
    if (helpBtn) {
        helpBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            window.nexusTour.start();
        });
    }
});
