/**
 * Main Police Command Application Orchestrator & State Manager
 */

class PoliceApp {
  constructor() {
    this.currentTab = 'dashboard';
    this.incidents = [];
    this.auditLogs = [];
    this.refreshInterval = null;
  }

  async init() {
    this.setupNavigation();
    this.setupAuthUI();
    this.startClock();
    
    const token = API.getToken();
    if (token) {
      this.showApp();
      await this.loadInitialData();
      window.alertWS.connect();
    } else {
      this.showLogin();
    }

    // Event Listeners
    window.addEventListener('auth:unauthorized', () => this.showLogin());
    window.addEventListener('incident:created', () => {
      this.refreshData();
    });

    // Auto-refresh every 5 seconds
    this.refreshInterval = setInterval(() => {
      if (API.getToken()) {
        this.refreshData(false);
      }
    }, 5000);
  }

  startClock() {
    const clockEl = document.getElementById('system-clock');
    const update = () => {
      const now = new Date();
      if (clockEl) {
        clockEl.innerText = now.toUTCString().replace('GMT', 'UTC');
      }
    };
    update();
    setInterval(update, 1000);
  }

  setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const tab = item.getAttribute('data-tab');
        this.switchTab(tab);
      });
    });
  }

  switchTab(tabName) {
    this.currentTab = tabName;
    document.querySelectorAll('.nav-item').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-tab') === tabName);
    });

    document.querySelectorAll('.tab-pane').forEach(el => {
      el.classList.toggle('active', el.id === `tab-${tabName}`);
    });

    if (tabName === 'dashboard' || tabName === 'live') {
      window.liveMonitor.init();
    } else if (tabName === 'user-cam') {
      this.initIntegratedUserCamera();
    } else if (tabName === 'zones') {
      window.zonesEditor.init();
    } else if (tabName === 'incidents' || tabName === 'evidence') {
      this.loadIncidents();
    } else if (tabName === 'audit') {
      this.loadAuditLogs();
    } else if (tabName === 'system') {
      this.loadPqcInfo();
    }
  }

  setupAuthUI() {
    // 3-Role Tab Selector (Admin, Police, Citizen User)
    const btnAdmin = document.getElementById('role-tab-admin');
    const btnPolice = document.getElementById('role-tab-police');
    const btnUser = document.getElementById('role-tab-user');
    const usernameInput = document.getElementById('login-username');
    const passwordInput = document.getElementById('login-password');
    const roleHint = document.getElementById('role-hint');

    const setRole = (role) => {
      [btnAdmin, btnPolice, btnUser].forEach(b => b && b.classList.remove('active'));
      if (role === 'admin') {
        if (btnAdmin) btnAdmin.classList.add('active');
        if (usernameInput) usernameInput.value = 'admin';
        if (passwordInput) passwordInput.value = 'PoliceSecure2026!';
        if (roleHint) roleHint.innerText = 'Role: HQ Administrator (Full Access)';
      } else if (role === 'police') {
        if (btnPolice) btnPolice.classList.add('active');
        if (usernameInput) usernameInput.value = 'officer';
        if (passwordInput) passwordInput.value = 'OfficerPass2026!';
        if (roleHint) roleHint.innerText = 'Role: Police Officer (Surveillance & Vault)';
      } else if (role === 'user') {
        if (btnUser) btnUser.classList.add('active');
        if (usernameInput) usernameInput.value = 'user';
        if (passwordInput) passwordInput.value = 'UserSecure2026!';
        if (roleHint) roleHint.innerText = 'Role: Citizen / Store Camera Node';
      }
    };

    if (btnAdmin) btnAdmin.onclick = () => setRole('admin');
    if (btnPolice) btnPolice.onclick = () => setRole('police');
    if (btnUser) btnUser.onclick = () => setRole('user');

    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.onsubmit = async (e) => {
        e.preventDefault();
        const u = document.getElementById('login-username').value;
        const p = document.getElementById('login-password').value;
        const errBox = document.getElementById('login-error-msg');
        errBox.style.display = 'none';

        try {
          const authData = await API.login(u, p);
          this.showApp();
          await this.loadInitialData();
          window.alertWS.connect();
        } catch (err) {
          errBox.innerText = `Login failed: ${err.message}`;
          errBox.style.display = 'block';
        }
      };
    }

    const logoutBtn = document.getElementById('btn-logout');
    if (logoutBtn) {
      logoutBtn.onclick = async () => {
        await API.logout();
        this.showLogin();
      };
    }
  }

  showLogin() {
    document.getElementById('login-screen').style.display = 'flex';
    document.getElementById('app-screen').style.display = 'none';
  }

  showApp() {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('app-screen').style.display = 'flex';

    const user = API.getUserInfo();
    const nameEl = document.getElementById('header-user-name');
    const roleEl = document.getElementById('header-user-role');
    if (nameEl) nameEl.innerText = user.full_name || 'Officer';
    if (roleEl) roleEl.innerText = `${(user.role || 'Officer').toUpperCase()} [${user.badge_number || '001'}]`;

    this.switchTab('dashboard');
  }

  async loadInitialData() {
    await Promise.all([
      this.loadStats(),
      this.loadIncidents(),
      this.loadAuditLogs()
    ]);
  }

  async refreshData(showSpinner = false) {
    await this.loadStats();
    if (this.currentTab === 'incidents' || this.currentTab === 'dashboard' || this.currentTab === 'evidence') {
      await this.loadIncidents();
    }
    if (this.currentTab === 'audit') {
      await this.loadAuditLogs();
    }
  }

  async loadStats() {
    try {
      const stats = await API.getStats();
      document.getElementById('stat-total-incidents').innerText = stats.total_incidents;
      document.getElementById('stat-critical-alerts').innerText = stats.critical_alerts;
      document.getElementById('stat-weapons-detected').innerText = stats.weapons_detected;
      document.getElementById('stat-violence-alerts').innerText = stats.violence_alerts;
      document.getElementById('stat-intrusion-alerts').innerText = stats.intrusion_alerts;
      document.getElementById('stat-evidence-files').innerText = stats.evidence_files;
    } catch (e) {
      console.warn('Stats fetch error:', e);
    }
  }

  async loadIncidents(filterType = '') {
    try {
      const params = filterType ? { detection_type: filterType } : {};
      this.incidents = await API.getIncidents(params);
      this.renderIncidentsTable(this.incidents);
      this.renderRecentAlerts(this.incidents.slice(0, 5));

      // Auto-select first incident in Evidence Vault if not selected
      if (this.incidents.length > 0 && !window.evidenceVault.selectedIncidentId) {
        window.evidenceVault.selectIncident(this.incidents[0].incident_id);
      }
    } catch (e) {
      console.warn('Incidents fetch error:', e);
    }
  }

  renderIncidentsTable(incidents) {
    const tbody = document.getElementById('incidents-table-body');
    if (!tbody) return;

    if (incidents.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 24px;">No security incidents recorded. System secure.</td></tr>';
      return;
    }

    tbody.innerHTML = incidents.map(inc => `
      <tr>
        <td><strong>${inc.incident_id}</strong></td>
        <td>${inc.detection_type} (${inc.object_detected})</td>
        <td>
          <span class="badge ${inc.severity === 'CRITICAL' ? 'badge-critical' : 'badge-high'}">
            ${inc.severity}
          </span>
        </td>
        <td>${inc.camera_code} - ${inc.location}</td>
        <td>${inc.confidence}%</td>
        <td style="font-family: var(--font-mono); font-size: 11px;">${inc.created_at.replace('T', ' ').slice(0, 19)}</td>
        <td>
          <span class="badge ${inc.status === 'NEW' ? 'badge-critical' : inc.status === 'INVESTIGATING' ? 'badge-high' : 'badge-verified'}">
            ${inc.status}
          </span>
        </td>
        <td>
          <div style="display: flex; gap: 6px; align-items: center;">
            <button class="btn-action" onclick="window.app.viewEvidence('${inc.incident_id}')">
              Vault 🔐
            </button>
            <button class="btn-action" style="background: rgba(255, 77, 77, 0.15); border-color: var(--accent-red); color: var(--accent-red); font-size: 11px; padding: 4px 8px;" onclick="window.app.deleteIncident('${inc.incident_id}')" title="Delete incident">
              🗑️
            </button>
          </div>
        </td>
      </tr>
    `).join('');
  }

  renderRecentAlerts(incidents) {
    const container = document.getElementById('recent-alerts-list');
    if (!container) return;

    if (incidents.length === 0) {
      container.innerHTML = '<div style="color: var(--text-muted); font-size: 12px;">No active alerts.</div>';
      return;
    }

    container.innerHTML = incidents.map(inc => `
      <div style="padding: 10px 14px; background: rgba(18, 24, 38, 0.6); border-left: 3px solid ${inc.severity === 'CRITICAL' ? 'var(--accent-red)' : 'var(--accent-amber)'}; border-radius: 4px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
        <div>
          <div style="font-weight: 600; font-size: 13px; color: ${inc.severity === 'CRITICAL' ? 'var(--accent-red)' : 'var(--text-primary)'}">
            ${inc.detection_type.toUpperCase()}: ${inc.object_detected} [${inc.confidence}%]
          </div>
          <div style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">
            ${inc.camera_code} | ${inc.incident_id} | ${inc.created_at.slice(11, 19)}
          </div>
        </div>
        <button class="btn-action" style="padding: 3px 8px; font-size: 11px;" onclick="window.app.viewEvidence('${inc.incident_id}')">
          Inspect
        </button>
      </div>
    `).join('');
  }

  viewEvidence(incidentId) {
    this.switchTab('evidence');
    window.evidenceVault.selectIncident(incidentId);
  }

  async clearAllIncidents() {
    if (!confirm('Are you sure you want to permanently clear all incidents and encrypted evidence from Police Command?')) {
      return;
    }
    try {
      await API.clearPoliceIncidents();
      await this.refreshData(true);
    } catch (err) {
      alert(`Failed to clear incidents: ${err.message}`);
    }
  }

  async deleteIncident(incidentId) {
    if (!confirm(`Are you sure you want to delete incident ${incidentId}?`)) {
      return;
    }
    try {
      await API.clearPoliceIncidents(incidentId);
      await this.refreshData(true);
    } catch (err) {
      alert(`Failed to delete incident: ${err.message}`);
    }
  }

  async loadAuditLogs() {
    try {
      this.auditLogs = await API.getAuditLogs();
      const tbody = document.getElementById('audit-table-body');
      if (!tbody) return;

      tbody.innerHTML = this.auditLogs.map(log => `
        <tr>
          <td style="font-family: var(--font-mono); font-size: 11px; color: var(--text-secondary);">
            ${log.timestamp.replace('T', ' ').slice(0, 19)}
          </td>
          <td><strong>${log.username}</strong></td>
          <td><span class="badge badge-medium">${log.action}</span></td>
          <td>${log.incident_id || '—'}</td>
          <td style="font-size: 12px; color: var(--text-secondary);">${log.details || '—'}</td>
          <td style="font-family: var(--font-mono); font-size: 11px;">${log.ip_address}</td>
        </tr>
      `).join('');
    } catch (e) {
      console.warn('Audit logs fetch error:', e);
    }
  }

  async loadPqcInfo() {
    try {
      const info = await API.getPqcInfo();
      const cont = document.getElementById('pqc-info-container');
      if (!cont) return;

      cont.innerHTML = `
        <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 24px;">
          <h3 style="font-family: var(--font-display); font-size: 20px; margin-bottom: 14px; color: var(--accent-cyan);">
            Quantum-Safe Cryptographic Architecture
          </h3>
          <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 20px; line-height: 1.6;">
            The framework uses a hybrid post-quantum cryptographic scheme combining symmetric authenticated encryption with lattice-based key encapsulation.
          </p>
          <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; font-family: var(--font-mono); font-size: 12px;">
            <div style="background: rgba(13, 18, 29, 0.8); padding: 16px; border-radius: var(--radius-sm); border: 1px solid var(--border-color);">
              <h4 style="color: var(--accent-cyan); margin-bottom: 8px;">Key Encapsulation (PQC)</h4>
              <div>• Algorithm: ${info.key_encapsulation.name}</div>
              <div>• Standard: ${info.key_encapsulation.fips_standard}</div>
              <div>• Hardness: ${info.key_encapsulation.lattice_basis}</div>
              <div>• Quantum Attack: ${info.key_encapsulation.quantum_attack_resistance}</div>
            </div>
            <div style="background: rgba(13, 18, 29, 0.8); padding: 16px; border-radius: var(--radius-sm); border: 1px solid var(--border-color);">
              <h4 style="color: var(--accent-purple); margin-bottom: 8px;">Symmetric Encryption</h4>
              <div>• Cipher: ${info.symmetric_cipher.name}</div>
              <div>• Key Size: ${info.symmetric_cipher.key_size_bits}-bit</div>
              <div>• Auth Tag: ${info.symmetric_cipher.tag_size_bits}-bit GCM</div>
              <div>• Nonce: ${info.symmetric_cipher.nonce_size_bits}-bit CSPRNG</div>
            </div>
          </div>
        </div>
      `;
    } catch (e) {
      console.warn('PQC info fetch error:', e);
    }
  }

  initIntegratedUserCamera() {
    const canvas = document.getElementById('integrated-user-canvas');
    const video = document.getElementById('integrated-webcam-video');
    const sourceSelect = document.getElementById('integrated-user-cam-source');
    const fileInput = document.getElementById('integrated-video-file-input');
    const uploadBtn = document.getElementById('btn-integrated-upload-video');
    const filenameSpan = document.getElementById('integrated-video-filename');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let simTime = 0;
    let simulatedWeapon = null;
    let lastAutoDispatch = 0;
    let lastBuzzerTime = 0;
    let stream = null;
    let source = sourceSelect ? sourceSelect.value : 'demo';
    let hasLoadedFile = false;
    let serverDetections = [];
    let isRequesting = false;

    const startWebcam = async () => {
      try {
        hasLoadedFile = false;
        if (video && video.src) video.src = '';
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 360 }, audio: false });
          if (video) {
            video.srcObject = stream;
            await video.play();
          }
        }
      } catch (e) {
        console.warn('Webcam access error:', e);
      }
    };

    const loadVideoFile = (file) => {
      if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
      source = 'file';
      hasLoadedFile = true;
      if (sourceSelect) sourceSelect.value = 'file';
      if (uploadBtn) uploadBtn.style.display = 'inline-block';
      if (video) {
        if (video.src && video.src.startsWith('blob:')) {
          try { URL.revokeObjectURL(video.src); } catch (e) {}
        }
        video.srcObject = null;
        video.src = URL.createObjectURL(file);
        video.loop = true;
        video.muted = true;
        video.playsInline = true;
        video.autoplay = true;
        video.currentTime = 0;
        video.load();

        const tryPlay = () => {
          const p = video.play();
          if (p !== undefined) {
            p.catch(e => console.warn('Video auto-play waiting:', e));
          }
        };

        video.onloadeddata = tryPlay;
        video.oncanplay = tryPlay;
        tryPlay();
      }
    };

    if (uploadBtn && fileInput) {
      uploadBtn.onclick = () => fileInput.click();
    }

    if (fileInput) {
      fileInput.onchange = (e) => {
        const file = e.target.files && e.target.files[0];
        if (file) {
          loadVideoFile(file);
          if (filenameSpan) {
            filenameSpan.innerText = file.name;
            filenameSpan.style.display = 'inline-block';
          }
        }
      };
    }

    if (sourceSelect) {
      sourceSelect.onchange = () => {
        source = sourceSelect.value;
        if (source === 'webcam') {
          if (uploadBtn) uploadBtn.style.display = 'none';
          if (filenameSpan) filenameSpan.style.display = 'none';
          if (video && video.src) video.src = '';
          startWebcam();
        } else if (source === 'file') {
          if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
          if (uploadBtn) uploadBtn.style.display = 'inline-block';
          if (fileInput && (!video || !video.src || video.src.length === 0)) {
            fileInput.click();
          }
        } else {
          if (uploadBtn) uploadBtn.style.display = 'none';
          if (filenameSpan) filenameSpan.style.display = 'none';
          if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
          if (video && video.src) video.src = '';
        }
      };
    }
    if (source === 'webcam') startWebcam();

    // Fast AI Inference Timer (4 times per sec)
    setInterval(async () => {
      const isVideoActive = source === 'webcam'
        ? (video && video.readyState >= 2)
        : (video && video.src && video.src.length > 5 && !video.paused && video.currentTime > 0.1 && video.readyState >= 2);

      if (this.currentTab === 'user-cam' && isVideoActive && !isRequesting && !simulatedWeapon) {
        try {
          isRequesting = true;
          const tempCanvas = document.createElement('canvas');
          tempCanvas.width = 480;
          tempCanvas.height = 270;
          const tctx = tempCanvas.getContext('2d');
          tctx.drawImage(video, 0, 0, 480, 270);
          const frameB64 = tempCanvas.toDataURL('image/jpeg', 0.6);

          const aiResult = await API.request('/user/detect-frame', {
            method: 'POST',
            body: JSON.stringify({ image_b64: frameB64 })
          });

          if (aiResult && aiResult.detections) {
            serverDetections = aiResult.detections.map(d => {
              const [nx1, ny1, nx2, ny2] = d.normalized_bbox || [0,0,0,0];
              return { ...d, bbox: [nx1 * 640, ny1 * 360, nx2 * 640, ny2 * 360] };
            });
          }
        } catch (e) {
        } finally {
          isRequesting = false;
        }
      }
    }, 220);

    const triggerSim = (type, obj, conf) => {
      this.playSecurityBuzzer();
      simulatedWeapon = { type, obj, conf };
      setTimeout(() => { simulatedWeapon = null; }, 7000);
    };

    const testBuzzerBtn = document.getElementById('btn-integrated-test-buzzer');
    if (testBuzzerBtn) {
      testBuzzerBtn.onclick = () => {
        this.playSecurityBuzzer();
      };
    }

    const simKnifeBtn = document.getElementById('btn-integrated-sim-knife') || document.getElementById('btn-integrated-sim-weapon');
    const simScissorsBtn = document.getElementById('btn-integrated-sim-scissors');
    const simFireBtn = document.getElementById('btn-integrated-sim-fire');
    const simGunBtn = document.getElementById('btn-integrated-sim-gun');

    if (simKnifeBtn) simKnifeBtn.onclick = () => triggerSim('Weapon', 'Knife (Blade)', 92.5);
    if (simScissorsBtn) simScissorsBtn.onclick = () => triggerSim('Weapon', 'Scissors (Sharp Edge)', 88.0);
    if (simFireBtn) simFireBtn.onclick = () => triggerSim('Hazard', 'Fire / Flame', 95.0);
    if (simGunBtn) simGunBtn.onclick = () => triggerSim('Weapon', 'Gun (Handgun)', 96.0);

    const sosBtn = document.getElementById('btn-integrated-panic-sos');
    if (sosBtn) {
      sosBtn.onclick = () => {
        this.dispatchEmergencyFromUserCamera('Weapon', 'Armed Robbery Emergency', 99.0);
      };
    }

    const loop = () => {
      requestAnimationFrame(loop);
      if (this.currentTab !== 'user-cam') return;
      simTime += 0.03;
      const w = canvas.width;
      const h = canvas.height;

      // Draw Feed
      if (source === 'file') {
        if (!hasLoadedFile) {
          ctx.fillStyle = '#0a0e17';
          ctx.fillRect(0, 0, w, h);
          ctx.strokeStyle = '#00f0ff';
          ctx.lineWidth = 1;
          ctx.strokeRect(40, 40, w - 80, h - 80);
          ctx.fillStyle = '#00f0ff';
          ctx.font = 'bold 14px "Inter", sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText('📁 PLEASE CLICK "CHOOSE FILE" TO LOAD AN MP4 SURVEILLANCE VIDEO', w / 2, h / 2 - 10);
          ctx.font = '11px "JetBrains Mono", monospace';
          ctx.fillStyle = '#8a9bb8';
          ctx.fillText('Select any video from sample_videos/ folder', w / 2, h / 2 + 18);
          ctx.textAlign = 'start';
          const hudEl = document.getElementById('integrated-hud-status');
          if (hudEl) hudEl.innerHTML = '<span style="color: var(--accent-cyan);">● WAITING FOR VIDEO SELECTION...</span>';
          return;
        }

        let drawn = false;
        if (video) {
          if (video.paused) { video.play().catch(() => {}); }
          try {
            ctx.drawImage(video, 0, 0, w, h);
            drawn = true;
          } catch (e) {
            drawn = false;
          }
        }

        if (!drawn) {
          ctx.fillStyle = '#0a0e17';
          ctx.fillRect(0, 0, w, h);
          ctx.fillStyle = '#00f0ff';
          ctx.font = '13px "Inter", sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText('⚡ LOADING SURVEILLANCE VIDEO...', w / 2, h / 2);
          ctx.textAlign = 'start';
        }
      } else if (source === 'webcam' && video && (video.readyState >= 1 || video.currentTime > 0)) {
        if (video.paused) { video.play().catch(() => {}); }
        try {
          ctx.drawImage(video, 0, 0, w, h);
        } catch (e) {}
      } else {
        // Store Interior Scene
        ctx.fillStyle = '#111722';
        ctx.fillRect(0, 0, w, 160);
        ctx.fillStyle = '#0a0e17';
        ctx.fillRect(0, 160, w, h - 160);

        ctx.fillStyle = '#1a2334';
        ctx.fillRect(80, 180, 180, 120);
        ctx.strokeStyle = '#00f0ff';
        ctx.strokeRect(80, 180, 180, 120);
        ctx.fillStyle = '#8a9bb8';
        ctx.font = '11px "JetBrains Mono"';
        ctx.fillText('[VAULT COUNTER #1]', 90, 200);

        ctx.fillStyle = '#1a2334';
        ctx.fillRect(380, 180, 180, 120);
        ctx.strokeStyle = '#00f0ff';
        ctx.strokeRect(380, 180, 180, 120);
        ctx.fillText('[VAULT COUNTER #2]', 390, 200);

        const px = 180 + Math.sin(simTime * 2) * 80;
        const py = 120;
        ctx.fillStyle = '#8a9bb8';
        ctx.beginPath();
        ctx.arc(px + 20, py - 30, 12, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#2d3e5e';
        ctx.fillRect(px + 10, py - 18, 20, 45);
      }

      let activeThreat = null;

      if (simulatedWeapon) {
        activeThreat = { detection_type: simulatedWeapon.type, object_detected: simulatedWeapon.obj, confidence: simulatedWeapon.conf };
        const icon = simulatedWeapon.obj.includes('Knife') ? '🔪' : simulatedWeapon.obj.includes('Scissors') ? '✂️' : simulatedWeapon.obj.includes('Fire') ? '🔥' : '🔫';
        ctx.strokeStyle = '#ff2b56';
        ctx.lineWidth = 3;
        ctx.strokeRect(240, 120, 160, 180);
        ctx.fillStyle = '#ff2b56';
        ctx.fillRect(240, 96, 180, 24);
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 11px "Inter", sans-serif';
        ctx.fillText(`${icon} ${simulatedWeapon.obj.toUpperCase()} [${simulatedWeapon.conf}%]`, 246, 113);
      } else if (serverDetections.length > 0) {
        for (const d of serverDetections) {
          const [x1, y1, x2, y2] = d.bbox || [0, 0, 0, 0];
          const isWeapon = d.is_weapon;
          const color = isWeapon ? '#ff2b56' : '#00e676';
          const icon = d.class_name.toLowerCase().includes('knife') ? '🔪' :
                       d.class_name.toLowerCase().includes('scissors') ? '✂️' :
                       d.class_name.toLowerCase().includes('fire') ? '🔥' :
                       d.class_name.toLowerCase().includes('gun') ? '🔫' :
                       (d.class_name.toLowerCase().includes('stick') || d.class_name.toLowerCase().includes('bat') || d.class_name.toLowerCase().includes('kattai')) ? '🏏' :
                       d.class_name.toLowerCase().includes('assault') ? '🥊' : '👤';

          ctx.strokeStyle = color;
          ctx.lineWidth = isWeapon ? 3 : 2;
          ctx.strokeRect(x1, y1, Math.max(20, x2 - x1), Math.max(20, y2 - y1));

          ctx.fillStyle = color;
          ctx.fillRect(x1, Math.max(0, y1 - 22), Math.max(160, x2 - x1), 22);
          ctx.fillStyle = '#fff';
          ctx.font = 'bold 11px "Inter", sans-serif';
          ctx.fillText(`${icon} ${d.class_name.toUpperCase()} [${d.confidence}%]`, x1 + 5, Math.max(14, y1 - 6));

          if (isWeapon && !activeThreat) {
            activeThreat = {
              detection_type: d.detection_type || 'Weapon',
              object_detected: d.class_name,
              confidence: d.confidence
            };
          }
        }
      }

      const hudEl = document.getElementById('integrated-hud-status');
      if (activeThreat) {
        const icon = activeThreat.object_detected.toLowerCase().includes('knife') ? '🔪' : 
                     activeThreat.object_detected.toLowerCase().includes('scissors') ? '✂️' : 
                     activeThreat.object_detected.toLowerCase().includes('fire') ? '🔥' : 
                     activeThreat.object_detected.toLowerCase().includes('gun') ? '🔫' :
                     (activeThreat.object_detected.toLowerCase().includes('stick') || activeThreat.object_detected.toLowerCase().includes('bat') || activeThreat.object_detected.toLowerCase().includes('kattai')) ? '🏏' :
                     activeThreat.object_detected.toLowerCase().includes('assault') ? '🥊' : '🚨';
        if (hudEl) hudEl.innerHTML = `<strong style="color: var(--accent-red); animation: pulse-red 0.8s infinite;">🔴 WEAPON DETECTED: ${icon} ${activeThreat.object_detected.toUpperCase()} [${activeThreat.confidence}%]</strong>`;

        const now = Date.now();
        if (now - lastBuzzerTime > 1200) {
          lastBuzzerTime = now;
          this.playSecurityBuzzer();
        }

        if (now - lastAutoDispatch > 4000) {
          lastAutoDispatch = now;
          this.dispatchEmergencyFromUserCamera(activeThreat.detection_type, activeThreat.object_detected, activeThreat.confidence);
        }
      } else {
        if (hudEl) hudEl.innerHTML = '<span style="color: var(--accent-green);">● STATUS: ALL SECURE — WEAPON SCANNER ONLINE</span>';
      }
    };

    loop();
  }

  captureVideoClipBlob() {
    return new Promise((resolve) => {
      let settled = false;
      const finish = (result) => {
        if (!settled) {
          settled = true;
          resolve(result);
        }
      };

      const safetyTimer = setTimeout(() => finish(null), 1500);

      try {
        const canvas = document.getElementById('integrated-user-canvas');
        if (!canvas) {
          clearTimeout(safetyTimer);
          return finish(null);
        }
        const stream = canvas.captureStream(15);
        let mimeType = 'video/webm';
        if (MediaRecorder.isTypeSupported('video/webm;codecs=vp8,opus')) {
          mimeType = 'video/webm;codecs=vp8,opus';
        } else if (MediaRecorder.isTypeSupported('video/webm')) {
          mimeType = 'video/webm';
        } else if (MediaRecorder.isTypeSupported('video/mp4')) {
          mimeType = 'video/mp4';
        }

        const recorder = new MediaRecorder(stream, { mimeType });
        const chunks = [];
        recorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) chunks.push(e.data);
        };
        recorder.onerror = () => {
          clearTimeout(safetyTimer);
          finish(null);
        };
        recorder.onstop = () => {
          clearTimeout(safetyTimer);
          try {
            const blob = new Blob(chunks, { type: mimeType });
            finish(blob);
          } catch (e) {
            finish(null);
          }
        };
        recorder.start();
        setTimeout(() => {
          try {
            if (recorder.state === 'recording') recorder.stop();
            else finish(null);
          } catch (e) {
            finish(null);
          }
        }, 1000);
      } catch (e) {
        clearTimeout(safetyTimer);
        finish(null);
      }
    });
  }

  playSecurityBuzzer() {
    try {
      const audioEl = document.getElementById('security-buzzer-audio-hq');
      if (audioEl) {
        audioEl.currentTime = 0;
        audioEl.volume = 1.0;
        const p = audioEl.play();
        if (p !== undefined) {
          p.catch(() => {
            if (window.alertWS && window.alertWS.playCriticalAlertSound) {
              window.alertWS.playCriticalAlertSound();
            }
          });
        }
        return;
      }
    } catch (e) {}

    try {
      if (window.alertWS && window.alertWS.playCriticalAlertSound) {
        window.alertWS.playCriticalAlertSound();
      }
    } catch (e) {}
  }

  async dispatchEmergencyFromUserCamera(type, obj, conf) {
    const randSuffix = Math.floor(1000 + Math.random() * 9000);
    const incId = `INC-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${randSuffix}`;
    const banner = document.getElementById('integrated-user-dispatch-banner');
    if (banner) {
      document.getElementById('integrated-user-banner-title').innerText = 
        `🔴 WEAPON DETECTED (${obj.toUpperCase()}) — RECORDING & DISPATCHING TO POLICE HQ!`;
      document.getElementById('integrated-user-banner-meta').innerText = 
        `Incident: ${incId} | Encrypted with AES-256-GCM + NIST FIPS 203 ML-KEM-768`;
      banner.style.display = 'flex';
    }

    try {
      const videoBlob = await this.captureVideoClipBlob();

      const formData = new FormData();
      formData.append('incident_id', incId);
      formData.append('detection_type', type);
      formData.append('object_detected', obj);
      formData.append('confidence', conf);

      if (videoBlob && videoBlob.size > 0) {
        formData.append('file', videoBlob, `${incId}.webm`);
      }

      await API.request('/user/dispatch-emergency', {
        method: 'POST',
        body: formData
      });
    } catch (e) {
      console.warn('Dispatch error:', e);
    } finally {
      this.refreshData();
    }
  }
}

window.app = new PoliceApp();
document.addEventListener('DOMContentLoaded', () => window.app.init());
