document.addEventListener('DOMContentLoaded', () => {
    // Button press-down visual effect
    document.querySelectorAll('button').forEach(button => {
        button.addEventListener('mousedown', () => {
            button.classList.add('scale-95');
        });
        button.addEventListener('mouseup', () => {
            button.classList.remove('scale-95');
        });
        button.addEventListener('mouseleave', () => {
            button.classList.remove('scale-95');
        });
    });

    // Movement history filter pills (All / Sales / Receipts)
    // FIX: original selector referenced ".MovementHistorySection", a class
    // that didn't exist anywhere in the HTML, so this never ran. Now scoped
    // to the real ".movement-history-section" class added on the <section>.
    const movementPills = document.querySelectorAll('.movement-history-section span.cursor-pointer');
    movementPills.forEach(pill => {
        pill.addEventListener('click', () => {
            movementPills.forEach(p => p.classList.remove('bg-surface-container-highest'));
            movementPills.forEach(p => p.classList.add('bg-surface-variant/20'));
            pill.classList.remove('bg-surface-variant/20');
            pill.classList.add('bg-surface-container-highest');
        });
    });
});