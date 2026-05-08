import logging
import re
from time import sleep
import unicodedata
from urllib.parse import urljoin

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import Settings
from models.job_offer import JobOffer
from platforms.base import BasePlatform
from services.question_answerer import CandidateQuestionAnswerer


class MagnetoPlatform(BasePlatform):
    BASE_URL = "https://www.magneto365.com"
    JOB_LINK_XPATH = "//a[contains(@href, '/empleos/')]"
    LOGIN_LINK_XPATH = (
        "//*[self::a or self::button][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'iniciar') "
        "and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sesi')]"
    )
    GOOGLE_LOGIN_XPATH = (
        "//*[self::a or self::button][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'google')]"
    )
    APPLY_BUTTON_XPATH = (
        "//button[contains(translate(., 'ÁÉÍÓÚABCDEFGHIJKLMNOPQRSTUVWXYZ', 'áéíóúabcdefghijklmnopqrstuvwxyz'), 'aplicar') "
        "or contains(translate(., 'ÁÉÍÓÚABCDEFGHIJKLMNOPQRSTUVWXYZ', 'áéíóúabcdefghijklmnopqrstuvwxyz'), 'postular')]"
        "|//a[contains(translate(., 'ÁÉÍÓÚABCDEFGHIJKLMNOPQRSTUVWXYZ', 'áéíóúabcdefghijklmnopqrstuvwxyz'), 'aplicar') "
        "or contains(translate(., 'ÁÉÍÓÚABCDEFGHIJKLMNOPQRSTUVWXYZ', 'áéíóúabcdefghijklmnopqrstuvwxyz'), 'postular')]"
    )
    YES_NO_ANSWER_RULES = [
        (("vinculo", "parentesco", "conyuge", "consejo directivo", "empleado de", "familiar"), "No"),
        (("conflicto de interes", "inhabilidad", "antecedentes", "sancionado", "investigacion"), "No"),
        (("discapacidad",), "No"),
        (("autorizo", "tratamiento de datos", "politica", "terminos", "condiciones"), "Si"),
        (("acepta", "acepto", "certifica", "declara"), "Si"),
    ]

    def __init__(self, driver: WebDriver, wait: WebDriverWait, settings: Settings) -> None:
        self.driver = driver
        self.wait = wait
        self.settings = settings
        self.question_answerer = CandidateQuestionAnswerer(settings.candidate_profile_path)

    def ensure_logged_in(self) -> None:
        self.driver.get(f"{self.BASE_URL}/co")
        self._close_optional_popups()

        if self._is_logged_in():
            logging.info("Sesion de Magneto detectada.")
            return

        logging.info("No hay sesion activa en Magneto. Abriendo inicio de sesion.")
        self._open_login()
        self._click_google_login_if_available()
        self._wait_for_login()

    def search(self, keyword: str) -> list[JobOffer]:
        search_url = self._build_search_url(keyword)
        logging.info("Buscando en Magneto: %s", search_url)
        self.driver.get(search_url)
        self._wait_for_results()
        offers = self._extract_offers(keyword=None)

        if offers:
            return offers

        logging.info("Busqueda por URL sin resultados. Usando pagina de ciudad para: %s", keyword)
        self.driver.get(self._build_city_url())
        self._wait_for_results()
        return self._extract_offers(keyword=keyword)

    def apply(self, offer: JobOffer) -> str:
        logging.info("Abriendo oferta: %s", offer.url)
        self.driver.get(str(offer.url))
        self._close_optional_popups()

        try:
            button = self.wait.until(EC.element_to_be_clickable((By.XPATH, self.APPLY_BUTTON_XPATH)))
        except TimeoutException:
            return "no disponible"

        button.click()
        return self._complete_application_flow()

    def _build_search_url(self, keyword: str) -> str:
        slug = self._slugify(keyword)
        return f"{self.BASE_URL}/co/trabajos/buscar/{slug}"

    def _build_city_url(self) -> str:
        city_slug = self._slugify(self.settings.magneto_city)
        return f"{self.BASE_URL}/co/trabajos/ofertas-empleo-en-{city_slug}/"

    def _wait_for_results(self) -> None:
        try:
            self.wait.until(lambda driver: len(driver.find_elements(By.XPATH, self.JOB_LINK_XPATH)) > 0)
        except TimeoutException:
            logging.info("No se encontraron resultados visibles en la búsqueda actual.")

    def _extract_offers(self, keyword: str | None) -> list[JobOffer]:
        offers: list[JobOffer] = []
        seen_urls: set[str] = set()

        for link in self.driver.find_elements(By.XPATH, self.JOB_LINK_XPATH):
            url = urljoin(self.BASE_URL, link.get_attribute("href") or "")
            if not url or url in seen_urls:
                continue

            text = self._extract_offer_text(link)
            if not self._matches_any_location(text):
                continue
            if keyword and not self._matches_keyword(text, keyword):
                continue

            offers.append(
                JobOffer(
                    title=self._clean_text(link.text) or self._extract_title(text),
                    company=self._extract_company(text),
                    url=url,
                    published_at=self._extract_date(text),
                    city=self._extract_city(text),
                    salary=self._extract_salary(text),
                    description=self._clean_text(text),
                )
            )
            seen_urls.add(url)

            if len(offers) >= self.settings.max_offers:
                break

        logging.info("Ofertas extraídas de Magneto: %s", len(offers))
        return offers

    def _close_optional_popups(self) -> None:
        close_selectors = [
            "//button[contains(@aria-label, 'Cerrar') or contains(@aria-label, 'Close')]",
            "//button[contains(., 'Aceptar')]",
            "//button[contains(., 'Entendido')]",
            "//button[contains(., 'Ahora no')]",
        ]
        for selector in close_selectors:
            for button in self.driver.find_elements(By.XPATH, selector):
                if button.is_displayed() and button.is_enabled():
                    button.click()

    def _open_login(self) -> None:
        for button in self.driver.find_elements(By.XPATH, self.LOGIN_LINK_XPATH):
            if button.is_displayed() and button.is_enabled():
                button.click()
                return
        self.driver.get(f"{self.BASE_URL}/co/login")

    def _click_google_login_if_available(self) -> None:
        try:
            google_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, self.GOOGLE_LOGIN_XPATH))
            )
            google_button.click()
        except TimeoutException:
            logging.info("No se encontro boton de Google. Esperando inicio manual.")

    def _wait_for_login(self) -> None:
        WebDriverWait(self.driver, self.settings.login_wait_seconds).until(lambda _: self._is_logged_in())
        logging.info("Sesion iniciada correctamente.")

    def _is_logged_in(self) -> bool:
        text = self._normalize_for_match(self.driver.find_element(By.TAG_NAME, "body").text)
        if "iniciar sesion" in text or "crear cuenta" in text:
            return False
        return True

    def _extract_offer_text(self, link) -> str:
        try:
            card = link.find_element(
                By.XPATH,
                './ancestor::*[self::article or self::li or self::div][.//a[contains(@href, "/empleos/")]][1]',
            )
            return card.text.strip()
        except Exception:
            return self._clean_text(link.text)

    def _complete_application_flow(self) -> str:
        clicked_submit = False
        stalled_iterations = 0
        self._wait_for_application_panel()

        for _ in range(12):
            self._close_optional_popups()
            self._attach_cv_if_requested()
            answered = self._answer_visible_questions()
            clicked = self._click_next_application_button()

            if clicked in {"Enviar respuestas", "Finalizar", "Postularme", "Aplicar", "Enviar"}:
                clicked_submit = True

            if not answered and not clicked:
                break

            if answered and not clicked:
                stalled_iterations += 1
                if stalled_iterations >= 2:
                    logging.info("Formulario detenido: respuestas dadas pero no hay boton de avance habilitado.")
                    break
            else:
                stalled_iterations = 0

            sleep(1)

        return "aplicado" if clicked_submit else "no disponible"

    def _wait_for_application_panel(self) -> None:
        try:
            WebDriverWait(self.driver, 8).until(
                lambda _: self._page_has_text("responder", "preguntas", "aplicacion", "postulacion")
            )
        except TimeoutException:
            logging.info("No aparecio panel de preguntas; intentando continuar flujo normal.")

    def _answer_visible_questions(self) -> bool:
        answered = False
        questions = self._extract_visible_questions()

        for question in questions:
            decision = self.question_answerer.answer(question["text"], question["options"])
            if not decision.should_answer or decision.value is None:
                logging.info("Pregunta omitida | razon=%s | pregunta=%s", decision.reason, question["text"][:160])
                continue

            if self._answer_question_element(question["element"], decision.value):
                logging.info(
                    "Pregunta respondida | respuesta=%s | confianza=%.2f | razon=%s | pregunta=%s",
                    decision.value,
                    decision.confidence,
                    decision.reason,
                    question["text"][:160],
                )
                answered = True
            else:
                logging.info("No se pudo aplicar respuesta | respuesta=%s | pregunta=%s", decision.value, question["text"][:160])

        return answered

    def _extract_visible_questions(self) -> list[dict]:
        script = """
            const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();
            const visible = (element) => {
              const style = window.getComputedStyle(element);
              const rect = element.getBoundingClientRect();
              return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
            };
            const actionPattern = /guardar|cancelar|enviar respuestas|continuar|siguiente|finalizar|postular|aplicar/i;
            const badContainerPattern = /magneto para:|requisitos para aplicar|ofertas de empleo|buscar por cargo|buscar por ubicacion/i;
            const questionPattern = /\\?|seleccion|respuest|anos|experiencia|salario|aspiracion|modalidad|ciudad|ubicacion|ingles|autoriz|acept|posee|tiene|cuenta|dispon|telefono|celular|correo|documento|cedula|formacion|conocimiento/i;
            const controlsSelector = 'button, [role="button"], input:not([type="hidden"]):not([type="file"]), textarea, select';
            const appRoot = Array.from(document.querySelectorAll('aside, section, form, div'))
              .filter(visible)
              .filter((element) => /enviar respuestas|solo falta|respuestas|aplicacion|postulacion/i.test(normalize(element.innerText || element.textContent || '')))
              .sort((a, b) => normalize(a.innerText).length - normalize(b.innerText).length)[0] || document.body;

            const controls = Array.from(appRoot.querySelectorAll(controlsSelector))
              .filter(visible)
              .filter((control) => {
                const text = normalize(control.innerText || control.value || control.getAttribute('aria-label') || control.getAttribute('placeholder'));
                return !actionPattern.test(text);
              });

            const containerFor = (control) => {
              const candidates = [];
              let node = control;
              while (node && node !== appRoot && candidates.length < 8) {
                if (node.nodeType === 1) candidates.push(node);
                node = node.parentElement;
              }
              return candidates
                .filter((element) => {
                  const text = normalize(element.innerText || element.textContent || '');
                  return text.length >= 6 && text.length <= 700 && questionPattern.test(text) && !badContainerPattern.test(text);
                })
                .sort((a, b) => normalize(a.innerText).length - normalize(b.innerText).length)[0] || control.parentElement;
            };

            const questionLike = controls
              .map((control) => {
                const element = containerFor(control);
                const rawText = normalize(element.innerText || element.textContent || control.getAttribute('placeholder') || control.getAttribute('aria-label') || '');
                const text = rawText
                  .replace(/\\b\\d+\\s+de\\s+\\d+\\b/gi, '')
                  .replace(actionPattern, '')
                  .trim();
                const localControls = Array.from(element.querySelectorAll(controlsSelector)).filter(visible);
                const options = localControls
                  .map((item) => normalize(item.innerText || item.value || item.getAttribute('aria-label') || item.getAttribute('placeholder')))
                  .filter(Boolean)
                  .filter((value) => !actionPattern.test(value))
                  .filter((value) => value.length <= 120);
                const tag = control.tagName.toLowerCase();
                const type = tag === 'select' ? 'select' : tag === 'textarea' ? 'text' : (control.getAttribute('role') === 'button' || tag === 'button') ? 'choice' : 'text';
                return { element, text, options: [...new Set(options)], type };
              })
              .filter((item) => item.text.length > 5 && item.text.length <= 700)
              .filter((item) => questionPattern.test(item.text) && !badContainerPattern.test(item.text));

            const result = [];
            const seen = new Set();
            for (const item of questionLike) {
              const compact = item.text.toLowerCase().replace(/\\s+/g, ' ');
              if ([...seen].some((value) => value.includes(compact) || compact.includes(value))) continue;
              seen.add(compact);
              result.push(item);
              if (result.length >= 10) break;
            }
            return result;
        """
        try:
            return list(self.driver.execute_script(script) or [])
        except Exception:
            return []

    def _answer_question_element(self, element, value: str) -> bool:
        script = """
            const root = arguments[0];
            const rawValue = arguments[1];
            const normalize = (value) => (value || '')
              .normalize('NFD')
              .replace(/[\\u0300-\\u036f]/g, '')
              .replace(/\\s+/g, ' ')
              .trim()
              .toLowerCase();
            const value = normalize(rawValue);
            const visible = (element) => {
              const style = window.getComputedStyle(element);
              const rect = element.getBoundingClientRect();
              return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
            };
            const setNativeValue = (element, value) => {
              const setter = Object.getOwnPropertyDescriptor(element.__proto__, 'value')?.set;
              setter ? setter.call(element, value) : element.value = value;
              element.dispatchEvent(new Event('input', { bubbles: true }));
              element.dispatchEvent(new Event('change', { bubbles: true }));
            };

            const clickable = Array.from(root.querySelectorAll('button, [role="button"], label, option'))
              .filter(visible)
              .filter((element) => {
                const text = normalize(element.innerText || element.textContent || element.value || element.getAttribute('aria-label'));
                if (text === 'guardar' || text.includes('guardar')) return false;
                if (/cancelar|enviar respuestas|continuar|siguiente|finalizar|postular|aplicar/.test(text)) return false;
                return text === value || (value.length > 2 && text.includes(value));
              });
            if (clickable.length) {
              clickable[0].scrollIntoView({ block: 'center', inline: 'center' });
              clickable[0].click();
              return true;
            }

            const select = Array.from(root.querySelectorAll('select')).find(visible);
            if (select) {
              const option = Array.from(select.options).find((item) => {
                const text = normalize(item.text || item.value);
                return text === value || (value.length > 2 && text.includes(value));
              });
              if (option) {
                select.value = option.value;
                select.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
              }
            }

            const input = Array.from(root.querySelectorAll('input:not([type="file"]), textarea'))
              .filter(visible)
              .find((element) => !element.disabled && !element.readOnly);
            if (input) {
              input.scrollIntoView({ block: 'center', inline: 'center' });
              input.focus();
              setNativeValue(input, rawValue);
              return true;
            }
            return false;
        """
        try:
            return bool(self.driver.execute_script(script, element, value))
        except Exception:
            return False

    def _click_next_application_button(self) -> str | None:
        for label in ["Enviar respuestas", "Continuar", "Siguiente", "Finalizar", "Enviar", "Postularme", "Aplicar"]:
            if self._click_button_by_text([label]):
                return label
        return None

    def _click_button_by_text(self, labels: list[str]) -> bool:
        normalized_labels = [self._normalize_for_match(label) for label in labels]
        script = """
            const labels = arguments[0];
            const normalize = (value) => (value || '')
              .normalize('NFD')
              .replace(/[\\u0300-\\u036f]/g, '')
              .replace(/\\s+/g, ' ')
              .trim()
              .toLowerCase();
            const selectors = [
              'button',
              'a',
              '[role="button"]',
              'input[type="button"]',
              'input[type="submit"]'
            ];
            const elements = Array.from(document.querySelectorAll(selectors.join(',')));
            const visible = (element) => {
              const style = window.getComputedStyle(element);
              const rect = element.getBoundingClientRect();
              return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
            };

            for (const element of elements) {
              const text = normalize(element.innerText || element.value || element.getAttribute('aria-label'));
              const disabled = element.disabled || element.getAttribute('aria-disabled') === 'true';
              if (text === 'guardar' || text.includes('guardar')) continue;
              if (!visible(element) || disabled) continue;
              if (!labels.some((label) => text === label || (label.length > 2 && text.includes(label)))) continue;
              element.scrollIntoView({ block: 'center', inline: 'center' });
              element.click();
              return true;
            }
            return false;
        """
        try:
            return bool(self.driver.execute_script(script, normalized_labels))
        except Exception:
            return False

    def _page_has_text(self, *values: str) -> bool:
        text = self._normalize_for_match(self.driver.find_element(By.TAG_NAME, "body").text)
        return any(value in text for value in values)

    def _attach_cv_if_requested(self) -> None:
        if not self.settings.cv_path.exists():
            return

        for file_input in self.driver.find_elements(By.XPATH, "//input[@type='file']"):
            try:
                file_input.send_keys(str(self.settings.cv_path))
            except Exception:
                logging.info("No fue posible adjuntar CV en este paso.")

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        stop_words = {"de", "del", "la", "las", "el", "los", "en", "y", "o"}
        words = re.findall(r"[a-z0-9]+", normalized.lower())
        return "-".join(word for word in words if word not in stop_words)

    @classmethod
    def _contains_city(cls, text: str, city: str) -> bool:
        return cls._normalize_for_match(city) in cls._normalize_for_match(text)

    def _matches_any_location(self, text: str) -> bool:
        normalized_text = self._normalize_for_match(text)
        if "colombia" in normalized_text or "remoto" in normalized_text or "teletrabajo" in normalized_text:
            return True
        return any(self._normalize_for_match(location) in normalized_text for location in self.settings.locations)

    @classmethod
    def _matches_keyword(cls, text: str, keyword: str) -> bool:
        normalized_text = cls._normalize_for_match(text)
        compact_text = normalized_text.replace(" ", "")
        normalized_keyword = cls._normalize_for_match(keyword)
        compact_keyword = normalized_keyword.replace(" ", "")
        keyword_parts = [part for part in re.findall(r"[a-z0-9]+", normalized_keyword) if len(part) > 2]

        if compact_keyword in compact_text:
            return True

        return all(part in normalized_text for part in keyword_parts)

    @staticmethod
    def _normalize_for_match(value: str) -> str:
        return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()

    @staticmethod
    def _clean_text(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _extract_title(text: str) -> str:
        return text.split(" - ")[0].split("|")[0].strip() or "Cargo no especificado"

    @staticmethod
    def _extract_company(text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) >= 3:
            return lines[2].split("|")[0].strip()
        parts = [part.strip() for part in re.split(r"\s+\|\s+", text) if part.strip()]
        if len(parts) >= 3:
            return parts[2]
        return "No especificada"

    @staticmethod
    def _extract_date(text: str) -> str:
        match = re.search(r"\b(20\d{2}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/20\d{2}|Hace\s+\d+\s+\w+)\b", text, re.IGNORECASE)
        return match.group(1) if match else "No especificada"

    @staticmethod
    def _extract_salary(text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines:
            if "$" in line or "salario" in line.lower() or "convenir" in line.lower():
                return line
        return "No especificado"

    def _extract_city(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        location_markers = {
            "bogota": "Bogota",
            "medellin": "Medellin",
            "cali": "Cali",
            "barranquilla": "Barranquilla",
            "bucaramanga": "Bucaramanga",
            "manizales": "Manizales",
            "colombia": "Colombia",
            "remoto": "Remoto",
            "teletrabajo": "Teletrabajo",
        }
        configured_locations = [
            (self._normalize_for_match(location), location)
            for location in self.settings.locations
        ]
        for line in lines:
            normalized = self._normalize_for_match(line)
            for normalized_location, display_location in configured_locations:
                if normalized_location in normalized:
                    return display_location
            for marker, display_location in location_markers.items():
                if marker in normalized:
                    return display_location
        return "No especificada"
