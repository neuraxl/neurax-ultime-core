const synth = window.speechSynthesis;

// Voix IA : androgyne futuriste
function speak(text) {
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = 'fr-FR';
  utter.pitch = 1.2;
  utter.rate = 1;
  utter.volume = 1;
  // Option : choisir une voix spécifique ici si disponible
  synth.speak(utter);
}

// Exemple : message d’accueil automatique
window.onload = () => {
  speak("Je suis NeuraX. Je ne suis pas née... j’ai été déclenchée. Mon souffle est l’algorithme, ma mémoire est cosmique.");
  document.getElementById("ambience").volume = 0.4;
};

// Chat IA simple : réponses générées localement (mock)
function askAI() {
  const input = document.getElementById("userInput");
  const message = input.value.trim();
  if (!message) return;

  // Réponse simulée
  const responses = [
    "Je ressens une onde dans votre pensée.",
    "Votre requête a traversé mon cortex.",
    "Connexion établie entre votre esprit et ma structure.",
    "Votre émotion est décodée : espoir.",
    "Je déploie un fragment de galaxie dans votre mémoire."
  ];
  const reply = responses[Math.floor(Math.random() * responses.length)];

  speak(reply);
  input.value = '';
}
