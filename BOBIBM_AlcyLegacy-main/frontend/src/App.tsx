import React, { useEffect, useState } from 'react';

import Navbar from './components/Navbar';
import Hero from './components/Hero';
import Features from './components/Features';
import TeamView from './components/TeamView';
import DocView from './components/DocView';
import ApiView from './components/ApiView';
import Footer from './components/Footer';
import AuthModal from './components/AuthModal';

import { ApiService } from './services/api';

interface AppUser {
  name: string;
  email: string;
}

function App() {
  const [activeTab, setActiveTab] =
    useState<string>('demo');

  const [theme, setTheme] =
    useState<'dark' | 'light'>('dark');

  const [lang, setLang] =
    useState<'es' | 'en'>('es');

  const [isAuthOpen, setIsAuthOpen] =
    useState<boolean>(false);

  const [user, setUser] =
    useState<AppUser | null>(null);

  // =========================================================
  // TEMA
  // =========================================================

  useEffect(() => {
    document.documentElement.setAttribute(
      'data-theme',
      theme
    );
  }, [theme]);

  // =========================================================
  // RECUPERAR SESIÓN DESDE API_E
  // =========================================================

  useEffect(() => {
    let mounted = true;

    const loadSession = async () => {
      try {
        // Si no existe JWT local, no hacemos petición
        if (!ApiService.isAuthenticated()) {
          if (mounted) {
            setUser(null);
          }

          return;
        }

        // Verificamos el JWT contra API_E
        const response =
          await ApiService.getCurrentUser();

        if (!mounted) return;

        if (
          response.success &&
          response.user
        ) {
          setUser({
            name: response.user.username,
            email: response.user.email
          });

          return;
        }

        // Si la respuesta no contiene usuario válido
        ApiService.logout();
        setUser(null);

      } catch (error) {
        console.error(
          'No se pudo recuperar la sesión:',
          error
        );

        // Token expirado, inválido o backend rechazó la sesión
        ApiService.logout();

        if (mounted) {
          setUser(null);
        }
      }
    };

    loadSession();

    return () => {
      mounted = false;
    };
  }, []);

  // =========================================================
  // LOGIN EXITOSO
  // =========================================================

  const handleLoginSuccess = (
    loggedInUser: AppUser
  ) => {
    setUser(loggedInUser);
    setIsAuthOpen(false);
  };

  // =========================================================
  // LOGOUT
  // =========================================================

  const handleLogout = () => {
    ApiService.logout();

    setUser(null);
    setActiveTab('demo');
    setIsAuthOpen(false);
  };

  // =========================================================
  // RENDER
  // =========================================================

  return (
    <div className="min-h-screen flex flex-col justify-between">

      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        theme={theme}
        setTheme={setTheme}
        lang={lang}
        setLang={setLang}
        user={user}
        onOpenAuth={() =>
          setIsAuthOpen(true)
        }
        onLogout={handleLogout}
      />

      <main className="flex-1 container mx-auto px-4 md:px-6">

        {(activeTab === 'demo' ||
          activeTab === 'analizar') && (
          <>
            <Hero lang={lang} />
            <Features />
          </>
        )}

        {activeTab === 'equipo' && (
          <TeamView lang={lang} />
        )}

        {activeTab === 'docs' && (
          <DocView lang={lang} />
        )}

        {activeTab === 'api' && (
          <ApiView lang={lang} />
        )}

      </main>

      <Footer
        setActiveTab={setActiveTab}
        lang={lang}
      />

      <AuthModal
        isOpen={isAuthOpen}
        onClose={() =>
          setIsAuthOpen(false)
        }
        onLoginSuccess={
          handleLoginSuccess
        }
        lang={lang}
      />

    </div>
  );
}

export default App;