const aedes = require('aedes')();
const net = require('net');

const server = net.createServer(aedes.handle);
const port = 1883;

server.listen(port, function () {
  console.log('Serveur MQTT Aedes démarré sur le port', port);
});

aedes.on('client', function (client) {
  console.log('Client connecté', client.id);
});

aedes.on('publish', function (packet, client) {
  console.log('Message publié:', packet.payload.toString());
});
