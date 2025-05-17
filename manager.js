const { exec } = require('child_process');
const path = require('path');

const repoURL = 'https://TOKEN@github.com/USERNAME/REPOSITORY.git'; // Remplace TOKEN, USERNAME, REPO
const commitMessage = '🚀 Déploiement automatique par NeuraX Bot';

function runCmd(cmd, cwd = process.cwd()) {
  return new Promise((resolve, reject) => {
    exec(cmd, { cwd }, (err, stdout, stderr) => {
      if (err) return reject(stderr);
      resolve(stdout);
    });
  });
}

async function deploy() {
  try {
    // Vérifier si dossier est un repo git
    await runCmd('git status');
  } catch {
    console.log('Initialisation du dépôt Git...');
    await runCmd('git init');
    await runCmd(`git remote add origin ${repoURL}`);
  }
  
  try {
    await runCmd('git add .');
    await runCmd(`git commit -m "${commitMessage}"`);
  } catch {
    console.log('Aucun changement détecté ou commit impossible.');
  }
  
  console.log('Push sur GitHub...');
  await runCmd('git push origin main --force');
  console.log('Déploiement terminé ! Va voir ta page GitHub Pages.');

  console.log('URL : https://USERNAME.github.io/REPOSITORY');
}

deploy().catch(console.error);
