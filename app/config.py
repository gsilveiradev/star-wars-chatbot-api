import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    env: str
    bedrock_aws_profile: str = "invalid-profile"
    bedrock_aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    sw_api_base: str = "https://swapi.dev/api/"
    max_tokens: int = 1000

settings = Settings()
