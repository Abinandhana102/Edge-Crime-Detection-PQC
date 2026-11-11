/**
 * Restricted Area Intrusion Polygon Zone Editor
 */

class ZonesEditor {
  constructor() {
    this.canvas = null;
    this.ctx = null;
    this.currentPoints = [];
    this.activeZones = [];
  }

  init() {
    this.canvas = document.getElementById('zone-canvas');
    if (this.canvas) {
      this.ctx = this.canvas.getContext('2d');
      this.setupEventListeners();
      this.loadZones();
    }
  }

  setupEventListeners() {
    this.canvas.addEventListener('click', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Normalize points to [0, 1]
      const nx = parseFloat((x / this.canvas.width).toFixed(3));
      const ny = parseFloat((y / this.canvas.height).toFixed(3));

      this.currentPoints.push([nx, ny]);
      this.draw();
      this.updatePointsPreview();
    });

    const resetBtn = document.getElementById('btn-reset-zone-points');
    if (resetBtn) {
      resetBtn.onclick = () => {
        this.currentPoints = [];
        this.draw();
        this.updatePointsPreview();
      };
    }

    const saveBtn = document.getElementById('btn-save-zone');
    if (saveBtn) {
      saveBtn.onclick = () => this.saveCurrentZone();
    }
  }

  async loadZones() {
    try {
      this.activeZones = await API.getZones();
      this.renderZonesTable();
      this.draw();
    } catch (err) {
      console.error('Error loading zones:', err);
    }
  }

  updatePointsPreview() {
    const preview = document.getElementById('zone-points-preview');
    if (preview) {
      preview.innerText = JSON.stringify(this.currentPoints);
    }
  }

  async saveCurrentZone() {
    if (this.currentPoints.length < 3) {
      alert('A restricted polygon zone must have at least 3 vertex points.');
      return;
    }

    const name = document.getElementById('zone-name-input').value.trim() || 'New Restricted Zone';
    const zoneCode = `ZONE-${Date.now().toString().slice(-4)}`;
    const severity = document.getElementById('zone-severity-select').value || 'HIGH';

    try {
      await API.createZone({
        zone_code: zoneCode,
        name: name,
        camera_id: 1,
        polygon_points_json: JSON.stringify(this.currentPoints),
        severity: severity
      });

      alert(`✅ Restricted Zone '${name}' created successfully!`);
      this.currentPoints = [];
      this.updatePointsPreview();
      await this.loadZones();
    } catch (err) {
      alert(`Failed to create zone: ${err.message}`);
    }
  }

  renderZonesTable() {
    const tbody = document.getElementById('zones-table-body');
    if (!tbody) return;

    if (this.activeZones.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No restricted zones configured.</td></tr>';
      return;
    }

    tbody.innerHTML = this.activeZones.map(z => `
      <tr>
        <td><strong>${z.zone_code}</strong></td>
        <td>${z.name}</td>
        <td><span class="badge ${z.severity === 'CRITICAL' ? 'badge-critical' : 'badge-high'}">${z.severity}</span></td>
        <td style="font-family: var(--font-mono); font-size: 11px;">${z.polygon_points_json.slice(0, 30)}...</td>
        <td>
          <button class="btn-action btn-danger" style="padding: 4px 8px;" onclick="window.zonesEditor.deleteZone(${z.id})">
            Delete
          </button>
        </td>
      </tr>
    `).join('');
  }

  async deleteZone(id) {
    if (confirm('Delete this restricted area perimeter?')) {
      await API.deleteZone(id);
      await this.loadZones();
    }
  }

  draw() {
    if (!this.canvas || !this.ctx) return;
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    // Clear
    ctx.fillStyle = '#0a0d14';
    ctx.fillRect(0, 0, w, h);

    // Draw reference camera background
    ctx.fillStyle = '#161c28';
    ctx.fillRect(0, 0, w, 150);
    ctx.strokeStyle = '#2d3e5e';
    ctx.strokeRect(200, 20, 240, 130);
    ctx.fillStyle = '#8a9bb8';
    ctx.font = '12px "Inter"';
    ctx.fillText('CAMERA VIEW: CAM-01 (MAIN GATE)', 20, 30);

    // Draw saved existing zones
    for (const z of this.activeZones) {
      try {
        const pts = JSON.parse(z.polygon_points_json);
        if (pts.length >= 3) {
          ctx.fillStyle = 'rgba(0, 240, 255, 0.15)';
          ctx.strokeStyle = '#00f0ff';
          ctx.beginPath();
          ctx.moveTo(pts[0][0] * w, pts[0][1] * h);
          for (let i = 1; i < pts.length; i++) {
            ctx.lineTo(pts[i][0] * w, pts[i][1] * h);
          }
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
        }
      } catch (e) {}
    }

    // Draw actively created polygon points
    if (this.currentPoints.length > 0) {
      ctx.fillStyle = 'rgba(255, 43, 86, 0.25)';
      ctx.strokeStyle = '#ff2b56';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(this.currentPoints[0][0] * w, this.currentPoints[0][1] * h);
      for (let i = 1; i < this.currentPoints.length; i++) {
        ctx.lineTo(this.currentPoints[i][0] * w, this.currentPoints[i][1] * h);
      }
      if (this.currentPoints.length >= 3) {
        ctx.closePath();
        ctx.fill();
      }
      ctx.stroke();

      // Vertex dots
      ctx.fillStyle = '#ff2b56';
      for (const pt of this.currentPoints) {
        ctx.beginPath();
        ctx.arc(pt[0] * w, pt[1] * h, 5, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }
}

window.zonesEditor = new ZonesEditor();
