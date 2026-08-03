// Micro-interactions for table rows
document.querySelectorAll('tr').forEach(row => {
    row.addEventListener('click', (e) => {
        if(e.target.tagName !== 'BUTTON') {
            // Logic for selecting a row or showing a quick preview
            console.log('Row clicked');
        }
    });
});

// Simple filter logic simulation
const selects = document.querySelectorAll('select');
selects.forEach(select => {
    select.addEventListener('change', () => {
        const toast = document.createElement('div');
        toast.className = 'fixed bottom-4 left-1/2 -translate-x-1/2 bg-on-surface text-surface px-6 py-3 rounded-full text-label-bold shadow-2xl z-[100] animate-bounce';
        toast.innerText = 'Updating product list based on filters...';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
    });
});