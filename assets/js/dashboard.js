/* DASHBOARD MODULE - ACTIVITY MONITORING */

/**
 * Handles pagination for the Activity Monitor feed.
 * @param {number} page - The page number to display.
 */
function changeActivityPage(page) {
    const p1 = document.getElementById('activityPage1');
    const p2 = document.getElementById('activityPage2');
    
    if (page === 1) {
        if(p1) p1.classList.remove('hidden');
        if(p2) p2.classList.add('hidden');
    } else {
        if(p1) p1.classList.add('hidden');
        if(p2) p2.classList.remove('hidden');
    }

    // Update button visual states
    const b1 = document.getElementById('btnPage1');
    const b2 = document.getElementById('btnPage2');
    
    const activeClass = 'w-7 h-7 flex items-center justify-center bg-primary text-white text-[11px] font-black rounded-lg shadow-lg shadow-primary/20 transition-all';
    const inactiveClass = 'w-7 h-7 flex items-center justify-center text-label/60 text-[11px] font-black hover:bg-surface-container rounded-lg cursor-pointer transition-all';

    if (page === 1) {
        if(b1) b1.className = activeClass;
        if(b2) b2.className = inactiveClass;
    } else {
        if(b1) b1.className = inactiveClass;
        if(b2) b2.className = activeClass;
    }
}
