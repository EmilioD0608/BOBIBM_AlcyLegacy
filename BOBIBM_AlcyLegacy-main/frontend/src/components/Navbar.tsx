import React from 'react';
import { Sun, Moon, ShieldAlert, LogOut, User as UserIcon } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  theme: 'dark' | 'light';
  setTheme: (theme: 'dark' | 'light') => void;
  lang: 'es' | 'en';
  setLang: (lang: 'es' | 'en') => void;
  user: { name: string; email: string } | null;
  onOpenAuth: () => void;
  onLogout: () => void;
}

const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  theme,
  setTheme,
  lang,
  setLang,
  user,
  onOpenAuth,
  onLogout,
}) => {
  const navItems = [
    { id: 'demo', label: lang === 'es' ? 'Demo' : 'Demo' },
    { id: 'analizar', label: lang === 'es' ? 'Analizar' : 'Analyze' },
    { id: 'equipo', label: lang === 'es' ? 'Equipo' : 'Team' },
    { id: 'docs', label: lang === 'es' ? 'Documentación' : 'Docs' },
    { id: 'api', label: lang === 'es' ? 'API' : 'API' },
  ];

  return (
    <header className="sticky top-0 z-50 topbar-bg px-5 py-3.5 flex items-center justify-between flex-wrap gap-3">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 flex items-center justify-center bg-[#4C7EFF] rounded p-1 flex-shrink-0 text-white shadow-[0_0_10px_rgba(76,126,255,0.4)]">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <div className="flex flex-col">
          <span className="font-mono-custom text-sm font-semibold tracking-tight text-[var(--text)]">Alcy Legacy</span>
          <span className="font-mono-custom text-[10px] text-[var(--muted)] tracking-widest uppercase">IBM Bob 2.0 Hackathon</span>
        </div>
      </div>

      <nav className="flex items-center gap-5 font-mono-custom text-xs text-[var(--muted)] overflow-x-auto py-1">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`transition-colors pb-1 border-b-2 ${
              activeTab === item.id
                ? 'text-[var(--blue)] border-[var(--blue)] font-semibold'
                : 'text-[var(--muted)] border-transparent hover:text-[var(--text)]'
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <div className="flex items-center gap-3">
        {/* Language Switcher */}
        <div className="flex border border-[var(--grid)] overflow-hidden font-mono-custom text-[11px]">
          <button
            onClick={() => setLang('es')}
            className={`px-2.5 py-1.5 transition-all ${
              lang === 'es' ? 'bg-[var(--blue)] text-white font-semibold' : 'text-[var(--muted)] hover:text-[var(--text)]'
            }`}
          >
            ES
          </button>
          <button
            onClick={() => setLang('en')}
            className={`px-2.5 py-1.5 transition-all ${
              lang === 'en' ? 'bg-[var(--blue)] text-white font-semibold' : 'text-[var(--muted)] hover:text-[var(--text)]'
            }`}
          >
            EN
          </button>
        </div>

        {/* Theme Toggle */}
        <button
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          className="w-8 h-8 rounded-full border border-[var(--grid)] bg-[var(--panel)] flex items-center justify-center text-[var(--text)] hover:border-[var(--blue)] transition-colors"
          title="Cambiar tema"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-blue-500" />}
        </button>

        {/* User Auth Chip */}
        {user ? (
          <div className="flex items-center gap-2 border border-[var(--grid)] px-3 py-1.5 bg-[var(--panel)] font-mono-custom text-xs">
            <div className="w-5 h-5 rounded-full bg-[var(--blue)] text-white text-[10px] font-bold flex items-center justify-center">
              {user.name.charAt(0).toUpperCase()}
            </div>
            <span className="text-[var(--text)] max-w-[100px] truncate">{user.name}</span>
            <button onClick={onLogout} className="text-[var(--muted)] hover:text-red-400 transition-colors ml-1" title="Cerrar sesión">
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            className="font-mono-custom text-xs font-medium text-[var(--text)] border border-[var(--grid)] px-3.5 py-1.5 hover:border-[var(--blue)] transition-all flex items-center gap-1.5"
          >
            <UserIcon className="w-3.5 h-3.5 text-[var(--blue)]" />
            {lang === 'es' ? 'Iniciar Sesión' : 'Sign In'}
          </button>
        )}
      </div>
    </header>
  );
};

export default Navbar;
