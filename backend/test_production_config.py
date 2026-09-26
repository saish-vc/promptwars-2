from app.core.config import Settings


def test_production_configuration_requires_all_services() -> None:
    settings = Settings(
        enable_fallback_mode=False,
        llm_provider="groq",
        groq_api_key="",
        redis_url="",
        s3_access_key="",
        s3_secret_key="",
    )
    assert {"REDIS_URL", "S3_ACCESS_KEY", "S3_SECRET_KEY", "GROQ_API_KEY"} <= set(
        settings.production_errors()
    )

    configured = Settings(
        enable_fallback_mode=False,
        llm_provider="groq",
        groq_api_key="test",
        redis_url="redis://localhost:6379/0",
        s3_access_key="test",
        s3_secret_key="test",
    )
    assert configured.production_errors() == []
