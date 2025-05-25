// static/js/dashboard.js
document.addEventListener('DOMContentLoaded', function () {
    const mapContainer = document.getElementById('cerebral-map-container');
    if (!mapContainer) {
        console.error("Le conteneur pour la carte cérébrale n'a pas été trouvé.");
        return;
    }
    mapContainer.innerHTML = ''; // Vider le message de chargement

    const width = mapContainer.clientWidth;
    const height = mapContainer.clientHeight;

    const svg = d3.select("#cerebral-map-container").append("svg")
        .attr("width", width)
        .attr("height", height);

    // Données factices pour les neurones
    let neurons = [
        { id: "n1", x: width * 0.2, y: height * 0.5, active: true, type: "input" },
        { id: "n2", x: width * 0.4, y: height * 0.3, active: false, type: "processing" },
        { id: "n3", x: width * 0.4, y: height * 0.7, active: true, type: "processing" },
        { id: "n4", x: width * 0.6, y: height * 0.5, active: true, type: "output" },
        { id: "n5", x: width * 0.8, y: height * 0.5, active: false, type: "memory", repairing: true }
    ];

    // Liens factices entre neurones
    let links = [
        { source: neurons[0], target: neurons[1] },
        { source: neurons[0], target: neurons[2] },
        { source: neurons[1], target: neurons[3] },
        { source: neurons[2], target: neurons[3] },
        { source: neurons[3], target: neurons[4] }
    ];

    // Créer les liens (lignes)
    svg.selectAll(".link")
        .data(links)
        .enter().append("line")
        .attr("class", "link")
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y)
        .style("stroke", "#999")
        .style("stroke-opacity", 0.6)
        .style("stroke-width", 2);

    // Créer les neurones (cercles)
    const neuronNodes = svg.selectAll(".neuron")
        .data(neurons)
        .enter().append("circle")
        .attr("class", "neuron")
        .attr("cx", d => d.x)
        .attr("cy", d => d.y)
        .attr("r", 15)
        .style("fill", d => {
            if (d.repairing) return "orange";
            return d.active ? "lightgreen" : "grey";
        })
        .style("stroke", "#fff")
        .style("stroke-width", 1.5);

    // Animation simple pour les neurones actifs
    function pulse() {
        neuronNodes.filter(d => d.active && !d.repairing)
            .transition()
            .duration(700)
            .attr("r", 18)
            .transition()
            .duration(700)
            .attr("r", 15)
            .on("end", pulse); // Boucle d'animation
    }

    pulse(); // Démarrer l'animation

    // Ajouter des labels (optionnel)
    svg.selectAll(".neuron-label")
        .data(neurons)
        .enter().append("text")
        .attr("x", d => d.x)
        .attr("y", d => d.y - 20) // Au-dessus du neurone
        .attr("text-anchor", "middle")
        .style("fill", "white")
        .style("font-size", "10px")
        .text(d => d.id + (d.repairing ? " (réparation)" : ""));

    addLogGlobal("Visualisation D3.js initialisée pour la carte cérébrale.");

    // Fonction pour mettre à jour la carte (à appeler quand les données du backend changent)
    // window.updateCerebralMap = function(newNeurons, newLinks) { ... }
});

// Fonction globale pour les logs, accessible depuis d'autres scripts si nécessaire
function addLogGlobal(message) {
    const logOutput = document.getElementById('logOutput');
    if (logOutput) {
        const time = new Date().toLocaleTimeString();
        logOutput.innerHTML += `[${time}] ${message}<br>`;
        logOutput.scrollTop = logOutput.scrollHeight;
    } else {
        console.log(`[${time}] ${message}`);
    }
}
