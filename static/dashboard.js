document.addEventListener('DOMContentLoaded', () => {
    // Hover effect for the low-stock table rows
    const rows = document.querySelectorAll('.zebra-row');
    rows.forEach(row => {
        row.addEventListener('mouseenter', () => {
            row.classList.add('bg-secondary-container/5');
        });
        row.addEventListener('mouseleave', () => {
            row.classList.remove('bg-secondary-container/5');
        });
    });

    // Simulated sync action for the header sync button
    const syncBtn = document.getElementById('sync-button');
    if (syncBtn) {
        syncBtn.addEventListener('click', () => {
            syncBtn.classList.add('animate-spin');
            setTimeout(() => {
                syncBtn.classList.remove('animate-spin');
                alert('Synchronizing with Central Depot... Success.');
            }, 1500);
        });
    }
});