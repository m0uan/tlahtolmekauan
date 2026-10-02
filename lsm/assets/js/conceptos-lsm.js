(() => {
  "use strict";

  const RUTA_CATALOGO = "/lsm/assets/data/conceptos-lsm.json";
  const RUTA_IMAGENES = "/lsm/assets/img/conceptos/";

  const formulario = document.querySelector("#formulario-conceptos");
  const campoConsulta = document.querySelector("#consulta-concepto");
  const mensaje = document.querySelector("#mensaje-concepto");
  const resultado = document.querySelector("#resultado-concepto");
  const galeria = document.querySelector("#galeria-concepto");
  const galeriaGeneral = document.querySelector("#galeria-general");
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

        if (!clave) {
          return;
        }

        if (!indice.has(clave)) {
          indice.set(clave, concepto);
        } else if (indice.get(clave).id !== concepto.id) {
          console.warn(
            `Término compartido: "${termino}"`,
            indice.get(clave).id,
            concepto.id
          );
        }
      });
    });

    return indice;
  }

  function buscarConcepto(consulta) {
    const clave = normalizarTexto(consulta);

    if (!clave) {
      return null;
    }

    return indiceBusqueda.get(clave) || null;
  }

  function obtenerImagenes(concepto) {
    if (
      Array.isArray(concepto.imagenes) &&
      concepto.imagenes.length > 0
    ) {
      return concepto.imagenes;
    }

    return [
      {
        tipo: "principal",
        archivo:
          concepto.imagen ||
          `${concepto.slug}.webp`,
        estado:
          concepto.estado_imagen ||
          "pendiente",
        alt:
          `Representación visual de ${concepto.etiqueta_principal}`
      }
    ];
  }

  function obtenerImagenPrincipal(concepto) {
    const imagenes = obtenerImagenes(concepto);

    return (
      imagenes.find(
        (datosImagen) =>
          datosImagen.tipo === "principal"
      ) ||
      imagenes[0]
    );
  }

  function obtenerRutaImagen(nombreArchivo) {
    return `${RUTA_IMAGENES}${nombreArchivo}`;
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
    const visible =
      Array.isArray(terminos) &&
      terminos.length > 0;

    grupo.hidden = !visible;
    llenarLista(lista, visible ? terminos : []);
  }

  function crearFichaGeneral(concepto) {
    const ficha = document.createElement("button");
    ficha.type = "button";
    ficha.className = "concept-overview-card";
    ficha.dataset.concepto = concepto.id;
    ficha.setAttribute(
      "aria-label",
      `Abrir concepto: ${concepto.etiqueta_principal}`
    );

    const marco = document.createElement("span");
    marco.className = "concept-overview-media";

    const datosImagen =
      obtenerImagenPrincipal(concepto);

    if (
      datosImagen &&
      datosImagen.estado !== "pendiente"
    ) {
      const imagen = document.createElement("img");

      imagen.src =
        obtenerRutaImagen(datosImagen.archivo);

      imagen.alt =
        datosImagen.alt ||
        `Representación visual de ${concepto.etiqueta_principal}`;

      imagen.loading = "lazy";
      imagen.decoding = "async";

      imagen.addEventListener("error", () => {
        marco.replaceChildren();

        const aviso = document.createElement("span");
        aviso.className = "image-pending";
        aviso.innerHTML =
          `<strong>Imagen no encontrada</strong>` +
          `<span>${datosImagen.archivo}</span>`;

        marco.appendChild(aviso);
      });

      marco.appendChild(imagen);
    } else {
      const aviso = document.createElement("span");
      aviso.className = "image-pending";
      aviso.innerHTML =
        `<strong>Imagen pendiente</strong>` +
        `<span>${datosImagen?.archivo || `${concepto.slug}.webp`}</span>`;

      marco.appendChild(aviso);
    }

    const cuerpo = document.createElement("span");
    cuerpo.className = "concept-overview-body";

    const nombre = document.createElement("strong");
    nombre.textContent = concepto.etiqueta_principal;

    const slug = document.createElement("small");
    slug.textContent = concepto.slug;

    cuerpo.append(nombre, slug);
    ficha.append(marco, cuerpo);

    ficha.addEventListener("click", () => {
      campoConsulta.value =
        concepto.etiqueta_principal;

      mostrarConcepto(
        concepto,
        concepto.etiqueta_principal
      );

      resultado.scrollIntoView({
        behavior: "smooth",
        block: "start"
      });
    });

    return ficha;
  }

  function renderizarGaleriaGeneral(datos) {
    galeriaGeneral.replaceChildren();

    const fragmento =
      document.createDocumentFragment();

    datos.forEach((concepto) => {
      fragmento.appendChild(
        crearFichaGeneral(concepto)
      );
    });

    galeriaGeneral.appendChild(fragmento);
  }

  function filtrarGaleriaGeneral(consulta) {
    const clave = normalizarTexto(consulta);

    if (!clave) {
      renderizarGaleriaGeneral(conceptos);
      mensaje.textContent =
        `${conceptos.length} conceptos disponibles.`;
      return;
    }

    const filtrados = conceptos.filter((concepto) => {
      return obtenerTerminos(concepto)
        .map(normalizarTexto)
        .some((termino) =>
          termino.includes(clave)
        );
    });

    renderizarGaleriaGeneral(filtrados);

    mensaje.textContent =
      `${filtrados.length} coincidencia` +
      `${filtrados.length === 1 ? "" : "s"} visible` +
      `${filtrados.length === 1 ? "" : "s"}.`;
  }

  function mostrarGaleria(concepto) {
    galeria.replaceChildren();

    obtenerImagenes(concepto).forEach(
      (datos, indice) => {
        const marco =
          document.createElement("figure");

        marco.className =
          "concept-image-frame";

        if (
          datos.tipo === "principal" ||
          indice === 0
        ) {
          marco.classList.add("is-primary");
        }

        if (datos.estado === "pendiente") {
          const pendiente =
            document.createElement("div");

          pendiente.className =
            "image-pending";

          pendiente.innerHTML =
            `<strong>Imagen pendiente</strong>` +
            `<span>${obtenerRutaImagen(datos.archivo)}</span>`;

          marco.appendChild(pendiente);
        } else {
          const img =
            document.createElement("img");

          img.src =
            obtenerRutaImagen(datos.archivo);

          img.alt =
            datos.alt ||
            `Representación visual de ${concepto.etiqueta_principal}`;

          img.loading =
            indice === 0 ? "eager" : "lazy";

          img.decoding = "async";

          img.addEventListener("error", () => {
            marco.innerHTML =
              `<div class="image-pending">` +
              `<strong>Imagen no encontrada</strong>` +
              `<span>${img.src}</span>` +
              `</div>`;
          });

          marco.appendChild(img);
        }

        const pie =
          document.createElement("figcaption");

        pie.textContent =
          datos.tipo === "auxiliar"
            ? "Vista auxiliar"
            : "Vista principal";

        marco.appendChild(pie);
        galeria.appendChild(marco);
      }
    );
  }

  function mostrarConcepto(concepto, consulta) {
    slugVisible.textContent =
      `slug: ${concepto.slug}`;

    titulo.textContent =
      concepto.etiqueta_principal;

    descripcion.textContent =
      concepto.descripcion || "";

    llenarLista(
      listas.equivalentes,
      concepto.terminos_equivalentes || []
    );

    actualizarGrupo(
      grupos.relacionados,
      listas.relacionados,
      concepto.terminos_relacionados
    );

    actualizarGrupo(
      grupos.especificos,
      listas.especificos,
      concepto.terminos_especificos
    );

    actualizarGrupo(
      grupos.colectivos,
      listas.colectivos,
      concepto.terminos_colectivos
    );

    mostrarGaleria(concepto);

    if (concepto.fuente) {
      referencia.hidden = false;
      referencia.textContent =
        `Fuente: ${concepto.fuente.id}` +
        `${concepto.fuente.pagina ? `, página ${concepto.fuente.pagina}` : ""}.`;
    } else {
      referencia.hidden = true;
      referencia.textContent = "";
    }

    if (concepto.nota_revision) {
      notaRevision.hidden = false;
      notaRevision.textContent =
        `Revisión pendiente: ${concepto.nota_revision}`;
    } else {
      notaRevision.hidden = true;
      notaRevision.textContent = "";
    }

    resultado.hidden = false;

    mensaje.textContent =
      `“${consulta}” se asocia con ` +
      `“${concepto.etiqueta_principal}”.`;
  }

  function ocultarResultado() {
    resultado.hidden = true;
    galeria.replaceChildren();
  }

  formulario.addEventListener(
    "submit",
    (evento) => {
      evento.preventDefault();

      const consulta =
        campoConsulta.value.trim();

      const concepto =
        buscarConcepto(consulta);

      filtrarGaleriaGeneral(consulta);

      if (concepto) {
        mostrarConcepto(concepto, consulta);
      } else {
        ocultarResultado();

        if (consulta) {
          mensaje.textContent +=
            " No existe una equivalencia exacta; se muestran coincidencias parciales.";
        }
      }
    }
  );

  campoConsulta.addEventListener("input", () => {
    filtrarGaleriaGeneral(
      campoConsulta.value
    );

    if (!campoConsulta.value.trim()) {
      ocultarResultado();
    }
  });

  async function cargarCatalogo() {
    try {
      const respuesta =
        await fetch(RUTA_CATALOGO);

      if (!respuesta.ok) {
        throw new Error(
          `HTTP ${respuesta.status}`
        );
      }

      const datos =
        await respuesta.json();

      if (!Array.isArray(datos)) {
        throw new TypeError(
          "El catálogo debe ser un arreglo JSON."
        );
      }

      conceptos = datos;
      indiceBusqueda =
        construirIndice(conceptos);

      renderizarGaleriaGeneral(conceptos);

      mensaje.textContent =
        `${conceptos.length} conceptos disponibles.`;

      const consultaURL =
        new URLSearchParams(
          location.search
        ).get("q");

      if (consultaURL) {
        campoConsulta.value = consultaURL;
        filtrarGaleriaGeneral(consultaURL);

        const concepto =
          buscarConcepto(consultaURL);

        if (concepto) {
          mostrarConcepto(
            concepto,
            consultaURL
          );
        }
      }
    } catch (error) {
      console.error(error);

      mensaje.textContent =
        "No se pudo cargar el catálogo de conceptos.";

      galeriaGeneral.innerHTML =
        `<p class="empty-state">` +
        `No se pudo cargar ` +
        `<code>${RUTA_CATALOGO}</code>.` +
        `</p>`;

      formulario
        .querySelector("button")
        .disabled = true;
    }
  }

  cargarCatalogo();
})();
