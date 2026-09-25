import React from 'react';
import { Github, Linkedin, Twitter } from 'lucide-react';

interface TeamViewProps {
  lang: 'es' | 'en';
}

const TeamView: React.FC<TeamViewProps> = ({ lang }) => {
  const teamMembers = [
    {
      name: 'Alcy Legacy Team',
      role: 'Core Lead & AI Specialist',
      avatar: 'AL',
      github: '#',
      linkedin: '#',
    },
    {
      name: 'IBM Bob Developer',
      role: 'Backend & Agent Engineer',
      avatar: 'IB',
      github: '#',
      linkedin: '#',
    },
    {
      name: 'Fullstack Engineer',
      role: 'Frontend & UX Architect',
      avatar: 'FE',
      github: '#',
      linkedin: '#',
    },
    {
      name: 'Security Researcher',
      role: 'Vulnerability Auditor',
      avatar: 'SR',
      github: '#',
      linkedin: '#',
    },
  ];

  return (
    <div className="max-w-5xl mx-auto py-12">
      <div className="text-center mb-12">
        <div className="eyebrow justify-center mb-2">IBM BOB 2.0 HACKATHON</div>
        <h1 className="font-mono-custom text-3xl font-bold text-[var(--text)] mb-3">
          {lang === 'es' ? 'Equipo Creador de Alcy Legacy' : 'The Alcy Legacy Team'}
        </h1>
        <p className="text-sm text-[var(--muted)] max-w-xl mx-auto font-mono-custom">
          {lang === 'es'
            ? 'Desarrollado para el Hackathon IBM Bob 2.0 por ingenieros enfocados en modernización de sistemas heredados.'
            : 'Built for IBM Bob 2.0 Hackathon by engineers focused on legacy system modernization.'}
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {teamMembers.map((member, i) => (
          <div key={i} className="panel-custom p-6 text-center hover:border-[var(--blue)] transition-all group">
            <div className="w-20 h-20 rounded-full bg-[var(--panel-2)] border-2 border-[var(--grid)] mx-auto mb-4 flex items-center justify-center font-mono-custom text-xl font-bold text-[var(--blue)] group-hover:border-[var(--blue)] transition-colors">
              {member.avatar}
            </div>
            <h3 className="font-mono-custom text-sm font-bold text-[var(--text)] mb-1">{member.name}</h3>
            <span className="inline-block font-mono-custom text-[10px] text-[var(--blue)] uppercase border border-[var(--blue-dim)] px-2.5 py-1 bg-[var(--blue)]/10 mb-4">
              {member.role}
            </span>
            <div className="flex justify-center gap-3">
              <a href={member.github} className="w-8 h-8 rounded-full border border-[var(--grid)] flex items-center justify-center text-[var(--muted)] hover:border-[var(--blue)] hover:text-[var(--blue)] transition-all">
                <Github className="w-4 h-4" />
              </a>
              <a href={member.linkedin} className="w-8 h-8 rounded-full border border-[var(--grid)] flex items-center justify-center text-[var(--muted)] hover:border-[var(--blue)] hover:text-[var(--blue)] transition-all">
                <Linkedin className="w-4 h-4" />
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TeamView;
