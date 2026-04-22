# UI Guide - Nexus Premium Design System

## 🎨 Design Tokens (Single Source of Truth)

Basado en `static/css/tokens.css` y configurado en Tailwind.

### Colores de Marca
- `--color-primary`: Indigo (#6366f1) - Uso en acciones principales.
- `--color-secondary`: Slate (#64748b) - Texto secundario y adornos.
- `--color-accent`: Violet (#8b5cf6) - Destacados y animaciones.
- `--color-success`: Emerald (#10b981) - Estados positivos.

### Superficies y Paneles
- `--color-body-bg`: Fondo principal (Light: #f8fafc | Dark: #0f172a).
- `--color-panel-fill`: Fondo de tarjetas y modales.
- `--color-panel-border`: Bordes sutiles de separadores.

### Tipografía y Espaciado
- **Fuente**: 'Inter', sans-serif.
- **Sistema 8pt**:
  - `space-1`: 4px
  - `space-2`: 8px
  - `radius-base`: 12px (Bordes redondeados premium)

## 🧩 Componentes Reutilizables

### 1. Botones Premium
Usa clases de Tailwind combinadas con tokens:
```html
<button class="bg-primary text-white px-6 py-3 rounded-base transition-all hover:scale-105 active:scale-95">
  Acción Principal
</button>
```

### 2. Paneles "Glass"
```html
<div class="bg-panel-fill border border-panel-border rounded-[32px] p-8 shadow-xl">
  Contenido Protegido
</div>
```

### 3. Inputs de Sistema
```html
<input class="bg-input-bg border-2 border-panel-border rounded-2xl p-4 transition-all focus:border-primary outline-none">
```

### 4. Blueprint Cards (Notifications)
```html
<button class="w-full flex items-center gap-4 p-4 rounded-2xl bg-slate-900/40 border border-white/5 hover:border-primary/40 hover:bg-primary/5 transition-all group">
    <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
        <svg>...</svg>
    </div>
    <div class="text-left">
        <p class="text-[10px] font-black uppercase tracking-widest text-white/90">Título</p>
        <p class="text-[8px] font-bold uppercase tracking-tighter text-label/40">Subtítulo Técnico</p>
    </div>
</button>
```

## 🌙 Modo Oscuro
El soporte es automático mediante la clase `dark` en el elemento `html`. El sistema detecta la preferencia del usuario y la persiste en `localStorage`.

## 🚫 Reglas de Oro
1. **NO** usar estilos inline (`style="..."`).
2. **NO** usar etiquetas `<style>` en templates.
3. **NO** usar etiquetas `<script>` con lógica en templates.
4. **TODO** el diseño debe derivar de los Design Tokens.
