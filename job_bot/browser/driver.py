from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

from config import Settings


def create_browser_driver(settings: Settings) -> webdriver.Chrome | webdriver.Edge:
    browser = settings.browser.strip().lower()

    if browser == "edge":
        return _create_edge_driver(settings)

    if browser == "chrome":
        return _create_chrome_driver(settings)

    raise ValueError(f"Navegador no soportado: {settings.browser}. Usa 'edge' o 'chrome'.")


def _create_edge_driver(settings: Settings) -> webdriver.Edge:
    try:
        return webdriver.Edge(options=_build_edge_options(settings.edge_user_data_dir, settings.edge_profile_directory, settings.edge_binary_path))
    except (SessionNotCreatedException, WebDriverException) as error:
        if not settings.allow_bot_profile_fallback:
            raise RuntimeError(
                "No se pudo abrir tu perfil real de Edge. Cierra todas las ventanas de Edge "
                "y desactiva Edge Startup Boost si sigue apareciendo este error. "
                "El bot necesita ese perfil para reutilizar tu sesion de Google/Magneto."
            ) from error

        settings.edge_bot_user_data_dir.mkdir(parents=True, exist_ok=True)
        return webdriver.Edge(options=_build_edge_options(settings.edge_bot_user_data_dir, "Default", settings.edge_binary_path))


def _create_chrome_driver(settings: Settings) -> webdriver.Chrome:
    return webdriver.Chrome(options=_build_chrome_options(settings))


def _build_edge_options(user_data_dir: Path, profile_directory: str, binary_path: Path) -> EdgeOptions:
    options = EdgeOptions()
    _add_common_options(options, user_data_dir, profile_directory)
    _set_binary_location(options, binary_path)
    return options


def _build_chrome_options(settings: Settings) -> ChromeOptions:
    options = ChromeOptions()
    _add_common_options(options, settings.chrome_user_data_dir, settings.chrome_profile_directory)
    return options


def _add_common_options(options: ChromeOptions | EdgeOptions, user_data_dir: Path, profile_directory: str) -> None:
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument(f"--profile-directory={profile_directory}")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-background-mode")
    options.add_argument("--disable-features=msEdgeStartupBoost")


def _set_binary_location(options: EdgeOptions, binary_path: Path) -> None:
    if binary_path.exists():
        options.binary_location = str(binary_path)
