(function () {
    "use strict";

    const data = window.PORTALES_DATA || { portales: [] };
    const grid = document.getElementById("portal-grid");
    const activeCount = document.getElementById("active-count");

    const isActive = (value) =>
        String(value || "").trim().toLocaleLowerCase("es") === "activo";

    const isYes = (value) =>
        ["si", "sí", "yes", "true", "1"].includes(
            String(value || "").trim().toLocaleLowerCase("es")
        );

    const portals = Array.isArray(data.portales)
        ? data.portales
            .filter((portal) => isActive(portal.Estado))
            .sort((a, b) => Number(a.Orden || 9999) - Number(b.Orden || 9999))
        : [];

    if (activeCount) {
        activeCount.textContent = String(portals.length);
    }

    if (!grid) {
        return;
    }

    if (portals.length === 0) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = "No hay portales activos disponibles en este momento.";
        grid.appendChild(empty);
        return;
    }

    portals.forEach((portal) => {
        const article = document.createElement("article");
        article.className = "portal-card";

        if (isYes(portal.Destacado)) {
            article.classList.add("is-featured");
        }

        const visual = document.createElement("div");
        visual.className = "card-visual";

        const image = document.createElement("img");
        image.src = `assets/icons/${portal.Icono}`;
        image.alt = "";
        image.loading = "lazy";
        image.decoding = "async";

        image.addEventListener(
            "error",
            () => {
                visual.innerHTML = "";
                visual.textContent = String(portal.Nombre || "Portal")
                    .slice(0, 1)
                    .toUpperCase();
                visual.style.fontSize = "5rem";
                visual.style.fontWeight = "900";
                visual.style.color = "#006b44";
            },
            { once: true }
        );

        visual.appendChild(image);

        const content = document.createElement("div");
        content.className = "card-content";

        const category = document.createElement("span");
        category.className = "card-category";
        category.textContent = portal.Categoria || "Investigación";

        const title = document.createElement("h3");
        title.className = "card-title";
        title.textContent = portal.Nombre || "Portal";

        const description = document.createElement("p");
        description.className = "card-description";
        description.textContent = portal.Descripcion || "";

        const link = document.createElement("a");
        link.className = "card-link";
        link.href = portal.URL || "#";
        link.setAttribute(
            "aria-label",
            `Acceder a ${portal.Nombre || "portal"}`
        );

        if (portal.URL) {
            link.target = "_blank";
            link.rel = "noopener noreferrer";
        }

        link.append(document.createTextNode("Acceder al portal "));

        const arrow = document.createElement("span");
        arrow.setAttribute("aria-hidden", "true");
        arrow.textContent = "→";
        link.appendChild(arrow);

        content.append(category, title, description, link);
        article.append(visual, content);
        grid.appendChild(article);
    });
})();