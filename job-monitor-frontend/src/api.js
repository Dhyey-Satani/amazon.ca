// API configuration
const API_BASE_URL = 'http://localhost:8000';


// https://www.youtube.com/watch?v=RIMTaJwqjTM
// API client class
class ApiClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Job endpoints
  async getJobs(limit = 50) {
    return this.request(`/jobs?limit=${limit}`);
  }

  // Status endpoint
  async getStatus() {
    return this.request('/status');
  }

  // Control endpoints
  async startMonitoring(pollInterval = null) {
    const body = pollInterval ? { poll_interval: pollInterval } : {};
    return this.request('/start', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async stopMonitoring() {
    return this.request('/stop', {
      method: 'POST',
    });
  }

  async restartMonitoring() {
    return this.request('/restart', {
      method: 'POST',
    });
  }

  // Logs endpoint
  async getLogs(limit = 50) {
    return this.request(`/logs?limit=${limit}`);
  }

  // Configuration endpoint
  async updateConfig(config) {
    return this.request('/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  // Clear jobs endpoint
  async clearJobs() {
    return this.request('/jobs', {
      method: 'DELETE',
    });
  }
}

export const apiClient = new ApiClient();
export default apiClient;