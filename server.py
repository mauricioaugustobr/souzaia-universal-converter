import os
import sys
import uuid
import json
import socket
import zipfile
import asyncio
import webbrowser
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from aiohttp import web

# Add root directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from core.universal_converter import UniversalConverter
from core.media_info import inspect_media, TARGET_FORMATS, EXTENSION_CATEGORIES

UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
STATIC_DIR = BASE_DIR / "static"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

executor = ThreadPoolExecutor(max_workers=4)

# In-memory job state store
jobs = {}

routes = web.RouteTableDef()

@routes.get('/')
async def index_handler(request):
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return web.Response(text="SOUZAIA Universal Converter inicializando...", content_type="text/plain; charset=utf-8")
    return web.FileResponse(index_file)

@routes.get('/api/health')
async def health_handler(request):
    return web.json_response({
        'status': 'online',
        'service': 'SOUZAIA Universal Converter',
        'version': '1.0.0'
    })

@routes.get('/api/formats')
async def formats_handler(request):
    return web.json_response({
        'categories': EXTENSION_CATEGORIES,
        'targets': TARGET_FORMATS
    })

@routes.post('/api/upload')
async def upload_handler(request):
    try:
        reader = await request.multipart()
    except Exception as e:
        return web.json_response({'error': f"Erro no upload: {str(e)}"}, status=400)

    uploaded_files = []

    while True:
        try:
            part = await reader.next()
        except Exception:
            break
        if part is None:
            break
        if part.filename:
            file_id = str(uuid.uuid4())
            orig_filename = part.filename
            stem = Path(orig_filename).stem
            ext = Path(orig_filename).suffix.lstrip('.')

            safe_filename = f"{file_id}_{orig_filename}"
            filepath = UPLOAD_DIR / safe_filename

            size = 0
            with open(filepath, 'wb') as f:
                while True:
                    chunk = await part.read_chunk()
                    if not chunk:
                        break
                    size += len(chunk)
                    f.write(chunk)

            # Inspect media
            try:
                info = inspect_media(str(filepath))
            except Exception as e:
                info = {
                    'filename': orig_filename,
                    'extension': ext,
                    'category': 'unknown',
                    'size_bytes': size,
                    'size_formatted': f"{size / 1024:.1f} KB",
                    'details': {'error': str(e)},
                    'target_formats': ['pdf', 'txt', 'png', 'mp3', 'mp4']
                }

            uploaded_files.append({
                'file_id': file_id,
                'original_name': orig_filename,
                'temp_path': str(filepath),
                'info': info
            })

    return web.json_response({'files': uploaded_files})

@routes.post('/api/convert')
async def convert_handler(request):
    try:
        data = await request.json()
    except Exception:
        return web.json_response({'error': 'JSON inválido na requisição.'}, status=400)

    file_id = data.get('file_id')
    temp_path = data.get('temp_path')
    target_format = data.get('target_format')
    options = data.get('options', {})

    if not temp_path or not target_format or not Path(temp_path).exists():
        return web.json_response({'error': 'Arquivo ou formato de destino inválido.'}, status=400)

    job_id = str(uuid.uuid4())
    job_output_dir = OUTPUT_DIR / job_id
    job_output_dir.mkdir(parents=True, exist_ok=True)

    jobs[job_id] = {
        'status': 'queued',
        'progress': 0.0,
        'message': 'Na fila de processamento...',
        'result': None,
        'error': None
    }

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    def progress_callback(pct: float, msg: str):
        if job_id in jobs:
            jobs[job_id]['progress'] = pct
            jobs[job_id]['message'] = msg
            jobs[job_id]['status'] = 'running'

    def run_conversion():
        try:
            jobs[job_id]['status'] = 'running'
            res = UniversalConverter.convert(
                input_path=temp_path,
                output_dir=str(job_output_dir),
                target_format=target_format,
                options=options,
                progress_callback=progress_callback
            )
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['progress'] = 100.0
            jobs[job_id]['message'] = 'Conversão concluída com sucesso!'
            jobs[job_id]['result'] = res
        except Exception as e:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = str(e)
            jobs[job_id]['message'] = f"Falha na conversão: {str(e)}"

    # Run in thread pool without blocking event loop
    loop.run_in_executor(executor, run_conversion)

    return web.json_response({'job_id': job_id, 'status': 'started'})

@routes.get('/api/progress/{job_id}')
async def progress_handler(request):
    job_id = request.match_info['job_id']
    job = jobs.get(job_id)
    if not job:
        return web.json_response({'error': 'Job não encontrado'}, status=404)
    return web.json_response(job)

@routes.get('/api/download/{job_id}')
async def download_handler(request):
    job_id = request.match_info['job_id']
    job = jobs.get(job_id)
    if not job or job.get('status') != 'completed':
        return web.Response(text="Arquivo ainda não pronto ou job inválido.", status=404)

    res = job.get('result')
    if not res or not Path(res['file_path']).exists():
        return web.Response(text="Arquivo convertido não foi encontrado.", status=404)

    file_path = Path(res['file_path'])
    return web.FileResponse(
        file_path,
        headers={
            'Content-Disposition': f'attachment; filename="{file_path.name}"'
        }
    )

@routes.post('/api/batch-download')
async def batch_download_handler(request):
    data = await request.json()
    job_ids = data.get('job_ids', [])
    if not job_ids:
        return web.json_response({'error': 'Nenhum arquivo selecionado'}, status=400)

    zip_id = str(uuid.uuid4())
    zip_path = OUTPUT_DIR / f"SOUZAIA_Convertidos_{zip_id[:8]}.zip"

    with zipfile.ZipFile(str(zip_path), 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for jid in job_ids:
            job = jobs.get(jid)
            if job and job.get('status') == 'completed' and job.get('result'):
                fpath = Path(job['result']['file_path'])
                if fpath.exists():
                    z.write(str(fpath), arcname=fpath.name)

    return web.FileResponse(
        zip_path,
        headers={
            'Content-Disposition': f'attachment; filename="{zip_path.name}"'
        }
    )

def find_available_port(start_port=5000, max_attempts=20):
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

def create_app(target_port=5000, auto_open_browser=True):
    app = web.Application(client_max_size=2048 * 1024 * 1024)  # 2 GB max upload
    app.add_routes(routes)
    # Correct prefix without trailing slash to match /static/css/style.css
    app.router.add_static('/static', path=str(STATIC_DIR), name='static')

    if auto_open_browser:
        async def on_startup(app_instance):
            async def open_delayed():
                await asyncio.sleep(0.8)
                url = f"http://127.0.0.1:{target_port}"
                print(f"[*] Abrindo navegador em: {url}")
                webbrowser.open(url)
            asyncio.create_task(open_delayed())

        app.on_startup.append(on_startup)

    return app

if __name__ == '__main__':
    is_cloud_or_docker = (
        os.path.exists('/.dockerenv') or 
        os.environ.get('RENDER') is not None or 
        os.environ.get('RAILWAY_STATIC_URL') is not None or
        sys.platform != 'win32'
    )

    port = int(os.environ.get('PORT', 5000 if not is_cloud_or_docker else 10000))
    host = '0.0.0.0' if is_cloud_or_docker else '127.0.0.1'
    auto_open = not is_cloud_or_docker

    if not is_cloud_or_docker:
        port = find_available_port(port)

    print(f"\n=======================================================")
    print(f" SOUZAIA UNIVERSAL CONVERTER - SERVIDOR INICIADO")
    print(f" Endereço: http://{host}:{port}")
    print(f" Modo: {'Nuvem / Docker' if is_cloud_or_docker else 'Desktop Local'}")
    print(f"=======================================================\n")

    app = create_app(target_port=port, auto_open_browser=auto_open)
    web.run_app(app, host=host, port=port)
