(() => {
  "use strict";

  /*
   * Fuente única de video: YouTube.
   *
   * Para habilitar una letra pendiente, agrega únicamente su youtubeId.
   * No existen rutas ni respaldos MP4 locales en este reproductor.
   */
  const VIDEOS_ALFABETO = [
    { letra: "A", youtubeId: "i6AsoR2iKTs" },
    { letra: "B", youtubeId: "XzfFDhy1DvI" },
    { letra: "C", youtubeId: "0M1gPUouMIk" },
    { letra: "D", youtubeId: "bLl1kM4VkBg" },
    { letra: "E", youtubeId: "SwSI5At1Bx0" },
    { letra: "F", youtubeId: "aXA67nglvp4" },
    { letra: "G", youtubeId: "r9pERow-Z7M" },
    { letra: "H", youtubeId: "Y2bACNgtSfE" },
    { letra: "I", youtubeId: "bbf_0TByk2Q" },
    { letra: "J", youtubeId: "YZyg3Z9YIXA" },
    { letra: "K", youtubeId: "qrKOcjdkg0s" },
    { letra: "L", youtubeId: "V0vhVCV8_6c" },
    { letra: "LL", youtubeId: "Pu0GodFgl9A" },
    { letra: "M", youtubeId: "aEUrGoxDjg0" },
    { letra: "N", youtubeId: "0AKfz8nvp14" },
    { letra: "Ñ", youtubeId: "Ixh6xGRRrV4" },
    { letra: "O", youtubeId: "hGCB_YImnnI" },
    { letra: "P", youtubeId: "dpHHCTj5iMY" },
    { letra: "Q", youtubeId: "PQi19fW48vc" },
    { letra: "R", youtubeId: "86MfF4A6oVA" },
    { letra: "RR", youtubeId: "ry-dz53Kg4w" },
    { letra: "S", youtubeId: "4z8OnAT6GXA" },
    { letra: "T", youtubeId: "o9_Xtyu_vE4" },
    { letra: "U", youtubeId: "Jy9ssAaz85g" },
    { letra: "V", youtubeId: "PTh7KL9G7fY" },
    { letra: "W", youtubeId: "5Wt30XIOT54" },
    { letra: "X", youtubeId: "s6de0jOS9Qw" },
    { letra: "Y", youtubeId: "KLIijkQf-5U" },
    { letra: "Z", youtubeId: "yNQSHWfr5RQ" }
  ];

  const youtube = document.querySelector("#youtube-alfabeto");
  const letraSeleccionada = document.querySelector("#letra-seleccionada");
  const cuadricula = document.querySelector("#cuadricula-alfabeto");
  const estado = document.querySelector("#estado-video");
  const errorVideo = document.querySelector("#error-video");
  const rutaFaltante = document.querySelector("#ruta-video-faltante");
  const repetir = document.querySelector("#repetir-video");

  let botonActivo = null;
  let entradaActiva = VIDEOS_ALFABETO[0];

  function obtenerRutaYouTube(youtubeId) {
    const parametros = new URLSearchParams({
      autoplay: "1",
      mute: "1",
      loop: "1",
      playlist: youtubeId,
      controls: "1",
      rel: "0"
    });

    return `https://www.youtube.com/embed/${encodeURIComponent(youtubeId)}?${parametros.toString()}`;
  }

  function marcarBotonActivo(boton) {
    if (botonActivo) {
      botonActivo.classList.remove("is-active");
      botonActivo.removeAttribute("aria-current");
    }

    botonActivo = boton;
    botonActivo.classList.add("is-active");
    botonActivo.setAttribute("aria-current", "true");
  }

  function ocultarYouTube() {
    youtube.hidden = true;
    youtube.src = "";
  }

  function mostrarPendiente(entrada) {
    ocultarYouTube();
    errorVideo.hidden = false;
    rutaFaltante.textContent = "Video pendiente de publicación en YouTube.";
    estado.textContent = `La letra ${entrada.letra} todavía no tiene video disponible en YouTube.`;
  }

  function cargarYouTube(entrada) {
    errorVideo.hidden = true;
    youtube.src = obtenerRutaYouTube(entrada.youtubeId);
    youtube.hidden = false;
    estado.textContent = `Reproduciendo la letra ${entrada.letra} desde YouTube.`;
  }

  function cargarLetra(entrada, boton) {
    entradaActiva = entrada;
    letraSeleccionada.textContent = entrada.letra;
    estado.textContent = `Cargando la letra ${entrada.letra}…`;
    errorVideo.hidden = true;

    if (entrada.youtubeId) {
      cargarYouTube(entrada);
    } else {
      mostrarPendiente(entrada);
    }

    if (boton) {
      marcarBotonActivo(boton);
    }

    const url = new URL(window.location.href);
    url.searchParams.set("letra", entrada.letra);
    window.history.replaceState({}, "", url);
  }

  function crearBoton(entrada) {
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "alphabet-letter";
    boton.textContent = entrada.letra;
    boton.dataset.letra = entrada.letra;
    boton.setAttribute("role", "listitem");
    boton.setAttribute("aria-label", `Mostrar la letra ${entrada.letra}`);

    if (!entrada.youtubeId) {
      boton.dataset.videoPendiente = "true";
      boton.setAttribute("title", "Video pendiente de publicación en YouTube");
    }

    boton.addEventListener("click", () => cargarLetra(entrada, boton));
    return boton;
  }

  function construirCuadricula() {
    const fragmento = document.createDocumentFragment();

    VIDEOS_ALFABETO.forEach((entrada, indice) => {
      const boton = crearBoton(entrada);
      if (indice === 0) marcarBotonActivo(boton);
      fragmento.appendChild(boton);
    });

    cuadricula.appendChild(fragmento);
  }

  repetir.addEventListener("click", () => {
    if (!entradaActiva.youtubeId) {
      mostrarPendiente(entradaActiva);
      return;
    }

    youtube.src = obtenerRutaYouTube(entradaActiva.youtubeId);
  });

  function cargarDesdeURL() {
    const parametro = new URLSearchParams(window.location.search).get("letra");
    if (!parametro) return false;

    const clave = parametro.toUpperCase();
    const entrada = VIDEOS_ALFABETO.find((item) => item.letra === clave);
    if (!entrada) return false;

    const boton = cuadricula.querySelector(`[data-letra="${CSS.escape(entrada.letra)}"]`);
    cargarLetra(entrada, boton);
    return true;
  }

  construirCuadricula();

  if (!cargarDesdeURL()) {
    const entradaInicial = VIDEOS_ALFABETO[0];
    const botonInicial = cuadricula.querySelector(
      `[data-letra="${CSS.escape(entradaInicial.letra)}"]`
    );
    cargarLetra(entradaInicial, botonInicial);
  }
})();
