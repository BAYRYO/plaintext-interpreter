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
                    let ws = new WebSocket(`ws://${location.host}/ws`);
                    ws.onmessage = function(event) {
                        if (event.data === 'reload') {
                            location.reload();
                        }
                    };
                    ws.onclose = function() {
                        setTimeout(() => {
                            ws = new WebSocket(`ws://${location.host}/ws`);
                        }, 1000);
                    };
                </script>
            """
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
