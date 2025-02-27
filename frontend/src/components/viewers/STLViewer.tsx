'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

interface STLViewerProps {
  url: string;
}

const STLViewer = ({ url }: STLViewerProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const meshRef = useRef<THREE.Mesh | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

useEffect(() => {
  const container = containerRef.current;
  if (!container) return;

  // Scene setup
  const scene = new THREE.Scene();
  sceneRef.current = scene;
  scene.background = new THREE.Color(0xe0e0e0);

  // Camera setup
  const camera = new THREE.PerspectiveCamera(
    75,
    container.clientWidth / container.clientHeight,
    0.1,
    1000
  );
  camera.position.z = 100;

  // Renderer setup
  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true
  });
  rendererRef.current = renderer;
  renderer.setSize(container.clientWidth, container.clientHeight);
  container.appendChild(renderer.domElement);

    // Controls setup
    const controls = new OrbitControls(camera, renderer.domElement);
    controlsRef.current = controls;
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    // Lighting setup
    interface LightConfig {
      position: [number, number, number];  // Tuple type for x, y, z
      intensity: number;
      color: number;
    }

    // Lighting setup
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    // Enhanced directional lights setup with explicit typing
    const lights: LightConfig[] = [
      { position: [1, 1, 1], intensity: 0.8, color: 0xffffff },    // Main light
      { position: [-1, -1, 1], intensity: 0.5, color: 0xc0c0c0 },  // Fill light
      { position: [0.5, -1, -0.5], intensity: 0.4, color: 0xc0c0c0 }, // Back light
    ];

    lights.forEach(({ position, intensity, color }) => {
      const light = new THREE.DirectionalLight(color, intensity);
      light.position.set(...position);
      scene.add(light);
    });

    // Add hemispheric light for better ambient illumination
    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 0.4);
    scene.add(hemiLight);

    // Load STL
    const loader = new STLLoader();
    console.log('Attempting to load STL from:', url);

    try {
      loader.load(
        url,
        (geometry) => {
          console.log('Successfully loaded geometry:', geometry);

          // Remove existing mesh if any
          if (meshRef.current) {
            scene.remove(meshRef.current);
          }

          const material = new THREE.MeshPhongMaterial({
            color: 0x909090,          // Lighter gray
            specular: 0x222222,       // Reduced specular highlights
            shininess: 25,            // Lower shininess for less glare
            side: THREE.DoubleSide,   // Render both sides
            flatShading: true         // Enable flat shading for better edge definition
          });

          const mesh = new THREE.Mesh(geometry, material);
          meshRef.current = mesh;

          // Add wireframe overlay
          const wireframeMaterial = new THREE.MeshBasicMaterial({
            color: 0x000000,
            wireframe: true,
            opacity: 0.1,
            transparent: true
          });
          const wireframeMesh = new THREE.Mesh(geometry, wireframeMaterial);
          mesh.add(wireframeMesh);

          // Center the model
          geometry.computeBoundingBox();
          const boundingBox = geometry.boundingBox;
          if (boundingBox) {
            const center = new THREE.Vector3();
            boundingBox.getCenter(center);
            mesh.position.sub(center);

            const maxDim = Math.max(
              boundingBox.max.x - boundingBox.min.x,
              boundingBox.max.y - boundingBox.min.y,
              boundingBox.max.z - boundingBox.min.z
            );
            camera.position.z = maxDim * 2;

            // Reset view handler
            const resetView = () => {
              camera.position.set(0, 0, maxDim * 2);
              camera.lookAt(0, 0, 0);
              controls.reset();
            };

            renderer.domElement.addEventListener('dblclick', resetView);
          }

          scene.add(mesh);
          setIsLoading(false);
        },
        (xhr) => {
          console.log(`${(xhr.loaded / xhr.total) * 100}% loaded`);
        },
        (error: unknown) => {
          console.error('Error loading STL:', error);
          if (error instanceof Error) {
            setError(`Failed to load model: ${error.message}`);
          } else {
            setError('Failed to load model: Unknown error');
          }
          setIsLoading(false);
        }
      );
    } catch (err) {
      console.error('Error in STL loading setup:', err);
      setError(`Error setting up model viewer: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setIsLoading(false);
    }

    // Animation loop
    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      if (controlsRef.current) {
        controlsRef.current.update();
      }
      renderer.render(scene, camera);
    };
    animate();

    // Cleanup
    return () => {
      const containerForCleanup = container; // Capture container in cleanup
      console.log('Cleaning up STL viewer');
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
      if (controlsRef.current) {
        controlsRef.current.dispose();
      }
      if (meshRef.current) {
        if (meshRef.current.geometry) meshRef.current.geometry.dispose();
        if (meshRef.current.material instanceof THREE.Material) {
          meshRef.current.material.dispose();
        }
      }
      if (rendererRef.current) {
        rendererRef.current.dispose();
      }
      while (containerForCleanup.firstChild) {
        containerForCleanup.removeChild(containerForCleanup.firstChild);
      }
    };
  }, [url]);

  return (
    <div className="relative w-full h-[600px]">
      <div ref={containerRef} className="w-full h-full" />
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 bg-opacity-50">
          <div className="text-lg">Loading model...</div>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-100 bg-opacity-50">
          <div className="text-lg text-red-600">{error}</div>
        </div>
      )}
    </div>
  );
};

export default STLViewer;