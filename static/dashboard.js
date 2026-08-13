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
});