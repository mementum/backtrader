$(function() {
    if (false) {
	var window_height = $(window).height(),
	    content_height = window_height - 150;
	$('#sidebar').height(content_height);
    }
});

$(window).resize(function() {
    if (false) {
	var window_height = $(window).height(),
	    content_height = window_height - 150;
	// $('.mygrid-wrapper-div').height(content_height);
	$('#sidebar').height(content_height);
    }
});
