from boto3.session import Session
from app.config import settings

def get_bedrock_client():
    session = Session()
    if settings.env == "development":
        session = Session(profile_name=settings.bedrock_aws_profile)
    return session.client("bedrock-runtime", region_name=settings.bedrock_aws_region)
