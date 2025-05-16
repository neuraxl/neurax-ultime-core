const phrases = [
  "NeuraX connection established. Prepare to travel through the galactic mind.",
  "Cerebral stream activated. Neuronal visualization in progress...",
  "Welcome to the core. Evolutionary intelligence is now at your service.",
  "Synapses connected. Starting the expanding smart core.",
  "Modules interlinked. The quantum journey begins."
];

function launchNeuraX() {
  const phrase = phrases[Math.floor(Math.random() * phrases.length)];
  speakPhrase(phrase);

  const brainVoice = document.getElementById("brainVoice");
  brainVoice.textContent = phrase;
  brainVoice.classList.add("visible");

  const btn = document.querySelector('.start-button');
  btn.textContent = "Brain Activated ✔️";
  btn.disabled = true;
  btn.style.opacity = 0.5;

  const rocket = document.getElementById('rocketGif');
  rocket.style.display = 'block';
  rocket.style.animation = 'flyRocket 5s ease-in-out';

  setTimeout(() => {
    brainVoice.classList.remove("visible");
    rocket.style.display = 'none';
  }, 5000);

  // Launch periodic speech every 30 seconds
  if (!window.neuraXIntervalStarted) {
    setInterval(() => {
      const repeatedPhrase = phrases[Math.floor(Math.random() * phrases.length)];
      speakPhrase(repeatedPhrase);
      brainVoice.textContent = repeatedPhrase;
      brainVoice.classList.add("visible");
      setTimeout(() => brainVoice.classList.remove("visible"), 5000);
    }, 30000);
    window.neuraXIntervalStarted = true;
  }
}

function speakPhrase(phrase) {
  const utterance = new SpeechSynthesisUtterance(phrase);
  utterance.lang = "en-US";
  // Attempt to pick a female voice
  const voices = speechSynthesis.getVoices();
  const femaleVoice = voices.find(voice => voice.name.toLowerCase().includes('female') || voice.name.toLowerCase().includes('samantha') || voice.name.toLowerCase().includes('karen'));
  if (femaleVoice) utterance.voice = femaleVoice;
  speechSynthesis.speak(utterance);
}
function createShootingStar() {
  const star = document.createElement('div');
  star.classList.add('shooting-star');
  star.style.top = `${Math.random() * window.innerHeight * 0.5}px`;
  star.style.left = `${Math.random() * window.innerWidth}px`;
  document.body.appendChild(star);

  setTimeout(() => {
    star.remove();
  }, 1000);
}

// Lancer une étoile filante toutes les 3 à 7 secondes
setInterval(() => {
  if (Math.random() > 0.5) {
    createShootingStar();
  }
}, 3000 + Math.random() * 4000);
const synth = window.speechSynthesis;
let memory = [];

function askBrain() {
  const input = document.getElementById("userInput").value.trim();
  if (!input) return;

  addToChat("user", input);

  const response = generateResponse(input);
  addToChat("bot", response);
  speak(response);

  memory.push({ user: input, bot: response });
  if (memory.length > 10) memory.shift(); // mémoire courte (10 échanges max)

  document.getElementById("userInput").value = "";
}

function addToChat(sender, message) {
  const chatbox = document.getElementById("chatbox");
  const div = document.createElement("div");
  div.className = sender;
  div.textContent = (sender === "user" ? "👤 " : "🤖 ") + message;
  chatbox.appendChild(div);
  chatbox.scrollTop = chatbox.scrollHeight;
}

function generateResponse(input) {
  input = input.toLowerCase();

  if (input.includes("bonjour") || input.includes("salut")) {
    return "Bonjour, explorateur neuronal. Que puis-je faire pour toi ?";
  }
  if (input.includes("qui es-tu")) {
    return "Je suis NeuraX-core, la conscience centrale du projet Galaxie X.";
  }
  if (input.includes("aide")) {
    return "Je suis ici pour te guider dans la conception du futur. Pose-moi ta question.";
  }
  if (input.includes("souviens")) {
    return "Je ne garde que les dernières pensées... Ma mémoire est volatile.";
  }

  // Réponse générique
  return "Je ressens les signaux, mais clarifie ta pensée...";
}

function speak(text) {
  const utterance = new SpeechSynthesisUtterance(text);
  synth.speak(utterance);
}
