// assets/js/brain_3d.js

import * as THREE from 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.module.min.js';

let scene, camera, renderer, brainMesh, particles;

function initBrain3D() {
    const canvas = document.getElementById('brainCanvas');
    if (!canvas) {
        console.error("Canvas element 'brainCanvas' not found.");
        return;
    }

    // 1. Scène
    scene = new THREE.Scene();

    // 2. Caméra
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 5;

    // 3. Rendu
    renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true }); // alpha: true pour la transparence
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);

    // 4. Lumière
    const ambientLight = new THREE.AmbientLight(0x0a0a0a);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x00ff00, 1, 100);
    pointLight.position.set(0, 0, 0);
    scene.add(pointLight);

    // 5. Création du Cerveau Abstrait (une sphère de base pour commencer)
    const brainGeometry = new THREE.SphereGeometry(1.5, 32, 32);
    const brainMaterial = new THREE.MeshStandardMaterial({
        color: 0x000000,
        emissive: 0x00ff00,
        emissiveIntensity: 0.1,
        metalness: 0.5,
        roughness: 0.5,
        transparent: true,
        opacity: 0.8
    });
    brainMesh = new THREE.Mesh(brainGeometry, brainMaterial);
    scene.add(brainMesh);

    // Effet de pulsation (contrôlé via l'intensité de l'émissivité)
    gsap.to(brainMaterial, {
        emissiveIntensity: 0.8,
        duration: 2,
        repeat: -1,
        yoyo: true,
        ease: "power1.inOut"
    });

    // 6. Effet de Particules (pour les connexions ou flux d'énergie)
    const particleGeometry = new THREE.BufferGeometry();
    const particleCount = 1000;
    const positions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount * 3; i++) {
        positions[i] = (Math.random() - 0.5) * 10;
    }

    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const particleMaterial = new THREE.PointsMaterial({
        color: 0x00ff00,
        size: 0.05,
        transparent: true,
        blending: THREE.AdditiveBlending
    });

    particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);

    // Animer les particules
    gsap.to(particles.rotation, {
        y: Math.PI * 2,
        duration: 20,
        repeat: -1,
        ease: "none"
    });

    // 7. Fonction d'animation
    function animate() {
        requestAnimationFrame(animate);

        // Rotation légère du cerveau
        brainMesh.rotation.y += 0.001;
        brainMesh.rotation.x += 0.0005;

        renderer.render(scene, camera);
    }

    animate();

    // Gestion du redimensionnement de la fenêtre
    window.addEventListener('resize', onWindowResize, false);
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

export { initBrain3D };
