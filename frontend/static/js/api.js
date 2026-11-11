/**
 * Police Dashboard REST API Client
 * Manages JWT tokens, authentication, and backend communication.
 */

const API = {
  baseUrl: window.location.origin + '/api',

  getToken() {
    return localStorage.getItem('police_jwt_token');
  },

  setToken(token) {
    localStorage.setItem('police_jwt_token', token);
  },

  clearToken() {
    localStorage.removeItem('police_jwt_token');
    localStorage.removeItem('police_user_info');
  },

  getUserInfo() {
    try {
      return JSON.parse(localStorage.getItem('police_user_info') || '{}');
    } catch {
      return {};
    }
  },

  setUserInfo(user) {
    localStorage.setItem('police_user_info', JSON.stringify(user));
  },

  async request(endpoint, options = {}) {
    const headers = options.headers || {};
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers
      });

      if (response.status === 401) {
        this.clearToken();
        window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        throw new Error('Session expired or unauthorized');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || 'API request failed');
      }

      return await response.json();
    } catch (err) {
      console.error(`[API Error] ${endpoint}:`, err);
      throw err;
    }
  },

  // Auth Endpoints
  async login(username, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    this.setToken(data.access_token);
    this.setUserInfo(data);
    return data;
  },

  async logout() {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } catch (e) {
      console.warn('Logout notification error:', e);
    } finally {
      this.clearToken();
    }
  },

  // Incidents
  async getIncidents(params = {}) {
    const query = new URLSearchParams(params).toString();
    return await this.request(`/incidents${query ? '?' + query : ''}`);
  },

  async getIncident(incidentId) {
    return await this.request(`/incidents/${incidentId}`);
  },

  async updateIncidentStatus(incidentId, status, notes = '') {
    return await this.request(`/incidents/${incidentId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status, notes })
    });
  },

  async clearUserIncidents(incidentId = '') {
    const url = incidentId ? `/user/my-incidents?incident_id=${encodeURIComponent(incidentId)}` : '/user/my-incidents';
    try {
      return await this.request(url, { method: 'DELETE' });
    } catch (err) {
      const postUrl = incidentId ? `/user/clear-incidents?incident_id=${encodeURIComponent(incidentId)}` : '/user/clear-incidents';
      return await this.request(postUrl, { method: 'POST' });
    }
  },

  async clearPoliceIncidents(incidentId = '') {
    const url = incidentId ? `/incidents/${encodeURIComponent(incidentId)}` : '/incidents';
    return await this.request(url, { method: 'DELETE' });
  },

  // Evidence
  async getEvidence(incidentId) {
    return await this.request(`/evidence/${incidentId}`);
  },

  async verifyEvidenceIntegrity(incidentId) {
    return await this.request(`/evidence/${incidentId}/verify`, { method: 'POST' });
  },

  async decryptEvidence(incidentId) {
    return await this.request(`/evidence/${incidentId}/decrypt`, { method: 'POST' });
  },

  // Cameras & Zones
  async getCameras() {
    return await this.request('/cameras');
  },

  async getZones() {
    return await this.request('/zones');
  },

  async createZone(zoneData) {
    return await this.request('/zones', {
      method: 'POST',
      body: JSON.stringify(zoneData)
    });
  },

  async deleteZone(zoneId) {
    return await this.request(`/zones/${zoneId}`, { method: 'DELETE' });
  },

  // Stats & Audit
  async getStats() {
    return await this.request('/stats');
  },

  async getAuditLogs(params = {}) {
    const query = new URLSearchParams(params).toString();
    return await this.request(`/audit${query ? '?' + query : ''}`);
  },

  async getPqcInfo() {
    return await this.request('/pqc/info');
  }
};
