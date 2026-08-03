// Form logic — shows/hides fields based on selected product and movement type.
// This is the real business logic from your TRS: controlled substances require
// counterparty details + prescription number (Loi n°97/019); adjustments/losses
// require a reason.
const productSelector = document.getElementById('product-selector');
const movementType = document.getElementById('movement-type');
const counterpartySection = document.getElementById('counterparty-section');
const controlledAlert = document.getElementById('controlled-alert');
const refLabel = document.getElementById('ref-label');
const reasonContainer = document.getElementById('reason-container');

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
}

productSelector.addEventListener('change', updateFormUI);
movementType.addEventListener('change', updateFormUI);

// Run once on load so the form starts in the correct state
updateFormUI();

// Button press-down visual effect
document.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('mousedown', () => btn.classList.add('scale-95'));
    btn.addEventListener('mouseup', () => btn.classList.remove('scale-95'));
    btn.addEventListener('mouseleave', () => btn.classList.remove('scale-95'));
});