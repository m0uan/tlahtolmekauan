(() => {
  "use strict";

  const contenedores =
    document.querySelectorAll(".youtube-video");

  contenedores.forEach((contenedor) => {
    const youtubeId =
      contenedor.dataset.youtubeId?.trim();

    const titulo =
      contenedor.dataset.titulo?.trim() ||
      "Video de Lengua de Señas Mexicana";

    if (!youtubeId) {
      contenedor.textContent =
        "No se ha especificado el video.";

      contenedor.classList.add(
        "youtube-video--error"
      );

      return;
    }

    const marco =
      document.createElement("div");

    marco.className =
      "youtube-video__marco";

    const iframe =
      document.createElement("iframe");

    iframe.src =
      "https://www.youtube.com/embed/" +
      encodeURIComponent(youtubeId);

    iframe.title = titulo;
    iframe.loading = "lazy";
    iframe.allowFullscreen = true;

    iframe.setAttribute(
      "allow",
      [
        "accelerometer",
        "autoplay",
        "clipboard-write",
        "encrypted-media",
        "gyroscope",
        "picture-in-picture",
        "web-share"
      ].join("; ")
    );

    iframe.setAttribute(
      "referrerpolicy",
      "strict-origin-when-cross-origin"
    );

    marco.appendChild(iframe);
    contenedor.appendChild(marco);
  });
})();
