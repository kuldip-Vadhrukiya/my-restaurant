/**
 * RAJKOT RASOI - Sharp POS Logic
 * Handles AJAX Billing, Payment Selection, and Table Settlements
 */

document.addEventListener("DOMContentLoaded", function() {
    console.log("Sharp POS Logic Initialized...");
});

// 1. LOAD BILL DATA VIA AJAX
function loadBillData(tableId, tableName) {
    const billItemsArea = document.getElementById('bill-items-area');
    const sideTableName = document.getElementById('side-table-name');
    const subVal = document.getElementById('sub-val');
    const totalVal = document.getElementById('total-val');
    const settleForm = document.getElementById('settle-form');
    const hiddenOrderId = document.getElementById('hidden-order-id');

    // Loading State
    billItemsArea.innerHTML = `
        <div class="h-full flex flex-col items-center justify-center">
            <i class="fa-solid fa-sync fa-spin text-2xl text-emerald-500 mb-2"></i>
            <p class="text-[10px] font-black uppercase tracking-widest text-slate-400">Fetching Data...</p>
        </div>`;

    // Fetch from View: get_bill_details
    fetch(`/cashier/get-bill/${tableId}/`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update Header & Hidden Fields
            sideTableName.innerText = "TABLE " + tableName;
            hiddenOrderId.value = data.order_id;
            
            // Update Totals (Monospace Formatting)
            subVal.innerText = "₹" + data.total.toFixed(2);
            totalVal.innerText = "₹" + data.total.toFixed(2);
            
            // Show Settle Form
            settleForm.classList.remove('hidden');

            // Render Items Table (Sharp Skeleton Style)
            let itemsTable = `
                <table class="w-full text-left text-[11px] mono">
                    <thead>
                        <tr class="border-b-2 border-slate-900 text-slate-400 uppercase font-black text-[9px]">
                            <th class="pb-2">DESCRIPTION</th>
                            <th class="pb-2 text-center">QTY</th>
                            <th class="pb-2 text-right">TOTAL</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">`;

            data.items.forEach(item => {
                itemsTable += `
                    <tr>
                        <td class="py-3 font-bold text-slate-800 uppercase">${item.item_name}</td>
                        <td class="py-3 text-center text-slate-500">x${item.qty}</td>
                        <td class="py-3 text-right font-black text-slate-900">₹${(item.qty * item.price).toFixed(2)}</td>
                    </tr>`;
            });

            itemsTable += `</tbody></table>`;
            billItemsArea.innerHTML = itemsHtml; // Error fix: itemsTable
            billItemsArea.innerHTML = itemsTable;

        } else {
            // No Active Order Found
            billItemsArea.innerHTML = `
                <div class="h-full flex flex-col items-center justify-center opacity-40">
                    <i class="fa-solid fa-circle-info text-3xl mb-2"></i>
                    <p class="text-[10px] font-black uppercase tracking-widest text-red-500">${data.message}</p>
                </div>`;
            settleForm.classList.add('hidden');
            sideTableName.innerText = "TABLE --";
            subVal.innerText = "₹0.00";
            totalVal.innerText = "₹0.00";
        }
    })
    .catch(error => {
        console.error("Error fetching bill:", error);
        billItemsArea.innerHTML = `<p class="text-red-500 text-[10px] font-bold uppercase text-center mt-10 tracking-widest">Network Error</p>`;
    });
}

// 2. SET PAYMENT MODE (Button Toggle)
function setMode(mode, btn) {
    // Update Hidden Input
    document.getElementById('pay-mode').value = mode;

    // Reset All Buttons Style
    document.querySelectorAll('.mode-btn').forEach(b => {
        b.classList.remove('bg-slate-900', 'text-white', 'border-slate-900', 'ring-2', 'ring-slate-900/20');
        b.classList.add('bg-white', 'text-slate-500', 'border-slate-300');
    });

    // Active Button Style
    btn.classList.remove('bg-white', 'text-slate-500', 'border-slate-300');
    btn.classList.add('bg-slate-900', 'text-white', 'border-slate-900', 'ring-2', 'ring-slate-900/20');
    
    console.log("Payment Mode Selected: " + mode);
}

// 3. DUMMY BILL FOR OFFLINE TESTING
function loadDummyBill(name, id, total) {
    const billItemsArea = document.getElementById('bill-items-area');
    document.getElementById('side-table-name').innerText = "TABLE " + name;
    document.getElementById('hidden-order-id').value = id;
    document.getElementById('sub-val').innerText = "₹" + total.toFixed(2);
    document.getElementById('total-val').innerText = "₹" + total.toFixed(2);
    document.getElementById('settle-form').classList.remove('hidden');

    billItemsArea.innerHTML = `
        <table class="w-full text-left text-[11px] mono animate-in slide-in-from-right-2">
            <thead>
                <tr class="border-b-2 border-slate-900 text-slate-400 uppercase font-black text-[9px]">
                    <th class="pb-2">ITEM DESCRIPTION</th>
                    <th class="pb-2 text-center">QTY</th>
                    <th class="pb-2 text-right">TOTAL</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
                <tr><td class="py-3 font-bold text-slate-800 uppercase">PANEER TIKKA</td><td class="py-3 text-center text-slate-500">x2</td><td class="py-3 text-right font-black text-slate-900">₹700.00</td></tr>
                <tr><td class="py-3 font-bold text-slate-800 uppercase">BUTTER NAAN</td><td class="py-3 text-center text-slate-500">x10</td><td class="py-3 text-right font-black text-slate-900">₹450.00</td></tr>
                <tr class="bg-emerald-50/50"><td class="py-3 font-bold text-emerald-700 uppercase">MANCHURIAN</td><td class="py-3 text-center text-emerald-700">x1</td><td class="py-3 text-right font-black text-emerald-700">₹300.00</td></tr>
            </tbody>
        </table>`;
}