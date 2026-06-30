import boto3
from botocore.config import Config
from config import AWS_REGION, S3_REGION

def get_bedrock_client():
    return boto3.client("bedrock-runtime", region_name=AWS_REGION)

def get_s3_client():
    return boto3.client("s3", region_name=S3_REGION, config=Config(signature_version='s3v4'))
