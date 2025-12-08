// =============================================================================
// AuthContext.jsx - MOCK USER (Autenticación real vendrá después)
// =============================================================================
// Por ahora simula un usuario logueado. Después agregaremos JWT real.
// =============================================================================

import { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

// Usuario mock - después esto vendrá del backend
const MOCK_USER = {
  id: 'user_001',
  email: 'jose@fintechmx.pro',
  name: 'Jose',
  plan: 'pro', // free | pro | enterprise
  createdAt: '2024-01-15',
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(MOCK_USER);
  const [isLoading, setIsLoading] = useState(false);

  // Funciones que después conectarán con el backend real
  const login = async (email, password) => {
    setIsLoading(true);
    // TODO: Llamar a /api/auth/login
    // Por ahora solo simula
    await new Promise(resolve => setTimeout(resolve, 500));
    setUser(MOCK_USER);
    setIsLoading(false);
    return { success: true };
  };

  const logout = () => {
    // TODO: Limpiar token JWT
    setUser(null);
  };

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
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
