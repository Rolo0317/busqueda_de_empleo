/** Forma del perfil, limitada a lo que el CV necesita renderizar. */

export interface Job {
  role: string;
  company: string;
  period: string;
  achievements: string[];
}

export interface Education {
  degree: string;
  institution: string;
  year: string;
}

export interface Certification {
  titulo: string;
  entidad: string;
  horas?: number;
  fecha: string;
  vigente?: boolean;
}

export interface SidebarSkill {
  label: string;
  primary: boolean;
}

export interface Language {
  label: string;
  level: number;
}

export interface Highlight {
  figure: string;
  detail: string;
}

export interface Reference {
  name: string;
  role: string;
  quote: string;
}

export interface CvSection {
  headline: string;
  photo: string;
  initials: string;
  highlights: Highlight[];
  sidebar_skills: SidebarSkill[];
  languages: Language[];
  interests: string[];
  tech_stack: string[];
  reference: Reference;
  private_fields: string[];
}

export interface Profile {
  name: string;
  email: string;
  phone: string;
  city: string;
  title: string;
  linkedin: string;
  soft_skills: string[];
  experience: Job[];
  education: Education[];
  certifications_detail: Certification[];
  cv: CvSection;
}

/** Que tanto del perfil se expone. La version publica omite datos sensibles. */
export type Audience = 'public' | 'ats';
