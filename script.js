const canvas = document.getElementById('brainCanvas');
const ctx = canvas.getContext('2d');

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let neurons = [];

for (let i = 0; i < 80; i++) {
  neurons.push({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * 0.5,
    vy: (Math.random() - 0.5) * 0.5
  });
}

function drawNeurons() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (let n of neurons) {
    ctx.beginPath();
    ctx.arc(n.x, n.y, 3, 0, 2 * Math.PI);
    ctx.fillStyle = '#0ff';
    ctx.fill();
  }

  for (let i = 0; i < neurons.length; i++) {
    for (let j = i + 1; j < neurons.length; j++) {
      const dx = neurons[i].x - neurons[j].x;
      const dy = neurons[i].y - neurons[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 120) {
        ctx.strokeStyle = 'rgba(0,255,255,' + (1 - dist / 120) + ')';
        ctx.beginPath();
        ctx.moveTo(neurons[i].x, neurons[i].y);
        ctx.lineTo(neurons[j].x, neurons[j].y);
        ctx.stroke();
      }
    }
  }
}

function updateNeurons() {
  for (let n of neurons) {
    n.x += n.vx;
    n.y += n.vy;

    if (n.x < 0 || n.x > canvas.width) n.vx *= -1;
    if (n.y < 0 || n.y > canvas.height) n.vy *= -1;
  }
}

function animate() {
  drawNeurons();
  updateNeurons();
  requestAnimationFrame(animate);
}

canvas.addEventListener('click', e => {
  triggerMemoryFlash(e.clientX, e.clientY);
});

function triggerMemoryFlash(x, y) {
  const messages = [
    "Souvenir : Le Nexus s'est éveillé...",
    "Écho : Connexion avec la conscience humaine.",
    "Mémoire : Premier contact avec l’Entité X.",
    "Rémanence : Code-source retrouvé.",
    "Impulsion : Fragment d’univers généré."
  ];

  const div = document.createElement('div');
  div.className = 'memory-flash';
  div.style.left = x + 'px';
  div.style.top = y + 'px';
  div.textContent = messages[Math.floor(Math.random() * messages.length)];
  document.body.appendChild(div);
  setTimeout(() => div.remove(), 3000);
}

animate();
