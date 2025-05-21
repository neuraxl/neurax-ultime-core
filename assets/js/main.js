// assets/js/main.js

import { initBrain3D } from './brain_3d.js';
import { initSectionAnimations } from './manifesto_scroll.js'; // Renommé
import { initAudioEvents } from './audio_manager.js';
import { initDashboardViz } from './dashboard_viz.js'; // NOUVEAU

document.addEventListener('DOMContentLoaded', () => {
    // Initialise l'animation 3D du cerveau
    initBrain3D();

    // Initialise les animations des sections (Manifeste, Analyse, Tableau de Bord)
    initSectionAnimations();

    // Initialise les événements audio
    initAudioEvents();

    // Initialise les visualisations du tableau de bord
    initDashboardViz();

    console.log("NeuraX-Ultime frontend initialized.");
});
