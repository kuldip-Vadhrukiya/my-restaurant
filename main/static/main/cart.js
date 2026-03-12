// OPEN DRAWER
function openCartDrawer() {
    document.getElementById("cartDrawer").style.height = "75vh";
    loadCart();
}

// CLOSE DRAWER
function closeCartDrawer() {
    document.getElementById("cartDrawer").style.height = "0";
}

// ADD ITEM WITH SPICE + INSTRUCTION
function addItem(id, spice, instruction) {
    fetch(`/cart/add/${id}/?spice=${spice}&instruction=${encodeURIComponent(instruction)}`)
        .then(() => {
            loadCart();          // Refresh cart UI
            updateCartBadge();   // Update badge count
            // No drawer opening
        });
}


// INC
function incItem(id) {
    fetch(`/cart/inc/${id}/`).then(() => loadCart());
}

// DEC
function decItem(id) {
    fetch(`/cart/dec/${id}/`).then(() => loadCart());
}

// UPDATE SPICE
function updateSpice(id, level) {
    fetch(`/cart/spice/${id}/${level}/`).then(() => loadCart());
}

// UPDATE INSTRUCTION
function updateInstruction(id, text) {
    fetch(`/cart/instruction/${id}/?text=${encodeURIComponent(text)}`);
}


// LOAD CART INTO UI
function loadCart() {
    fetch("/cart/data/")
        .then(res => res.json())
        .then(data => {

            let container = document.getElementById("cartItems");
            let emptyBox = document.getElementById("emptyCartBox");
            let totalBox = document.getElementById("cartTotal");
            let badge = document.getElementById("cartBadge");

            container.innerHTML = "";
            let total = 0;
            let count = 0;

            if (data.items.length === 0) {
                emptyBox.classList.remove("hidden");
                totalBox.innerText = "₹0";
                badge.innerText = 0;
                return;
            }

            emptyBox.classList.add("hidden");

            data.items.forEach(item => {
                total += item.total;
                count += item.qty;

                container.innerHTML += `
<div class="flex items-start justify-between bg-gray-50 p-3 rounded-xl shadow-sm">

    <div class="flex gap-3">

        <img src="${item.image}" class="w-14 h-14 rounded-lg shadow">

        <div>
            <p class="font-semibold text-gray-900 text-base">${item.name}</p>
            <p class="text-sm text-gray-600">₹${item.price}</p>

            <div class="mt-2">
                <label class="text-xs font-medium text-gray-500">Spice:</label>
                <div class="flex gap-1 mt-1">

                    <button onclick="updateSpice(${item.id}, 'Regular')"
                    class="px-2 py-1 rounded-full text-xs font-semibold 
                    ${item.spice === 'Regular' ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-700'}">
                        Regular
                    </button>

                    <button onclick="updateSpice(${item.id}, 'Medium')"
                    class="px-2 py-1 rounded-full text-xs font-semibold 
                    ${item.spice === 'Medium' ? 'bg-orange-500 text-white' : 'bg-gray-200 text-gray-700'}">
                        Medium
                    </button>

                    <button onclick="updateSpice(${item.id}, 'Spicy')"
                    class="px-2 py-1 rounded-full text-xs font-semibold 
                    ${item.spice === 'Spicy' ? 'bg-red-500 text-white' : 'bg-gray-200 text-gray-700'}">
                        Spicy
                    </button>

                </div>
            </div>

            <textarea
                placeholder="Add instructions..."
                onkeyup="updateInstruction(${item.id}, this.value)"
                class="w-full mt-2 text-xs bg-white border border-gray-300 rounded-lg p-2 resize-none">${item.instruction || ""}</textarea>

        </div>
    </div>

    <div class="flex flex-col items-center gap-2">
        <button onclick="incItem(${item.id})"
            class="w-7 h-7 bg-emerald-500 text-white rounded-full flex items-center justify-center font-bold">+</button>

        <span class="font-semibold text-gray-900">${item.qty}</span>

        <button onclick="decItem(${item.id})"
            class="w-7 h-7 bg-gray-300 text-gray-700 rounded-full flex items-center justify-center font-bold">-</button>
    </div>

</div>
`;
            });

            totalBox.innerText = "₹" + total;
            badge.innerText = count;
        });
}


