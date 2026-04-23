# 🧠 MEMORY UI - NEXUS DESIGN SYSTEM

## 🧱 Design Tokens Base

- **Checkbox Oficial**: `.nexus-checkbox` (Usar siempre con contenedor `flex items-center justify-center`).
- **Botón Simétrico**: `w-[180px] h-12 rounded-xl text-[10px] uppercase font-black`.
- **Selección de Fila**: `.nexus-row-selected` (Fondo transparente, solo indicador en checkbox).

## 🧩 Componentes Reutilizables

### 1. Botón de Acción Gris
```html
<button class="w-[180px] h-12 bg-label/10 text-label/60 border border-panel-border ...">
    <!-- Icono + Texto -->
</button>
```

### 2. Tabla Administrativa (Layout)
- Header: `bg-slate-900/50 uppercase tracking-[0.2em]`.
- Fila: `border-spacing-y-1.5 transition-all duration-300`.
