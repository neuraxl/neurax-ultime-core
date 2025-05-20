function changeMode() {
    let hours = new Date().getHours();
    if (hours > 18) {
        document.body.classList.add("dark-mode");
    } else {
        document.body.classList.remove("dark-mode");
    }
}
window.onload = changeMode;
async function askAI() {
    let userInput = document.getElementById("userInput").value;
    let responseText = "Je réfléchis...";

    let response = await fetch("https://api.openai.com/v1/completions", {
        method: "POST",
        headers: { "Authorization": "Bearer YOUR_API_KEY", "Content-Type": "application/json" },
        body: JSON.stringify({ model: "gpt-4", prompt: userInput })
    });

    let data = await response.json();
    responseText = data.choices[0].text;

    document.getElementById("response").innerText = responseText;
}
async function askAI() {
    let userInput = document.getElementById("userInput").value;
    let responseText = "Je réfléchis...";

    // Simulation IA (API GPT-4)
    let response = await fetch("https://api.openai.com/v1/completions", {
        method: "POST",
        headers: { "Authorization": "Bearer YOUR_API_KEY", "Content-Type": "application/json" },
        body: JSON.stringify({ model: "gpt-4", prompt: userInput })
    });

    let data = await response.json();
    responseText = data.choices[0].text;

    document.getElementById("response").innerText = responseText;
}

function changeMode() {
    document.body.classList.toggle("dark-mode");
    alert("Mode activé !");
}const synth = window.speechSynthesis;

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
