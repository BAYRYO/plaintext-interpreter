import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .html_converter import HTMLConverter
from .utils.logging_utils import get_logger
from aiohttp import web
import webbrowser
import aiofiles
import time
from typing import Set

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, queue: asyncio.Queue, input_file: Path):
        self.queue = queue
        self.input_file = input_file
        self.last_event_time = 0
        self.debounce_delay = 0.5

    def on_modified(self, event):
        current_time = time.time()
        if event.src_path == str(self.input_file) and \
           current_time - self.last_event_time >= self.debounce_delay:
            self.last_event_time = current_time
            try:
                self.queue.put_nowait(event.src_path)
            except asyncio.QueueFull:
                pass  # Skip if queue is full

class LiveEditor:
    def __init__(self, converter, input_file: str, output_file: str, port: int = 5000):
        self.converter = converter
        self.input_file = Path(input_file).resolve()
        self.output_file = Path(output_file).resolve()
        self.port = port
        self.logger = get_logger('live_editor')
        self.app = web.Application()
        self.setup_routes()
        self.ws_clients: Set[web.WebSocketResponse] = set()
        self.change_queue = asyncio.Queue(maxsize=100)
        self.conversion_lock = asyncio.Lock()
        self.running = True
        self.tasks = set()
        self.observer = None

    def setup_routes(self):
        self.app.router.add_static('/assets/', path=Path('templates/assets'))
        self.app.router.add_get('/', self.serve_output)
        self.app.router.add_get('/ws', self.websocket_handler)
        self.app.on_shutdown.append(self.on_shutdown)

    async def process_changes(self):
        try:
            while self.running:
                try:
                    _ = await self.change_queue.get()
                    if not self.running:
                        break

                    async with self.conversion_lock:
                        await self.converter.convert_async(
                            str(self.input_file),
                            str(self.output_file)
                        )
                        self.logger.info(
                            f"Live update: converted {self.input_file} to {self.output_file}"
                        )
                        await self.notify_clients()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Error processing change: {str(e)}")
                finally:
                    try:
                        self.change_queue.task_done()
                    except ValueError:
                        pass  # Queue might already be empty
        except Exception as e:
            self.logger.error(f"Process changes loop error: {str(e)}")

    async def websocket_handler(self, request):
        ws = web.WebSocketResponse(heartbeat=30)
        await ws.prepare(request)
        self.ws_clients.add(ws)

        try:
            async for _ in ws:
                pass  # We don't expect any incoming messages
        except asyncio.CancelledError:
            pass
        finally:
            self.ws_clients.discard(ws)
        return ws

    async def notify_clients(self):
        dead_clients = set()
        for ws in self.ws_clients:
            try:
                await ws.send_str('reload')
            except Exception as e:
                self.logger.error(f"Failed to notify client: {str(e)}")
                dead_clients.add(ws)

        # Clean up dead connections
        self.ws_clients.difference_update(dead_clients)

    async def serve_output(self, request):
        try:
            async with aiofiles.open(self.output_file, mode='r', encoding='utf-8') as f:
                content = await f.read()

            ws_script = """
                <script>
                    // Sauvegarder le thème actuel avant le rechargement
                    function saveCurrentTheme() {
                        const currentTheme = document.documentElement.getAttribute('data-theme');
                        if (currentTheme) {
                            localStorage.setItem('theme', currentTheme);
                        }
                    }

                    // Configurer la WebSocket
                    let ws = new WebSocket(`ws://${location.host}/ws`);
                    ws.onmessage = function(event) {
                        if (event.data === 'reload') {
                            // Sauvegarder le thème actuel
                            saveCurrentTheme();

                            // Ajouter une classe pour la transition fluide
                            document.documentElement.classList.add('theme-transition');

                            // Recharger la page après un court délai pour permettre la sauvegarde
                            setTimeout(() => {
                                location.reload();
                            }, 50);
                        }
                    };
                    ws.onclose = function() {
                        setTimeout(() => {
                            ws = new WebSocket(`ws://${location.host}/ws`);
                        }, 1000);
                    };

                    // S'assurer que le bouton de mode sombre est créé en mode live
                    document.addEventListener("DOMContentLoaded", () => {
                        // Vérifier si le bouton existe déjà
                        if (!document.querySelector('.theme-toggle')) {
                            // Créer le bouton de bascule du thème
                            const themeToggle = document.createElement('button');
                            themeToggle.className = 'theme-toggle';

                            // Déterminer l'icône en fonction du thème actuel
                            const currentTheme = document.documentElement.getAttribute('data-theme');
                            themeToggle.innerHTML = currentTheme === 'dark' ?
                                '<i class="fas fa-sun"></i>' :
                                '<i class="fas fa-moon"></i>';

                            themeToggle.setAttribute('aria-label', 'Basculer entre le mode clair et sombre');
                            document.body.appendChild(themeToggle);

                            // Fonction pour définir le thème avec transition fluide
                            function setTheme(theme, instant = false) {
                                // Ajouter une classe de transition si ce n'est pas un changement instantané
                                if (!instant) {
                                    document.documentElement.classList.add('theme-transition');

                                    // Retirer la classe après la fin de la transition
                                    setTimeout(() => {
                                        document.documentElement.classList.remove('theme-transition');
                                    }, 300); // Correspond à la durée de transition CSS (0.3s)
                                }

                                if (theme === 'dark') {
                                    document.documentElement.setAttribute('data-theme', 'dark');
                                    themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
                                    localStorage.setItem('theme', 'dark');
                                } else {
                                    document.documentElement.removeAttribute('data-theme');
                                    themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
                                    localStorage.setItem('theme', 'light');
                                }
                            }

                            // Appliquer le thème initial sans transition (instant=true)
                            const savedTheme = localStorage.getItem('theme');
                            if (savedTheme) {
                                setTheme(savedTheme, true);
                            }

                            // Basculer le thème au clic sur le bouton
                            themeToggle.addEventListener('click', () => {
                                const currentTheme = document.documentElement.getAttribute('data-theme');
                                setTheme(currentTheme === 'dark' ? 'light' : 'dark');
                            });
                        }
                    });
                </script>
            """
            # Injecter les styles CSS pour le bouton de mode sombre directement dans le HTML
            dark_mode_styles = """
                <style>
                    /* Variables CSS pour le mode clair et sombre */
                    :root {
                        /* Mode clair (par défaut) */
                        --primary-color: #3498db;
                        --secondary-color: #2980b9;
                        --text-color: #333;
                        --background-color: #f4f4f9;
                        --code-background: #ecf0f1;
                        --border-color: #e0e0e0;
                        --shadow-color: rgba(0, 0, 0, 0.1);
                        --box-background: #fff;
                        --blockquote-background: #f9f9f9;
                        --input-background: #f9f9f9;
                        --table-header-background: #f2f2f2;
                        --table-row-even: #f8f8f8;
                        --table-row-hover: #f1f1f1;
                    }

                    /* Mode sombre */
                    [data-theme="dark"] {
                        --primary-color: #61dafb;
                        --secondary-color: #4fa3d1;
                        --text-color: #e0e0e0;
                        --background-color: #1a1a1a;
                        --code-background: #2d2d2d;
                        --border-color: #444;
                        --shadow-color: rgba(0, 0, 0, 0.3);
                        --box-background: #2d2d2d;
                        --blockquote-background: #2a2a2a;
                        --input-background: #333;
                        --table-header-background: #333;
                        --table-row-even: #2a2a2a;
                        --table-row-hover: #3a3a3a;
                    }

                    /* Styles pour le bouton de mode sombre */
                    .theme-toggle {
                        background: linear-gradient(135deg, var(--primary-color, #3498db), var(--secondary-color, #2980b9));
                        color: #fff;
                        padding: 12px;
                        border: none;
                        border-radius: 50%;
                        width: 45px;
                        height: 45px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        position: fixed;
                        bottom: 20px;
                        right: 20px;
                        z-index: 1000;
                        overflow: hidden;
                    }

                    .theme-toggle:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
                    }

                    .theme-toggle:active {
                        transform: translateY(0);
                    }

                    /* Animation du bouton lors du changement de thème */
                    .theme-toggle-active {
                        animation: theme-toggle-spin 0.5s ease;
                    }

                    @keyframes theme-toggle-spin {
                        0% {
                            transform: rotate(0) scale(1);
                        }
                        50% {
                            transform: rotate(180deg) scale(1.2);
                        }
                        100% {
                            transform: rotate(360deg) scale(1);
                        }
                    }

                    /* Icônes pour le mode sombre */
                    .fa-moon::before {
                        content: "\f186";
                        font-family: 'Font Awesome 6 Free';
                        font-weight: 900;
                    }

                    .fa-sun::before {
                        content: "\f185";
                        font-family: 'Font Awesome 6 Free';
                        font-weight: 900;
                    }

                    /* Classe appliquée uniquement pendant les transitions de thème */
                    html.theme-transition,
                    html.theme-transition *,
                    html.theme-transition *:before,
                    html.theme-transition *:after {
                        transition: color 0.3s ease, background-color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease !important;
                        transition-delay: 0s !important;
                    }

                    /* Appliquer les variables CSS aux éléments */
                    body {
                        background-color: var(--background-color);
                        color: var(--text-color);
                        transition: background-color 0.3s ease, color 0.3s ease;
                    }

                    a {
                        color: var(--primary-color);
                    }

                    a:hover {
                        color: var(--secondary-color);
                    }

                    pre, code {
                        background-color: var(--code-background);
                        color: var(--text-color);
                    }

                    table {
                        color: var(--text-color);
                    }
                </style>
            """

            # Injecter les styles et le script
            content = content.replace('</head>', f'{dark_mode_styles}</head>')
            content = content.replace('</body>', f'{ws_script}</body>')

            return web.Response(text=content, content_type='text/html')
        except Exception as e:
            self.logger.error(f"Error serving output: {str(e)}")
            return web.Response(text="Error loading content", status=500)

    async def on_shutdown(self, app):
        self.running = False

        # Close all WebSocket connections
        for ws in set(self.ws_clients):
            await ws.close(code=1000, message='Server shutdown')
        self.ws_clients.clear()

        # Stop the file watcher
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=2)

        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()

        # Clear the queue
        while not self.change_queue.empty():
            try:
                self.change_queue.get_nowait()
                self.change_queue.task_done()
            except (asyncio.QueueEmpty, ValueError):
                break

    async def start(self):
        # Initial conversion
        try:
            await self.converter.convert_async(str(self.input_file), str(self.output_file))
            self.logger.info("Initial conversion completed")
        except Exception as e:
            self.logger.error(f"Initial conversion failed: {str(e)}")
            raise

        # Start the change processor
        processor_task = asyncio.create_task(self.process_changes())
        self.tasks.add(processor_task)
        processor_task.add_done_callback(self.tasks.discard)

        # Setup file watcher
        event_handler = FileChangeHandler(self.change_queue, self.input_file)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.input_file.parent), recursive=False)
        self.observer.start()

        # Start web server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()

        # Open browser
        webbrowser.open(f'http://localhost:{self.port}')

        self.logger.info(f"Live editing server started at http://localhost:{self.port}")
        self.logger.info(f"Watching for changes in {self.input_file}")

        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            self.logger.info("Shutting down live editor...")
        finally:
            await runner.cleanup()
