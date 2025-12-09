// =============================================================================
// api.js - CLIENTE API LYA
// =============================================================================

// --- CONFIGURACIÓN DE CONEXIÓN ---
// Descomenta la opción que necesites:

// OPCIÓN 1: LOCAL (Para desarrollo en tu PC)
// const API_BASE = 'http://localhost:7071/api';

// OPCIÓN 2: NUBE (Para producción en Azure)
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
    
    // --- MANEJO DE SESIÓN ---
    // Si es 401 (No autorizado) y NO es un intento de login, expulsar al usuario.
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
    
    // Manejo de contenido texto vs JSON
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
// AUTH - Login simple
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
// MANUSCRITOS
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

  async getChanges(projectId) {
    return await apiFetch(`project/${projectId}/changes`);
  },

  async saveChangeDecision(projectId, changeId, action) {
    return await apiFetch(`project/${projectId}/changes/${changeId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    });
  },

  async export(projectId) {
    return await apiFetch(`project/${projectId}/export`, {
      method: 'POST',
    });
  },
};

// =============================================================================
// UPLOAD & TOOLS
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

  // Nueva función para cotizar (Pública)
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
      // Remover encabezado data:application/vnd...;base64,
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