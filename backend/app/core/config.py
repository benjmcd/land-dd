from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.api.secret_specs import normalize_secret_spec

API_KEY_STATUS_ACTIVE = "active"
API_KEY_STATUS_RETIRED = "retired"
API_KEY_STATUSES = frozenset({API_KEY_STATUS_ACTIVE, API_KEY_STATUS_RETIRED})
LOCAL_APP_ENVS = frozenset({"local", "dev", "development", "test"})
SHA256_SECRET_PREFIX = "sha256:"
DEFAULT_REVIEWER_ACCOUNTS = "fixture-reviewer:fixture-token-123"
DEFAULT_REVIEWER_ACCOUNT_SCOPES = (
    "fixture-reviewer:"
    "connector:run|connector:review|operations:read|report:approve|report:retry|report:run"
)


@dataclass(frozen=True)
class ApiKeySpec:
    key_id: str
    status: str
    secret_spec: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="land-diligence", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    database_url: str = Field(
        default="postgresql+psycopg://land:land@localhost:5432/land_diligence",
        alias="DATABASE_URL",
    )
    use_db_services: bool = Field(
        default=False,
        alias="USE_DB_SERVICES",
        description=(
            "Use Postgres-backed API repositories and job stores instead of in-memory "
            "services. Required outside local/dev/development/test APP_ENV values."
        ),
    )
    object_store_root: str = Field(
        default="./local_artifacts/object_store", alias="OBJECT_STORE_ROOT"
    )
    enable_live_connectors: bool = Field(default=False, alias="ENABLE_LIVE_CONNECTORS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    require_api_key: bool = Field(default=False, alias="REQUIRE_API_KEY")
    api_keys: str = Field(
        default="",
        alias="API_KEYS",
        description=(
            "Comma-separated API keys for production API access. "
            "Only used when REQUIRE_API_KEY is true."
        ),
    )
    api_key_specs: str = Field(
        default="",
        alias="API_KEY_SPECS",
        description=(
            "Comma-separated id|status|secret API-key lifecycle specs. "
            "Status must be active or retired; secret may be raw or sha256:<64-hex>."
        ),
    )
    ui_auth_cookie_secret: str | None = Field(
        default=None,
        alias="UI_AUTH_COOKIE_SECRET",
        description=(
            "Optional high-entropy signing secret for /ui API-key session cookies. "
            "Required when REQUIRE_API_KEY is true outside local/dev/development/test "
            "APP_ENV values; otherwise a per-process local fallback is generated."
        ),
    )
    ui_auth_cookie_secure: bool = Field(
        default=False,
        alias="UI_AUTH_COOKIE_SECURE",
        description=(
            "Force the /ui API-key session cookie to be HTTPS-only. Non-local APP_ENV "
            "values enable this automatically."
        ),
    )
    enable_rate_limit: bool = Field(default=False, alias="ENABLE_RATE_LIMIT")
    rate_limit_requests: int = Field(default=120, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")
    reviewer_accounts: str = Field(
        default=DEFAULT_REVIEWER_ACCOUNTS,
        alias="REVIEWER_ACCOUNTS",
        description=(
            "Comma-separated id:token pairs for connector reviewer auth. "
            "Example: 'op1:secret1,op2:secret2'. "
            "Defaults to a local fixture account; override in production."
        ),
    )
    reviewer_account_scopes: str = Field(
        default=DEFAULT_REVIEWER_ACCOUNT_SCOPES,
        alias="REVIEWER_ACCOUNT_SCOPES",
        description=(
            "Comma-separated id:scope|scope entries for connector reviewer auth. "
            "Every REVIEWER_ACCOUNTS id must have explicit scopes."
        ),
    )
    report_auth_mode: str = Field(default="trusted_headers", alias="REPORT_AUTH_MODE")
    report_identity_token_secret: str | None = Field(
        default=None,
        alias="REPORT_IDENTITY_TOKEN_SECRET",
    )
    db_pool_size: int = Field(
        default=5,
        alias="DB_POOL_SIZE",
        description=(
            "Number of persistent connections to keep open in the SQLAlchemy connection pool. "
            "Ignored when DATABASE_URL uses SQLite."
        ),
    )
    db_max_overflow: int = Field(
        default=10,
        alias="DB_MAX_OVERFLOW",
        description=(
            "Maximum number of connections to allow above DB_POOL_SIZE before blocking. "
            "Ignored when DATABASE_URL uses SQLite."
        ),
    )
    db_pool_timeout: int = Field(
        default=30,
        alias="DB_POOL_TIMEOUT",
        description=(
            "Seconds to wait for a connection from the pool before raising a timeout error. "
            "Ignored when DATABASE_URL uses SQLite."
        ),
    )
    db_pool_recycle: int = Field(
        default=1800,
        alias="DB_POOL_RECYCLE",
        description=(
            "Seconds after which idle connections are recycled to avoid stale-connection errors. "
            "Ignored when DATABASE_URL uses SQLite."
        ),
    )
    connector_auto_approve: bool = Field(
        default=False,
        alias="CONNECTOR_AUTO_APPROVE",
        description=(
            "When true, connector runs classified as READY_FOR_CONNECTOR_QA are "
            "automatically approved without manual review-action. "
            "Safe for fixture and federal public-source connectors. "
            "Do not enable for unreviewed third-party vendor connectors."
        ),
    )

    def is_local_app_env(self) -> bool:
        return self.app_env.lower() in LOCAL_APP_ENVS

    def validate_secret_hygiene(self) -> None:
        if self.is_local_app_env():
            return
        if self.api_keys.strip() or self.require_api_key:
            self.parsed_api_keys()
        elif self.api_key_specs.strip():
            self.parsed_api_key_specs()
        accounts = self.parsed_reviewer_accounts()
        scopes = self.parsed_reviewer_account_scopes()
        missing_scopes = sorted(set(accounts) - set(scopes))
        if missing_scopes:
            raise ValueError(
                "Non-local APP_ENV values require explicit REVIEWER_ACCOUNT_SCOPES "
                f"for reviewer id: {missing_scopes[0]!r}"
            )
        unknown_scopes = sorted(set(scopes) - set(accounts))
        if unknown_scopes:
            raise ValueError(
                "REVIEWER_ACCOUNT_SCOPES references unknown reviewer id: "
                f"{unknown_scopes[0]!r}"
            )

    def parsed_api_keys(self) -> frozenset[str]:
        if not self.is_local_app_env():
            if self.api_keys.strip():
                raise ValueError(
                    "API_KEYS is local-only; non-local APP_ENV values must use "
                    "API_KEY_SPECS."
                )
            if self.require_api_key and not self.api_key_specs.strip():
                raise ValueError(
                    "API_KEY_SPECS is required when REQUIRE_API_KEY=true outside "
                    "local/dev/development/test APP_ENV values."
                )
        keys: set[str] = set()
        for entry in self.api_keys.split(","):
            raw_key = entry.strip()
            if not raw_key:
                continue
            key = normalize_secret_spec(raw_key, "API_KEYS entry")
            if key in keys:
                raise ValueError("Duplicate API_KEYS entry")
            keys.add(key)
        for spec in self.parsed_api_key_specs():
            if spec.status != API_KEY_STATUS_ACTIVE:
                continue
            if spec.secret_spec in keys:
                raise ValueError("Duplicate active API key secret")
            keys.add(spec.secret_spec)
        return frozenset(keys)

    def parsed_api_key_specs(self) -> tuple[ApiKeySpec, ...]:
        specs: list[ApiKeySpec] = []
        seen_ids: set[str] = set()
        seen_secrets: set[str] = set()
        for entry in self.api_key_specs.split(","):
            raw_entry = entry.strip()
            if not raw_entry:
                continue
            parts = [part.strip() for part in raw_entry.split("|")]
            if len(parts) != 3:
                raise ValueError(
                    f"API_KEY_SPECS entry must be id|status|secret, got: {raw_entry!r}"
                )
            key_id, status, secret = parts
            if not key_id or not status or not secret:
                raise ValueError("API_KEY_SPECS entries must include id, status, and secret")
            if key_id in seen_ids:
                raise ValueError(f"Duplicate API_KEY_SPECS id: {key_id!r}")
            normalized_status = status.lower()
            if normalized_status not in API_KEY_STATUSES:
                raise ValueError("API_KEY_SPECS status must be active or retired")
            secret_spec = normalize_secret_spec(secret, "API_KEY_SPECS secret")
            if not self.is_local_app_env() and not secret_spec.startswith(
                SHA256_SECRET_PREFIX
            ):
                raise ValueError(
                    "Non-local APP_ENV API_KEY_SPECS secrets must use "
                    "sha256:<64-hex>."
                )
            if secret_spec in seen_secrets:
                raise ValueError("Duplicate API_KEY_SPECS secret")
            seen_ids.add(key_id)
            seen_secrets.add(secret_spec)
            specs.append(
                ApiKeySpec(
                    key_id=key_id,
                    status=normalized_status,
                    secret_spec=secret_spec,
                )
            )
        return tuple(specs)

    def parsed_rate_limit(self) -> tuple[int, int]:
        if self.rate_limit_requests < 1:
            raise ValueError("RATE_LIMIT_REQUESTS must be at least 1")
        if self.rate_limit_window_seconds < 1:
            raise ValueError("RATE_LIMIT_WINDOW_SECONDS must be at least 1")
        return self.rate_limit_requests, self.rate_limit_window_seconds

    def parsed_reviewer_accounts(self) -> dict[str, str]:
        non_local = not self.is_local_app_env()
        if non_local and self.reviewer_accounts.strip() == DEFAULT_REVIEWER_ACCOUNTS:
            raise ValueError("The default fixture reviewer account is local-only.")
        accounts: dict[str, str] = {}
        for pair in self.reviewer_accounts.split(","):
            pair = pair.strip()
            if not pair:
                continue
            if ":" not in pair:
                raise ValueError(f"REVIEWER_ACCOUNTS entry must be id:token, got: {pair!r}")
            reviewer_id, token = pair.split(":", 1)
            reviewer_id = reviewer_id.strip()
            token = token.strip()
            if not reviewer_id or not token:
                raise ValueError("REVIEWER_ACCOUNTS entries must include id and token")
            if reviewer_id in accounts:
                raise ValueError(f"Duplicate REVIEWER_ACCOUNTS id: {reviewer_id!r}")
            token_spec = normalize_secret_spec(
                token,
                "REVIEWER_ACCOUNTS token",
            )
            if non_local and not token_spec.startswith(SHA256_SECRET_PREFIX):
                raise ValueError(
                    "Non-local APP_ENV REVIEWER_ACCOUNTS tokens must use "
                    "sha256:<64-hex>."
                )
            accounts[reviewer_id] = token_spec
        return accounts

    def parsed_reviewer_account_scopes(self) -> dict[str, frozenset[str]]:
        if (
            not self.is_local_app_env()
            and not self.reviewer_account_scopes.strip()
        ):
            raise ValueError(
                "Non-local APP_ENV values require explicit REVIEWER_ACCOUNT_SCOPES."
            )
        scoped_accounts: dict[str, frozenset[str]] = {}
        for entry in self.reviewer_account_scopes.split(","):
            entry = entry.strip()
            if not entry:
                continue
            if ":" not in entry:
                raise ValueError(
                    f"REVIEWER_ACCOUNT_SCOPES entry must be id:scope|scope, got: {entry!r}"
                )
            reviewer_id, scopes_text = entry.split(":", 1)
            reviewer_id = reviewer_id.strip()
            scopes = frozenset(scope.strip() for scope in scopes_text.split("|") if scope.strip())
            if not reviewer_id or not scopes:
                raise ValueError("REVIEWER_ACCOUNT_SCOPES entries must include id and scopes")
            if reviewer_id in scoped_accounts:
                raise ValueError(f"Duplicate REVIEWER_ACCOUNT_SCOPES id: {reviewer_id!r}")
            scoped_accounts[reviewer_id] = scopes
        return scoped_accounts


@lru_cache
def get_settings() -> Settings:
    return Settings()
