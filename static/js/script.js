let menu = document.querySelector('#menu-icon');
let navbar = document.querySelector('.navbar');

menu.onclick = () => {
	menu.classList.toggle('bx-x');
	navbar.classList.toggle('open');
};

window.onscroll = () => {
	menu.classList.remove('bx-x');
	navbar.classList.remove('open');
};

let darkmode = document.querySelector('#darkmode');

darkmode.onclick = () => {
	if(darkmode.classList.contains('bx-moon')){
		darkmode.classList.replace('bx-moon', 'bx-sun');
		document.body.classList.add('dark');
	}else{
		darkmode.classList.replace('bx-sun', 'bx-moon');
		document.body.classList.remove('dark')
	}
}

document.addEventListener('DOMContentLoaded', () => {
  const addToCartButtons = document.querySelectorAll('.add-to-cart');

  addToCartButtons.forEach((button) => {
    button.addEventListener('click', async () => {
      const itemId = button.getAttribute('data-item-id');
      await addToCart(itemId);
    });
  });
});

async function addToCart(itemId) {
	const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
	const response = await fetch('/add_to_cart', {
	  method: 'POST',
	  headers: {
		'Content-Type': 'application/json',
		'X-CSRFToken': csrfToken,
	  },
	  body: JSON.stringify({ item_id: itemId }),
	});
  
	if (response.ok) {
	  // Show a success message or update the cart count
	  alert('Item added to cart!');
	} else {
	  // Log the raw response text to the console
	  const rawText = await response.text();
	  console.log('Raw response text:', rawText);
  
	  // Show an error message
	  try {
		const error = JSON.parse(rawText); // Change this line
		console.error(error);
	  } catch (e) {
		console.error('Error parsing JSON:', e);
	  }
  
	  alert('Error adding item to cart.');
	}
  }
  