const Tlahtolmekauan = {
	CONFIG: {
		API_BASE: location.protocol === "file:"
			? "http://127.0.0.1:8875"
			: location.origin,
	},

	STATE: {
		direccion: "sp_ntl",
		traduciendo: false,
	},

	DOM: {},

	init() {
		this.cacheDOM();
		this.bindEvents();
		this.updateSuggestionCharCount();
		this.updateLabels();
		this.updateCharCount();
		this.verificarServidor();
	},

	cacheDOM() {
		this.DOM.entrada = document.getElementById("texto-entrada");
		this.DOM.resultado = document.getElementById("texto-resultado");
		this.DOM.boton = document.getElementById("traducir-boton");
		this.DOM.estado = document.getElementById("estado-traduccion");
		this.DOM.entradaLabel = document.getElementById("entrada-label");
		this.DOM.resultadoLabel = document.getElementById("resultado-label");
		this.DOM.ntlSpOutputNote = document.getElementById("ntl-sp-output-note");
		this.DOM.directions = [...document.querySelectorAll(".direction-button")];
		this.DOM.charCount = document.getElementById("char-count");
		this.DOM.indicator = document.getElementById("server-indicator");
		this.DOM.swapButton = document.getElementById("swap-button");
		this.DOM.clearButton = document.getElementById("clear-button");
		this.DOM.pasteButton = document.getElementById("paste-button");
		this.DOM.copyButton = document.getElementById("copy-button");
		this.DOM.toast = document.getElementById("toast");
		this.DOM.suggestionOpenButton = document.getElementById("suggestion-open-button");
		this.DOM.suggestionModal = document.getElementById("suggestion-modal");
		this.DOM.suggestionCloseButton = document.getElementById("suggestion-close-button");
		this.DOM.suggestionCancelButton = document.getElementById("suggestion-cancel-button");
		this.DOM.suggestionForm = document.getElementById("suggestion-form");
		this.DOM.suggestionMessage = document.getElementById("suggestion-message");
		this.DOM.suggestionStatus = document.getElementById("suggestion-status");
		this.DOM.suggestionSendButton = document.getElementById("suggestion-send-button");
		this.DOM.suggestionCharCount = document.getElementById("suggestion-char-count");
		this.DOM.suggestionPage = document.getElementById("suggestion-page");
		this.DOM.suggestionBackdrop = this.DOM.suggestionModal.querySelector("[data-suggestion-close]");
	},

	bindEvents() {
		this.DOM.directions.forEach((button) => {
			button.addEventListener("click", () => {
				this.setDirection(button.dataset.direction);
			});
		});

		this.DOM.boton.addEventListener("click", () => this.traducir());
		this.DOM.entrada.addEventListener("input", () => this.updateCharCount());
		this.DOM.entrada.addEventListener("keydown", (event) => this.handleInputKeydown(event));
		this.DOM.swapButton.addEventListener("click", () => this.swapDirection());
		this.DOM.clearButton.addEventListener("click", () => this.clearTranslation());
		this.DOM.pasteButton.addEventListener("click", () => this.pasteText());
		this.DOM.copyButton.addEventListener("click", () => this.copyResult());
		this.DOM.suggestionOpenButton.addEventListener("click", () => this.openSuggestionModal());
		this.DOM.suggestionCloseButton.addEventListener("click", () => this.closeSuggestionModal());
		this.DOM.suggestionCancelButton.addEventListener("click", () => this.closeSuggestionModal());
		this.DOM.suggestionBackdrop.addEventListener("click", () => this.closeSuggestionModal());
		this.DOM.suggestionMessage.addEventListener("input", () => this.updateSuggestionCharCount());
		this.DOM.suggestionForm.addEventListener("submit", (event) => this.sendSuggestion(event));
		document.addEventListener("keydown", (event) => this.handleDocumentKeydown(event));
	},

	showToast(message) {
		this.DOM.toast.textContent = message;
		this.DOM.toast.classList.add("show");
		clearTimeout(this.showToastTimer);

		this.showToastTimer = setTimeout(() => {
			this.DOM.toast.classList.remove("show");
		}, 1800);
	},

	updateLabels() {
		const spToNtl = this.STATE.direccion === "sp_ntl";

		this.DOM.entradaLabel.textContent = spToNtl ? "Español" : "Náhuatl";
		this.DOM.resultadoLabel.textContent = spToNtl ? "Náhuatl" : "Español";
		this.DOM.ntlSpOutputNote.hidden = spToNtl;

		this.DOM.entrada.placeholder = spToNtl
			? "Escribe una expresión...\nze ilyotl xitlakuilo..."
			: "ze ilyotl xitlakuilo...\nEscribe una expresión...";

		this.DOM.directions.forEach((item) => {
			item.classList.toggle(
				"active",
				item.dataset.direction === this.STATE.direccion
			);
		});
	},

	setDirection(nextDirection, moveText = false) {
		if (moveText && this.DOM.resultado.value.trim()) {
			this.DOM.entrada.value = this.DOM.resultado.value.trim();
			this.DOM.resultado.value = "";
			this.updateCharCount();
		}

		this.STATE.direccion = nextDirection;
		this.updateLabels();

		this.DOM.estado.textContent = "Engine prepared.";
		this.DOM.estado.className = "";

		this.DOM.entrada.focus();
	},

	swapDirection() {
		const nextDirection = this.STATE.direccion === "sp_ntl"
			? "ntl_sp"
			: "sp_ntl";

		this.setDirection(nextDirection, true);
	},

	updateCharCount() {
		const count = this.DOM.entrada.value.length;

		this.DOM.charCount.textContent =
			`${count} ${count === 1 ? "carácter" : "caracteres"}`;
	},

	handleInputKeydown(event) {
		if (
			!event.repeat &&
			(event.ctrlKey || event.metaKey) &&
			event.key === "Enter"
		) {
			event.preventDefault();
			this.traducir();
		}
	},

	handleDocumentKeydown(event) {
		if (
			event.key === "Escape" &&
			!this.DOM.suggestionModal.hidden
		) {
			this.closeSuggestionModal();
		}
	},

	async verificarServidor() {
		try {
			const response = await fetch(
				`${this.CONFIG.API_BASE}/api/estado`,
				{ cache: "no-store" }
			);

			const data = await response.json();

			if (!response.ok || !data.ok) {
				throw new Error(
					data.error || "Motor no disponible"
				);
			}

			this.DOM.indicator.className =
				"server-indicator online";

			this.DOM.indicator
				.querySelector("span")
				.textContent = "Motor en línea";

			return true;

		} catch (error) {
			this.DOM.indicator.className =
				"server-indicator error";

			this.DOM.indicator
				.querySelector("span")
				.textContent = "Motor desconectado";

			this.DOM.estado.textContent =
				location.protocol === "file:"
					? "Ejecuta INICIAR_EN_WINDOWS.bat y usa la pestaña que se abrirá."
					: `El servidor no está disponible: ${error.message}`;

			this.DOM.estado.className = "error";

			return false;
		}
	},

	async traducir() {
		if (this.STATE.traduciendo) {
			return;
		}

		const texto = this.DOM.entrada.value.trim();

		if (!texto) {
			this.DOM.estado.textContent =
				"Escribe un texto para traducir.";

			this.DOM.estado.className = "error";
			this.DOM.entrada.focus();

			return;
		}

		this.STATE.traduciendo = true;

		this.DOM.boton.disabled = true;
		this.DOM.resultado.value = "";

		this.DOM.estado.textContent = "Traduciendo...";
		this.DOM.estado.className = "";

		const requestId = (
			globalThis.crypto?.randomUUID?.() ||
			`${Date.now()}-${Math.random().toString(36).slice(2)}`
		);

		try {
			const response = await fetch(
				`${this.CONFIG.API_BASE}/api/traducir`,
				{
					method: "POST",

					headers: {
						"Content-Type": "application/json",
						"Idempotency-Key": requestId,
					},

					body: JSON.stringify({
						texto,
						direccion: this.STATE.direccion,
						request_id: requestId,
					}),
				}
			);

			const data =
				await response.json().catch(() => ({}));

			if (!response.ok || !data.ok) {
				throw new Error(
					data.error || "No se pudo traducir."
				);
			}

			this.DOM.resultado.value =
				data.resultado || "";

			this.DOM.estado.textContent =
				"Traducción terminada.";

			this.DOM.estado.className = "success";

			if (
				typeof window.refreshLicenseStatus ===
				"function"
			) {
				await window.refreshLicenseStatus();
			}

		} catch (error) {
			this.DOM.estado.textContent =
				location.protocol === "file:"
					? "Abre el sitio mediante INICIAR_EN_WINDOWS.bat."
					: `No se pudo conectar con el servidor: ${error.message}`;

			this.DOM.estado.className = "error";

		} finally {
			this.STATE.traduciendo = false;
			this.DOM.boton.disabled = false;
		}
	},

	clearTranslation() {
		this.DOM.entrada.value = "";
		this.DOM.resultado.value = "";

		this.updateCharCount();

		this.DOM.estado.textContent =
			"Motor preparado.";

		this.DOM.estado.className = "";

		this.DOM.entrada.focus();
	},

	async pasteText() {
		try {
			this.DOM.entrada.value =
				await navigator.clipboard.readText();

			this.updateCharCount();
			this.DOM.entrada.focus();

		} catch {
			this.showToast(
				"El navegador no permitió pegar automáticamente."
			);
		}
	},

	async copyResult() {
		if (!this.DOM.resultado.value.trim()) {
			this.showToast(
				"Todavía no hay resultado para copiar."
			);

			return;
		}

		try {
			await navigator.clipboard.writeText(
				this.DOM.resultado.value
			);

			this.showToast("Resultado copiado.");

		} catch {
			this.showToast(
				"No se pudo copiar automáticamente."
			);
		}
	},

	openSuggestionModal() {
		this.DOM.suggestionModal.hidden = false;

		document.body.classList.add(
			"suggestion-modal-open"
		);

		this.DOM.suggestionStatus.textContent = "";
		this.DOM.suggestionStatus.className =
			"suggestion-status";

		this.DOM.suggestionPage.value =
			window.location.href;

		window.setTimeout(() => {
			this.DOM.suggestionMessage.focus();
		}, 50);
	},

	closeSuggestionModal() {
		this.DOM.suggestionModal.hidden = true;

		document.body.classList.remove(
			"suggestion-modal-open"
		);

		this.DOM.suggestionOpenButton.focus();
	},

	updateSuggestionCharCount() {
		const count =
			this.DOM.suggestionMessage.value.length;

		this.DOM.suggestionCharCount.textContent =
			`${count} / 4000`;
	},

	async sendSuggestion(event) {
		event.preventDefault();

		const message =
			this.DOM.suggestionMessage.value.trim();

		if (!message) {
			this.DOM.suggestionStatus.textContent =
				"Escribe un mensaje antes de enviarlo.";

			this.DOM.suggestionStatus.className =
				"suggestion-status error";

			this.DOM.suggestionMessage.focus();

			return;
		}

		this.DOM.suggestionSendButton.disabled = true;

		this.DOM.suggestionSendButton.textContent =
			"Enviando...";

		this.DOM.suggestionStatus.textContent =
			"Enviando tu mensaje...";

		this.DOM.suggestionStatus.className =
			"suggestion-status";

		try {
			const formData =
				new FormData(this.DOM.suggestionForm);

			const payload =
				Object.fromEntries(formData.entries());

			const response = await fetch(
				`${this.CONFIG.API_BASE}/api/sugerencias`,
				{
					method: "POST",

					headers: {
						"Content-Type": "application/json",
						Accept: "application/json",
					},

					body: JSON.stringify(payload),
				}
			);

			const data =
				await response.json().catch(() => ({}));

			if (!response.ok || !data.ok) {
				throw new Error(
					data.error ||
					"No se pudo enviar el mensaje."
				);
			}

			this.DOM.suggestionStatus.textContent =
				data.message ||
				"Gracias. Tu mensaje fue recibido correctamente.";

			this.DOM.suggestionStatus.className =
				"suggestion-status success";

			this.DOM.suggestionForm.reset();

			this.DOM.suggestionPage.value =
				window.location.href;

			this.updateSuggestionCharCount();

			window.setTimeout(() => {
				this.closeSuggestionModal();
			}, 2200);

		} catch (error) {
			this.DOM.suggestionStatus.textContent =
				error.message ||
				"No se pudo enviar el mensaje.";

			this.DOM.suggestionStatus.className =
				"suggestion-status error";

		} finally {
			this.DOM.suggestionSendButton.disabled = false;

			this.DOM.suggestionSendButton.textContent =
				"Send message";
		}
	},
};


/* =========================================================
   IMÁGENES DE LOS 20 TONALTIN
   ========================================================= */

const TONAL_IMAGE_MAP = {
	zipaktli: "001_zipaktli_px.png",
	ehekatl: "002_ehekatl_px.png",
	kalli: "003_kalli_px.png",
	ketzpalli: "004_ketzpalli_px.png",
	koatl: "005_koatl_px.png",
	mikiztli: "006_mikiztli_px.png",
	mazatl: "007_mazatl_px.png",
	tochtli: "008_tochtli_px.png",
	atl: "009_atl_px.png",
	itzkuintli: "010_itzkuintli_px.png",
	ozomahtli: "011_ozomahtli_px.png",
	malinalli: "012_malinalli_px.png",
	akatl: "013_akatl_px.png",
	ozelotl: "014_ozelotl_px.png",
	kuauhtli: "015_kuauhtli_px.png",
	kozkakuauhtli: "016_kozkakuauhtli_px.png",
	olin: "017_naui_olin_px.png",
	tekpatl: "018_tekpatl_px.png",
	kiauitl: "019_kiauitl_px.png",
	xochitl: "020_xochitl_px.png",
};


/* =========================================================
   LOS CUATRO NOMBRES DE XIU
   ========================================================= */

const XIU_NAMES = [
	"tochtli",
	"akatl",
	"tekpatl",
	"kalli",
];


/* =========================================================
   IDENTIFICAR EL NOMBRE DEL TONAL O DEL XIU
   ========================================================= */

function getCalendarImageName(
	value,
	allowedNames = Object.keys(TONAL_IMAGE_MAP)
) {
	const normalized = String(value || "")
		.normalize("NFC")
		.toLowerCase()
		.trim();

	const namesByLength = [...allowedNames].sort(
		(a, b) => b.length - a.length
	);

	return (
		namesByLength.find(
			(name) => normalized.endsWith(name)
		) || null
	);
}


/* =========================================================
   MOSTRAR RESULTADO DE TONALLI UAN XIUITL
   ========================================================= */

function renderCalendarResult(
	container,
	tonal,
	xiu
) {
	container.replaceChildren();

	const tonalName =
		getCalendarImageName(tonal);

	const xiuName =
		getCalendarImageName(
			xiu,
			XIU_NAMES
		);

	const items = [
		{
			label: "tonalli",
			value: tonal,
			name: tonalName,
		},
		{
			label: "xiuitl",
			value: xiu,
			name: xiuName,
		},
	];

	const grid =
		document.createElement("div");

	grid.className =
		"calendar-result-grid";

	items.forEach((item) => {
		const card =
			document.createElement("div");

		card.className =
			"calendar-result-card";

		const text =
			document.createElement("div");

		text.className =
			"calendar-result-text";

		text.textContent =
			`${item.label}: ${item.value}`;

		card.appendChild(text);

		if (
			item.name &&
			TONAL_IMAGE_MAP[item.name]
		) {
			const img =
				document.createElement("img");

			img.className =
				"calendar-result-image";

			img.src =
				`/assets/img/tonaltin/${TONAL_IMAGE_MAP[item.name]}`;

			img.alt =
				item.name;

			img.loading =
				"lazy";

			img.style.display =
				"block";

			img.style.width =
				"90px";

			img.style.maxWidth =
				"100%";

			img.style.height =
				"auto";

			img.style.marginTop =
				"4px";

			card.appendChild(img);
		}

		grid.appendChild(card);
	});

	container.appendChild(grid);
}


/* =========================================================
   HERRAMIENTAS DEL PROYECTO
   TONALLI UAN XIUITL / POUALYOTL
   ========================================================= */

function initProjectTools() {
	const day =
		document.getElementById("tonal-day");

	const month =
		document.getElementById("tonal-month");

	const year =
		document.getElementById("tonal-year");

	const tonalButton =
		document.getElementById("tonal-calculate");

	const tonalResult =
		document.getElementById("tonal-result");


	const numberInput =
		document.getElementById("poualyotl-number");

	const poualyotlButton =
		document.getElementById("poualyotl-convert");

	const poualyotlResult =
		document.getElementById("poualyotl-result");


	/* Fecha actual por defecto */

	if (
		day &&
		month &&
		year
	) {
		const today =
			new Date();

		day.value =
			today.getDate();

		month.value =
			today.getMonth() + 1;

		year.value =
			today.getFullYear();
	}


	/* =====================================================
	   TONALLI UAN XIUITL
	   ===================================================== */

	tonalButton?.addEventListener(
		"click",
		async () => {
			tonalResult.className =
				"utility-result";

			tonalResult.textContent =
				"Calculando...";

			try {
				const response =
					await fetch(
						"/api/tonal-uan-xiu",
						{
							method: "POST",

							headers: {
								"Content-Type":
									"application/json",
							},

							body: JSON.stringify({
								day: day.value,
								month: month.value,
								year: year.value,
							}),
						}
					);

				const data =
					await response
						.json()
						.catch(() => ({}));

				if (
					!response.ok ||
					!data.ok
				) {
					throw new Error(
						data.error ||
						"No se pudo calcular."
					);
				}

				renderCalendarResult(
					tonalResult,
					data.tonal,
					data.xiu
				);

			} catch (error) {
				tonalResult.className =
					"utility-result error";

				tonalResult.textContent =
					error.message;
			}
		}
	);


	/* =====================================================
	   POUALYOTL
	   ===================================================== */

	poualyotlButton?.addEventListener(
		"click",
		async () => {
			poualyotlResult.className =
				"utility-result";

			poualyotlResult.textContent =
				"Convirtiendo...";

			try {
				const response =
					await fetch(
						"/api/poualyotl",
						{
							method: "POST",

							headers: {
								"Content-Type":
									"application/json",
							},

							body: JSON.stringify({
								numero:
									numberInput.value,
							}),
						}
					);

				const data =
					await response
						.json()
						.catch(() => ({}));

				if (
					!response.ok ||
					!data.ok
				) {
					throw new Error(
						data.error ||
						"No se pudo convertir."
					);
				}

				poualyotlResult.textContent =
					`${data.simbolo}\n${data.nombre}`;

			} catch (error) {
				poualyotlResult.className =
					"utility-result error";

				poualyotlResult.textContent =
					error.message;
			}
		}
	);
}


/* =========================================================
   INICIO
   ========================================================= */

document.addEventListener(
	"DOMContentLoaded",
	() => {
		Tlahtolmekauan.init();
		initProjectTools();
	}
);