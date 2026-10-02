(() => {
	"use strict";

	async function loadLicenseComponent() {
		const root = document.getElementById("license-root");

		if (!root) {
			console.error("No se encontró #license-root.");
			return;
		}

		try {
			const response = await fetch("/components/licencias.html", {
				method: "GET",
				cache: "no-store"
			});

			if (!response.ok) {
				throw new Error(`No fue posible cargar licencias.html (${response.status}).`);
			}

			root.innerHTML = await response.text();
			initializeLicenses();
		} catch (error) {
			console.error(error);
			root.innerHTML = '<p class="license-load-error">No fue posible cargar el panel de licencias.</p>';
		}
	}

	function initializeLicenses() {
		(() => {
		        "use strict";

		        const modal = document.getElementById("licenseModal");
		        const openButton = document.getElementById("openLicenseModal");
		        const closeButton = document.getElementById("closeLicenseModal");
		        const backdrop = modal.querySelector("[data-close-license-modal]");

		        const statusElement = document.getElementById("licenseStatus");
		        const detailElement = document.getElementById("licenseDetail");
		        const messageElement = document.getElementById("licenseMessage");

		        const fileInput = document.getElementById("licenseFile");
		        const selectFileButton = document.getElementById("selectLicenseFile");

		        const showMachineIdButton =
		            document.getElementById("showMachineId");

		        const machineIdBox = document.getElementById("machineIdBox");
		        const machineIdValue = document.getElementById("machineIdValue");
		        const copyMachineIdButton =
		            document.getElementById("copyMachineId");

		        const ownerCodeInput = document.getElementById("ownerCode");
		        const activateOwnerButton = document.getElementById("activateOwner");
		        const ownerInbox = document.getElementById("ownerInbox");
		        const ownerInboxList = document.getElementById("ownerInboxList");
		        const ownerInboxStatus = document.getElementById("ownerInboxStatus");
		        const refreshOwnerInboxButton = document.getElementById("refreshOwnerInbox");
		        const ownerInboxBadge = document.getElementById("ownerInboxBadge");
		        const ownerInboxSearch = document.getElementById("ownerInboxSearch");
		        const ownerInboxCategory = document.getElementById("ownerInboxCategory");
		        const ownerInboxFilter = document.getElementById("ownerInboxFilter");
		        let ownerMessages = [];
		        let ownerInboxTimer = null;
		        let lastUnreadCount = 0;

		        function openModal() {
		            modal.classList.add("is-open");
		            modal.setAttribute("aria-hidden", "false");
		            document.body.classList.add("license-modal-open");
		            closeButton.focus();
		        }

		        function closeModal() {
		            modal.classList.remove("is-open");
		            modal.setAttribute("aria-hidden", "true");
		            document.body.classList.remove("license-modal-open");
		            openButton.focus();
		        }

		        function showMessage(text, type = "") {
		            messageElement.textContent = text;
		            messageElement.className = "license-message";

		            if (type) {
		                messageElement.classList.add(`is-${type}`);
		            }
		        }

		        async function readJsonResponse(response) {
		            const contentType =
		                response.headers.get("content-type") || "";

		            if (contentType.includes("application/json")) {
		                return response.json();
		            }

		            const text = await response.text();

		            // Si el servidor devolvió una página HTML (por ejemplo un 404),
		            // no mostrar todo el código HTML al usuario.
		            if (
		                text.trim().startsWith("<!DOCTYPE") ||
		                text.trim().startsWith("<html")
		            ) {
		                return {
		                    ok: response.ok,
		                    message:
		                        response.status === 404
		                            ? "La función todavía no está implementada en el servidor."
		                            : `Error del servidor (${response.status}).`
		                };
		            }

		            return {
		                ok: response.ok,
		                message: text
		            };
		        }


		        function escapeHtml(value) {
		            return String(value ?? "")
		                .replaceAll("&", "&amp;")
		                .replaceAll("<", "&lt;")
		                .replaceAll(">", "&gt;")
		                .replaceAll('"', "&quot;")
		                .replaceAll("'", "&#039;");
		        }

		        function formatOwnerMessageDate(value) {
		            if (!value) return "Fecha no indicada";
		            const date = new Date(value);
		            if (Number.isNaN(date.getTime())) return value;
		            return new Intl.DateTimeFormat("es-MX", {
		                dateStyle: "medium",
		                timeStyle: "short",
		            }).format(date);
		        }

		        async function manageOwnerMessage(messageId, action, value = true) {
		            const encodedId = encodeURIComponent(messageId);
		            const routes = {
		                read: `/api/propietario/mensajes/${encodedId}/leer`,
		                archive: `/api/propietario/mensajes/${encodedId}/archivar`,
		                favorite: `/api/propietario/mensajes/${encodedId}/favorito`,
		                delete: `/api/propietario/mensajes/${encodedId}`,
		            };

		            const response = await fetch(routes[action], {
		                method: action === "delete" ? "DELETE" : "POST",
		                headers: { "Content-Type": "application/json", "Accept": "application/json" },
		                credentials: "same-origin",
		                cache: "no-store",
		                body: action === "delete" ? undefined : JSON.stringify({
		                    [action === "read" ? "read" : action === "archive" ? "archived" : "favorite"]: value,
		                }),
		            });
		            const data = await readJsonResponse(response);
		            if (!response.ok || !data.ok) {
		                throw new Error(data.error || "No fue posible actualizar el mensaje.");
		            }
		            await loadOwnerInbox();
		        }

		        function renderOwnerInbox() {
		            const query = (ownerInboxSearch?.value || "").trim().toLowerCase();
		            const categoryFilter = ownerInboxCategory?.value || "all";
		            const stateFilter = ownerInboxFilter?.value || "active";
		            const filtered = ownerMessages.filter((item) => {
		                const haystack = [item.name, item.email, item.category, item.message].join(" ").toLowerCase();
		                if (query && !haystack.includes(query)) return false;
		                if (categoryFilter !== "all" && item.category !== categoryFilter) return false;
		                if (stateFilter === "active" && item.archived === true) return false;
		                if (stateFilter === "unread" && item.read === true) return false;
		                if (stateFilter === "favorite" && item.favorite !== true) return false;
		                if (stateFilter === "archived" && item.archived !== true) return false;
		                return true;
		            });
		            ownerInboxStatus.textContent = ownerMessages.length
		                ? `${filtered.length} mostrado(s) de ${ownerMessages.length}.`
		                : "Todavía no hay mensajes.";
		            ownerInboxList.innerHTML = filtered.map((item) => {
		                const sender = item.name || "Persona anónima";
		                const email = item.email || "Sin correo";
		                const category = item.category || "Mensaje";
		                const formattedDate = formatOwnerMessageDate(item.created_at);
		                const messageId = item.id || "";
		                const isRead = item.read === true;
		                const isArchived = item.archived === true;
		                const isFavorite = item.favorite === true;
		                const attachments = Array.isArray(item.attachments) ? item.attachments : [];
		                const attachmentHtml = attachments.length
		                    ? `<div class="owner-message__attachments">${attachments.map((file) => `<a href="${escapeHtml(file.url)}" target="_blank" rel="noopener">Ver imagen: ${escapeHtml(file.name || "adjunto")}</a>`).join("")}</div>`
		                    : "";
		                const replyBox = item.email ? `<details class="owner-message__reply"><summary>Responder desde la plataforma</summary><form data-reply-form><input name="subject" maxlength="160" value="Respuesta de tlahtolmekauan" required/><textarea name="body" rows="5" maxlength="4000" placeholder="Escribe tu respuesta" required></textarea><button class="owner-message__button" type="submit">Enviar respuesta</button><span data-reply-status></span></form></details>` : "";
		                return `<article class="owner-message${isRead ? " is-read" : " is-unread"}${isArchived ? " is-archived" : ""}" data-message-id="${escapeHtml(messageId)}">
		                    <header class="owner-message__header"><div><span class="owner-message__category">${escapeHtml(category)}</span><h4 class="owner-message__sender">${escapeHtml(sender)}</h4></div><div class="owner-message__status-group">${!isRead ? '<span class="owner-message__badge">Nuevo</span>' : ""}${isFavorite ? '<span class="owner-message__badge owner-message__badge--favorite">Importante</span>' : ""}${isArchived ? '<span class="owner-message__badge owner-message__badge--archived">Archivado</span>' : ""}<time class="owner-message__date">${escapeHtml(formattedDate)}</time></div></header>
		                    <dl class="owner-message__details"><div><dt>Correo</dt><dd>${escapeHtml(email)}</dd></div></dl>
		                    <div class="owner-message__content"><p>${escapeHtml(item.message)}</p></div>${attachmentHtml}
		                    <div class="owner-message__actions"><button class="owner-message__button owner-message__button--favorite" type="button" data-message-action="favorite" data-message-value="${isFavorite ? "false" : "true"}">${isFavorite ? "Quitar importante" : "Marcar importante"}</button><button class="owner-message__button owner-message__button--secondary" type="button" data-message-action="read" data-message-value="${isRead ? "false" : "true"}">${isRead ? "Marcar sin leer" : "Marcar leído"}</button><button class="owner-message__button owner-message__button--secondary" type="button" data-message-action="archive" data-message-value="${isArchived ? "false" : "true"}">${isArchived ? "Restaurar" : "Archivar"}</button><button class="owner-message__button owner-message__button--danger" type="button" data-message-action="delete">Eliminar</button></div>${replyBox}
		                </article>`;
		            }).join("");
		        }

		        async function loadOwnerInbox({ silent = false } = {}) {
		            if (!ownerInbox || ownerInbox.hidden) return;
		            if (!silent) ownerInboxStatus.textContent = "Cargando mensajes…";
		            try {
		                const response = await fetch("/api/propietario/mensajes?limit=200", { headers: { "Accept": "application/json" }, credentials: "same-origin", cache: "no-store" });
		                const data = await readJsonResponse(response);
		                if (!response.ok || !data.ok) throw new Error(data.error || "No fue posible abrir la bandeja.");
		                ownerMessages = Array.isArray(data.messages) ? data.messages : [];
		                const unreadCount = Number(data.unread_count || 0);
		                ownerInboxBadge.textContent = String(unreadCount);
		                ownerInboxBadge.hidden = unreadCount < 1;
		                if (silent && unreadCount > lastUnreadCount && "Notification" in window && Notification.permission === "granted") {
		                    new Notification("Nuevo mensaje en tlahtolmekauan", { body: `Tienes ${unreadCount} mensaje(s) sin leer.` });
		                }
		                lastUnreadCount = unreadCount;
		                const categories = [...new Set(ownerMessages.map((item) => item.category || "Mensaje"))].sort();
		                const selected = ownerInboxCategory.value;
		                ownerInboxCategory.innerHTML = '<option value="all">Todas las categorías</option>' + categories.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join("");
		                ownerInboxCategory.value = categories.includes(selected) ? selected : "all";
		                renderOwnerInbox();
		            } catch (error) {
		                ownerInboxStatus.textContent = error.message || "No fue posible abrir la bandeja.";
		                ownerInboxList.innerHTML = "";
		            }
		        }

		        async function sendOwnerReply(form, messageId) {
		            const status = form.querySelector("[data-reply-status]");
		            const payload = Object.fromEntries(new FormData(form).entries());
		            status.textContent = "Enviando…";
		            const response = await fetch(`/api/propietario/mensajes/${encodeURIComponent(messageId)}/responder`, { method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" }, credentials: "same-origin", body: JSON.stringify(payload) });
		            const data = await readJsonResponse(response);
		            if (!response.ok || !data.ok) throw new Error(data.error || "No fue posible enviar la respuesta.");
		            status.textContent = "Respuesta enviada.";
		            form.reset();
		            await loadOwnerInbox({ silent: true });
		        }


		        async function refreshLicenseStatus() {
		            try {
		                const response = await fetch("/api/estado", {
		                    method: "GET",
		                    headers: {
		                        "Accept": "application/json"
		                    },
		                    cache: "no-store"
		                });

		                const data = await readJsonResponse(response);

		                if (!response.ok) {
		                    throw new Error(
		                        data.message ||
		                        data.error ||
		                        "No fue posible consultar la licencia."
		                    );
		                }

		                /*
		                 * El código acepta distintas denominaciones posibles
		                 * provenientes del servidor.
		                 */
		                const kind =
		                    data.kind ||
		                    data.tipo ||
		                    data.license_kind ||
		                    "free";

		                const valid =
		                    data.valid !== false &&
		                    data.valida !== false;

		                const remaining =
		                    data.translations_remaining_today ??
		                    data.traducciones_restantes ??
		                    data.remaining ??
		                    null;

		                const expiresOn =
		                    data.expires_on ||
		                    data.fecha_vencimiento ||
		                    data.expires ||
		                    "";

		                if (!valid) {
		                    statusElement.textContent = "Licencia inválida";
		                    detailElement.textContent =
		                        data.message ||
		                        data.mensaje ||
		                        "La licencia instalada no es válida.";

		                    return;
		                }

		                if (kind === "owner" || kind === "propietario") {
		                    statusElement.textContent = "Licencia de Propietario";
		                    detailElement.textContent = "Acceso ilimitado";
		                    if (ownerInbox) ownerInbox.hidden = false;
		                    await loadOwnerInbox();
		                    if ("Notification" in window && Notification.permission === "default") Notification.requestPermission().catch(() => {});
		                    window.clearInterval(ownerInboxTimer);
		                    ownerInboxTimer = window.setInterval(() => loadOwnerInbox({ silent: true }), 60000);
		                    return;
		                }

		                if (kind === "permanent" || kind === "permanente") {
		                    statusElement.textContent = "Licencia permanente";
		                    detailElement.textContent = "Uso ilimitado";
		                    return;
		                }

		                if (
		                    kind === "temporary" ||
		                    kind === "temporal"
		                ) {
		                    statusElement.textContent = "Licencia temporal";
		                    detailElement.textContent = expiresOn
		                        ? `Vence: ${expiresOn}`
		                        : "Uso ilimitado durante el periodo contratado";

		                    return;
		                }

		                if (ownerInbox) ownerInbox.hidden = true;
		                statusElement.textContent = "Licencia gratuita";

		                detailElement.textContent =
		                    remaining !== null
		                        ? `Disponibles hoy: ${remaining} de 10`
		                        : "10 traducciones diarias";
		            } catch (error) {
		                console.error(error);

		                statusElement.textContent =
		                    "No fue posible comprobar la licencia";

		                detailElement.textContent =
		                    error.message || "Error de comunicación.";
		            }
		        }

		        async function activateOwnerAccess() {
		            const code = ownerCodeInput?.value.trim() || "";

		            if (!code) {
		                showMessage("Escribe el código de propietario.", "error");
		                ownerCodeInput?.focus();
		                return;
		            }

		            const originalButtonText =
		                activateOwnerButton.textContent.trim() || "Activar acceso ilimitado";

		            activateOwnerButton.disabled = true;
		            activateOwnerButton.textContent = "Activando…";
		            showMessage("Comprobando el código de propietario…");

		            const controller = new AbortController();
		            const timeoutId = window.setTimeout(() => controller.abort(), 15000);

		            try {
		                const response = await fetch("/api/propietario/activar", {
		                    method: "POST",
		                    headers: {
		                        "Content-Type": "application/json",
		                        "Accept": "application/json"
		                    },
		                    credentials: "same-origin",
		                    cache: "no-store",
		                    signal: controller.signal,
		                    body: JSON.stringify({ code })
		                });

		                const data = await readJsonResponse(response);

		                if (!response.ok || !data.ok) {
		                    throw new Error(
		                        data.error ||
		                        data.message ||
		                        "No fue posible activar el acceso."
		                    );
		                }

		                if (
		                    data.kind !== "owner" &&
		                    data.kind !== "propietario" &&
		                    data.unlimited !== true
		                ) {
		                    throw new Error(
		                        "El servidor aceptó la solicitud, pero no confirmó el acceso de propietario."
		                    );
		                }

		                ownerCodeInput.value = "";
		                await refreshLicenseStatus();

		                activateOwnerButton.textContent = "Acceso activado";

		                showMessage(
		                    "Acceso ilimitado del propietario activado.",
		                    "success"
		                );
		            } catch (error) {
		                console.error(error);

		                showMessage(
		                    error.name === "AbortError"
		                        ? "El servidor tardó demasiado en responder."
		                        : error.message || "No fue posible activar el acceso.",
		                    "error"
		                );
		            } finally {
		                window.clearTimeout(timeoutId);
		                activateOwnerButton.disabled = false;

		                if (activateOwnerButton.textContent.trim() === "Activando…") {
		                    activateOwnerButton.textContent = originalButtonText;
		                }
		            }
		        }

		        async function activateLicense(file) {
		            if (!file) {
		                return;
		            }

		            if (!file.name.toLowerCase().endsWith(".json")) {
		                showMessage(
		                    "Selecciona un archivo de licencia con extensión .json.",
		                    "error"
		                );
		                return;
		            }

		            const formData = new FormData();

		            /*
		             * El nombre "license" debe coincidir con el campo
		             * esperado por tu servidor.
		             */
		            formData.append("license", file);

		            showMessage("Comprobando la licencia…");

		            try {
		                const response = await fetch(
		                    "/api/activar-licencia",
		                    {
		                        method: "POST",
		                        body: formData
		                    }
		                );

		                const data = await readJsonResponse(response);

		                if (!response.ok) {
		                    throw new Error(
		                        data.message ||
		                        data.mensaje ||
		                        data.error ||
		                        "La licencia no pudo activarse."
		                    );
		                }

		                showMessage(
		                    data.message ||
		                    data.mensaje ||
		                    "Licencia activada correctamente.",
		                    "success"
		                );

		                await refreshLicenseStatus();
		            } catch (error) {
		                console.error(error);

		                showMessage(
		                    error.message ||
		                    "No fue posible activar la licencia.",
		                    "error"
		                );
		            } finally {
		                fileInput.value = "";
		            }
		        }

		        async function loadMachineId() {
		            showMessage("Consultando el identificador…");

		            try {
		                const response = await fetch(
		                    "/api/identificador-equipo",
		                    {
		                        method: "GET",
		                        headers: {
		                            "Accept": "application/json"
		                        },
		                        cache: "no-store"
		                    }
		                );

		                const data = await readJsonResponse(response);

		                if (!response.ok) {
		                    throw new Error(
		                        data.message ||
		                        data.mensaje ||
		                        data.error ||
		                        "No fue posible obtener el identificador."
		                    );
		                }

		                const machineId =
		                    data.machine_id ||
		                    data.identificador ||
		                    data.id;

		                if (!machineId) {
		                    throw new Error(
		                        "El servidor no devolvió el identificador."
		                    );
		                }

		                machineIdValue.textContent = machineId;
		                machineIdBox.hidden = false;
		                showMessage("");
		            } catch (error) {
		                console.error(error);

		                showMessage(
		                    error.message ||
		                    "No fue posible consultar el identificador.",
		                    "error"
		                );
		            }
		        }

		        async function copyMachineId() {
		            const machineId = machineIdValue.textContent.trim();

		            if (!machineId) {
		                return;
		            }

		            try {
		                await navigator.clipboard.writeText(machineId);
		                showMessage(
		                    "Identificador copiado al portapapeles.",
		                    "success"
		                );
		            } catch (error) {
		                console.error(error);

		                showMessage(
		                    "No fue posible copiar automáticamente el identificador.",
		                    "error"
		                );
		            }
		        }

		        async function requestLicense(plan, event) {
		            if (event) {
		                event.preventDefault();
		                event.stopPropagation();
		            }

		            const button = event?.currentTarget;
		            const originalText = button?.textContent || "Comprar";
		            const email = window.prompt(
		                "Escribe el correo electrónico con el que identificarás tu compra:"
		            );

		            if (email === null) {
		                return;
		            }

		            if (button) {
		                button.disabled = true;
		                button.textContent = "Abriendo Mercado Pago…";
		            }

		            try {
		                const response = await fetch(
		                    "/api/pagos/crear-preferencia",
		                    {
		                        method: "POST",
		                        headers: {
		                            "Content-Type": "application/json",
		                            "Accept": "application/json"
		                        },
		                        body: JSON.stringify({
		                            plan,
		                            email: email.trim()
		                        })
		                    }
		                );
		                const data = await readJsonResponse(response);

		                if (!response.ok || !data.ok || !data.checkout_url) {
		                    throw new Error(
		                        data.error || "No fue posible iniciar el cobro."
		                    );
		                }

		                window.location.assign(data.checkout_url);
		            } catch (error) {
		                console.error(error);
		                showMessage(
		                    error.message || "No fue posible abrir Mercado Pago.",
		                    "error"
		                );
		                if (button) {
		                    button.disabled = false;
		                    button.textContent = originalText;
		                }
		            }
		        }

		        async function showPaymentResult() {
		            const params = new URLSearchParams(window.location.search);
		            const orderId = params.get("orden");
		            const orderToken = params.get("token");
		            const result = params.get("resultado");

		            if (!orderId || !orderToken) {
		                return;
		            }

		            if (result === "fallido") {
		                showMessage("El pago no se completó. Puedes intentarlo nuevamente.", "error");
		                return;
		            }

		            if (result === "pendiente") {
		                showMessage("Mercado Pago dejó el pago pendiente. Te avisaremos cuando cambie.", "success");
		            }

		            try {
		                const response = await fetch(
		                    `/api/pagos/orden/${encodeURIComponent(orderId)}?token=${encodeURIComponent(orderToken)}`,
		                    { headers: { "Accept": "application/json" } }
		                );
		                const data = await readJsonResponse(response);
		                if (!response.ok || !data.ok) {
		                    throw new Error(data.error || "No fue posible consultar el pago.");
		                }

		                if (data.order?.status === "approved") {
		                    await refreshLicenseStatus();
		                    showMessage(
		                        "Pago aprobado. El acceso quedó activado automáticamente para este navegador y registrado con el correo " +
		                        data.order.email + ".",
		                        "success"
		                    );
		                } else if (result === "aprobado") {
		                    showMessage(
		                        "Mercado Pago recibió el pago. Estamos esperando la confirmación segura del servidor.",
		                        "success"
		                    );
		                }
		            } catch (error) {
		                console.error(error);
		            }
		        }

		        openButton.addEventListener("click", openModal);
		        closeButton.addEventListener("click", closeModal);
		        backdrop.addEventListener("click", closeModal);

		        /*
		         * Este botón es el único necesario:
		         * al seleccionar el JSON, la activación se realiza automáticamente.
		         */
		        selectFileButton.disabled = false;
		        selectFileButton.removeAttribute("disabled");

		        selectFileButton.addEventListener("click", () => {
		            fileInput.click();
		        });

		        fileInput.addEventListener("change", () => {
		            const [file] = fileInput.files;
		            activateLicense(file);
		        });

		        showMachineIdButton.addEventListener(
		            "click",
		            loadMachineId
		        );

		        copyMachineIdButton.addEventListener(
		            "click",
		            copyMachineId
		        );

		        if (activateOwnerButton && ownerCodeInput) {
		            activateOwnerButton.disabled = false;
		            activateOwnerButton.removeAttribute("disabled");
		            activateOwnerButton.textContent = "Activar acceso ilimitado";

		            ownerCodeInput.addEventListener("input", () => {
		                activateOwnerButton.disabled = false;
		                activateOwnerButton.removeAttribute("disabled");
		            });

		            ownerCodeInput.addEventListener("keydown", (event) => {
		                if (event.key === "Enter") {
		                    event.preventDefault();
		                    activateOwnerAccess();
		                }
		            });

		            activateOwnerButton.addEventListener(
		                "click",
		                activateOwnerAccess
		            );
		        }

		        refreshOwnerInboxButton?.addEventListener("click", () => loadOwnerInbox());
		        ownerInboxSearch?.addEventListener("input", renderOwnerInbox);
		        ownerInboxCategory?.addEventListener("change", renderOwnerInbox);
		        ownerInboxFilter?.addEventListener("change", renderOwnerInbox);

		        ownerInboxList?.addEventListener("submit", async (event) => {
		            const form = event.target.closest("[data-reply-form]");
		            if (!form) return;
		            event.preventDefault();
		            const messageId = form.closest("[data-message-id]")?.dataset.messageId;
		            if (!messageId) return;
		            try { await sendOwnerReply(form, messageId); }
		            catch (error) { form.querySelector("[data-reply-status]").textContent = error.message; }
		        });

		        ownerInboxList?.addEventListener("click", async (event) => {
		            const button = event.target.closest("[data-message-action]");
		            if (!button) return;

		            const article = button.closest("[data-message-id]");
		            const messageId = article?.dataset.messageId;
		            const action = button.dataset.messageAction;
		            const value = button.dataset.messageValue !== "false";
		            if (!messageId || !action) return;

		            if (action === "delete" && !window.confirm("¿Eliminar definitivamente este mensaje?")) {
		                return;
		            }

		            button.disabled = true;
		            try {
		                await manageOwnerMessage(messageId, action, value);
		            } catch (error) {
		                ownerInboxStatus.textContent = error.message || "No fue posible actualizar el mensaje.";
		            } finally {
		                button.disabled = false;
		            }
		        });

		        document.querySelectorAll("[data-license-plan]")
		          .forEach((button) => {
		              button.type = "button";

		              button.addEventListener("click", (event) => {
		                  requestLicense(
		                      button.dataset.licensePlan,
		                      event
		                  );
		              });
		          });

		        document.addEventListener("keydown", (event) => {
		            if (
		                event.key === "Escape" &&
		                modal.classList.contains("is-open")
		            ) {
		                closeModal();
		            }
		        });

		        refreshLicenseStatus();
		        showPaymentResult();

		        /*
		         * Puedes llamar esta función después de cada traducción
		         * para actualizar inmediatamente el contador gratuito:
		         *
		         * window.refreshLicenseStatus();
		         */
		        window.refreshLicenseStatus = refreshLicenseStatus;
		    })();
	}

	loadLicenseComponent();
})();
