// Highlights a row when its checkbox is selected
document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
    checkbox.addEventListener('change', function() {
        const row = this.closest('tr');
        if (row && row.tagName === 'TR') {
            if (this.checked) {
                row.classList.add('bg-secondary-container/10');
            } else {
                row.classList.remove('bg-secondary-container/10');
            }
        }
    });
});