function parler(texte, langue = "fr-FR", voixNom = null) {
  const utterance = new SpeechSynthesisUtterance(texte);
  utterance.lang = langue;

  // Si une voix spécifique est demandée
  if (voixNom) {
    const voixDisponibles = speechSynthesis.getVoices();
    const voixChoisie = voixDisponibles.find(v => v.name.includes(voixNom));
    if (voixChoisie) utterance.voice = voixChoisie;
  }

  speechSynthesis.speak(utterance);
}
async function openCivilizationWindow(planetId) {
  brainState.stats.queries++;
  const thought = await queryGPT(`Décris brièvement la civilisation sur la planète P${planetId}`);
  saveNeuralState(brainState);
  const newWindow = window.open('', '_blank', 'width=600,height=400');
  newWindow.document.write(`
    <html>
    <head>
      <title>Civilisation de P${planetId}</title>
      <style>
        body {
          font-family: sans-serif;
          background: #0a0a0a;
          color: #00ffe1;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          height: 100vh;
          text-align: center;
        }
        h1 { font-size: 2em; }
        p { font-size: 1em; margin: 1em 0; }
        button {
          margin-top: 2em;
          padding: 0.8em 1.5em;
          background: transparent;
          border: 2px solid #00ffe1;
          color: #00ffe1;
          border-radius: 10px;
          font-weight: bold;
          cursor: pointer;
          transition: all 0.3s ease;
        }
        button:hover {
          background: #00ffe1;
          color: #000;
        }
      </style>
    </head>
    <body>
      <div>
        <h1>Bienvenue dans la civilisation de P${planetId}!</h1>
        <p>${thought}</p>
        <button onclick="window.close()">⬅️ Retour</button>
      </div>
    </body>
    </html>
  `);
  newWindow.document.close();
}
async function speakResponse(prompt) {
  const text = await queryGPT(prompt);
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "fr-FR";
  speechSynthesis.speak(utterance);
}
