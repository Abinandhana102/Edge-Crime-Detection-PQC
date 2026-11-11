/**
 * User & Store Camera Security Portal Client
 * Handles webcam stream, real-time weapon detection, automatic post-quantum encryption,
 * and dispatching to Police Command HQ.
 */

class UserPortal {
  constructor() {
    this.source = 'webcam';
    this.videoEl = null;
    this.canvas = null;
    this.ctx = null;
    this.stream = null;
    this.hasLoadedFile = false;
    this.isDetecting = true;
    this.isDispatching = false;
    this.lastDispatchTime = 0;
    this.lastBuzzerTime = 0;
    this.audioCtx = null;
    this.simulatedWeapon = false;
    this.simulatedWeaponTimeout = null;
    this.simTime = 0;
  }

  async init() {
    this.setupAuthUI();
    
    const token = API.getToken();
    const userInfo = API.getUserInfo();

    if (token && userInfo.username) {
      this.showPortal(userInfo);
    } else {
      this.showAuthScreen();
    }
  }

  setupAuthUI() {
    // Tab switching Login vs Register
    const loginTabBtn = document.getElementById('tab-btn-user-login');
    const regTabBtn = document.getElementById('tab-btn-user-register');
    const loginForm = document.getElementById('user-login-form');
    const regForm = document.getElementById('user-register-form');
    const errBox = document.getElementById('user-auth-error');

    if (loginTabBtn && regTabBtn) {
      loginTabBtn.onclick = () => {
        loginTabBtn.classList.add('active');
        regTabBtn.classList.remove('active');
        loginForm.style.display = 'block';
        regForm.style.display = 'none';
        errBox.style.display = 'none';
      };

      regTabBtn.onclick = () => {
        regTabBtn.classList.add('active');
        loginTabBtn.classList.remove('active');
        loginForm.style.display = 'none';
        regForm.style.display = 'block';
        errBox.style.display = 'none';
      };
    }

    // Login Submission
    if (loginForm) {
      loginForm.onsubmit = async (e) => {
        e.preventDefault();
        const u = document.getElementById('u-login-username').value;
        const p = document.getElementById('u-login-password').value;
        errBox.style.display = 'none';

        try {
          const authData = await API.login(u, p);
          this.showPortal(authData);
        } catch (err) {
          errBox.innerText = `Login failed: ${err.message}`;
          errBox.style.display = 'block';
        }
      };
    }

    // Register Submission
    if (regForm) {
      regForm.onsubmit = async (e) => {
        e.preventDefault();
        const fullname = document.getElementById('u-reg-fullname').value;
        const org = document.getElementById('u-reg-org').value;
        const loc = document.getElementById('u-reg-location').value;
        const u = document.getElementById('u-reg-username').value;
        const p = document.getElementById('u-reg-password').value;
        errBox.style.display = 'none';

        try {
          const regRes = await API.request(`/user/register?organization=${encodeURIComponent(org)}&location_address=${encodeURIComponent(loc)}`, {
            method: 'POST',
            body: JSON.stringify({
              username: u,
              badge_number: `USR-${Date.now().toString().slice(-4)}`,
              full_name: fullname,
              role: 'citizen',
              password: p
            })
          });

          // Auto-login after registration
          const authData = await API.login(u, p);
          this.showPortal(authData);
        } catch (err) {
          errBox.innerText = `Registration failed: ${err.message}`;
          errBox.style.display = 'block';
        }
      };
    }

    // Logout
    const logoutBtn = document.getElementById('btn-user-logout');
    if (logoutBtn) {
      logoutBtn.onclick = async () => {
        await API.logout();
        this.stopCamera();
        this.showAuthScreen();
      };
    }
  }

  showAuthScreen() {
    document.getElementById('user-auth-screen').style.display = 'flex';
    document.getElementById('user-portal-app').style.display = 'none';
  }

  showPortal(userInfo) {
    document.getElementById('user-auth-screen').style.display = 'none';
    document.getElementById('user-portal-app').style.display = 'flex';

    // Populate user details
    const orgEl = document.getElementById('user-org-display');
    const nameEl = document.getElementById('user-fullname-display');
    const addrEl = document.getElementById('user-address-display');

    if (orgEl) orgEl.innerText = userInfo.organization || 'Store & Property Security Node';
    if (nameEl) nameEl.innerText = userInfo.full_name || userInfo.username;
    if (addrEl) addrEl.innerText = userInfo.location_address || 'Registered Facility';

    this.initCamera();
    this.setupCameraControls();
    this.loadUserIncidents();

    // Auto-refresh Incident History Log every 3 seconds so history table dynamically updates in real-time
    if (this.historyPollInterval) clearInterval(this.historyPollInterval);
    this.historyPollInterval = setInterval(() => {
      this.loadUserIncidents();
    }, 3000);
  }

  async initCamera() {
    this.videoEl = document.getElementById('user-webcam-video');
    this.canvas = document.getElementById('user-camera-canvas');
    if (this.canvas) {
      this.ctx = this.canvas.getContext('2d');
    }

    const sourceSelect = document.getElementById('user-cam-source-select');
    const fileInput = document.getElementById('user-video-file-input');
    const uploadBtn = document.getElementById('btn-user-upload-video');
    const filenameSpan = document.getElementById('user-video-filename');

    if (uploadBtn && fileInput) {
      uploadBtn.onclick = () => fileInput.click();
    }

    if (fileInput) {
      fileInput.onchange = (e) => {
        const file = e.target.files && e.target.files[0];
        if (file) {
          this.loadVideoFile(file);
          if (filenameSpan) {
            filenameSpan.innerText = file.name;
            filenameSpan.style.display = 'inline-block';
          }
        }
      };
    }

    if (sourceSelect) {
      this.source = sourceSelect.value;
      sourceSelect.onchange = () => {
        this.source = sourceSelect.value;
        if (this.source === 'webcam') {
          if (uploadBtn) uploadBtn.style.display = 'none';
          if (filenameSpan) filenameSpan.style.display = 'none';
          this.startWebcam();
        } else if (this.source === 'file') {
          this.stopWebcam();
          if (uploadBtn) uploadBtn.style.display = 'inline-block';
          if (fileInput && (!this.videoEl || !this.videoEl.src || this.videoEl.src.length === 0)) {
            fileInput.click();
          }
        } else {
          if (uploadBtn) uploadBtn.style.display = 'none';
          if (filenameSpan) filenameSpan.style.display = 'none';
          this.stopWebcam();
        }
      };
    }

    if (this.source === 'webcam') {
      await this.startWebcam();
    }

    this.startDetectionLoop();
  }

  loadVideoFile(file) {
    this.stopWebcam();
    this.source = 'file';
    this.hasLoadedFile = true;
    const sourceSelect = document.getElementById('user-cam-source-select');
    if (sourceSelect) sourceSelect.value = 'file';

    const uploadBtn = document.getElementById('btn-user-upload-video');
    if (uploadBtn) uploadBtn.style.display = 'inline-block';

    if (this.videoEl) {
      if (this.videoEl.src && this.videoEl.src.startsWith('blob:')) {
        try { URL.revokeObjectURL(this.videoEl.src); } catch (e) {}
      }
      this.videoEl.srcObject = null;
      this.videoEl.src = URL.createObjectURL(file);
      this.videoEl.loop = true;
      this.videoEl.muted = true;
      this.videoEl.playsInline = true;
      this.videoEl.autoplay = true;
      this.videoEl.currentTime = 0;
      this.videoEl.load();

      const tryPlay = () => {
        const p = this.videoEl.play();
        if (p !== undefined) {
          p.catch(err => console.warn('Video auto-play waiting:', err));
        }
      };

      this.videoEl.onloadeddata = tryPlay;
      this.videoEl.oncanplay = tryPlay;
      tryPlay();
    }

    if (!this.isLoopRunning) {
      this.startDetectionLoop();
    }
  }

  async startWebcam() {
    try {
      if (this.videoEl && this.videoEl.src) {
        this.videoEl.src = '';
      }
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        this.stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 360 },
          audio: false
        });
        if (this.videoEl) {
          this.videoEl.srcObject = this.stream;
          await this.videoEl.play();
        }
      }
    } catch (err) {
      console.warn('Physical webcam unavailable, using demo mode:', err);
      const sourceSelect = document.getElementById('user-cam-source-select');
      if (sourceSelect) sourceSelect.value = 'demo';
      this.source = 'demo';
    }
  }

  stopWebcam() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
  }

  stopCamera() {
    this.stopWebcam();
    this.isDetecting = false;
  }

  initAudio() {
    if (!this.audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        this.audioCtx = new AudioContext();
      }
    }
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
  }

  playSecurityBuzzer() {
    try {
      const audioEl = document.getElementById('security-buzzer-audio');
      if (audioEl) {
        audioEl.currentTime = 0;
        audioEl.volume = 1.0;
        const p = audioEl.play();
        if (p !== undefined) {
          p.catch(() => this.playSynthesizedBuzzer());
        }
        return;
      }
    } catch (e) {}

    this.playSynthesizedBuzzer();
  }

  playSynthesizedBuzzer() {
    try {
      this.initAudio();
      if (!this.audioCtx) return;

      const now = this.audioCtx.currentTime;

      // Pulse 1: Urgent 880Hz security buzzer beep
      const osc1 = this.audioCtx.createOscillator();
      const gain1 = this.audioCtx.createGain();
      osc1.type = 'sawtooth';
      osc1.frequency.setValueAtTime(880, now);
      osc1.frequency.exponentialRampToValueAtTime(700, now + 0.16);

      gain1.gain.setValueAtTime(0.4, now);
      gain1.gain.exponentialRampToValueAtTime(0.01, now + 0.16);

      osc1.connect(gain1);
      gain1.connect(this.audioCtx.destination);
      osc1.start(now);
      osc1.stop(now + 0.16);

      // Pulse 2: Higher 980Hz security buzzer beep
      const osc2 = this.audioCtx.createOscillator();
      const gain2 = this.audioCtx.createGain();
      osc2.type = 'sawtooth';
      osc2.frequency.setValueAtTime(980, now + 0.20);
      osc2.frequency.exponentialRampToValueAtTime(760, now + 0.38);

      gain2.gain.setValueAtTime(0.4, now + 0.20);
      gain2.gain.exponentialRampToValueAtTime(0.01, now + 0.38);

      osc2.connect(gain2);
      gain2.connect(this.audioCtx.destination);
      osc2.start(now + 0.20);
      osc2.stop(now + 0.38);
    } catch (e) {
      console.warn('Audio buzzer play prevented:', e);
    }
  }

  setupCameraControls() {
    // Unlock audio on first user gesture
    const unlockAudio = () => {
      const audioEl = document.getElementById('security-buzzer-audio');
      if (audioEl) {
        audioEl.volume = 0.01;
        audioEl.play().then(() => {
          audioEl.pause();
          audioEl.currentTime = 0;
          audioEl.volume = 1.0;
        }).catch(() => {});
      }
      this.initAudio();
    };
    document.addEventListener('click', unlockAudio, { once: true });
    document.addEventListener('keydown', unlockAudio, { once: true });

    // Test Buzzer Button
    const testBuzzerBtn = document.getElementById('btn-user-test-buzzer');
    if (testBuzzerBtn) {
      testBuzzerBtn.onclick = () => {
        this.playSecurityBuzzer();
      };
    }

    // Simulate Knife / Gun / Scissors / Fire buttons
    const simKnifeBtn = document.getElementById('btn-user-sim-knife') || document.getElementById('btn-user-simulate-weapon');
    const simGunBtn = document.getElementById('btn-user-sim-gun');
    const simScissorsBtn = document.getElementById('btn-user-sim-scissors');
    const simFireBtn = document.getElementById('btn-user-sim-fire');

    const triggerSim = (type, obj, conf) => {
      this.playSecurityBuzzer();
      this.simulatedWeapon = {
        detection_type: type,
        object_detected: obj,
        confidence: conf
      };
      clearTimeout(this.simulatedWeaponTimeout);
      this.simulatedWeaponTimeout = setTimeout(() => {
        this.simulatedWeapon = null;
      }, 7000);
    };

    if (simKnifeBtn) simKnifeBtn.onclick = () => triggerSim('Weapon', 'Knife (Blade)', 92.5);
    if (simGunBtn) simGunBtn.onclick = () => triggerSim('Weapon', 'Gun (Handgun)', 96.0);
    if (simScissorsBtn) simScissorsBtn.onclick = () => triggerSim('Weapon', 'Scissors (Sharp Edge)', 88.0);
    if (simFireBtn) simFireBtn.onclick = () => triggerSim('Hazard', 'Fire / Flame', 95.0);

    // Manual Panic SOS Button
    const sosBtn = document.getElementById('btn-user-manual-sos');
    if (sosBtn) {
      sosBtn.onclick = () => {
        this.triggerEmergencyDispatch({
          detection_type: 'Weapon',
          object_detected: 'Panic SOS: Armed Intruder',
          confidence: 99.0
        });
      };
    }

    // Refresh Incidents Button
    const refBtn = document.getElementById('btn-refresh-user-incidents');
    if (refBtn) {
      refBtn.onclick = () => this.loadUserIncidents();
    }

    // Clear Incidents Button
    const clearBtn = document.getElementById('btn-clear-user-incidents');
    if (clearBtn) {
      clearBtn.onclick = () => this.clearAllIncidents();
    }
  }

  startDetectionLoop() {
    let serverDetections = [];
    let isRequesting = false;

    // Fast AI Inference Timer (runs 4 times per second for instant real-time weapon trigger)
    setInterval(async () => {
      const isVideoReady = this.source === 'webcam'
        ? (this.videoEl && this.videoEl.readyState >= 1)
        : (this.videoEl && this.hasLoadedFile && (this.videoEl.readyState >= 1 || this.videoEl.currentTime > 0));

      if (isVideoReady && !isRequesting && !this.simulatedWeapon) {
        try {
          isRequesting = true;
          // Capture current frame from canvas
          const tempCanvas = document.createElement('canvas');
          tempCanvas.width = 480;
          tempCanvas.height = 270;
          const tctx = tempCanvas.getContext('2d');
          tctx.drawImage(this.videoEl, 0, 0, 480, 270);
          const frameB64 = tempCanvas.toDataURL('image/jpeg', 0.6);

          const aiResult = await API.request('/user/detect-frame', {
            method: 'POST',
            body: JSON.stringify({ image_b64: frameB64 })
          });

          if (aiResult && aiResult.detections) {
            // Scale bboxes back to 640x360
            serverDetections = aiResult.detections.map(d => {
              const [nx1, ny1, nx2, ny2] = d.normalized_bbox || [0,0,0,0];
              return {
                ...d,
                bbox: [nx1 * 640, ny1 * 360, nx2 * 640, ny2 * 360]
              };
            });
          }
        } catch (e) {
          // Ignore drop
        } finally {
          isRequesting = false;
        }
      }
    }, 220);

    const loop = () => {
      // Schedule next tick immediately to guarantee loop NEVER terminates
      requestAnimationFrame(loop);

      if (!this.canvas || !this.ctx) return;
      this.simTime += 0.03;
      const w = this.canvas.width;
      const h = this.canvas.height;

      // 1. Draw Camera Frame to Canvas
      if (this.source === 'file') {
        if (!this.hasLoadedFile) {
          this.ctx.fillStyle = '#0a0e17';
          this.ctx.fillRect(0, 0, w, h);
          this.ctx.strokeStyle = '#00f0ff';
          this.ctx.lineWidth = 1;
          this.ctx.strokeRect(40, 40, w - 80, h - 80);
          this.ctx.fillStyle = '#00f0ff';
          this.ctx.font = 'bold 14px "Inter", sans-serif';
          this.ctx.textAlign = 'center';
          this.ctx.fillText('📁 PLEASE CLICK "CHOOSE FILE" TO LOAD AN MP4 SURVEILLANCE VIDEO', w / 2, h / 2 - 10);
          this.ctx.font = '11px "JetBrains Mono", monospace';
          this.ctx.fillStyle = '#8a9bb8';
          this.ctx.fillText('Supports 50+ Real CCTV Crime Videos from sample_videos/', w / 2, h / 2 + 18);
          this.ctx.textAlign = 'start';
          const hudEl = document.getElementById('user-hud-threat');
          if (hudEl) hudEl.innerHTML = '<span style="color: var(--accent-cyan);">● WAITING FOR VIDEO SELECTION...</span>';
          return;
        }

        // File loaded: actively play and draw video frame
        let drawn = false;
        if (this.videoEl) {
          if (this.videoEl.paused) {
            this.videoEl.play().catch(() => {});
          }
          try {
            this.ctx.drawImage(this.videoEl, 0, 0, w, h);
            drawn = true;
          } catch (e) {
            drawn = false;
          }
        }

        if (!drawn) {
          this.ctx.fillStyle = '#0a0e17';
          this.ctx.fillRect(0, 0, w, h);
          this.ctx.fillStyle = '#00f0ff';
          this.ctx.font = '13px "Inter", sans-serif';
          this.ctx.textAlign = 'center';
          this.ctx.fillText('⚡ LOADING SURVEILLANCE VIDEO...', w / 2, h / 2);
          this.ctx.textAlign = 'start';
        }
      } else if (this.source === 'webcam' && this.videoEl && (this.videoEl.readyState >= 1 || this.videoEl.currentTime > 0)) {
        if (this.videoEl.paused) { this.videoEl.play().catch(() => {}); }
        try {
          this.ctx.drawImage(this.videoEl, 0, 0, w, h);
        } catch (e) {}
      } else {
        this.drawSimulatedStoreCamera();
      }

      // 2. Render Detected Bounding Boxes (Real Webcam AI Inference)
      let activeThreat = null;

      if (this.simulatedWeapon) {
        activeThreat = this.simulatedWeapon;
        const icon = activeThreat.object_detected.includes('Knife') ? '🔪' : 
                     activeThreat.object_detected.includes('Scissors') ? '✂️' : 
                     activeThreat.object_detected.includes('Fire') ? '🔥' : '🔫';

        this.ctx.strokeStyle = '#ff2b56';
        this.ctx.lineWidth = 3;
        this.ctx.strokeRect(240, 120, 160, 180);
        this.ctx.fillStyle = '#ff2b56';
        this.ctx.fillRect(240, 96, 180, 24);
        this.ctx.fillStyle = '#fff';
        this.ctx.font = 'bold 12px "Inter", sans-serif';
        this.ctx.fillText(`${icon} ${activeThreat.object_detected.toUpperCase()} [${activeThreat.confidence}%]`, 246, 113);
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
                       (d.class_name.toLowerCase().includes('assault') || d.class_name.toLowerCase().includes('violence') || d.class_name.toLowerCase().includes('strike')) ? '🥊' : '👤';

          this.ctx.strokeStyle = color;
          this.ctx.lineWidth = isWeapon ? 3 : 2;
          this.ctx.strokeRect(x1, y1, Math.max(20, x2 - x1), Math.max(20, y2 - y1));

          this.ctx.fillStyle = color;
          this.ctx.fillRect(x1, Math.max(0, y1 - 22), Math.max(160, x2 - x1), 22);
          this.ctx.fillStyle = '#fff';
          this.ctx.font = 'bold 11px "Inter", sans-serif';
          this.ctx.fillText(`${icon} ${d.class_name.toUpperCase()} [${d.confidence}%]`, x1 + 5, Math.max(14, y1 - 6));

          if (isWeapon && !activeThreat) {
            activeThreat = {
              detection_type: d.detection_type || 'Weapon',
              object_detected: d.class_name,
              confidence: d.confidence
            };
          }
        }
      }

      // 3. Update HUD Status & Trigger Emergency Dispatch if Threat Detected
      const hudEl = document.getElementById('user-hud-threat');
      if (activeThreat) {
        if (hudEl) {
          const icon = activeThreat.object_detected.toLowerCase().includes('knife') ? '🔪' : 
                       activeThreat.object_detected.toLowerCase().includes('scissors') ? '✂️' : 
                       activeThreat.object_detected.toLowerCase().includes('fire') ? '🔥' : 
                       activeThreat.object_detected.toLowerCase().includes('gun') ? '🔫' :
                       (activeThreat.object_detected.toLowerCase().includes('stick') || activeThreat.object_detected.toLowerCase().includes('bat') || activeThreat.object_detected.toLowerCase().includes('kattai')) ? '🏏' :
                       (activeThreat.object_detected.toLowerCase().includes('assault') || activeThreat.object_detected.toLowerCase().includes('violence') || activeThreat.object_detected.toLowerCase().includes('strike')) ? '🥊' : '🚨';
          hudEl.innerHTML = `<strong style="color: var(--accent-red); animation: pulse-red 0.8s infinite;">🔴 THREAT / WEAPON DETECTED: ${icon} ${activeThreat.object_detected.toUpperCase()} [${activeThreat.confidence}%]</strong>`;
        }

        const now = Date.now();

        // Real-Time Security Audio Buzzer (sounds dual-pulse beeps while weapon is in camera view)
        if (now - this.lastBuzzerTime > 1200) {
          this.lastBuzzerTime = now;
          this.playSecurityBuzzer();
        }

        // Automatic dispatch to Police & Admin HQ (4-second throttle between dispatches)
        if (now - this.lastDispatchTime > 4000 && !this.isDispatching) {
          this.triggerEmergencyDispatch(activeThreat);
        }
      } else {
        if (hudEl) {
          hudEl.innerHTML = '<span style="color: var(--accent-green);">● STATUS: ALL SECURE — WEAPON SCANNER ONLINE</span>';
        }
      }
    };

    loop();
  }

  drawSimulatedStoreCamera() {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    // Store Interior Background
    ctx.fillStyle = '#111722';
    ctx.fillRect(0, 0, w, 160);
    ctx.fillStyle = '#0a0e17';
    ctx.fillRect(0, 160, w, h - 160);

    // Jewelry Display Counters
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

    // Walking Customer / Subject
    const cycle = this.simTime % 10;
    const px = 180 + Math.sin(this.simTime * 2) * 80;
    const py = 120;

    // Person
    ctx.fillStyle = '#8a9bb8';
    ctx.beginPath();
    ctx.arc(px + 20, py - 30, 12, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#2d3e5e';
    ctx.fillRect(px + 10, py - 18, 20, 45);

    // Draw normal subject box
    ctx.strokeStyle = '#00e676';
    ctx.lineWidth = 2;
    ctx.strokeRect(px + 4, py - 45, 32, 80);
    ctx.fillStyle = '#00e676';
    ctx.fillRect(px + 4, py - 56, 75, 12);
    ctx.fillStyle = '#000';
    ctx.font = '9px "Inter"';
    ctx.fillText('PERSON 96.2%', px + 6, py - 47);

    // Camera Watermark
    ctx.fillStyle = 'rgba(7, 9, 14, 0.85)';
    ctx.fillRect(0, 0, w, 28);
    ctx.fillStyle = '#00f0ff';
    ctx.font = '11px "JetBrains Mono"';
    ctx.fillText('STORE CAM-01 [FRONT VAULT] | AI WEAPON SCANNER: ACTIVE | PQC: ML-KEM-768', 12, 18);
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

      // Hard safety timer: never block dispatch for more than 1.5 seconds!
      const safetyTimer = setTimeout(() => finish(null), 1500);

      try {
        if (!this.canvas) {
          clearTimeout(safetyTimer);
          return finish(null);
        }
        const stream = this.canvas.captureStream(15);
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

  async triggerEmergencyDispatch(threat) {
    if (this.isDispatching) return;
    this.isDispatching = true;
    this.lastDispatchTime = Date.now();

    const randEntropy = Math.floor(1000 + Math.random() * 9000);
    const incidentId = `INC-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${randEntropy}`;

    // Show Red Dispatch Banner
    const banner = document.getElementById('user-dispatch-banner');
    if (banner) {
      document.getElementById('user-dispatch-banner-title').innerText = 
        `🔴 WEAPON DETECTED (${threat.object_detected.toUpperCase()}) — RECORDING & DISPATCHING TO POLICE HQ!`;
      document.getElementById('user-dispatch-banner-meta').innerText = 
        `Incident: ${incidentId} | Encrypting with AES-256-GCM + NIST FIPS 203 ML-KEM-768...`;
      banner.style.display = 'flex';
    }

    try {
      // Record actual live video clip from canvas (with guaranteed non-blocking timeout)
      const videoBlob = await this.captureVideoClipBlob();

      const formData = new FormData();
      formData.append('incident_id', incidentId);
      formData.append('detection_type', threat.detection_type || 'Weapon');
      formData.append('object_detected', threat.object_detected || 'Knife');
      formData.append('confidence', threat.confidence || 95.0);

      if (videoBlob && videoBlob.size > 0) {
        formData.append('file', videoBlob, `${incidentId}.webm`);
      }

      const res = await API.request('/user/dispatch-emergency', {
        method: 'POST',
        body: formData
      });

      if (banner) {
        document.getElementById('user-dispatch-banner-title').innerText = 
          `✅ EVIDENCE ENCRYPTED & RECEIVED AT POLICE HQ COMMAND VAULT!`;
        document.getElementById('user-dispatch-banner-meta').innerText = 
          `Incident: ${incidentId} | Threat: ${threat.object_detected} | Police dispatched.`;
        setTimeout(() => {
          if (banner) banner.style.display = 'none';
        }, 5000);
      }
    } catch (err) {
      console.error('Emergency dispatch error:', err);
    } finally {
      this.isDispatching = false;
      // Refresh user incident history immediately
      await this.loadUserIncidents();
    }
  }

  async loadUserIncidents() {
    try {
      const incidents = await API.request('/user/my-incidents');
      const tbody = document.getElementById('user-incidents-table-body');
      if (!tbody) return;

      if (incidents.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 20px;">No incidents reported. Facility secure.</td></tr>';
        return;
      }

      tbody.innerHTML = incidents.map(inc => `
        <tr>
          <td><strong>${inc.incident_id}</strong></td>
          <td><span style="color: var(--accent-red); font-weight: 600;">${inc.detection_type} (${inc.object_detected})</span></td>
          <td><span class="badge ${inc.severity === 'CRITICAL' ? 'badge-critical' : 'badge-high'}">${inc.severity}</span></td>
          <td style="font-family: var(--font-mono); font-size: 11px;">${inc.created_at.replace('T', ' ').slice(0, 19)}</td>
          <td><span class="badge badge-encrypted">NIST ML-KEM-768</span></td>
          <td>
            <span class="badge ${inc.status === 'NEW' ? 'badge-critical' : inc.status === 'INVESTIGATING' ? 'badge-high' : 'badge-verified'}">
              ${inc.status === 'NEW' ? 'POLICE DISPATCHED 🚨' : inc.status === 'INVESTIGATING' ? 'INVESTIGATING 🔍' : 'RESOLVED ✅'}
            </span>
          </td>
          <td>
            <div style="display: flex; gap: 6px; align-items: center;">
              <button class="btn-action" style="background: rgba(0, 240, 255, 0.15); border-color: var(--accent-cyan); color: var(--accent-cyan); font-size: 11px; padding: 4px 10px;" onclick="window.userPortal.openVideoModal('${inc.incident_id}', '${inc.object_detected}', '${inc.confidence}')">
                🎬 Play Video
              </button>
              <button class="btn-action" style="background: rgba(255, 77, 77, 0.15); border-color: var(--accent-red); color: var(--accent-red); font-size: 11px; padding: 4px 8px;" onclick="window.userPortal.deleteIncident('${inc.incident_id}')" title="Delete incident log">
                🗑️ Clear
              </button>
            </div>
          </td>
        </tr>
      `).join('');
    } catch (err) {
      console.warn('Error loading user incidents:', err);
    }
  }

  async clearAllIncidents() {
    if (!confirm('Are you sure you want to clear all incident logs for your facility? This will remove all recorded alerts and evidence.')) {
      return;
    }

    const tbody = document.getElementById('user-incidents-table-body');
    if (tbody) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--accent-cyan); padding: 20px;">⚡ Clearing all incident records...</td></tr>';
    }

    try {
      const res = await API.clearUserIncidents();
      await this.loadUserIncidents();
    } catch (err) {
      alert(`Notice: ${err.message}`);
      await this.loadUserIncidents();
    }
  }

  async deleteIncident(incidentId) {
    if (!confirm(`Are you sure you want to clear incident ${incidentId}?`)) {
      return;
    }

    try {
      const res = await API.clearUserIncidents(incidentId);
      await this.loadUserIncidents();
    } catch (err) {
      alert(`Notice: ${err.message}`);
      await this.loadUserIncidents();
    }
  }

  openVideoModal(incidentId, threatName, conf) {
    const modal = document.getElementById('user-video-modal');
    const video = document.getElementById('user-playback-video');
    const title = document.getElementById('modal-video-title');
    const meta = document.getElementById('modal-video-meta');
    const closeBtn = document.getElementById('btn-close-video-modal');

    if (!modal || !video) return;

    if (title) title.innerText = `Recorded Threat Video: ${threatName || 'Weapon'} (${conf || 95}%)`;
    if (meta) meta.innerText = `Incident ID: ${incidentId} | Sent to Police & Admin Command`;

    video.src = `/api/user/video/${incidentId}`;
    modal.style.display = 'flex';
    video.play().catch(() => {});

    if (closeBtn) {
      closeBtn.onclick = () => {
        video.pause();
        video.src = '';
        modal.style.display = 'none';
      };
    }
  }
}

window.userPortal = new UserPortal();
document.addEventListener('DOMContentLoaded', () => window.userPortal.init());
