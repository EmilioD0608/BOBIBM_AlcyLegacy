import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import Features from './components/Features';
import TeamView from './components/TeamView';
import DocView from './components/DocView';
import ApiView from './components/ApiView';
import Footer from './components/Footer';
import AuthModal from './components/AuthModal';

function App() {
  const [activeTab, setActiveTab] = useState<string>('demo');
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [lang, setLang] = useState<'es' | 'en'>('es');
  const [isAuthOpen, setIsAuthOpen] = useState<boolean>(false);
  const [user, setUser] = useState<{ name: string; email: string } | null>(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

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
        onOpenAuth={() => setIsAuthOpen(true)}
        onLogout={() => setUser(null)}
      />

      <main className="flex-1 container mx-auto px-4 md:px-6">
        {(activeTab === 'demo' || activeTab === 'analizar') && (
          <>
            <Hero lang={lang} />
            <Features />
          </>
        )}

        {activeTab === 'equipo' && <TeamView lang={lang} />}
        {activeTab === 'docs' && <DocView lang={lang} />}
        {activeTab === 'api' && <ApiView lang={lang} />}
      </main>

      <Footer setActiveTab={setActiveTab} lang={lang} />

      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onLoginSuccess={(loggedInUser) => setUser(loggedInUser)}
        lang={lang}
      />
    </div>
  );
}

export default App;
