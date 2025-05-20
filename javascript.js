async function speakResponse(prompt) {
  const text = await queryGPT(prompt);
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "fr-FR";
  speechSynthesis.speak(utterance);
}
