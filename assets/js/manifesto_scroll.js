// assets/js/manifesto_scroll.js

function initSectionAnimations() {
    // Animer l'apparition de la section Manifeste
    gsap.fromTo(".manifeste-section",
        { opacity: 0, y: 50 },
        {
            opacity: 1,
            y: 0,
            duration: 1.5,
            ease: "power2.out",
            scrollTrigger: {
                trigger: ".manifeste-section",
                start: "top 80%",
                toggleActions: "play none none reverse",
                // markers: true // Décommenter pour visualiser les marqueurs de ScrollTrigger
            }
        }
    );

    // Animer l'apparition de la section Analyse Fonctionnelle
    gsap.fromTo(".analysis-section",
        { opacity: 0, y: 50 },
        {
            opacity: 1,
            y: 0,
            duration: 1.5,
            ease: "power2.out",
            scrollTrigger: {
                trigger: ".analysis-section",
                start: "top 80%",
                toggleActions: "play none none reverse",
                // markers: true
            }
        }
    );

    // Animer l'apparition de la section Tableau de Bord
    gsap.fromTo(".dashboard-section",
        { opacity: 0, y: 50 },
        {
            opacity: 1,
            y: 0,
            duration: 1.5,
            ease: "power2.out",
            scrollTrigger: {
                trigger: ".dashboard-section",
                start: "top 80%",
                toggleActions: "play none none reverse",
                // markers: true
            }
        }
    );

    // Animer l'apparition des éléments du manifeste
    const manifestoItems = document.querySelectorAll('.manifeste-section ul li, .manifeste-section p:not(.conclusion)');
    gsap.fromTo(manifestoItems,
        { opacity: 0, x: -30 },
        {
            opacity: 1,
            x: 0,
            duration: 0.8,
            stagger: 0.2,
            ease: "power2.out",
            scrollTrigger: {
                trigger: ".manifeste-section",
                start: "top 60%", // Commence l'animation des items quand la section est bien visible
                toggleActions: "play none none reverse",
                // markers: true
            }
        }
    );
}

export { initSectionAnimations };
