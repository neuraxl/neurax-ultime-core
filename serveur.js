// server.js
const WebSocket = require('ws');

const wss = new WebSocket.Server({ port: 8080 }, () => {
  console.log('Serveur WebSocket en écoute sur ws://localhost:8080');
});

wss.on('connection', (ws) => {
  console.log('Client connecté');

  ws.on('message', (message) => {
    console.log(`Message reçu : ${message}`);
    ws.send(`Echo : ${message}`);
  });

  ws.on('close', () => {
    console.log('Client déconnecté');
  });
});
