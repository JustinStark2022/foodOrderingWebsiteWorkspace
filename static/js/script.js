let menu = document.querySelector('#menu-icon');
let navbar = document.querySelector('.navbar');

if (menu) {
    menu.onclick = () => {
        menu.classList.toggle('bx-x');
        navbar.classList.toggle('open');
    };
}

window.onscroll = () => {
    menu.classList.remove('bx-x');
    navbar.classList.remove('open');
};

let darkmode = document.querySelector('#darkmode');

darkmode.onclick = () => {
    if (darkmode.classList.contains('bx-moon')) {
        darkmode.classList.replace('bx-moon', 'bx-sun');
        document.body.classList.add('dark');
    } else {
        darkmode.classList.replace('bx-sun', 'bx-moon');
        document.body.classList.remove('dark')
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const addToCartButtons = document.querySelectorAll('.add-to-cart');

    addToCartButtons.forEach((button) => {
        button.addEventListener('click', async () => {
            const itemId = button.getAttribute('data-item-id');
            const result = await addToCart(itemId);
            if (result) {
                updateCartItemCount();
            }
        });
    });
});

async function addToCart(itemId) {
    console.log("Item ID to add:", itemId);
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    try {
        const response = await fetch('/add_to_cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ item_id: itemId }),
        });

        if (!response.ok) {
            throw new Error('Error adding item to cart.');
        }

        const data = await response.json();
        if (data.success) {
            alert('Item added to cart!');
            return true;
        } else {
            console.error('Error adding item to cart:', data.message);
            return false;
        }
    } catch (error) {
        console.error('Error adding item to cart:', error);
        alert('Error adding item to cart.');
        return false;
    }
}

function updateCartItemCount() {
    const cartItemCount = document.querySelector('#cart-item-count');
    if (cartItemCount) {
        const currentCount = parseInt(cartItemCount.textContent, 10);
        cartItemCount.textContent = currentCount + 1;
    }
}

function incrementQuantity(itemId) {
    console.log('incrementQuantity called with itemId:', itemId);
    const currentQuantity = parseInt(document.querySelector(`input[name="item_id"][value="${itemId}"]`).closest('.content').querySelector(".unit span").textContent, 10);
    updateCart("increment", itemId, currentQuantity + 1);
}

function decrementQuantity(itemId) {
    console.log('decrementQuantity called with itemId:', itemId);
    const currentQuantity = parseInt(document.querySelector(`input[name="item_id"][value="${itemId}"]`).closest('.content').querySelector(".unit span").textContent, 10);
    if (currentQuantity > 1) {
        updateCart("decrement", itemId, currentQuantity - 1);
    } else {
        updateCart("delete", itemId, 0);
    }
}

function deleteItem(itemId) {
	updateCart('delete', itemId);
  }

async function updateCart(action, itemId, quantity) {
    console.log("Updating cart:", action, itemId, quantity);
    const csrfToken = document.getElementsByName("csrf-token")[0].getAttribute("content");

    const data = {
        "action": action,
        "item_id": itemId,
        "quantity": quantity
    };

    const response = await fetch("/update_cart", {
        method: "POST",
        body: JSON.stringify(data),
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        }
    });

    if (response.ok) {
        location.reload();
    } else {
        const error = await response.text();
        throw new Error("Error updating cart.");
    }
}
