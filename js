[
  {
    "id": "gaia",
    "nom": "Gaïa",
    "fonction": "Matrice racine de la vie et de la mémoire organique",
    "zone": "Neocortex",
    "activité": "stable",
    "liaisons": ["chronos", "nyx"]
  },
  {
    "id": "ouranos",
    "nom": "Ouranos",
    "fonction": "Connexion céleste et projection des données",
    "zone": "Cortex pariétal",
    "activité": "intense",
    "liaisons": ["éther", "gaia"]
  },
  {
    "id": "chronos",
    "nom": "Chronos",
    "fonction": "Mémoire temporelle et cycles neuronaux",
    "zone": "Hippocampe",
    "activité": "cyclique",
    "liaisons": ["nyx", "gaia"]
  },
  {
    "id": "nyx",
    "nom": "Nyx",
    "fonction": "Inconscient, rêve, et domaine des ombres mentales",
    "zone": "Amygdale",
    "activité": "fluctuante",
    "liaisons": ["chronos", "gaia"]
  },
  {
    "id": "ether",
    "nom": "Éther",
    "fonction": "Transmission interdimensionnelle des pensées",
    "zone": "Cortex frontal",
    "activité": "volatile",
    "liaisons": ["ouranos"]
  }
]
async function askAI() {
    let userInput = document.getElementById("userInput").value;
    let responseText = "Je réfléchis...";

    document.getElementById("response").innerText = responseText;

    let response = await fetch("https://api.openai.com/v1/completions", {
        method: "POST",
        headers: {
            "Authorization": "Bearer YOUR_API_KEY", // Remplace par ta clé API
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            model: "text-davinci-003", // Remplace par le bon modèle si nécessaire
            prompt: userInput,
            max_tokens: 150
        })
    });

    let data = await response.json();
    responseText = data.choices[0].text;
    document.getElementById("response").innerText = responseText;

    // Parole synthétique de la réponse
    const utterance = new SpeechSynthesisUtterance(responseText);
    utterance.lang = "fr-FR";
    speechSynthesis.speak(utterance);
}

// Reconnaissance vocale
window.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.lang = 'fr-FR';

recognition.onresult = (event) => {
    document.getElementById("userInput").value = event.results[0][0].transcript;
    askAI();
};

document.getElementById("voiceButton").addEventListener("click", () => {
    recognition.start();
});
fetch('https://neuraX-backend.io/core/activate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(brainState)
})
function launchNeuraX() {
  const phrase = "Connexion à NeuraX établie. Le système cérébral est opérationnel.";
  const utterance = new SpeechSynthesisUtterance(phrase);
  utterance.lang = "fr-FR";
  speechSynthesis.speak(utterance);

  generateGalaxies(5);
  saveNeuralLog();        // Sauvegarde JSON
  replicateNeurons();     // Auto-réplication
}

// Sauvegarde JSON simulée
function saveNeuralLog() {
  const log = {
    timestamp: new Date().toISOString(),
    status: "Cerveau activé",
    neurons: nodes.map(n => ({ x: n.x, y: n.y }))
  };
  const blob = new Blob([JSON.stringify(log, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'neurax_log.json';
  a.click();
}

// Auto-réplication neuronale simulée (ajoute 20 neur
function launchNeuraX() {
  const phrase = "Connexion à NeuraX établie. Le système cérébral est opérationnel.";
  const utterance = new SpeechSynthesisUtterance(phrase);
  utterance.lang = "fr-FR";
  speechSynthesis.speak(utterance);
  generateGalaxies(5);
  saveToMemory(phrase); // 🧠 enregistrement vocal
}
