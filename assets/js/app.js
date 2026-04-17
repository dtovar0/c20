document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggle');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('sidebar--collapsed');
            
            // Optional: Save state to localStorage
            const isCollapsed = sidebar.classList.contains('sidebar--collapsed');
            localStorage.setItem('sidebarState', isCollapsed ? 'collapsed' : 'expanded');
        });

        // Restore state
        const savedState = localStorage.getItem('sidebarState');
        if (savedState === 'collapsed') {
            sidebar.classList.add('sidebar--collapsed');
        }
    }
});
