function resize( e ) {
	style = getComputedStyle(e)
	var border =
		- parseFloat(style.getPropertyValue("padding-top"))
		- parseFloat(style.getPropertyValue("padding-bottom"))

	e.style.height = (e.scrollHeight + border) + "px"
}

window.addEventListener('load', function () {
	var textareas = Array.prototype.slice.call(document.getElementsByTagName("textarea"))
	textareas.forEach( e => {
		resize(e)
		e.addEventListener('input', function() {
			resize(this)
		});
	})
})
