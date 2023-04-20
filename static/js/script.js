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

async function fetchItems() {
	const response = await fetch('/items');
	const items = await response.json();
	// Render items in the frontend
  }
  
  async function addItem(name) {
	const response = await fetch('/items', {
	  method: 'POST',
	  headers: {
		'Content-Type': 'application/json',
	  },
	  body: JSON.stringify({name: name}),
	});
	const newItem = await response.json();
	// Update the frontend with the new item
  }