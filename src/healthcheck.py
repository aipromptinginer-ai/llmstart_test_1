"""HTTP сервер для healthcheck Railway."""
import asyncio
import logging
from aiohttp import web

logger = logging.getLogger(__name__)

async def health_handler(request):
    """Обработчик healthcheck запроса."""
    return web.json_response({
        "status": "healthy",
        "service": "llm-learning-goals-bot",
        "version": "1.0.0"
    })

async def start_healthcheck_server(port: int = 8080):
    """Запуск HTTP сервера для healthcheck."""
    app = web.Application()
    app.router.add_get('/', health_handler)
    app.router.add_get('/health', health_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"Healthcheck server started on port {port}")
    return runner
