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
