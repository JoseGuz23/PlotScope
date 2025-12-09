// =============================================================================
// AuthContext.jsx - AUTENTICACIÓN REAL
// =============================================================================

import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // Estado inicial basado en si existe el token en localStorage
  const [user, setUser] = useState(authAPI.isAuthenticated() ? { role: 'editor' } : null);

  // Función de Login (Sincroniza estado)
  const login = async (password) => {
    await authAPI.login(password);
    setUser({ role: 'editor' });
  };

  // Función de Logout (La que fallaba)
  const logout = () => {
    authAPI.logout(); // Llama a la API para borrar token y redirigir
    setUser(null);    // Limpia el estado local
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: authAPI.isAuthenticated() }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe usarse dentro de AuthProvider');
  }
  return context;
}

export default AuthContext;