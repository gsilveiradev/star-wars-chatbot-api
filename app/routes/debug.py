from fastapi import APIRouter
from boto3.session import Session

from app.config import settings
from app.clients.bedrock import get_bedrock_client

router = APIRouter()
session = Session()

# Initialize the session with the AWS profile if in development environment
# This allows for local testing with a specific AWS profile
if settings.env == "development":
    session = Session(profile_name=settings.bedrock_aws_profile)

bedrock = session.client("bedrock", region_name=settings.bedrock_aws_region)

@router.get("/debug/bedrock/models")
async def list_models():
    response = bedrock.list_foundation_models()

    models = [
        {
            "modelId": model["modelId"],
            "providerName": model["providerName"],
            "modelName": model.get("modelName"),
            "inputModalities": model.get("inputModalities"),
            "outputModalities": model.get("outputModalities"),
            "customizable": model.get("customizable"),
            "inferenceTypesSupported": model.get("inferenceTypesSupported")
        }
        for model in response.get("modelSummaries", [])
    ]

    return { "models": models, "settings": {
        "env": settings.env,
        "bedrock_aws_profile": settings.bedrock_aws_profile,
        "bedrock_aws_region": settings.bedrock_aws_region,
        "bedrock_model_id": settings.bedrock_model_id
    }}