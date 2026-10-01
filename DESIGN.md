---
name: Arquitectura Medallón
description: Hoja de vida en papel impreso — un estrato de tinta que sangra al borde, tres acentos con función asignada y ni un gris intermedio.
colors:
  papel: "#FAFAF7"
  tinta: "#14181F"
  oro: "#C8960C"
  plata: "#59636F"
  bronce: "#8C5A2B"
  filete: "#C7CDD4"
  filete-tinta: "rgba(250,250,247,.30)"
typography:
  display:
    fontFamily: "Segoe UI, system-ui, -apple-system, Arial, sans-serif"
    fontSize: "58px"
    fontWeight: 700
    lineHeight: 0.92
    letterSpacing: "-0.03em"
  display-compact:
    fontFamily: "Segoe UI, system-ui, -apple-system, Arial, sans-serif"
    fontSize: "34px"
    fontWeight: 700
    lineHeight: 0.92
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "Segoe UI, system-ui, -apple-system, Arial, sans-serif"
    fontSize: "19px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Segoe UI, system-ui, -apple-system, Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 700
    lineHeight: 1.42
    letterSpacing: "normal"
  body:
    fontFamily: "Segoe UI, system-ui, -apple-system, Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.42
    letterSpacing: "normal"
    fontFeature: "tabular-nums"
  body-dense:
    fontFamily: "Segoe UI, system-ui, -apple-system, Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.38
    letterSpacing: "normal"
  label:
    fontFamily: "Segoe UI, system-ui, -apple-system, Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0.16em"
  label-role:
    fontFamily: "Segoe UI, system-ui, -apple-system, Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.13em"
rounded:
  none: "0"
  frame: "2px"
spacing:
  hair: "3px"
  xs: "4px"
  sm: "9px"
  md: "13px"
  lg: "16px"
  xl: "22px"
  margen: "10mm"
components:
  header-stratum:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.papel}"
    rounded: "{rounded.none}"
    padding: "16px 22px 13px"
  stat-figure:
    textColor: "{colors.oro}"
    typography: "{typography.headline}"
  stat-caption:
    textColor: "{colors.papel}"
    typography: "{typography.body-dense}"
  section-heading:
    textColor: "{colors.plata}"
    typography: "{typography.label}"
    padding: "0 0 4px"
  job-meta:
    textColor: "{colors.plata}"
    typography: "{typography.body-dense}"
  credential-row:
    backgroundColor: "{colors.papel}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.none}"
    padding: "4px 0"
  credential-issuer:
    textColor: "{colors.bronce}"
    typography: "{typography.body-dense}"
  tech-tag:
    backgroundColor: "transparent"
    textColor: "{colors.tinta}"
    rounded: "{rounded.none}"
    padding: "0 12px 0 0"
  tech-tag-primary:
    backgroundColor: "transparent"
    textColor: "{colors.tinta}"
    typography: "{typography.title}"
    rounded: "{rounded.none}"
  contact-item:
    textColor: "{colors.papel}"
    typography: "{typography.body-dense}"
  contact-item-principal:
    textColor: "{colors.papel}"
    typography: "{typography.title}"
  avatar-frame:
    rounded: "{rounded.frame}"
    width: "72px"
    height: "72px"
---

# Design System: Arquitectura Medallón

## Overview

**Creative North Star: "El estrato de mineral"**

Este mundo trata el documento como una veta cortada: una franja de tinta compacta arriba, y debajo capas de papel separadas únicamente por filetes. Cada metal del mundo tiene un trabajo asignado antes de tener un color. El oro marca lo probado con cifra, el bronce la credencial verificable, la plata la trayectoria y las etiquetas. Ningún metal se gasta para decorar: cuando algo necesita destacar y no es una cifra, una credencial ni una fecha, se destaca con peso y escala, nunca con un acento.

La densidad es alta y deliberada — el artefacto tiene que caber en dos páginas A4 y ser leído por un filtro ATS antes que por una persona. De ahí que no haya tarjetas, ni cajas, ni fondos de bloque: la única superficie con fondo propio en todo el documento es el estrato de tinta del encabezado, que sangra a los bordes del papel anulando el margen de página. Todo lo demás vive directamente sobre el papel y se separa con líneas de un píxel que cruzan la hoja entera.

No hay grises intermedios. Cada trozo de texto resuelve a tinta o a uno de los tres acentos; el filete existe solo como línea y nunca como color de texto. Esa disciplina es también lo que sostiene el contraste: los tres acentos se midieron sobre el papel real y todos superan AA.

**Key Characteristics:**
- Un solo fondo en todo el documento: el estrato de tinta que sangra al borde.
- Tres acentos con función asignada, nunca decorativa.
- Cero grises intermedios; todo texto es tinta o acento.
- Separación por filetes de ancho completo, jamás por cajas ni píldoras.
- Énfasis por peso y escala; los acentos no se gastan en énfasis.
- Densidad calibrada a dos páginas A4 con piso tipográfico de 12px.

## Colors

Una paleta de papel y metales: fondo cálido casi blanco, tinta azulada profunda y tres metales que solo aparecen cuando su función aparece.

### Primary
- **Oro Probado** (`{colors.oro}`): exclusivo de las cuatro cifras de resultado en el estrato de tinta. No toca ningún otro elemento del documento — ni títulos, ni enlaces, ni viñetas. Vive siempre sobre tinta (6.63:1).

### Secondary
- **Bronce Credencial** (`{colors.bronce}`): exclusivo del emisor de una credencial verificable — institución, entidad certificadora, cargo de quien da la referencia. Si el dato no se puede verificar con un tercero, no lleva bronce. Sobre papel: 5.56:1.

### Tertiary
- **Plata Trayectoria** (`{colors.plata}`): la capa de contexto — títulos de sección, empresa, periodo, año, competencias blandas, la viñeta de logro. Es el color de "cuándo y dónde", no de "qué". Sobre papel: 5.84:1.

### Neutral
- **Papel Cálido** (`{colors.papel}`): el fondo del documento entero y el color del texto dentro del estrato de tinta.
- **Tinta Profunda** (`{colors.tinta}`): todo el texto sustantivo sobre papel, y el fondo del estrato del encabezado. No existe un segundo nivel de gris para texto.
- **Filete** (`{colors.filete}`): líneas y separadores sobre papel. Nunca texto.
- **Filete sobre Tinta** (`{colors.filete-tinta}`): la única línea dentro del estrato oscuro, la que separa las cifras del bloque de contacto.

### Named Rules
**La Regla del Metal con Oficio.** Cada acento tiene un oficio y solo uno: oro = cifra probada, bronce = credencial verificable, plata = trayectoria y etiqueta. Un elemento nuevo recibe un acento solo si cae dentro de uno de esos tres oficios; si no cae en ninguno, va en tinta.

**La Regla de Cero Grises.** No existe texto en gris intermedio. Todo carácter resuelve a tinta, a papel o a un acento. Bajar la opacidad de un texto o inventar un `#6b7280` rompe el mundo y baja el contraste medido.

**La Regla del Filete Mudo.** El filete es color de línea y nunca de texto. Un separador puede ser filete; una palabra, jamás.

**La Regla del Contraste Medido.** Un acento nuevo o retocado no entra sin contraste medido contra su fondo real (papel o tinta) y sin superar 4.5:1. La plata original de la dirección (`#8A95A5`) daba 2.90:1 y fue corregida a `{colors.plata}` por esa razón; el valor medido manda sobre el valor propuesto.

## Typography

**Display Font:** Segoe UI (con `system-ui`, `-apple-system`, Arial de respaldo)
**Body Font:** la misma familia. El documento es monotipográfico por requisito funcional: el PDF se imprime y se parsea sin fuentes incrustadas, así que no hay webfont en ninguna capa.

**Character:** Una sola voz neutra que se diferencia solo por peso, escala y tracking. La personalidad no viene de la letra, viene de la jerarquía: un nombre enorme y apretado contra etiquetas diminutas y muy espaciadas.

### Hierarchy
- **Display** (700, 58px, line-height .92, tracking -0.03em, mayúsculas): el nombre, y solo el nombre. Es la única jugada de escala del documento; en pantallas ≤640px baja a 34px (**display-compact**).
- **Headline** (700, 19px, tracking -0.01em): las cifras de resultado. Único texto en oro.
- **Title** (700, 13px): cargo de cada puesto, correo y teléfono, tecnología destacada, nombre de quien da la referencia.
- **Body** (400, 13px, line-height 1.42, cifras tabulares): el párrafo de perfil y el texto general.
- **Body-dense** (400, 12px, line-height 1.38): logros, credenciales, stack, competencias, contacto secundario. Es el piso: nada baja de 12px.
- **Label** (700, 12px, tracking 0.16em, mayúsculas): títulos de sección, en plata y sobre un filete.
- **Label-role** (600, 12px, tracking 0.13em, mayúsculas): el cargo profesional bajo el nombre, en papel sobre tinta.

### Named Rules
**La Regla del Piso de 12px.** Ningún texto — de cuerpo, funcional, de apoyo o legal — baja de 12px. Si algo no cabe, se recorta el contenido, no el tamaño.

**La Regla de la Jugada Única.** Existe exactamente un salto de escala grande en el documento, el nombre. Un segundo elemento a escala de display destruye la jerarquía y se prohíbe.

**La Regla del Énfasis Barato.** El énfasis dentro de un párrafo se hace con `font-weight: 700` sobre tinta. Nunca con color, nunca con subrayado, nunca con fondo.

## Layout

Columna única de ancho medido en papel: el contenedor es de `190mm` centrado, con margen de página `{spacing.margen}` en A4. No hay barra lateral, ni columnas paralelas, ni rejilla de contenido — el orden de lectura del HTML es el orden visual, que es lo que exige el parseo ATS.

El ritmo vertical es cerrado y se apoya en pocos pasos: `{spacing.md}` entre secciones y bloques de cifras, `{spacing.sm}` entre puestos y bajo cada título de sección, `{spacing.xs}` dentro de una fila de credencial, `{spacing.hair}` entre una viñeta y la siguiente. El estrato de tinta lleva el único padding grande del documento (`16px 22px 13px`).

Dos rejillas locales, ambas dentro del encabezado o de la lista de credenciales: las cifras en cuatro columnas iguales (`repeat(4,1fr)`, gap 13px) y cada credencial en dos columnas (`1fr auto`, título a la izquierda y año alineado a la derecha).

**Responsive.** Un solo punto de corte, `max-width: 640px`, y explícitamente solo en `screen`. Ahí: las cifras pasan a dos columnas, el nombre baja a 34px, el retrato deja de ser absoluto y pasa al flujo sobre el nombre, el encabezado de puesto se apila y la credencial pasa a una columna con el año alineado a la izquierda.

**Impresión.** La ruta de impresión es una superficie de primera clase, no un extra: `@page { size: A4; margin: 10mm }`, colores forzados con `print-color-adjust: exact`, y protección de cortes (`break-inside: avoid` en sección, puesto y credencial; `break-after: avoid` en títulos de sección y en el estrato). El inset negativo que hace sangrar el estrato a los bordes vive **solo** dentro de `@media print`; en pantalla desbordaba por la izquierda a 390px.

### Named Rules
**La Regla del Orden Lineal.** Una sola columna, el orden del DOM es el orden de lectura. Ninguna reordenación visual (grid areas, `order`, posicionamiento) puede separar lo que se ve de lo que lee la máquina.

**La Regla de las Dos Páginas.** El artefacto cabe en dos páginas A4. Todo elemento nuevo se paga con densidad en otro sitio; ninguna adición puede empujar a una tercera página.

**La Regla del Sangrado Solo en Papel.** El inset negativo que lleva el estrato hasta el borde pertenece a `@media print`. En pantalla el estrato respeta el contenedor.

## Elevation & Depth

Este sistema no tiene sombras. Ni una sola: no hay `box-shadow`, `text-shadow` ni `filter` en toda la hoja de estilos. Es un documento de papel y se comporta como tal.

La profundidad se consigue por dos medios, ambos planos: **inversión tonal** (el estrato de tinta sobre el papel, que hace que el encabezado se lea como una placa incrustada y no como una tarjeta flotante) y **filetes de un píxel** que separan capas de contenido. No hay capas intermedias; el documento tiene exactamente dos niveles tonales, papel y tinta.

### Named Rules
**La Regla del Papel Plano.** Cero sombras, en cualquier estado. La profundidad se expresa invirtiendo tono o trazando una línea; si una superficie necesita "levantarse", está mal planteada.

**La Regla del Estrato Único.** Existe un solo bloque con fondo propio en el documento. Añadir una segunda superficie con fondo la convierte en una tarjeta y rompe el mundo.

## Shapes

Esquinas rectas en todo. El único radio del documento es `{rounded.frame}` en el marco del retrato (72×72px, recorte `object-fit: cover` anclado arriba) — un ablandamiento apenas perceptible que existe para que la foto no parezca pegada.

La forma dominante no es un contenedor sino una línea: el filete de un píxel, siempre de ancho completo cuando separa contenido (bajo cada título de sección, entre credenciales, entre cifras y contacto). Hay dos usos de línea vertical, ambos en filete neutro y ambos como marca, no como caja: el separador entre etiquetas de stack (`::after` de 1px entre elementos) y la barra izquierda del bloque de referencia (`border-left: 1px`). La viñeta de logro es también una línea: un guion de 4×1px en plata, no un punto ni un glifo.

### Named Rules
**La Regla de la Línea, no la Caja.** El mundo separa con reglas, no con recipientes. Cuando dos cosas necesitan distinguirse, se traza un filete entre ellas; no se mete una en una caja.

**La Regla del Trazo Neutro.** Cualquier línea del documento — horizontal, vertical, divisoria o de viñeta — es filete o plata. Una línea de color de acento no existe en este mundo.

## Components

### Estrato de tinta (encabezado)
La placa que abre el documento: fondo tinta, texto papel, esquinas rectas, padding `16px 22px 13px`. Contiene el nombre a escala display, el cargo en etiqueta espaciada, la rejilla de cuatro cifras y la fila de contacto. Es el único bloque con fondo propio. En impresión se extiende hasta los bordes de la hoja con el inset negativo del margen.

### Cifra probada
- **Forma:** sin caja, sin fondo, sin borde. Una columna de la rejilla de cuatro.
- **Color:** la cifra en oro (19px, 700); la glosa debajo en papel (12px, line-height 1.3).
- **Regla:** solo entra aquí un resultado con número o estado verificable. Es el único lugar del documento donde aparece el oro.

### Título de sección
- **Forma:** texto en mayúsculas con tracking 0.16em, en plata, sobre un filete de ancho completo con 4px de aire arriba de la línea y 9px debajo.
- **Comportamiento de impresión:** `break-after: avoid` — nunca queda huérfano al pie de página.

### Fila de puesto
- **Forma:** cabecera de dos partes alineadas a la línea base (cargo + empresa a la izquierda, periodo a la derecha, `white-space: nowrap`).
- **Color:** cargo en tinta 700 (13px); empresa y periodo en plata 600 (12px).
- **Logros:** lista sin marcador, sangría de 11px, viñeta dibujada como guion de 4×1px en plata a 7px del tope de línea.
- **Móvil:** la cabecera se apila (`flex-direction: column`, gap 1px).

### Fila de credencial
- **Forma:** rejilla `1fr auto`, padding vertical 4px, separada de la siguiente por un filete de ancho completo; la última fila no lleva filete.
- **Color:** título en tinta 600 (12px); emisor en bronce (12px); año en plata 600 alineado a la derecha. Una nota de estado dentro del emisor (`em`, sin cursiva) baja a plata.
- **Regla:** educación y certificaciones comparten esta fila porque comparten oficio — credencial verificable.

### Etiqueta de stack
- **Forma:** texto desnudo con 12px de padding derecho y un filete vertical de 1px dibujado con `::after`; el último elemento no lo lleva. No es una píldora: no tiene fondo, ni borde, ni radio.
- **Estado destacado:** peso 700. Nunca color.

### Ítem de contacto
- **Forma:** icono SVG en línea de 14px (trazo `currentColor`, opacidad .75) seguido del valor, en fila con gap 5px.
- **Jerarquía:** teléfono y correo son la acción primaria y se marcan a 13px/700; ciudad y LinkedIn quedan a 12px/400. La jerarquía es de peso, no de color: todo el bloque es papel sobre tinta.

### Bloque de referencia
- **Forma:** barra izquierda de 1px en filete con 12px de sangría. Sin fondo, sin caja.
- **Color:** nombre en tinta 700 (12px); cargo en bronce; la cita en tinta a 12px/1.38.

## Do's and Don'ts

### Do:
- **Do** asignar a cada acento su oficio antes de usarlo: oro solo en cifra probada, bronce solo en credencial verificable, plata en trayectoria y etiqueta.
- **Do** medir el contraste de cualquier color nuevo contra su fondo real (papel `{colors.papel}` o tinta `{colors.tinta}`) y exigirle ≥4.5:1 antes de aceptarlo.
- **Do** resolver todo texto a tinta, papel o un acento; sin grises intermedios ni opacidades para "suavizar".
- **Do** enfatizar con `font-weight: 700` y con escala.
- **Do** separar contenido con un filete de ancho completo.
- **Do** mantener el piso de 12px en todo texto.
- **Do** mantener el orden del DOM igual al orden de lectura visual, en una sola columna.
- **Do** probar cada cambio en las tres rutas — 1440px, 390px e impresión A4 — y confirmar que sigue cabiendo en dos páginas.
- **Do** dejar cualquier truco de sangrado al borde dentro de `@media print`.
- **Do** dibujar los iconos como SVG en línea con trazo `currentColor`.

### Don't:
- **Don't** anidar una tarjeta dentro de otra; de hecho, no introducir una segunda superficie con fondo propio: el estrato de tinta es la única.
- **Don't** usar píldoras, chips ni etiquetas con fondo y radio. Las listas se separan con filetes verticales.
- **Don't** usar bordes laterales **de color de acento** como marca de bloque. Una barra izquierda en filete neutro sí es del mundo (el bloque de referencia la usa); teñirla de oro, bronce o plata no lo es.
- **Don't** gastar un acento en énfasis. Un acento marca una función, no una intensidad.
- **Don't** añadir sombras de ningún tipo, ni difusas ni duras ni desplazadas.
- **Don't** introducir un segundo elemento a escala de display; el nombre es la única jugada de escala.
- **Don't** meter grises intermedios, ni usar `{colors.filete}` como color de texto.
- **Don't** añadir una segunda columna, una barra lateral ni reordenar visualmente respecto al DOM.
- **Don't** añadir puntos de corte más allá de `640px`, ni tocar la ruta de impresión desde un media query de pantalla.
- **Don't** usar fuentes de icono ni glifos de texto como iconos.
- **Don't** incrustar webfonts: la familia del sistema es requisito de portabilidad del PDF y de parseo ATS, no una preferencia estética.
