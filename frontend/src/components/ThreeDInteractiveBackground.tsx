import React, { useEffect, useRef } from 'react';
import { useTheme } from '../context/ThemeContext';
import { themeConfig } from '../theme.config';

/**
 * Helper to convert HEX color string to RGB.
 * Used for dynamic canvas stroke opacity injection.
 */
function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const cleanHex = hex.trim().replace('#', '');
  const num = parseInt(cleanHex, 16);
  return {
    r: (num >> 16) & 255,
    g: (num >> 8) & 255,
    b: num & 255
  };
}

interface Particle3D {
  x: number;
  y: number;
  z: number;
  ox: number; // original X
  oy: number; // original Y
  oz: number; // original Z
  speed: number;
  size: number;
  phase: number;
}

export const ThreeDInteractiveBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const { theme } = useTheme();
  
  // Track mouse coordinates for subtle rotation easing
  const mouseRef = useRef({ x: 0, y: 0, targetX: 0, targetY: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // Mouse move handler
    const handleMouseMove = (e: MouseEvent) => {
      // Normalize mouse positions to range [-0.5, 0.5]
      mouseRef.current.targetX = e.clientX / window.innerWidth - 0.5;
      mouseRef.current.targetY = e.clientY / window.innerHeight - 0.5;
    };

    // Resize handler
    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('resize', handleResize);

    // 3D Grid Parameters
    const cols = 22;
    const rows = 22;
    const spacing = 75;
    const gridWidth = (cols - 1) * spacing;
    const gridDepth = (rows - 1) * spacing;

    // Create floating particles
    const particleCount = 45;
    const particles: Particle3D[] = [];
    for (let i = 0; i < particleCount; i++) {
      const px = (Math.random() - 0.5) * gridWidth * 1.2;
      const py = (Math.random() - 0.5) * height * 1.5;
      const pz = (Math.random() - 0.5) * gridDepth;
      particles.push({
        x: px,
        y: py,
        z: pz,
        ox: px,
        oy: py,
        oz: pz,
        speed: 0.2 + Math.random() * 0.4,
        size: 1.5 + Math.random() * 2.5,
        phase: Math.random() * Math.PI * 2,
      });
    }

    // Camera angles
    let rotX = 0.5; // Default tilt
    let rotY = -0.2;
    let time = 0;

    // Animation Loop
    const draw = () => {
      time += 0.004;

      // Clear canvas
      ctx.clearRect(0, 0, width, height);

      // Smoothly interpolate camera angles (lerp)
      const targetRotX = 0.4 + mouseRef.current.targetY * 0.25; // Tilt up/down
      const targetRotY = -0.15 + mouseRef.current.targetX * 0.35; // Pan left/right

      rotX += (targetRotX - rotX) * 0.04;
      rotY += (targetRotY - rotY) * 0.04;

      const centerX = width / 2;
      const centerY = height * 0.55; // Slightly lower center for horizon look
      const focalLength = 700;

      // Extract current theme colors dynamically
      const lightRgb = hexToRgb(themeConfig.palette.oak);
      const darkRgb = hexToRgb(themeConfig.palette.nightWarm);
      const colorRGB = theme === 'light' ? lightRgb : darkRgb;
      const baseAlpha = theme === 'light' ? 0.42 : 0.34;

      // Create a map to store 2D coordinates for grid drawing
      const projectedPoints: { x: number; y: number; alpha: number }[][] = [];

      // Cosine / Sine variables for rotation
      const cosX = Math.cos(rotX);
      const sinX = Math.sin(rotX);
      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);

      // 1. Project Grid Points
      for (let r = 0; r < rows; r++) {
        projectedPoints[r] = [];
        for (let c = 0; c < cols; c++) {
          // Original 3D space
          const ox = c * spacing - gridWidth / 2;
          const oy = r * spacing - gridDepth / 2;
          
          // Generate organic wave height (Z in 3D coordinate, which will be our Y-displacement)
          // Simple multi-frequency waves
          const wave1 = Math.sin(time + ox * 0.005) * Math.cos(time + oy * 0.005) * 80;
          const wave2 = Math.sin(time * 1.5 + (ox + oy) * 0.002) * 30;
          const heightY = wave1 + wave2;

          // Perform 3D rotation
          // Rotate around Y axis
          const x1 = ox * cosY - oy * sinY;
          const z1 = ox * sinY + oy * cosY;

          // Rotate around X axis
          const y2 = heightY * cosX - z1 * sinX;
          const z2 = heightY * sinX + z1 * cosX;

          // Translate camera distance
          const cameraZ = z2 + 800; // Push away from camera

          if (cameraZ > 100) {
            const screenX = centerX + (x1 * focalLength) / cameraZ;
            const screenY = centerY + (y2 * focalLength) / cameraZ;

            // Opacity falls off based on Z distance (depth fog)
            const maxDepth = 1500;
            const depthRatio = Math.max(0, Math.min(1, (cameraZ - 400) / maxDepth));
            const pointAlpha = (1 - depthRatio) * baseAlpha;

            projectedPoints[r][c] = { x: screenX, y: screenY, alpha: pointAlpha };
          } else {
            projectedPoints[r][c] = { x: 0, y: 0, alpha: 0 };
          }
        }
      }

      // 2. Draw Grid Lines
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const pt = projectedPoints[r][c];
          if (pt.alpha <= 0) continue;

          // Draw line to next column item
          if (c < cols - 1) {
            const nextColPt = projectedPoints[r][c + 1];
            if (nextColPt.alpha > 0) {
              const alpha = Math.min(pt.alpha, nextColPt.alpha);
              ctx.beginPath();
              ctx.moveTo(pt.x, pt.y);
              ctx.lineTo(nextColPt.x, nextColPt.y);
              ctx.strokeStyle = `rgba(${colorRGB.r}, ${colorRGB.g}, ${colorRGB.b}, ${alpha * 0.95})`;
              ctx.lineWidth = theme === 'light' ? 1.35 : 1.15;
              ctx.stroke();
            }
          }

          // Draw line to next row item
          if (r < rows - 1) {
            const nextRowPt = projectedPoints[r + 1][c];
            if (nextRowPt.alpha > 0) {
              const alpha = Math.min(pt.alpha, nextRowPt.alpha);
              ctx.beginPath();
              ctx.moveTo(pt.x, pt.y);
              ctx.lineTo(nextRowPt.x, nextRowPt.y);
              ctx.strokeStyle = `rgba(${colorRGB.r}, ${colorRGB.g}, ${colorRGB.b}, ${alpha * 0.95})`;
              ctx.lineWidth = theme === 'light' ? 1.35 : 1.15;
              ctx.stroke();
            }
          }
        }
      }

      // 3. Draw and Animate 3D Particles
      particles.forEach((p) => {
        // Drift upwards
        p.oy -= p.speed;
        p.phase += 0.008;

        // Soft horizontal wiggle
        const curX = p.ox + Math.sin(p.phase) * 20;
        const curY = p.oy;
        const curZ = p.oz;

        // Reset if drifted too high
        if (p.oy < -height) {
          p.oy = height * 0.8;
          p.ox = (Math.random() - 0.5) * gridWidth * 1.2;
        }

        // Apply same rotation
        const x1 = curX * cosY - curZ * sinY;
        const z1 = curX * sinY + curZ * cosY;
        const y2 = curY * cosX - z1 * sinX;
        const z2 = curY * sinX + z1 * cosX;

        const cameraZ = z2 + 800;

        if (cameraZ > 100) {
          const screenX = centerX + (x1 * focalLength) / cameraZ;
          const screenY = centerY + (y2 * focalLength) / cameraZ;

          const depthRatio = Math.max(0, Math.min(1, (cameraZ - 400) / 1500));
          const pAlpha = (1 - depthRatio) * (theme === 'light' ? 0.62 : 0.5);

          // Draw small glowing particle dot
          ctx.beginPath();
          ctx.arc(screenX, screenY, (p.size * focalLength) / cameraZ, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${colorRGB.r}, ${colorRGB.g}, ${colorRGB.b}, ${pAlpha})`;
          ctx.fill();
        }
      });

      animationId = requestAnimationFrame(draw);
    };

    draw();

    // Clean up
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationId);
    };
  }, [theme]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 0, // Draw behind everything but above base layer
        pointerEvents: 'none',
        opacity: theme === 'light' ? 0.62 : 0.55,
        mixBlendMode: theme === 'light' ? 'multiply' : 'screen',
      }}
    />
  );
};
