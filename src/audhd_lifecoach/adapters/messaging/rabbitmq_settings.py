import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class RabbitMQSettings:
    """RabbitMQ connection and queue settings loaded from environment variables."""

    # Connection settings
    host: str = os.getenv("RABBITMQ_HOST", "localhost")
    port: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    username: str = os.getenv("RABBITMQ_USERNAME", "guest")
    password: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    virtual_host: str = os.getenv("RABBITMQ_VIRTUAL_HOST", "/")

    # Queue and exchange names (set by infrastructure)
    consume_queue_name: str = os.getenv("RABBITMQ_CONSUME_QUEUE", "communications")
    publish_exchange_name: str = os.getenv(
        "RABBITMQ_PUBLISH_EXCHANGE", "audhd_lifecoach"
    )

    # Connection tuning - these were missing!
    connection_attempts: int = int(os.getenv("RABBITMQ_CONNECTION_ATTEMPTS", "3"))
    retry_delay: int = int(os.getenv("RABBITMQ_RETRY_DELAY", "2"))
    connection_timeout: int = int(os.getenv("RABBITMQ_CONNECTION_TIMEOUT", "30"))
    heartbeat: int = int(os.getenv("RABBITMQ_HEARTBEAT", "600"))

    # SSL settings (optional)
    use_ssl: bool = os.getenv("RABBITMQ_USE_SSL", "false").lower() == "true"
    ssl_ca_cert_path: Optional[str] = os.getenv("RABBITMQ_SSL_CA_CERT_PATH")
    ssl_cert_path: Optional[str] = os.getenv("RABBITMQ_SSL_CERT_PATH")
    ssl_key_path: Optional[str] = os.getenv("RABBITMQ_SSL_KEY_PATH")

    def __post_init__(self):
        """Validate settings after initialization."""
        if self.port <= 0 or self.port > 65535:
            raise ValueError(f"Invalid port number: {self.port}")

        if self.connection_timeout <= 0:
            raise ValueError(
                f"Connection timeout must be positive: {self.connection_timeout}"
            )

        if self.connection_attempts <= 0:
            raise ValueError(
                f"Connection attempts must be positive: {self.connection_attempts}"
            )

        if self.retry_delay < 0:
            raise ValueError(f"Retry delay cannot be negative: {self.retry_delay}")

        if not self.consume_queue_name:
            raise ValueError("Consume queue name cannot be empty")

        if not self.publish_exchange_name:
            raise ValueError("Publish exchange name cannot be empty")
