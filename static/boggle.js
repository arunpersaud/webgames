var timer_span = $("#time");

function update_timer() {
    var value = Number(timer_span.text());
    timer_span.text(value-1);
    if (value <=0)
	location.reload();
}

var setTime = setInterval( update_timer, 1000 );
