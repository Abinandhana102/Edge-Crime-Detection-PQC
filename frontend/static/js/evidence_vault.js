/**
 * Quantum-Safe Evidence Vault & Authorized Video Playback Controller
 */

class EvidenceVault {
  constructor() {
    this.selectedIncidentId = null;
  }

  async selectIncident(incidentId) {
    this.selectedIncidentId = incidentId;
    const detailsContainer = document.getElementById('evidence-detail-view');
    if (!detailsContainer) return;

    detailsContainer.innerHTML = '<div style="padding: 20px; color: var(--text-secondary);">Loading quantum-safe evidence metadata...</div>';

    try {
      const incident = await API.getIncident(incidentId);
      const evidence = await API.getEvidence(incidentId).catch(() => null);

      this.renderEvidenceDetails(incident, evidence);
    } catch (err) {
      detailsContainer.innerHTML = `<div style="padding: 20px; color: var(--accent-red);">Error loading evidence: ${err.message}</div>`;
    }
  }

  renderEvidenceDetails(incident, evidence) {
    const container = document.getElementById('evidence-detail-view');
    if (!container) return;

    const hasEv = !!evidence;
    const isVerified = evidence && evidence.integrity_status === 'VERIFIED';

    container.innerHTML = `
      <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
          <div>
            <h3 style="font-family: var(--font-display); font-size: 22px; color: #fff; margin-bottom: 4px;">
              Incident Evidence: ${incident.incident_id}
            </h3>
            <div style="font-size: 13px; color: var(--text-secondary); font-family: var(--font-mono);">
              Camera: ${incident.camera_code} (${incident.location}) | Detection: ${incident.detection_type} (${incident.object_detected})
            </div>
          </div>
          <div>
            <span class="badge ${incident.severity === 'CRITICAL' ? 'badge-critical' : 'badge-high'}">${incident.severity}</span>
            <span class="badge badge-encrypted" style="margin-left: 8px;">QUANTUM-SAFE ENCRYPTED</span>
          </div>
        </div>

        <!-- Cryptographic Specification Banner -->
        <div style="background: rgba(13, 18, 29, 0.8); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 16px; margin-bottom: 20px;">
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; font-size: 12px; font-family: var(--font-mono);">
            <div>
              <span style="color: var(--text-muted);">PQC Key Protection:</span>
              <div style="color: var(--accent-cyan); font-weight: 600; margin-top: 2px;">NIST FIPS 203 ML-KEM-768</div>
            </div>
            <div>
              <span style="color: var(--text-muted);">Symmetric Cipher:</span>
              <div style="color: var(--accent-purple); font-weight: 600; margin-top: 2px;">AES-256-GCM (Authenticated)</div>
            </div>
            <div>
              <span style="color: var(--text-muted);">Integrity Algorithm:</span>
              <div style="color: var(--accent-green); font-weight: 600; margin-top: 2px;">SHA-256 (FIPS 180-4)</div>
            </div>
          </div>

          ${hasEv ? `
            <div style="margin-top: 14px; padding-top: 12px; border-top: 1px solid rgba(45, 62, 94, 0.3); font-size: 11px; font-family: var(--font-mono); color: var(--text-secondary);">
              <div><strong style="color: var(--text-primary);">Encrypted Package (.qsep):</strong> ${evidence.encrypted_filename} (${(evidence.file_size_bytes / 1024).toFixed(1)} KB)</div>
              <div style="margin-top: 4px; word-break: break-all;"><strong style="color: var(--text-primary);">Pre-Encryption SHA-256:</strong> ${evidence.plaintext_sha256}</div>
            </div>
          ` : '<div style="margin-top: 10px; color: var(--accent-amber); font-size: 12px;">⚠️ Evidence package recording in progress or pending upload...</div>'}
        </div>

        <!-- Action Controls -->
        <div style="display: flex; gap: 12px; margin-bottom: 20px;">
          <button id="btn-verify-integrity" class="btn-action btn-verify" ${!hasEv ? 'disabled' : ''}>
            🛡️ Verify SHA-256 Integrity
          </button>
          <button id="btn-retrieve-decrypt" class="btn-action" style="background: linear-gradient(90deg, #0077ff, #00f0ff); border: none;" ${!hasEv ? 'disabled' : ''}>
            🔓 Authorized Decrypt & Play
          </button>
        </div>

        <!-- Verification Results Callout -->
        <div id="integrity-result-box" style="display: none; padding: 14px 18px; border-radius: var(--radius-sm); margin-bottom: 20px; font-size: 13px; font-family: var(--font-mono);"></div>

        <!-- Video Player Section -->
        <div id="video-playback-section" style="display: none; background: #000; border-radius: var(--radius-sm); overflow: hidden; border: 1px solid var(--border-color);">
          <div style="padding: 8px 14px; background: rgba(18, 24, 38, 0.9); font-size: 12px; font-family: var(--font-mono); color: var(--accent-green); display: flex; justify-content: space-between;">
            <span>● SECURE DECRYPTED STREAM [AUTHORIZED OFFICER SESSION]</span>
            <span id="player-integrity-badge">✅ SHA-256 VERIFIED</span>
          </div>
          <video id="decrypted-evidence-player" controls style="width: 100%; aspect-ratio: 16/9; display: block;"></video>
        </div>
      </div>
    `;

    // Attach Action Listeners
    if (hasEv) {
      document.getElementById('btn-verify-integrity').onclick = () => this.handleVerifyIntegrity(incident.incident_id);
      document.getElementById('btn-retrieve-decrypt').onclick = () => this.handleRetrieveAndDecrypt(incident.incident_id);
    }
  }

  async handleVerifyIntegrity(incidentId) {
    const resultBox = document.getElementById('integrity-result-box');
    resultBox.style.display = 'block';
    resultBox.style.background = 'rgba(0, 240, 255, 0.1)';
    resultBox.style.border = '1px solid var(--accent-cyan)';
    resultBox.style.color = 'var(--text-primary)';
    resultBox.innerHTML = '⏳ Computing SHA-256 cryptographic digest over evidence package...';

    try {
      const res = await API.verifyEvidenceIntegrity(incidentId);
      if (res.is_valid) {
        resultBox.style.background = 'rgba(0, 230, 118, 0.15)';
        resultBox.style.border = '1px solid var(--accent-green)';
        resultBox.style.color = '#fff';
        resultBox.innerHTML = `
          <div style="font-weight: 700; color: var(--accent-green); margin-bottom: 4px;">✅ Evidence Integrity Verified</div>
          <div style="font-size: 12px; color: var(--text-secondary);">${res.message}</div>
          <div style="margin-top: 6px; font-size: 11px; color: var(--accent-green); word-break: break-all;">Computed Digest: ${res.calculated_sha256}</div>
        `;
      } else {
        resultBox.style.background = 'rgba(255, 43, 86, 0.15)';
        resultBox.style.border = '1px solid var(--accent-red)';
        resultBox.style.color = '#fff';
        resultBox.innerHTML = `
          <div style="font-weight: 700; color: var(--accent-red); margin-bottom: 4px;">❌ Evidence Integrity Check Failed</div>
          <div style="font-size: 12px;">Possible bitstream tampering or corrupt file.</div>
        `;
      }
    } catch (err) {
      resultBox.style.background = 'rgba(255, 43, 86, 0.15)';
      resultBox.style.border = '1px solid var(--accent-red)';
      resultBox.innerHTML = `❌ Verification Error: ${err.message}`;
    }
  }

  async handleRetrieveAndDecrypt(incidentId) {
    const playerSection = document.getElementById('video-playback-section');
    const player = document.getElementById('decrypted-evidence-player');
    const resultBox = document.getElementById('integrity-result-box');

    try {
      const res = await API.decryptEvidence(incidentId);
      playerSection.style.display = 'block';
      player.src = res.video_stream_url;
      player.load();
      player.play().catch(err => {
        console.warn('Playback click required:', err);
      });

      resultBox.style.display = 'block';
      resultBox.style.background = 'rgba(0, 230, 118, 0.15)';
      resultBox.style.border = '1px solid var(--accent-green)';
      resultBox.innerHTML = `
        <div style="font-weight: 700; color: var(--accent-green); margin-bottom: 4px;">🔓 Post-Quantum Decapsulation & Decryption Successful</div>
        <div style="font-size: 12px; color: var(--text-secondary);">${res.pqc_decapsulation_status} | ${res.symmetric_decryption_status}</div>
      `;
    } catch (err) {
      alert(`Decryption Error: ${err.message}`);
    }
  }
}

window.evidenceVault = new EvidenceVault();
