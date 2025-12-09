// =============================================================================
// api.js - CLIENTE API SYLPHRENA (MEJORADO)
// =============================================================================

// --- CONFIGURACIÓN DE CONEXIÓN ---
const API_BASE = import.meta.env.VITE_API_URL || 'https://sylphrena-orchestrator-ece2a4epbdbrfbgk.westus3-01.azurewebsites.net/api';

console.log('🔗 API CONECTADA A:', API_BASE);

// =============================================================================
// HELPER - Fetch con autenticación
// =============================================================================

function getAuthHeaders() {
  const token = localStorage.getItem('sylphrena_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE}/${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
        ...options.headers,
      },
    });
    
    if (response.status === 401 && !endpoint.includes('auth/login')) {
      console.warn('⚠️ Sesión expirada. Redirigiendo a login...');
      localStorage.removeItem('sylphrena_token');
      window.location.href = '/login';
      throw new Error('Sesión expirada');
    }
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Error del servidor: ${response.status}`);
    }
    
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('text/plain')) {
      return await response.text();
    }
    
    return await response.json();
  } catch (error) {
    console.error(`❌ Error en ${endpoint}:`, error);
    throw error;
  }
}

// =============================================================================
// AUTH
// =============================================================================

export const authAPI = {
  async login(password) {
    const response = await apiFetch('auth/login', {
      method: 'POST',
      body: JSON.stringify({ password }),
    });
    
    if (response.token) {
      localStorage.setItem('sylphrena_token', response.token);
    }
    
    return response;
  },
  
  logout() {
    localStorage.removeItem('sylphrena_token');
    window.location.href = '/login';
  },
  
  isAuthenticated() {
    return !!localStorage.getItem('sylphrena_token');
  },
  
  getToken() {
    return localStorage.getItem('sylphrena_token');
  }
};

// =============================================================================
// PROYECTOS
// =============================================================================

export const projectsAPI = {
  async getAll() {
    const data = await apiFetch('projects');
    return data.projects || [];
  },

  async getById(projectId) {
    return await apiFetch(`project/${projectId}`);
  },
};

// =============================================================================
// BIBLIA NARRATIVA
// =============================================================================

export const bibleAPI = {
  async get(projectId) {
    return await apiFetch(`project/${projectId}/bible`);
  },

  async save(projectId, bibleData) {
    return await apiFetch(`project/${projectId}/bible`, {
      method: 'POST',
      body: JSON.stringify(bibleData),
    });
  },

  async approve(projectId) {
    return await apiFetch(`project/${projectId}/bible/approve`, {
      method: 'POST',
    });
  },
};

// =============================================================================
// MANUSCRITOS - MEJORADO
// =============================================================================

export const manuscriptAPI = {
  async getEdited(projectId) {
    return await apiFetch(`project/${projectId}/manuscript/edited`);
  },

  async getAnnotated(projectId) {
    return await apiFetch(`project/${projectId}/manuscript/annotated`);
  },

  async getChangesHTML(projectId) {
    return await apiFetch(`project/${projectId}/manuscript/changes-html`);
  },

  async getSummary(projectId) {
    return await apiFetch(`project/${projectId}`);
  },

  // Obtener cambios estructurados
  async getChanges(projectId) {
    return await apiFetch(`project/${projectId}/changes`);
  },

  // NUEVO: Obtener capítulos consolidados con contenido completo
  async getChapters(projectId) {
    return await apiFetch(`project/${projectId}/chapters`);
  },

  // Guardar decisión de un cambio
  async saveChangeDecision(projectId, changeId, action) {
    return await apiFetch(`project/${projectId}/changes/${changeId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    });
  },

  // Guardar todas las decisiones de cambios (batch)
  async saveAllDecisions(projectId, decisions) {
    return await apiFetch(`project/${projectId}/changes/decisions`, {
      method: 'POST',
      body: JSON.stringify({ decisions }),
    });
  },

  // Exportar manuscrito final
  async export(projectId, acceptedChanges) {
    return await apiFetch(`project/${projectId}/export`, {
      method: 'POST',
      body: JSON.stringify({ accepted_changes: acceptedChanges }),
    });
  },
};

// =============================================================================
// UPLOAD
// =============================================================================

export const uploadAPI = {
  async uploadManuscript(file, projectName) {
    const base64 = await fileToBase64(file);
    return await apiFetch('project/upload', {
      method: 'POST',
      body: JSON.stringify({
        filename: file.name,
        projectName: projectName,
        content: base64,
      }),
    });
  },

  async analyzeForQuote(file) {
    const base64 = await fileToBase64(file);
    return await apiFetch('analyze-file', {
      method: 'POST',
      body: JSON.stringify({
        filename: file.name,
        content: base64,
      }),
    });
  },
};

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const base64 = reader.result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
  });
}

export default {
  auth: authAPI,
  projects: projectsAPI,
  bible: bibleAPI,
  manuscript: manuscriptAPI,
  upload: uploadAPI,
};