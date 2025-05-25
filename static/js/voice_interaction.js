// static/js/voice_interaction.js
document.addEventListener('DOMContentLoaded', function () {
    const speakButton = document.getElementById('speakButton');
    const toggleVoiceOutputButton = document.getElementById('toggleVoiceOutput');
    const userInput = document.getElementById('userInput');
    let voiceOutputEnabled = true; // Activé par défaut

    // Vérifier la compatibilité avec Web Speech API
    const synth = window.speechSynthesis;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;

    if (!synth) {
        addLogGlobal("ERREUR: Votre navigateur ne supporte pas la synthèse vocale (Web Speech API).");
        if(speakButton) speakButton.disabled = true;
    }

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.lang = 'fr-FR'; // Définir la langue
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.onresult = function(event) {
            const speechResult = event.results[0][0].transcript;
            addLogGlobal(`Entrée vocale reconnue: "${speechResult}"`);
            if (userInput) userInput.value = speechResult;
            // Simuler l'envoi au backend
            document.getElementById('sendInputButton').click();
        }

        recognition.onspeechend = function() {
            recognition.stop();
            if(speakButton) speakButton.innerHTML = '<i class="fas fa-microphone"></i> Parler';
            addLogGlobal("Reconnaissance vocale terminée.");
        }

        recognition.onerror = function(event) {
            addLogGlobal(`Erreur de reconnaissance vocale: ${event.error}`);
            if(speakButton) speakButton.innerHTML = '<i class="fas fa-microphone"></i> Parler';
        }
    } else {
        addLogGlobal("INFO: Votre navigateur ne supporte pas la reconnaissance vocale (Web Speech API).");
        if(speakButton) speakButton.disabled = true;
    }

    if (toggleVoiceOutputButton) {
        toggleVoiceOutputButton.addEventListener('click', () => {
            voiceOutputEnabled = !voiceOutputEnabled;
            addLogGlobal(`Synthèse vocale ${voiceOutputEnabled ? "activée" : "désactivée"}.`);
            toggleVoiceOutputButton.textContent = voiceOutputEnabled ? "Désactiver Voix" : "Activer Voix";
            toggleVoiceOutputButton.classList.toggle('btn-danger', !voiceOutputEnabled);
            toggleVoiceOutputButton.classList.toggle('btn-success', voiceOutputEnabled);
        });
    }

    // Fonction pour faire parler NeuraX
    window.neuraxSpeak = function(text) {
        if (synth && voiceOutputEnabled) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'fr-FR'; // S'assurer que la langue est correcte
            // Options de voix (peuvent être étendues)
            // const voices = synth.getVoices();
            // utterance.voice = voices.find(voice => voice.lang === 'fr-FR' && voice.name.includes('Google')); // Exemple
            utterance.pitch = 1; // 0 à 2
            utterance.rate = 1; // 0.1 à 10
            synth.speak(utterance);
            addLogGlobal(`NeuraX dit: "${text}"`);
        } else if (!voiceOutputEnabled) {
            addLogGlobal(`NeuraX (silencieux): "${text}"`);
        } else {
            addLogGlobal(`NeuraX (synthèse vocale non dispo): "${text}"`);
        }
    }

    // Exemple d'utilisation
    setTimeout(() => {
        neuraxSpeak("Bienvenue dans l'interface de NeuraX Ultime.");
    }, 2000);


    if (speakButton && recognition) {
        speakButton.addEventListener('click', () => {
            try {
                recognition.start();
                speakButton.innerHTML = '<i class="fas fa-microphone-slash"></i> Écoute...';
                addLogGlobal("Reconnaissance vocale démarrée...");
            } catch(e) {
                // Peut arriver si une reconnaissance est déjà en cours
                addLogGlobal("Erreur au démarrage de la reconnaissance vocale. Réessayez.");
                recognition.stop(); // Tenter de réinitialiser
                 speakButton.innerHTML = '<i class="fas fa-microphone"></i> Parler';
            }
        });
    }

    // Intercepter les logs "NeuraX:" pour la synthèse vocale
    const originalAddLog = window.addLog || addLogGlobal; // S'assurer d'utiliser la fonction de log définie dans index.html
    const logInterceptor = (message) => {
        originalAddLog(message); // Appeler la fonction de log originale
        if (message.startsWith("NeuraX:") && voiceOutputEnabled) {
            const textToSpeak = message.substring("NeuraX:".length).trim();
            neuraxSpeak(textToSpeak);
        }
    };
    // Remplacer la fonction de log si elle existe globalement, sinon définir addLogGlobal
    if (window.addLog) {
        window.addLog = logInterceptor;
    } else {
         // Si addLogGlobal est déjà la fonction que nous voulons utiliser,
         // nous devons être prudents pour ne pas créer une récursion infinie.
         // Pour simplifier, nous allons supposer que la fonction de log principale
         // est celle dans index.html. Le code ci-dessus dans dashboard.js définit addLogGlobal.
         // Si on veut centraliser, il faudrait une seule définition de addLogGlobal.
         // Pour cet exemple, on va supposer que la fonction de log dans index.html est la source de vérité.
         const mainLogFunction = document.getElementById('logOutput') ? (msg) => {
            const logOutput = document.getElementById('logOutput');
            const time = new Date().toLocaleTimeString();
            logOutput.innerHTML += `[${time}] ${msg}<br>`;
            logOutput.scrollTop = logOutput.scrollHeight;
            if (msg.startsWith("NeuraX:") && voiceOutputEnabled) {
                const textToSpeak = msg.substring("NeuraX:".length).trim();
                neuraxSpeak(textToSpeak);
            }
         } : console.log;

         // Remplacer la fonction de log dans le script de index.html
         // Ceci est un peu un hack pour l'exemple; une meilleure gestion des modules JS serait préférable.
         // (Par exemple, en utilisant des modules ES6 ou un gestionnaire d'événements)
    }


});
