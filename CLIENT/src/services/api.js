// =============================================================================
// api.js - TODO PASA POR LA API (no acceso directo a blob)
// =============================================================================

const API_BASE = import.meta.env.VITE_API_URL || 'https://sylphrena-orchestrator-ece2a4epbdbrfbgk.westus3-01.azurewebsites.net/api';

console.log('🔗 API URL:', API_BASE);

// =============================================================================
// HELPER - Fetch con autenticación
// =============================================================================

function getAuthHeaders() {
  const token = localStorage.getItem('sylphrena_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE}/${endpoint}`;
  console.log(`📡 ${options.method || 'GET'} ${url}`);
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
        ...options.headers,
      },
    });
    
    // Si es 401, redirigir a login
    if (response.status === 401) {
      localStorage.removeItem('sylphrena_token');
      window.location.href = '/login';
      throw new Error('No autorizado');
    }
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Error ${response.status}`);
    }
    
    // Algunos endpoints devuelven texto plano (markdown)
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
    console.log('📚 Cargando biblia desde API...');
    return await apiFetch(`project/${projectId}/bible`);
  },

  async save(projectId, bibleData) {
    console.log('💾 Guardando biblia editada...');
    return await apiFetch(`project/${projectId}/bible`, {
      method: 'POST',
      body: JSON.stringify(bibleData),
    });
  },

  async approve(projectId) {
    console.log('✅ Aprobando biblia...');
    return await apiFetch(`project/${projectId}/bible/approve`, {
      method: 'POST',
    });
  },
};

// =============================================================================
// MANUSCRITOS - Todo pasa por la API
// =============================================================================

export const manuscriptAPI = {
  async getEdited(projectId) {
    console.log('📄 Cargando manuscrito editado...');
    return await apiFetch(`project/${projectId}/manuscript/edited`);
  },

  async getAnnotated(projectId) {
    console.log('📝 Cargando manuscrito anotado...');
    return await apiFetch(`project/${projectId}/manuscript/annotated`);
  },

  async getChangesHTML(projectId) {
    console.log('🔄 Cargando control de cambios HTML...');
    return await apiFetch(`project/${projectId}/manuscript/changes-html`);
  },

  async getSummary(projectId) {
    console.log('📊 Cargando resumen ejecutivo...');
    return await apiFetch(`project/${projectId}`);
  },

  async getChanges(projectId) {
    return await apiFetch(`project/${projectId}/changes`);
  },

  async saveChangeDecision(projectId, changeId, action) {
    console.log(`📝 Guardando decisión: ${changeId} -> ${action}`);
    return await apiFetch(`project/${projectId}/changes/${changeId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    });
  },

  async export(projectId) {
    console.log('📤 Exportando manuscrito final...');
    return await apiFetch(`project/${projectId}/export`, {
      method: 'POST',
    });
  },
};

// =============================================================================
// UPLOAD
// =============================================================================

export const uploadAPI = {
  async uploadManuscript(file, projectName) {
    console.log('📤 Subiendo manuscrito:', projectName);
    
    // Convertir archivo a base64
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

// =============================================================================
// EXPORT DEFAULT
// =============================================================================

export default {
  auth: authAPI,
  projects: projectsAPI,
  bible: bibleAPI,
  manuscript: manuscriptAPI,
  upload: uploadAPI,
};
