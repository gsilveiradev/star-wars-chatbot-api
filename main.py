import logging, time, uuid
from fastapi import FastAPI, Request
from app.routes.chat import router as chat_router
from app.routes.suggestions import router as suggestions_router
from app.routes.debug import router as listmodels_router
from app.routes.health import router as health_router
from app.logger.config import setup_logging, log_extra_data, get_common_attributes

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()

@app.middleware("http")
async def json_logger_middleware(request: Request, call_next):
    start_time = time.time()
    request_id = str(uuid.uuid4())

    base_log_attributes = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else "unknown",
    }
    base_log_attributes.update(get_common_attributes())

    token = log_extra_data.set(base_log_attributes)

    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # in milliseconds

        current_log_data = log_extra_data.get()
        current_log_data["status_code"] = response.status_code
        current_log_data["duration_ms"] = round(process_time, 2)
        log_extra_data.set(current_log_data)
        
        logger.info("Request completed successfully")
        
        return response

    finally:
        log_extra_data.reset(token)

app.include_router(chat_router, tags=["chat"])
app.include_router(suggestions_router, tags=["suggestions"])
app.include_router(listmodels_router, tags=["list"])
app.include_router(health_router, tags=["health"])
