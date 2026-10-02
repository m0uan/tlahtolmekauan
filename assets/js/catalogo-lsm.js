
(() => {
  "use strict";

  const DATA_URL = "../assets/data/catalogo-lsm.json";
  const IMAGE_ROOT = "../assets/img/senas/";
  const PAGE_SIZE = 60;

  const state = {
    all: [],
    filtered: [],
    rendered: 0,
    query: "",
    configuration: "todas"
  };

  const grid = document.querySelector("#sign-grid");
  const status = document.querySelector("#catalog-status");
  const search = document.querySelector("#sign-search");
  const loadMore = document.querySelector("#load-more");
  const filters = [...document.querySelectorAll("[data-configuration]")];

  const normalize = value => String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();

  function imageName(entry) {
    return entry.archivo_imagen_sugerido || `${entry.identificador_web}.webp`;
  }

  function createCard(entry) {
    const article = document.createElement("article");
    article.className = "sign-card";

    const media = document.createElement("div");
    media.className = "sign-media";

    const img = document.createElement("img");
    img.alt = `Seña: ${entry.etiqueta_visible || entry.nombre_pdf}`;
    img.loading = "lazy";
    img.decoding = "async";
    img.src = IMAGE_ROOT + imageName(entry);

    const pending = document.createElement("div");
    pending.className = "image-pending";
    pending.innerHTML = "<strong>Imagen pendiente</strong><span>Espacio reservado</span>";

    img.addEventListener("load", () => pending.remove(), { once: true });
    img.addEventListener("error", () => img.remove(), { once: true });
    media.append(img, pending);

    const body = document.createElement("div");
    body.className = "sign-body";

    const code = document.createElement("div");
    code.className = "sign-code";
    code.textContent = entry.codigo_pdf;

    const title = document.createElement("h3");
    title.textContent = entry.etiqueta_visible || entry.nombre_pdf;

    const path = document.createElement("p");
    path.className = "sign-path";
    path.textContent = `assets/img/senas/${imageName(entry)}`;

    body.append(code, title, path);
    article.append(media, body);
    return article;
  }

  function updateStatus() {
    const total = state.filtered.length;
    const shown = Math.min(state.rendered, total);
    status.textContent = `${shown.toLocaleString("es-MX")} de ${total.toLocaleString("es-MX")} entradas`;
    loadMore.hidden = shown >= total;
  }

  function renderNext() {
    const fragment = document.createDocumentFragment();
    const next = state.filtered.slice(state.rendered, state.rendered + PAGE_SIZE);

    next.forEach(entry => fragment.appendChild(createCard(entry)));
    grid.appendChild(fragment);
    state.rendered += next.length;
    updateStatus();
  }

  function applyFilters() {
    const q = normalize(state.query);

    state.filtered = state.all.filter(entry => {
      const matchesConfiguration =
        state.configuration === "todas" ||
        entry.configuracion === state.configuration;

      const searchable = normalize([
        entry.codigo_pdf,
        entry.nombre_pdf,
        entry.etiqueta_visible,
        entry.configuracion
      ].join(" "));

      return matchesConfiguration && (!q || searchable.includes(q));
    });

    grid.replaceChildren();
    state.rendered = 0;

    if (!state.filtered.length) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "No se encontraron entradas con esos criterios.";
      grid.appendChild(empty);
      updateStatus();
      return;
    }

    renderNext();
  }

  search?.addEventListener("input", event => {
    state.query = event.target.value;
    applyFilters();
  });

  filters.forEach(button => {
    button.addEventListener("click", () => {
      filters.forEach(item => item.classList.remove("is-active"));
      button.classList.add("is-active");
      state.configuration = button.dataset.configuration;
      applyFilters();
    });
  });

  loadMore?.addEventListener("click", renderNext);

  fetch(DATA_URL)
    .then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(data => {
      state.all = Array.isArray(data) ? data : [];
      applyFilters();
    })
    .catch(error => {
      console.error(error);
      status.textContent = "No se pudo cargar el catálogo.";
      grid.innerHTML = `
        <p class="empty-state">
          Comprueba que el sitio se esté abriendo desde un servidor y que exista
          <code>assets/data/catalogo-lsm.json</code>.
        </p>`;
      loadMore.hidden = true;
    });
})();
