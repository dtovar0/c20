// 1. Tailwind Configuration
if (window.tailwind) {
    window.tailwind.config = {
        darkMode: 'class',
        theme: {
            extend: {
                colors: {
                    primary: 'var(--color-primary)',
                    bg: 'var(--color-bg)',
                    text: 'var(--color-text)',
                    accent: 'var(--color-accent)',
                    secondary: 'var(--color-secondary)',
                },
                borderRadius: {
                    'base': 'var(--radius-base)',
                }
            }
        }
    }
}

// 2. DOM Interaction Logic
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.classList.add('dark');
    }

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            const isMobile = window.innerWidth < 1024;
            
            if (isMobile) {
                sidebar.classList.toggle('-translate-x-full');
            } else {
                // Toggle collapsed state
                sidebar.classList.toggle('w-64');
                sidebar.classList.toggle('w-20');
                sidebar.classList.toggle('is-collapsed'); // New helper class
                
                document.querySelectorAll('.sidebar-text').forEach(el => {
                    el.classList.toggle('hidden');
                });
                
                const brandText = document.querySelector('.brand-text');
                if (brandText) brandText.classList.toggle('hidden');
            }
        });
    }
});
