from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    region: str = "us-east-1"
    data_bucket: str = "local-demo"
    kinesis_stream: str = "fiap-alfabetizacao-dev-indicadores"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            region=os.getenv("AWS_REGION", "us-east-1"),
            data_bucket=os.getenv("AWS_DATA_BUCKET", "local-demo"),
            kinesis_stream=os.getenv(
                "AWS_KINESIS_STREAM", "fiap-alfabetizacao-dev-indicadores"
            ),
        )
