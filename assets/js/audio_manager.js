// assets/js/audio_manager.js

// Initialise Howler.js pour les sons
const sounds = {};

function loadSounds() {
    sounds.click = new Howl({
        src: ['assets/sounds/click.mp3'], // Assurez-vous que le fichier existe
        volume: 0.5
    });
    sounds.scroll = new Howl({
        src: ['assets/sounds/scroll.mp3'], // Assurez-vous que le fichier existe
        volume: 0.2,
        html5: true // Utilise HTML5 Audio pour éviter les problèmes de mémoire sur les longs sons
    });

    // Précharge tous les sons
    for (const key in sounds) {
        if (sounds[key] instanceof Howl) {
            sounds[key].load();
        }
    }
}

function playSound(name) {
    if (sounds[name] && sounds[name].state() === 'loaded') {
        sounds[name].play();
    } else {
        console.warn(`Son "${name}" non chargé ou en cours de chargement.`);
    }
}

function initAudioEvents() {
    loadSounds(); // Charge les sons au démarrage

    // Son au clic sur les liens GitHub
    document.querySelectorAll('.github-links a, .action-button').forEach(element => {
        element.addEventListener('click', () => {
            playSound('click');
        });
    });

    // Son au défilement (déclenchement moins fréquent)
    // On utilise GSAP ScrollTrigger pour déclencher le son à des intervalles de scroll
    // ou à l'entrée/sortie de sections pour un meilleur contrôle.
    // Par exemple, on peut déclencher un son léger à l'entrée de chaque section.
    gsap.utils.toArray("section").forEach(section => {
        ScrollTrigger.create({
            trigger: section,
            start: "top 75%",
            onEnter: () => playSound('scroll'),
            onLeaveBack: () => playSound('scroll'), // Optionnel: son au retour en arrière
            // markers: true
        });
    });
}

export { initAudioEvents, playSound }; // Exporter playSound pour une utilisation externe
