import { pathToFileURL } from 'node:url';
import { chromium } from 'playwright';

export interface PdfResult {
  pages: number;
  bytes: number;
}

/**
 * Exporta el HTML ya escrito en disco. Se usa el archivo y no una cadena para que
 * el PDF resuelva la foto y cualquier recurso relativo igual que el navegador.
 */
export async function exportPdf(htmlPath: string, pdfPath: string): Promise<PdfResult> {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'networkidle' });
    await page.emulateMedia({ media: 'print' });

    const pdf = await page.pdf({ format: 'A4', printBackground: true, path: pdfPath });
    return { pages: countPages(pdf), bytes: pdf.length };
  } finally {
    await browser.close();
  }
}

const PAGINA_PDF = /[/]Type\s*[/]Page[^s]/g;

function countPages(pdf: Buffer): number {
  return (pdf.toString('latin1').match(PAGINA_PDF) ?? []).length;
}
