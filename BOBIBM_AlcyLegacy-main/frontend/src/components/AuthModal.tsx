import React, { useState } from 'react';
import { X } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (user: { name: string; email: string }) => void;
  lang: 'es' | 'en';
}

const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onLoginSuccess, lang }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const userName = name || email.split('@')[0] || 'Usuario';
    onLoginSuccess({ name: userName, email: email || 'user@ibm.com' });
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
      <div className="relative w-full max-w-md bg-[#101A2E] border border-[#1E2C47] p-8 shadow-2xl">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-[#7C8BA8] hover:text-[#E8EDF5] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="font-mono-custom text-lg font-bold text-[#E8EDF5] mb-2">
          {isRegister 
            ? (lang === 'es' ? 'Crear Cuenta — Alcy Legacy' : 'Create Account — Alcy Legacy')
            : (lang === 'es' ? 'Iniciar Sesión' : 'Sign In')}
        </h3>
        <p className="text-xs text-[#7C8BA8] mb-6 leading-relaxed">
          {lang === 'es' 
            ? 'Accede al prototipo del Skill de IBM Bob para guardar tus análisis de código legacy.'
            : 'Access the IBM Bob Skill prototype to save your legacy code analyses.'}
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="block font-mono-custom text-[10px] text-[#7C8BA8] uppercase tracking-wider mb-1">
                {lang === 'es' ? 'Nombre completo' : 'Full Name'}
              </label>
              <input 
                type="text" 
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Developer IBM"
                className="w-full bg-[#17223A] border border-[#1E2C47] text-[#E8EDF5] font-mono-custom text-xs p-3 focus:outline-none focus:border-[#4C7EFF]"
              />
            </div>
          )}

          <div>
            <label className="block font-mono-custom text-[10px] text-[#7C8BA8] uppercase tracking-wider mb-1">
              Email
            </label>
            <input 
              type="email" 
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="developer@ibm.com"
              className="w-full bg-[#17223A] border border-[#1E2C47] text-[#E8EDF5] font-mono-custom text-xs p-3 focus:outline-none focus:border-[#4C7EFF]"
            />
          </div>

          <div>
            <label className="block font-mono-custom text-[10px] text-[#7C8BA8] uppercase tracking-wider mb-1">
              {lang === 'es' ? 'Contraseña' : 'Password'}
            </label>
            <input 
              type="password" 
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-[#17223A] border border-[#1E2C47] text-[#E8EDF5] font-mono-custom text-xs p-3 focus:outline-none focus:border-[#4C7EFF]"
            />
          </div>

          <button 
            type="submit"
            className="w-full bg-[#4C7EFF] text-white font-mono-custom text-xs font-bold py-3 uppercase tracking-wider hover:bg-[#3b66d9] transition-all shadow-[0_0_15px_rgba(76,126,255,0.3)] mt-2"
          >
            {isRegister 
              ? (lang === 'es' ? 'Registrarse' : 'Register') 
              : (lang === 'es' ? 'Ingresar' : 'Sign In')}
          </button>
        </form>

        <div className="flex items-center gap-3 my-6">
          <div className="flex-1 h-px bg-[#1E2C47]"></div>
          <span className="font-mono-custom text-[10px] text-[#7C8BA8] uppercase">O</span>
          <div className="flex-1 h-px bg-[#1E2C47]"></div>
        </div>

        <button 
          onClick={() => {
            onLoginSuccess({ name: 'IBM Developer', email: 'developer@ibm.com' });
            onClose();
          }}
          className="w-full bg-white text-gray-900 font-sans text-xs font-medium py-3 px-4 flex items-center justify-center gap-3 hover:bg-gray-100 transition-colors"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
          </svg>
          {lang === 'es' ? 'Continuar con Google' : 'Continue with Google'}
        </button>

        <p className="font-mono-custom text-center text-xs text-[#7C8BA8] mt-6">
          {isRegister ? (lang === 'es' ? '¿Ya tienes cuenta?' : 'Already have an account?') : (lang === 'es' ? '¿No tienes cuenta?' : "Don't have an account?")}{' '}
          <button 
            onClick={() => setIsRegister(!isRegister)}
            className="text-[#4C7EFF] underline underline-offset-2 ml-1"
          >
            {isRegister ? (lang === 'es' ? 'Inicia sesión' : 'Sign In') : (lang === 'es' ? 'Regístrate' : 'Register')}
          </button>
        </p>
      </div>
    </div>
  );
};

export default AuthModal;
