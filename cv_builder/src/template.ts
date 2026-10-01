import type { Certification, Profile } from './types.js';
import { splitName } from './profile.js';
import { esc, mesAnio } from './formato.js';

function certSubtitle(cert: Certification): string {
  const partes = [esc(cert.entidad)];
  if (cert.horas !== undefined) partes.push(`${cert.horas} horas`);
  if (cert.vigente === false) partes.push('<em>vigencia vencida</em>');
  return partes.join(' · ');
}

const ICONOS: Record<string, string> = {
  phone: '<path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07A19.5 19.5 0 013.95 12a19.79 19.79 0 01-3.07-8.67A2 2 0 012.85 1h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L7.09 8.64a16 16 0 006.29 6.29l1-.95a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z"/>',
  mail: '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>',
  pin: '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/>',
  linkedin: '<path d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-2-2 2 2 0 00-2 2v7h-4v-7a6 6 0 016-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/>',
};

function contactItem(icon: keyof typeof ICONOS, value: string, principal = false): string {
  const clase = principal ? 'contact-item principal' : 'contact-item';
  return `<div class="${clase}">
      <svg class="ico" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">${ICONOS[icon]}</svg>
      ${esc(value)}
    </div>`;
}

/** Renderiza el CV completo. El CSS entra ya leido para que esta funcion sea pura. */
export function renderCv(profile: Profile, css: string): string {
  const { cv } = profile;
  const [firstNames, lastNames] = splitName(profile.name);

  const contacto = [
    contactItem('phone', profile.phone, true),
    contactItem('mail', profile.email, true),
    contactItem('pin', profile.city),
    contactItem('linkedin', profile.linkedin),
  ].join('\n      ');

  const logros = cv.highlights
    .map((h) => `<div class="logro-card">
          <strong>${esc(h.figure)}</strong>
          <span>${esc(h.detail)}</span>
        </div>`)
    .join('\n        ');

  const experiencia = profile.experience
    .map((job) => `<div class="job">
        <div class="job-header">
          <div>
            <div class="job-title">${esc(job.role)}</div>
            <div class="job-company">${esc(job.company)}</div>
          </div>
          <span class="job-date">${esc(job.period)}</span>
        </div>
        <ul>
          ${job.achievements.map((a) => `<li>${esc(a)}.</li>`).join('\n          ')}
        </ul>
      </div>`)
    .join('\n      ');

  // Educacion y certificados comparten el estrato bronce: ambos son credencial verificable.
  const credenciales = [
    ...profile.education.map((e) => ({
      titulo: e.degree,
      sub: esc(e.institution),
      anio: e.year,
    })),
    ...profile.certifications_detail.map((c) => ({
      titulo: c.titulo,
      sub: certSubtitle(c),
      anio: mesAnio(c.fecha),
    })),
  ]
    .map((item) => `<div class="credencial">
          <div>
            <div class="edu-title">${esc(item.titulo)}</div>
            <div class="edu-inst">${item.sub}</div>
          </div>
          <span class="edu-year">${esc(item.anio)}</span>
        </div>`)
    .join('\n        ');

  const destacadas = new Set(
    cv.sidebar_skills.filter((s) => s.primary).map((s) => s.label),
  );
  const stack = cv.tech_stack
    .map((techName) => {
      const clase = destacadas.has(techName) ? 'tech-tag destacada' : 'tech-tag';
      return `<span class="${clase}">${esc(techName)}</span>`;
    })
    .join('\n        ');

  const idiomas = cv.languages
    .map((l) => `<span>${esc(l.label)}</span>`)
    .join('\n        ');

  return `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CV - ${esc(profile.name)}</title>
<meta name="description" content="${esc(profile.title)} — ${esc(profile.city)}">
<style>
${css}
</style>
</head>
<body>
<div class="page">

  <header class="estrato-oro">
    <div class="avatar-frame">
      <img src="${esc(cv.photo)}" alt="${esc(profile.name)}">
    </div>
    <div class="name-block">
      <h1>${esc(firstNames)}<span>${esc(lastNames)}</span></h1>
      <p>${esc(profile.title)}</p>
    </div>

    <div class="logro-grid">
        ${logros}
    </div>

    <div class="contacto">
      ${contacto}
    </div>
  </header>

  <main class="main">

    <div class="headline">
      <p>${cv.headline}</p>
    </div>

    <section class="section">
      <h2>Experiencia profesional</h2>
      ${experiencia}
    </section>

    <section class="section">
      <h2>Formación y certificaciones verificables</h2>
      ${credenciales}
    </section>

    <section class="section">
      <h2>Stack técnico</h2>
      <div class="tech-grid">
        ${stack}
      </div>
      <div class="idiomas">
        ${idiomas}
      </div>
      <div class="competencias">${esc(profile.soft_skills.join(' · '))}</div>
    </section>

    <section class="section">
      <h2>Referencia laboral</h2>
      <div class="ref-card">
        <strong>${esc(cv.reference.name)}</strong>
        <em>${esc(cv.reference.role)}</em>
        <p>"${esc(cv.reference.quote)}"</p>
      </div>
    </section>

  </main>
</div>
</body>
</html>
`;
}
