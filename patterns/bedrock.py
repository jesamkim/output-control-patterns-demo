"""Bedrock client and LLM call utilities."""

import os

import boto3
from botocore.config import Config as BotoConfig

DEFAULT_MODEL_ID = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
DEFAULT_REGION = "us-west-2"

_client = None
_model_id = None


def get_model_id() -> str:
    global _model_id
    if _model_id is None:
        _model_id = os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
    return _model_id


def set_model_id(model_id: str) -> None:
    global _model_id, _client
    _model_id = model_id
    _client = None


def _get_client():
    global _client
    if _client is None:
        region = os.environ.get("BEDROCK_REGION", DEFAULT_REGION)
        _client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            config=BotoConfig(read_timeout=120, retries={"max_attempts": 3}),
        )
    return _client


def call_bedrock(
    system: str,
    user: str,
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> str:
    """Bedrock Converse API call."""
    client = _get_client()
    response = client.converse(
        modelId=get_model_id(),
        system=[{"text": system}],
        messages=[{"role": "user", "content": [{"text": user}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
    )
    return response["output"]["message"]["content"][0]["text"]
