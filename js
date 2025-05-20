function launchNeuraX() {
  const phrase = "Connexion à NeuraX établie. Le système cérébral est opérationnel.";
  const utterance = new SpeechSynthesisUtterance(phrase);
  utterance.lang = "fr-FR";
  speechSynthesis.speak(utterance);
  generateGalaxies(5);
  saveToMemory(phrase); // 🧠 enregistrement vocal
}
