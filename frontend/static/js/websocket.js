/**
 * WebSocket Real-Time Alert & Audio Siren Client
 */

class AlertWebSocketClient {
  constructor() {
    this.ws = null;
    this.reconnectTimer = null;
    this.audioCtx = null;
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

  playCriticalAlertSound() {
    try {
      this.initAudio();
      if (!this.audioCtx) return;

      const now = this.audioCtx.currentTime;
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();

      osc.type = 'sawtooth';
      // Alarm modulation
      osc.frequency.setValueAtTime(880, now);
      osc.frequency.exponentialRampToValueAtTime(440, now + 0.3);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.6);

      gain.gain.setValueAtTime(0.3, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.8);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start(now);
      osc.stop(now + 0.8);
    } catch (e) {
      console.warn('Audio synthesis disabled or blocked by browser policy');
    }
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/alerts`;

    console.log('[WebSocket] Connecting to alert broadcast channel:', wsUrl);
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('[WebSocket] ✅ Connected to Police Alert Channel');
      const pill = document.getElementById('ws-status-pill');
      if (pill) {
        pill.innerHTML = '<span class="dot online"></span> WS CONNECTED';
      }
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'CRITICAL_ALERT') {
          this.handleCriticalAlert(message.data);
        } else if (message.type === 'AI_TELEMETRY') {
          window.dispatchEvent(new CustomEvent('ai:telemetry', { detail: message.data }));
        }
      } catch (err) {
        console.error('[WebSocket] Message parsing error:', err);
      }
    };

    this.ws.onclose = () => {
      console.warn('[WebSocket] Alert connection lost. Reconnecting in 3s...');
      const pill = document.getElementById('ws-status-pill');
      if (pill) {
        pill.innerHTML = '<span class="dot alert"></span> WS RECONNECTING';
      }
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = setTimeout(() => this.connect(), 3000);
    };

    this.ws.onerror = (err) => {
      console.error('[WebSocket] Socket error:', err);
      this.ws.close();
    };
  }

  handleCriticalAlert(alertData) {
    console.warn('[CRITICAL ALERT RECEIVED]', alertData);
    this.playCriticalAlertSound();

    // Trigger visual red banner
    const alertBar = document.getElementById('critical-alert-bar');
    if (alertBar) {
      document.getElementById('alert-bar-text').innerText = 
        `🔴 CRITICAL ALERT: ${alertData.detection_type.toUpperCase()} (${alertData.object_detected.toUpperCase()}) DETECTED AT ${alertData.location.toUpperCase()} [${alertData.confidence}%]`;
      document.getElementById('alert-bar-meta').innerText = 
        `Incident: ${alertData.incident_id} | Camera: ${alertData.camera_code} | Time: ${alertData.timestamp}`;
      alertBar.style.display = 'flex';
    }

    // Trigger Critical Alert Modal Popup
    const modal = document.getElementById('critical-alert-modal');
    if (modal) {
      document.getElementById('modal-alert-type').innerText = alertData.detection_type.toUpperCase();
      document.getElementById('modal-alert-object').innerText = alertData.object_detected;
      document.getElementById('modal-alert-camera').innerText = `${alertData.camera_code} - ${alertData.location}`;
      document.getElementById('modal-alert-confidence').innerText = `${alertData.confidence}%`;
      document.getElementById('modal-alert-incident-id').innerText = alertData.incident_id;
      document.getElementById('modal-alert-time').innerText = alertData.timestamp;

      document.getElementById('modal-btn-view-incident').onclick = () => {
        modal.style.display = 'none';
        window.app.switchTab('evidence');
        window.evidenceVault.selectIncident(alertData.incident_id);
      };

      modal.style.display = 'flex';
    }

    // Refresh incidents and dashboard metrics
    window.dispatchEvent(new CustomEvent('incident:created', { detail: alertData }));
  }
}

window.alertWS = new AlertWebSocketClient();
