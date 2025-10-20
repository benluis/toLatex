# built-in
import os

# external
from dotenv import load_dotenv
import boto3

# load environment variables from .env file
load_dotenv()

s3_client = boto3.client("s3")