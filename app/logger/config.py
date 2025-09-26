import logging
import sys
from contextvars import ContextVar
from pythonjsonlogger import jsonlogger
from app.config import settings

log_extra_data: ContextVar[dict] = ContextVar("log_extra_data", default={})


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Get data from the ContextVar and add it to the log record
        context_data = log_extra_data.get()
        if context_data:
            log_record.update(context_data)
        
        # Standardize log level and timestamp fields
        log_record['level'] = log_record['levelname']
        log_record['timestamp'] = log_record.pop('asctime', None) or log_record.pop('created', None)
        log_record.pop('levelname', None) # remove redundant field


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    
    formatter = CustomJsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    
    handler.setFormatter(formatter)
    
    # Clear existing handlers and add the new one
    if logger.hasHandlers():
        logger.handlers.clear()
    
    logger.addHandler(handler)

def get_common_attributes():
    return {
        "settings.bedrock.aws_profile": settings.bedrock_aws_profile,
        "settings.bedrock.aws_region": settings.bedrock_aws_region,
        "settings.bedrock.model_id": settings.bedrock_model_id
    }