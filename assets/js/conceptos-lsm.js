(() => {
  "use strict";

  const RUTA_CATALOGO = "/lsm/assets/data/conceptos-lsm.json";
  const RUTA_IMAGENES = "/lsm/assets/img/conceptos/";

  const formulario = document.querySelector("#formulario-conceptos");
  const campoConsulta = document.querySelector("#consulta-concepto");
  const mensaje = document.querySelector("#mensaje-concepto");
  const resultado = document.querySelector("#resultado-concepto");
  const galeria = document.querySelector("#galeria-concepto");
  const slugVisible = document.querySelector("#slug-concepto");
  const titulo = document.querySelector("#titulo-concepto");
  const descripcion = document.querySelector("#descripcion-concepto");
  const referencia = document.querySelector("#referencia-concepto");
  const notaRevision = document.querySelector("#nota-revision");
  const listas = {
    equivalentes: document.querySelector("#terminos-equivalentes"),
    relacionados: document.querySelector("#terminos-relacionados"),
    especificos: document.querySelector("#terminos-especificos"),
    colectivos: document.querySelector("#terminos-colectivos")
  };
  const grupos = {
    relacionados: document.querySelector("#grupo-relacionados"),
    especificos: document.querySelector("#grupo-especificos"),
    colectivos: document.querySelector("#grupo-colectivos")
  };

  let conceptos = [];
  let indiceBusqueda = new Map();

  function normalizarTexto(texto) {
    return String(texto ?? "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[¿?¡!.,;:()[\]{}"'«»]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function obtenerTerminos(concepto) {
    return [
      concepto.etiqueta_principal,
      ...(concepto.terminos_equivalentes || []),
      ...(concepto.terminos_relacionados || []),
      ...(concepto.terminos_especificos || []),
      ...(concepto.terminos_colectivos || [])
    ].filter(Boolean);
  }

  function construirIndice(datos) {
    const indice = new Map();
    datos.forEach((concepto) => {
      obtenerTerminos(concepto).forEach((termino) => {
        const clave = normalizarTexto(termino);
        if (!clave) return;
        if (!indice.has(clave)) indice.set(clave, concepto);
        else if (indice.get(clave).id !== concepto.id) {
          console.warn(`Término compartido: "${termino}"`, indice.get(clave).id, concepto.id);
        }
      });
    });
    return indice;
  }

  function buscarConcepto(consulta) {
    return indiceBusqueda.get(normalizarTexto(consulta)) || null;
  }

  function obtenerImagenes(concepto) {
    if (Array.isArray(concepto.imagenes) && concepto.imagenes.length) {
      return concepto.imagenes;
    }
    return [{
      tipo: "principal",
      archivo: concepto.imagen || `${concepto.slug}.webp`,
      estado: concepto.estado_imagen || "pendiente",
      alt: `Representación visual de ${concepto.etiqueta_principal}`
    }];
  }

  function llenarLista(elemento, terminos) {
    elemento.replaceChildren();
    (terminos || []).forEach((termino) => {
      const item = document.createElement("li");
      item.textContent = termino;
      elemento.appendChild(item);
    });
  }

  function actualizarGrupo(grupo, lista, terminos) {
    const visible = Array.isArray(terminos) && terminos.length > 0;
    grupo.hidden = !visible;
    llenarLista(lista, visible ? terminos : []);
  }

  function mostrarGaleria(concepto) {
    galeria.replaceChildren();
    obtenerImagenes(concepto).forEach((datos, indice) => {
      const marco = document.createElement("figure");
      marco.className = "concept-image-frame";
      if (datos.tipo === "principal" || indice === 0) marco.classList.add("is-primary");

      if (datos.estado === "pendiente") {
        const pendiente = document.createElement("div");
        pendiente.className = "image-pending";
        pendiente.innerHTML = `<strong>Imagen pendiente</strong><span>${RUTA_IMAGENES}${datos.archivo}</span>`;
        marco.appendChild(pendiente);
      } else {
        const img = document.createElement("img");
        img.src = `${RUTA_IMAGENES}${datos.archivo}`;
        img.alt = datos.alt || `Representación visual de ${concepto.etiqueta_principal}`;
        img.loading = indice === 0 ? "eager" : "lazy";
        img.decoding = "async";
        img.addEventListener("error", () => {
          marco.innerHTML = `<div class="image-pending"><strong>Imagen no encontrada</strong><span>${img.src}</span></div>`;
        });
        marco.appendChild(img);
      }

      const pie = document.createElement("figcaption");
      pie.textContent = datos.tipo === "auxiliar" ? "Vista auxiliar" : "Vista principal";
      marco.appendChild(pie);
      galeria.appendChild(marco);
    });
  }

  function mostrarConcepto(concepto, consulta) {
    slugVisible.textContent = `slug: ${concepto.slug}`;
    titulo.textContent = concepto.etiqueta_principal;
    descripcion.textContent = concepto.descripcion || "";
    llenarLista(listas.equivalentes, concepto.terminos_equivalentes || []);
    actualizarGrupo(grupos.relacionados, listas.relacionados, concepto.terminos_relacionados);
    actualizarGrupo(grupos.especificos, listas.especificos, concepto.terminos_especificos);
    actualizarGrupo(grupos.colectivos, listas.colectivos, concepto.terminos_colectivos);
    mostrarGaleria(concepto);

    if (concepto.fuente) {
      referencia.hidden = false;
      referencia.textContent = `Fuente: ${concepto.fuente.id}${concepto.fuente.pagina ? `, página ${concepto.fuente.pagina}` : ""}.`;
    } else {
      referencia.hidden = true;
      referencia.textContent = "";
    }

    if (concepto.nota_revision) {
      notaRevision.hidden = false;
      notaRevision.textContent = `Revisión pendiente: ${concepto.nota_revision}`;
    } else {
      notaRevision.hidden = true;
      notaRevision.textContent = "";
    }

    resultado.hidden = false;
    mensaje.textContent = `“${consulta}” se asocia con “${concepto.etiqueta_principal}”.`;
  }

  function ocultarResultado() {
    resultado.hidden = true;
    galeria.replaceChildren();
  }

  formulario.addEventListener("submit", (evento) => {
    evento.preventDefault();
    const consulta = campoConsulta.value.trim();
    const concepto = buscarConcepto(consulta);
    if (concepto) mostrarConcepto(concepto, consulta);
    else {
      ocultarResultado();
      mensaje.textContent = "No se encontró un concepto asociado con esa búsqueda.";
    }
  });

  async function cargarCatalogo() {
    try {
      const respuesta = await fetch(RUTA_CATALOGO);
      if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`);
      const datos = await respuesta.json();
      if (!Array.isArray(datos)) throw new TypeError("El catálogo debe ser un arreglo JSON.");
      conceptos = datos;
      indiceBusqueda = construirIndice(conceptos);
      mensaje.textContent = `${conceptos.length} conceptos disponibles.`;
      const consultaURL = new URLSearchParams(location.search).get("q");
      if (consultaURL) {
        campoConsulta.value = consultaURL;
        const concepto = buscarConcepto(consultaURL);
        if (concepto) mostrarConcepto(concepto, consultaURL);
      }
    } catch (error) {
      console.error(error);
      mensaje.textContent = "No se pudo cargar el catálogo de conceptos.";
      formulario.querySelector("button").disabled = true;
    }
  }

  cargarCatalogo();
})();
