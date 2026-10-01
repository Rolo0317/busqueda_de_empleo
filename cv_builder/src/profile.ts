import { readFile } from 'node:fs/promises';
import type { Profile } from './types.js';

/** Unica fuente de verdad del perfil. */
export async function loadProfile(path: string): Promise<Profile> {
  const raw = await readFile(path, 'utf-8');
  const profile = JSON.parse(raw) as Profile;
  assertComplete(profile);
  return profile;
}

/**
 * Falla temprano y con un mensaje util: un CV a medias se publica sin que nadie
 * lo note hasta que un reclutador lo abre.
 */
function assertComplete(profile: Profile): void {
  const required: (keyof Profile)[] = [
    'name', 'title', 'experience', 'education', 'certifications_detail', 'cv',
  ];
  const missing = required.filter((key) => profile[key] === undefined);
  if (missing.length > 0) {
    throw new Error(`El perfil no tiene: ${missing.join(', ')}`);
  }
  if (profile.experience.length === 0) {
    throw new Error('El perfil no tiene experiencia laboral');
  }
}

/** "Ana Maria Perez Gomez" -> ["Ana Maria", "Perez Gomez"] */
export function splitName(fullName: string): [string, string] {
  const parts = fullName.trim().split(/\s+/);
  const mid = Math.ceil(parts.length / 2);
  return [parts.slice(0, mid).join(' '), parts.slice(mid).join(' ')];
}
