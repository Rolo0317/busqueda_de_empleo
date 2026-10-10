import { mkdir, readFile, writeFile, copyFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadProfile } from './profile.js';
import { renderCv } from './template.js';
import { renderCvAts } from './template_ats.js';
import { exportPdf } from './pdf.js';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = resolve(AQUI, '..', '..');

const RUTAS = {
  perfil: join(RAIZ, 'job_bot', 'candidate_profile.json'),
  css: join(RAIZ, 'cv_builder', 'static', 'cv.css'),
  cssAts: join(RAIZ, 'cv_builder', 'static', 'cv_ats.css'),
  foto: join(RAIZ, 'cv_builder', 'static', 'foto_corporativa.jpeg'),
  // Versionada a proposito: Vercel la publica tal cual, porque alla no estan
  // el perfil privado ni el Chromium que generan el PDF.
  salida: join(RAIZ, 'sitio'),
} as const;

/** El limite no es estetico: un CV de 3 paginas se descarta antes de leerse. */
const MAX_PAGINAS = 2;

interface Version {
  /** Para quien es: aparece en el resumen del build. */
  nombre: string;
  html: string;
  archivoHtml: string;
  archivoPdf: string;
}

async function main(): Promise<void> {
  const [profile, css, cssAts] = await Promise.all([
    loadProfile(RUTAS.perfil),
    readFile(RUTAS.css, 'utf-8'),
    readFile(RUTAS.cssAts, 'utf-8'),
  ]);

  await mkdir(RUTAS.salida, { recursive: true });
  await copyFile(RUTAS.foto, join(RUTAS.salida, 'foto_corporativa.jpeg'));

  // Dos versiones del mismo perfil: la de diseño para personas y la web, y la
  // sobria para los filtros automaticos de las bolsas de empleo.
  const versiones: Version[] = [
    { nombre: 'diseño', html: renderCv(profile, css),
      archivoHtml: 'index.html', archivoPdf: 'cv_william_solano.pdf' },
    { nombre: 'ATS', html: renderCvAts(profile, cssAts),
      archivoHtml: 'ats.html', archivoPdf: 'cv_william_solano_ats.pdf' },
  ];

  let excedido = false;
  for (const version of versiones) {
    excedido = (await generar(version)) || excedido;
  }

  // Con CV_STRICT=1 el exceso rompe el build, para que un despliegue no publique
  // un CV demasiado largo sin que nadie lo revise.
  if (excedido && process.env['CV_STRICT'] === '1') process.exitCode = 1;
}

/** Escribe el HTML, exporta el PDF y avisa si pasa del limite de paginas. */
async function generar(version: Version): Promise<boolean> {
  const htmlPath = join(RUTAS.salida, version.archivoHtml);
  const pdfPath = join(RUTAS.salida, version.archivoPdf);
  await writeFile(htmlPath, version.html, 'utf-8');

  const { pages, bytes } = await exportPdf(htmlPath, pdfPath);
  console.log(`[${version.nombre}] ${pdfPath}  (${pages} paginas, ${(bytes / 1024).toFixed(0)} KB)`);

  if (pages > MAX_PAGINAS) {
    console.error(`  AVISO: ocupa ${pages} paginas y el limite es ${MAX_PAGINAS}.`);
    return true;
  }
  return false;
}

main().catch((error: unknown) => {
  console.error('Fallo la generacion del CV:', error);
  process.exit(1);
});
