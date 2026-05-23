document.addEventListener("DOMContentLoaded", function() {
    // On cherche tous les conteneurs de badges sur la page
    const containers = document.querySelectorAll(".avp-badges");

    containers.forEach(container => {
        const clotureStr = container.getAttribute("data-cloture");
        const pubStr = container.getAttribute("data-publication");
        
        const today = new Date();
        today.setHours(0, 0, 0, 0); // On se cale à minuit pour un calcul propre

        let htmlBadges = "";

        // 1. Gestion de la date de clôture (Urgent / Clos)
        if (clotureStr && clotureStr !== "N/A") {
            const clotureDate = new Date(clotureStr);
            clotureDate.setHours(0, 0, 0, 0);
            
            // Calcul de la différence en jours
            const diffTime = clotureDate - today;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            if (diffDays < 0) {
                htmlBadges += '<span class="md-tag md-tag--closed">OFFRE CLÔTURÉE</span> ';
            } else if (diffDays <= 7) {
                htmlBadges += `<span class="md-tag md-tag--urgent">URGENT (J-${diffDays})</span> `;
            }
        }

        // 2. Gestion de la nouveauté (Nouveau si < 3 jours)
        if (pubStr && pubStr !== "N/A") {
            const pubDate = new Date(pubStr);
            pubDate.setHours(0, 0, 0, 0);
            
            const diffTime = today - pubDate;
            const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

            if (diffDays <= 3 && diffDays >= 0) {
                htmlBadges += '<span class="md-tag md-tag--new">NOUVELLE OFFRE</span> ';
            }
        }

        // On injecte les badges générés en temps réel dans la page
        container.innerHTML = htmlBadges;
    });
});