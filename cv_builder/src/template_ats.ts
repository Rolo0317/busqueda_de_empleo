import type { Certification, Profile } from './types.js';
import { esc, mesAnio, sinEtiquetas } from './formato.js';

/**
 * Version del CV pensada para los filtros automaticos (ATS).
 *
 * La version de diseño se lee bien por una persona, pero un ATS la extraia asi:
 * el nombre en la linea 18, "E X P E R I E N C I A" letra por letra, las cifras
 * grandes cortadas y los cuatro cargos juntos antes de sus logros. Aqui el orden
 * del HTML es el orden de lectura: una sola columna, sin tablas, sin iconos ni
 * texto decorativo, con los titulos de seccion que los ATS reconocen.
 *
 * Mismo perfil, misma verdad: solo cambia la forma.
 */
export function renderCvAts(profile: Profile, css: string): string {
  const { cv } = profile;

  const contacto = [profile.phone, profile.email, profile.city, profile.linkedin]
    .filter(Boolean)
    .map(esc)
    .join(' | ');

  const experiencia = profile.experience
    .map((job) => `<section class="empleo">
      <h3>${esc(job.role)}</h3>
      <p class="empresa">${esc(job.company)} | ${esc(job.period)}</p>
      <ul>
        ${job.achievements.map((a) => `<li>${esc(a)}.</li>`).join('\n        ')}
      </ul>
    </section>`)
    .join('\n    ');

  const educacion = profile.education
    .map((e) => `<li>${esc(e.degree)} | ${esc(e.institution)} | ${esc(e.year)}</li>`)
    .join('\n      ');

  const certificaciones = profile.certifications_detail
    .map((c) => `<li>${lineaCertificado(c)}</li>`)
    .join('\n      ');

  const idiomas = cv.languages.map((l) => esc(l.label)).join(', ');

  return `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>${esc(profile.name)} - ${esc(profile.title)}</title>
<style>
${css}
</style>
</head>
<body>
  <h1>${esc(profile.name)}</h1>
  <p class="titulo">${esc(profile.title)}</p>
  <p class="contacto">${contacto}</p>

  <h2>Perfil profesional</h2>
  <p>${esc(sinEtiquetas(cv.headline))}</p>

  <h2>Experiencia laboral</h2>
    ${experiencia}

  <h2>Educación</h2>
  <ul>
      ${educacion}
  </ul>

  <h2>Certificaciones</h2>
  <ul>
      ${certificaciones}
  </ul>

  <h2>Habilidades técnicas</h2>
  <p>${cv.tech_stack.map(esc).join(', ')}</p>

  <h2>Competencias</h2>
  <p>${profile.soft_skills.map(esc).join(', ')}</p>

  <h2>Idiomas</h2>
  <p>${idiomas}</p>
</body>
</html>
`;
}

function lineaCertificado(cert: Certification): string {
  const partes = [esc(cert.titulo), esc(cert.entidad)];
  if (cert.horas !== undefined) partes.push(`${cert.horas} horas`);
  partes.push(mesAnio(cert.fecha));
  return partes.join(' | ');
}
