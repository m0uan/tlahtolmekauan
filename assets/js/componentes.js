(() => {
	"use strict";

	const COMPONENTS = [
		{
			rootId: "sidebar-root",
			url: "/components/sidebar.html",
			name: "barra lateral",
			stylesheet: "/assets/css/sidebar.css?v=20260812-3",
			onLoad: initializeSidebar,
		},
		{
			rootId: "footer-root",
			url: "/components/footer.html",
			name: "pie de página",
		},
	];

	function ensureStylesheet(url) {
		if (!url) return;

		const existing = Array.from(document.querySelectorAll('link[rel="stylesheet"]'))
			.some((link) => link.href.includes(url.split("?")[0]));

		if (existing) return;

		const link = document.createElement("link");
		link.rel = "stylesheet";
		link.href = url;
		document.head.appendChild(link);
	}

	function initializeSidebar(sidebar) {
		if (!sidebar) return;

		const mainGroup = sidebar.querySelector("[data-sidebar-accordion]");
		const subgroups = Array.from(
			sidebar.querySelectorAll("[data-sidebar-subgroup]")
		);

		/*
		 * Siempre inicia compacto. Esto evita que el navegador restaure
		 * un estado abierto anterior y vuelva a mostrar una lista enorme.
		 */
		mainGroup?.removeAttribute("open");
		subgroups.forEach((group) => group.removeAttribute("open"));

		subgroups.forEach((group) => {
			group.addEventListener("toggle", () => {
				if (!group.open) return;

				subgroups.forEach((other) => {
					if (other !== group) {
						other.removeAttribute("open");
					}
				});
			});
		});
	}

	async function loadComponent(component) {
		const root = document.getElementById(component.rootId);

		if (!root) return;

		ensureStylesheet(component.stylesheet);

		try {
			const response = await fetch(component.url, {
				method: "GET",
				cache: "no-store",
			});

			if (!response.ok) {
				throw new Error(
					`No fue posible cargar ${component.name} (${response.status}).`
				);
			}

			const html = await response.text();
			const template = document.createElement("template");
			template.innerHTML = html.trim();

			const node = template.content.firstElementChild;

			if (!node) {
				throw new Error(`El componente ${component.name} está vacío.`);
			}

			root.replaceWith(node);
			component.onLoad?.(node);
		} catch (error) {
			console.error(error);
			root.dataset.componentError = "true";
		}
	}

	COMPONENTS.forEach(loadComponent);
})();
