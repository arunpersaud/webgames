var pagetimer = $("#timer");
var age = $("#age");

async function update_page() {
    let response = await fetch(window.location.href+'/update');
    let data = await response.json();
    if (data > 0) {
	var current = Number(age.html());
	if (data > current)
	    location.reload();
    }

    var value = Number(pagetimer.html());
    pagetimer.html(value-1);
}

function start_game() {
    fetch(window.location.href+'/start');
}

var setTime = setInterval( update_page, 1000 );
