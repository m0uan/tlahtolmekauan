(() => {
	"use strict";

	const protectedSelector = ".guide-main, .guide-toc, .document-copy";

	function insideProtectedArea(target) {
		return target instanceof Element && Boolean(target.closest(protectedSelector));
	}

	document.addEventListener("copy", (event) => {
		if (insideProtectedArea(event.target)) {
			event.preventDefault();
		}
	});

	document.addEventListener("cut", (event) => {
		if (insideProtectedArea(event.target)) {
			event.preventDefault();
		}
	});

	document.addEventListener("contextmenu", (event) => {
		if (insideProtectedArea(event.target)) {
			event.preventDefault();
		}
	});

	document.addEventListener("dragstart", (event) => {
		if (insideProtectedArea(event.target)) {
			event.preventDefault();
		}
	});
})();
