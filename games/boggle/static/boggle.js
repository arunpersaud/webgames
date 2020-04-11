var pagetimer = $("#timer");
var age = $("#age");
var boggle = $("#boggle");

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

var step = 0 ;
function rotate(d) {
    step += d;
    boggle.css('transform', 'rotate('+ step*90 +'deg)');
}

function rotate_tiles() {
    $('#boggle td img').each(function() {
	var orientation = Math.floor(Math.random() * 4);
	$(this).css('transform', 'rotate('+ orientation*90 +'deg)');
    });
}
