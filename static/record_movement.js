const productSelector = document.getElementById('product-selector');
const batchSelector = document.getElementById('batch-selector');
const movementType = document.getElementById('movement-type');
const counterpartySection = document.getElementById('counterparty-section');
const controlledAlert = document.getElementById('controlled-alert');
const refLabel = document.getElementById('ref-label');
const referenceField = document.getElementById('reference-number-field');
const prescriptionField = document.getElementById('prescription-number-field');
const reasonContainer = document.getElementById('reason-container');
const adjustmentDirectionContainer = document.getElementById('adjustment-direction-container');

// When a product is picked, fetch its real batches from the server and
// populate the batch dropdown - batches aren't known until a product is chosen.
productSelector.addEventListener('change', async () => {
    const productId = productSelector.value;
    batchSelector.innerHTML = '<option value="">Loading batches...</option>';
    batchSelector.disabled = true;

    if (!productId) {
        batchSelector.innerHTML = '<option value="">Select a product first...</option>';
        updateFormUI();
        return;
    }

    try {
        const response = await fetch(`/api/products/${productId}/batches`);
        const batches = await response.json();

        if (batches.length === 0) {
            batchSelector.innerHTML = '<option value="">No batches for this product</option>';
        } else {
            batchSelector.innerHTML = '<option value="">Select active batch...</option>' +
                batches.map(b =>
                    `<option value="${b.id}">${b.batch_number} (Exp: ${b.expiry_date || 'N/A'} - Qty: ${b.quantity_remaining})</option>`
                ).join('');
            batchSelector.disabled = false;
        }
    } catch (err) {
        batchSelector.innerHTML = '<option value="">Could not load batches</option>';
    }

    updateFormUI();
});

function updateFormUI() {
    const selectedOption = productSelector.options[productSelector.selectedIndex];
    const isControlled = selectedOption?.dataset?.controlled === 'true';
    const mType = movementType.value;

    if (isControlled) {
        controlledAlert.classList.remove('hidden');
        counterpartySection.classList.remove('hidden');
        refLabel.textContent = "Prescription Number (Required)";
    } else {
        controlledAlert.classList.add('hidden');
        if (['transfer', 'return', 'destruction'].includes(mType)) {
            counterpartySection.classList.remove('hidden');
        } else {
            counterpartySection.classList.add('hidden');
        }
        refLabel.textContent = "Reference / Invoice #";
    }

    if (['adjustment', 'loss', 'destruction'].includes(mType)) {
        reasonContainer.classList.remove('hidden');
    } else {
        reasonContainer.classList.add('hidden');
    }

    adjustmentDirectionContainer.style.display = (mType === 'adjustment') ? 'block' : 'none';
}

// Keep the hidden prescription_number field in sync with the visible input
// when the product is controlled, so the right database column gets it.
document.getElementById('movement-form').addEventListener('submit', () => {
    const selectedOption = productSelector.options[productSelector.selectedIndex];
    const isControlled = selectedOption?.dataset?.controlled === 'true';
    prescriptionField.value = isControlled ? referenceField.value : '';
});

productSelector.addEventListener('change', updateFormUI);
movementType.addEventListener('change', updateFormUI);
updateFormUI();

document.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('mousedown', () => btn.classList.add('scale-95'));
    btn.addEventListener('mouseup', () => btn.classList.remove('scale-95'));
    btn.addEventListener('mouseleave', () => btn.classList.remove('scale-95'));
});