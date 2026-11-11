/**
 * Live Surveillance Monitor & Interactive Stream Renderer
 */

class LiveMonitor {
  constructor() {
    this.activeSource = 'demo';
    this.animationId = null;
    this.videoElement = null;
    this.canvas = null;
    this.ctx = null;
    this.simTime = 0;
  }

  init() {
    this.canvas = document.getElementById('live-feed-canvas');
    this.canvasGrid = document.getElementById('live-feed-canvas-grid1');
    if (this.canvas) {
      this.ctx = this.canvas.getContext('2d');
    }
    if (this.canvasGrid) {
      this.ctxGrid = this.canvasGrid.getContext('2d');
    }
    if (!this.animationId) {
      this.startStreamRenderer();
    }
  }

  startStreamRenderer() {
    const render = () => {
      this.drawSurveillanceScene();
      this.animationId = requestAnimationFrame(render);
    };
    render();
  }

  drawSurveillanceScene() {
    this.simTime += 0.03;
    const canvases = [
      { c: this.canvas, ctx: this.ctx },
      { c: this.canvasGrid, ctx: this.ctxGrid }
    ];

    for (const item of canvases) {
      if (!item.c || !item.ctx) continue;
      const ctx = item.ctx;
      const w = item.c.width;
      const h = item.c.height;

    // Draw Dark CCTV Hallway Background
    ctx.fillStyle = '#10141d';
    ctx.fillRect(0, 0, w, 180);
    ctx.fillStyle = '#0a0d14';
    ctx.fillRect(0, 180, w, h - 180);

    // Floor Grid lines
    ctx.strokeStyle = '#1e2838';
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 60) {
      ctx.beginPath();
      ctx.moveTo(x, 180);
      ctx.lineTo(x * 1.5 - 120, h);
      ctx.stroke();
    }
    for (let y = 180; y < h; y += 35) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Doorway / Secure Entrance
    ctx.fillStyle = '#07090e';
    ctx.fillRect(220, 30, 200, 150);
    ctx.strokeStyle = '#00f0ff';
    ctx.lineWidth = 2;
    ctx.strokeRect(220, 30, 200, 150);
    ctx.fillStyle = '#00f0ff';
    ctx.font = '11px "JetBrains Mono"';
    ctx.fillText('MAIN GATE ENTRANCE', 250, 50);

    // Restricted Zone Polygon Markings
    ctx.fillStyle = 'rgba(255, 179, 0, 0.15)';
    ctx.strokeStyle = '#ffb300';
    ctx.beginPath();
    ctx.moveTo(140, 200);
    ctx.lineTo(500, 200);
    ctx.lineTo(560, 380);
    ctx.lineTo(80, 380);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = '#ffb300';
    ctx.fillText('RESTRICTED ZONE [PERIMETER-01]', 160, 220);

    // Animated Walking Subject
    const cycle = this.simTime % 14;
    const px = 80 + (cycle / 14) * 480;
    const py = 250 + Math.sin(this.simTime * 6) * 3;

    // Head
    ctx.fillStyle = '#8a9bb8';
    ctx.beginPath();
    ctx.arc(px + 20, py - 45, 14, 0, Math.PI * 2);
    ctx.fill();

    // Body
    ctx.fillStyle = '#2d3e5e';
    ctx.fillRect(px + 8, py - 30, 24, 50);

    // Legs
    const legOffset = Math.sin(this.simTime * 8) * 10;
    ctx.strokeStyle = '#1a2436';
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.moveTo(px + 14, py + 20);
    ctx.lineTo(px + 10 + legOffset, py + 65);
    ctx.moveTo(px + 26, py + 20);
    ctx.lineTo(px + 30 - legOffset, py + 65);
    ctx.stroke();

    // Weapon appearance simulation between 4s and 9s
    const isWeapon = cycle >= 4 && cycle <= 9;
    if (isWeapon) {
      // Gun in hand
      ctx.fillStyle = '#ff2b56';
      ctx.fillRect(px + 32, py - 10, 24, 8);
      ctx.fillRect(px + 38, py - 2, 8, 12);

      // Bounding Box - Weapon
      ctx.strokeStyle = '#ff2b56';
      ctx.lineWidth = 3;
      ctx.strokeRect(px + 28, py - 18, 35, 30);
      ctx.fillStyle = '#ff2b56';
      ctx.fillRect(px + 28, py - 32, 80, 14);
      ctx.fillStyle = '#ffffff';
      ctx.font = '10px "Inter"';
      ctx.fillText('GUN 94.2%', px + 32, py - 22);

      // Subject Bounding Box
      ctx.strokeStyle = '#00e676';
      ctx.lineWidth = 2;
      ctx.strokeRect(px - 5, py - 65, 50, 135);
      ctx.fillStyle = '#00e676';
      ctx.fillRect(px - 5, py - 78, 80, 14);
      ctx.fillStyle = '#000000';
      ctx.fillText('PERSON 96.5%', px, py - 68);
    } else {
      // Subject Bounding Box (Normal)
      ctx.strokeStyle = '#00e676';
      ctx.lineWidth = 2;
      ctx.strokeRect(px - 5, py - 65, 50, 135);
      ctx.fillStyle = '#00e676';
      ctx.fillRect(px - 5, py - 78, 80, 14);
      ctx.fillStyle = '#000000';
      ctx.fillText('PERSON 95.8%', px, py - 68);
    }

    // Top Telemetry Header
    ctx.fillStyle = 'rgba(7, 9, 14, 0.85)';
    ctx.fillRect(0, 0, w, 32);
    ctx.fillStyle = '#00f0ff';
    ctx.font = '11px "JetBrains Mono"';
    ctx.fillText('CAM: CAM-01 [MAIN GATE NORTH] | AI: ACTIVE | PQC: ML-KEM-768 | AES-256-GCM', 15, 20);

    // Live Timestamp
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0] + '.' + String(now.getMilliseconds()).padStart(3, '0');
    ctx.fillStyle = '#00e676';
    ctx.fillText(`REC [●] ${timeStr}`, w - 160, 20);
    } // End of canvases loop
  }
}

window.liveMonitor = new LiveMonitor();
