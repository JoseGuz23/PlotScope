// =============================================================================
// api.js - CONEXIÓN REAL CON AZURE BLOB STORAGE
// =============================================================================
// Conecta directamente con tu storage de Azure
// =============================================================================

// Storage de Azure - TU URL REAL
const STORAGE_BASE = 'https://sylphrenastorage.blob.core.windows.net/sylphrena-outputs';

// URL del backend Azure Functions (para cuando lo necesites)
const API_BASE = import.meta.env.VITE_API_URL || 'https://tu-function-app.azurewebsites.net/api';

// =============================================================================
// PROYECTOS - Por ahora datos locales + conexión real para archivos
// =============================================================================

export const projectsAPI = {
  // Lista de proyectos (mock por ahora, después conectará con DB)
  async getAll() {
    // TODO: Cuando tengas base de datos, esto llamará al backend
    // Por ahora retornamos datos conocidos + tu proyecto real
    return [
      {
        id: 'bb841d8a189243faa35647773561aa6f',
        name: 'Piel_Morena',
        status: 'completed',
        createdAt: '2025-12-03T17:39:01',
        wordCount: 4931,
        chaptersCount: 2,
        changesCount: 23,
      },
      {
        id: 'demo_project_002',
        name: 'La_Sombra_del_Viento',
        status: 'processing',
        createdAt: '2025-12-07T10:00:00',
        wordCount: 85240,
        chaptersCount: 25,
        progress: 45,
      },
      {
        id: 'demo_project_003',
        name: 'Cien_Años_de_Soledad',
        status: 'pending_bible',
        createdAt: '2025-12-06T08:30:00',
        wordCount: 120000,
        chaptersCount: 40,
      },
    ];
  },

  async getById(projectId) {
    const projects = await this.getAll();
    return projects.find(p => p.id === projectId);
  },
};

// =============================================================================
// BIBLIA - CONEXIÓN REAL CON AZURE BLOB
// =============================================================================

export const bibleAPI = {
  // Cargar biblia REAL desde Azure Blob Storage
  async get(projectId) {
    const url = `${STORAGE_BASE}/${projectId}/biblia_validada.json`;
    
    console.log('📚 Cargando biblia desde:', url);
    
    try {
      const response = await fetch(url, {
        method: 'GET',
        // Sin headers especiales - el blob debe ser público o tener SAS
      });
      
      if (!response.ok) {
        console.error('❌ Error HTTP:', response.status, response.statusText);
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ Biblia cargada:', data);
      return data;
      
    } catch (error) {
      console.error('❌ Error cargando biblia:', error);
      
      // Si falla, mostrar mensaje útil
      throw new Error(
        `No se pudo cargar la biblia. ` +
        `Verifica que el archivo exista en: ${url} ` +
        `y que CORS esté configurado en tu Storage Account.`
      );
    }
  },

  // Guardar biblia editada (TODO: implementar endpoint)
  async save(projectId, bibleData) {
    console.log('💾 Guardando biblia para proyecto:', projectId);
    // TODO: Implementar cuando tengas endpoint
    // Por ahora simula éxito
    await new Promise(resolve => setTimeout(resolve, 500));
    return { success: true };
  },

  // Aprobar biblia (TODO: implementar endpoint)
  async approve(projectId) {
    console.log('✅ Aprobando biblia para proyecto:', projectId);
    // TODO: Implementar cuando tengas endpoint
    await new Promise(resolve => setTimeout(resolve, 500));
    return { success: true };
  },
};

// =============================================================================
// MANUSCRITOS - CONEXIÓN REAL CON AZURE BLOB
// =============================================================================

export const manuscriptAPI = {
  // Manuscrito editado (limpio)
  async getEdited(projectId) {
    const url = `${STORAGE_BASE}/${projectId}/manuscrito_editado.md`;
    console.log('📄 Cargando manuscrito editado desde:', url);
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Manuscrito editado no encontrado');
    return await response.text();
  },

  // Manuscrito anotado (con cambios inline)
  async getAnnotated(projectId) {
    const url = `${STORAGE_BASE}/${projectId}/manuscrito_anotado.md`;
    console.log('📝 Cargando manuscrito anotado desde:', url);
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Manuscrito anotado no encontrado');
    return await response.text();
  },

  // Control de cambios HTML
  async getChangesHTML(projectId) {
    const url = `${STORAGE_BASE}/${projectId}/control_cambios.html`;
    console.log('🔄 Cargando control de cambios desde:', url);
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Control de cambios no encontrado');
    return await response.text();
  },

  // Resumen ejecutivo
  async getSummary(projectId) {
    const url = `${STORAGE_BASE}/${projectId}/resumen_ejecutivo.json`;
    console.log('📊 Cargando resumen desde:', url);
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Resumen no encontrado');
    return await response.json();
  },
};

// =============================================================================
// UPLOAD - Pendiente de implementar
// =============================================================================

export const uploadAPI = {
  async uploadManuscript(file, projectName) {
    console.log('📤 Upload pendiente de implementar');
    // TODO: Implementar con SAS token del backend
    throw new Error('Upload no implementado aún');
  },
};

// =============================================================================
// EXPORT
// =============================================================================

export default {
  projects: projectsAPI,
  bible: bibleAPI,
  manuscript: manuscriptAPI,
  upload: uploadAPI,
};
