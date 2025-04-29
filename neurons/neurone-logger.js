const mqtt = require('mqtt')
const client = mqtt.connect('mqtt://localhost:1883')

client.on('connect', function () {
    client.subscribe('log', function (err) {
        if (!err) {
            console.log('Logger connecté au topic log');
        }
    })
})

client.on('message', function (topic, message) {
    console.log('LOG:', message.toString())
})
