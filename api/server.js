const express = require('express');
const app = express();
const port = 3000;

app.use(express.json());

app.post('/neuron', (req, res) => {
  console.log('Neuron data received:', req.body);
  res.send('Neuron data received');
});

app.listen(port, () => {
  console.log(API Server listening at http://localhost:${port});
});
