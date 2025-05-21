// assets/js/dashboard_viz.js

import { playSound } from './audio_manager.js'; // Pour les sons d'interaction

function initDashboardViz() {
    const neuronActivityGrid = document.getElementById('neuronActivityGrid');
    const neuronFluxStatus = document.getElementById('neuronFluxStatus');
    const memoryGraph = document.getElementById('memoryGraph');
    const memoryContextStatus = document.getElementById('memoryContextStatus');
    const logConsole = document.getElementById('logConsole');
    const systemStatus = document.getElementById('systemStatus');
    const lightOnline = document.getElementById('lightOnline');
    const lightProcessing = document.getElementById('lightProcessing');
    const lightSecure = document.getElementById('lightSecure');
    const startModuleButton = document.getElementById('startModuleButton');
    const versionStatus = document.getElementById('versionStatus');

    // --- 1. Panneau d'Activité Neuronale ---
    const numNeurons = 9;
    const neurons = [];
    for (let i = 0; i < numNeurons; i++) {
        const dot = document.createElement('div');
        dot.classList.add('neuron-dot');
        neuronActivityGrid.appendChild(dot);
        neurons.push(dot);
    }

    function animateNeurons() {
        neurons.forEach(dot => dot.classList.remove('active')); // Désactive tout
        const activeCount = Math.floor(Math.random() * (numNeurons / 2)) + 1; // 1 à 4 neurones actifs
        for (let i = 0; i < activeCount; i++) {
            const randomIndex = Math.floor(Math.random() * numNeurons);
            neurons[randomIndex].classList.add('active');
        }
        const flux = Math.random() < 0.3 ? 'Élevé' : (Math.random() < 0.6 ? 'Modéré' : 'Faible');
        neuronFluxStatus.textContent = flux;
    }
    setInterval(animateNeurons, 700); // Met à jour toutes les 0.7 secondes

    // --- 2. Panneau de Mémoire Vivante ---
    const numMemorySegments = 5;
    const segments = [];
    for (let i = 0; i < numMemorySegments; i++) {
        const segment = document.createElement('div');
        segment.classList.add('memory-segment', `s${i+1}`);
        memoryGraph.appendChild(segment);
        segments.push(segment);
    }

    function animateMemory() {
        segments.forEach(seg => seg.classList.remove('active'));
        const activeSegments = Math.floor(Math.random() * numMemorySegments) + 1; // 1 à 5 segments actifs
        for (let i = 0; i < activeSegments; i++) {
            segments[i].classList.add('active');
        }
        const context = Math.floor(Math.random() * (100 - 80) + 80); // Entre 80 et 99%
        memoryContextStatus.textContent = `${context}%`;
    }
    setInterval(animateMemory, 1200); // Met à jour toutes les 1.2 secondes

    // --- 3. Panneau des Logs Neuronaux ---
    const logMessages = [
        { msg: "[00:01:35] System heartbeat: Stable", type: "success" },
        { msg: "[00:01:37] Data stream: Incoming from external source...", type: "info" },
        { msg: "[00:01:40] Mem: Cache optimization initiated", type: "info" },
        { msg: "[00:01:42] Controller: Routing query to 'Science' galaxy", type: "info" },
        { msg: "[00:01:45] Neurax-memory: Context saved for conversation ID #12345", type: "success" },
        { msg: "[00:01:48] Viz module: Rendering 3D brain model", type: "info" },
        { msg: "[00:01:50] Replicating agent: PID_877 new instance detected", type: "warning" },
        { msg: "[00:01:53] Audit: Security protocol active - Layer 7", type: "success" },
        { msg: "[00:01:55] User input detected: Processing request...", type: "info" },
        { msg: "[00:01:58] System: Self-diagnosis complete. No anomalies found.", type: "success" },
        { msg: "[00:02:01] Response generated: Awaiting dispatch", type: "info" }
    ];
    let currentLogIndex = 0;

    function addLogLine() {
        const logData = logMessages[currentLogIndex % logMessages.length];
        const span = document.createElement('span');
        span.classList.add('log-line', logData.type);
        span.textContent = logData.msg;
        logConsole.appendChild(span);

        // Défilement automatique
        logConsole.scrollTop = logConsole.scrollHeight;

        currentLogIndex++;
        const statusTypes = ["Optimal", "En cours", "Surveillance"];
        systemStatus.textContent = statusTypes[Math.floor(Math.random() * statusTypes.length)];
    }
    setInterval(addLogLine, 1000); // Ajoute un log chaque seconde

    // --- 4. Panneau de Contrôle ---
    const lights = {
        online: { element: lightOnline, activeClass: 'online' },
        processing: { element: lightProcessing, activeClass: 'processing' },
        secure: { element: lightSecure, activeClass: 'secure' }
    };

    function animateLights() {
        // Simule l'activité des lumières
        gsap.to(lights.online.element, {
            opacity: Math.random() * 0.5 + 0.5,
            duration: 0.5,
            repeat: -1,
            yoyo: true
        });
        gsap.to(lights.processing.element, {
            opacity: Math.random() * 0.5 + 0.5,
            duration: 0.3,
            repeat: -1,
            yoyo: true
        });
        gsap.to(lights.secure.element, {
            opacity: Math.random() * 0.5 + 0.5,
            duration: 0.7,
            repeat: -1,
            yoyo: true
        });

        // Initialisation des lumières au démarrage
        lightOnline.classList.add('online');
        lightProcessing.classList.add('processing');
        lightSecure.classList.add('secure');
    }
    animateLights(); // Lance l'animation des lumières

    // Bouton Démarrer Module
    startModuleButton.addEventListener('click', () => {
        playSound('click'); // Utilise le son de clic global
        alert("Module de NeuraX-Ultime démarré ! (Simulation)");
        // Ici, vous pourriez déclencher une animation visuelle ou un log spécifique
        logConsole.appendChild(document.createElement('span')).outerHTML = '<span class="log-line success">[CMD] New module requested. Initializing...</span>';
        logConsole.scrollTop = logConsole.scrollHeight;
    });

    versionStatus.textContent = "Alpha 0.7"; // Initialisation du statut de version
}

export { initDashboardViz };
