// A USB barcode scanner behaves like a keyboard: it types the barcode's
// characters into whatever field is focused, then sends an Enter keypress.
// So all this needs to do is listen for Enter on the scan field and react.

const scanField = document.getElementById('barcode-scan-field');
const statusText = document.getElementById('barcode-status');
const nameField = document.getElementById('name');

if (scanField) {
    scanField.addEventListener('keydown', async (e) => {
        if (e.key !== 'Enter') return;
        e.preventDefault();

        const barcode = scanField.value.trim();
        if (!barcode) return;

        statusText.textContent = 'Checking...';
        statusText.className = 'mt-2 text-body-sm text-on-surface-variant';

        try {
            const response = await fetch(`/api/barcode-lookup?barcode=${encodeURIComponent(barcode)}`);
            const data = await response.json();

            if (data.exists) {
                // Already registered — send the pharmacist straight to it
                // instead of letting them create a duplicate product.
                statusText.textContent = `Already registered as "${data.product.name}". Opening it...`;
                statusText.className = 'mt-2 text-body-sm text-error';
                setTimeout(() => {
                    window.location.href = `/products/${data.product.id}`;
                }, 1200);
            } else {
                statusText.textContent = 'New barcode — fill in the details below.';
                statusText.className = 'mt-2 text-body-sm text-on-tertiary-container';
                if (nameField) nameField.focus();
            }
        } catch (err) {
            statusText.textContent = 'Could not check barcode (offline?). You can still fill the form manually.';
            statusText.className = 'mt-2 text-body-sm text-on-surface-variant';
        }
    });
}