import React from 'react';
import { Github, Linkedin, Twitter } from 'lucide-react';

interface TeamViewProps {
  lang: 'es' | 'en';
}

const TeamView: React.FC<TeamViewProps> = ({ lang }) => {
  const teamMembers = [
    {
      name: 'Montoy4d',
      role: 'Security Engineering & Systems Integration',
      avatar: '/avatars/montoy4d.jpg',
      github: 'https://github.com/montoyak20',
      linkedin: null,
      twitter: null,
    },
    {
      name: 'Jamar Masias',
      role: 'Product Lead, Frontend Architecture & Security',
      avatar: '/avatars/jamar_masias.jpg',
      github: 'https://github.com/jammar24',
      linkedin: 'https://www.linkedin.com/in/jamar-masias/',
      twitter: 'https://x.com/3m3r4lsec',
    },
    {
      name: 'Daniel Tumbaco',
      role: 'Backend Architecture, Database & Core Auth',
      avatar: '/avatars/daniel_tumbaco.jpg',
      github: 'https://github.com/DTumbacoE',
      linkedin: 'https://www.linkedin.com/in/daniel-tumbaco-espa%C3%B1a-51b2a035b/',
      twitter: 'https://x.com/espana83782',
    },
    {
      name: 'Emilio Delgado',
      role: 'DevOps Lead & AI Infrastructure',
      avatar: '/avatars/emilio_delgado.jpg',
      github: 'https://github.com/EmilioD0608',
      linkedin: 'https://www.linkedin.com/in/emilio-d-d-l/',
      twitter: 'https://x.com/MilioSlime',
    },
  ];

  return (
    <div className="max-w-5xl mx-auto py-12">
      <div className="text-center mb-12">
        <div className="eyebrow justify-center mb-2">IBM BOB 2.0 HACKATHON</div>
        <h1 className="font-mono-custom text-3xl font-bold text-[var(--text)] mb-3">
          {lang === 'es' ? 'Nuestro equipo' : 'Our team'}
        </h1>
        <p className="text-sm text-[var(--muted)] max-w-xl mx-auto font-mono-custom">
          {lang === 'es'
            ? 'El talento multidisciplinario detrás de Alcy Legacy — construido en 48 horas para el IBM Bob 2.0 Hackathon.'
            : 'The multidisciplinary talent behind Alcy Legacy — built in 48 hours for the IBM Bob 2.0 Hackathon.'}
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {teamMembers.map((member, i) => (
          <div key={i} className="panel-custom p-6 text-center hover:border-[var(--blue)] transition-all group flex flex-col justify-between">
            <div>
              <div className="w-24 h-24 rounded-full border-2 border-[var(--grid)] mx-auto mb-4 overflow-hidden group-hover:border-[var(--blue)] transition-colors shadow-md bg-[var(--panel-2)]">
                <img
                  src={member.avatar}
                  alt={member.name}
                  className="w-full h-full object-cover"
                  loading="lazy"
                  onError={(e) => {
                    // Fallback to initials if image fails
                    (e.target as HTMLElement).style.display = 'none';
                  }}
                />
              </div>
              <h3 className="font-mono-custom text-base font-bold text-[var(--text)] mb-1">{member.name}</h3>
              <span className="inline-block font-mono-custom text-[10px] text-[var(--blue)] uppercase border border-[var(--blue-dim)] px-2.5 py-1 bg-[var(--blue)]/10 mb-4 tracking-wider leading-relaxed">
                {member.role}
              </span>
            </div>
            <div className="flex justify-center gap-3 pt-2 border-t border-[var(--grid)]">
              {member.github && (
                <a
                  href={member.github}
                  target="_blank"
                  rel="noopener noreferrer"
                  title="GitHub"
                  className="w-8 h-8 rounded-full border border-[var(--grid)] flex items-center justify-center text-[var(--muted)] hover:border-[var(--blue)] hover:text-[var(--blue)] transition-all"
                >
                  <Github className="w-4 h-4" />
                </a>
              )}
              {member.linkedin && (
                <a
                  href={member.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  title="LinkedIn"
                  className="w-8 h-8 rounded-full border border-[var(--grid)] flex items-center justify-center text-[var(--muted)] hover:border-[var(--blue)] hover:text-[var(--blue)] transition-all"
                >
                  <Linkedin className="w-4 h-4" />
                </a>
              )}
              {member.twitter && (
                <a
                  href={member.twitter}
                  target="_blank"
                  rel="noopener noreferrer"
                  title="X / Twitter"
                  className="w-8 h-8 rounded-full border border-[var(--grid)] flex items-center justify-center text-[var(--muted)] hover:border-[var(--blue)] hover:text-[var(--blue)] transition-all"
                >
                  <Twitter className="w-4 h-4" />
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TeamView;
