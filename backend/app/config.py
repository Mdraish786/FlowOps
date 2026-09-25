from functools import lru_cache
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'sqlite:///./flowops.db'
    jwt_secret: str
    environment: str = 'development'
    frontend_origin: str = (f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}" if os.getenv('RENDER_EXTERNAL_HOSTNAME') else os.getenv('RENDER_EXTERNAL_URL', 'http://localhost:8080'))
    redis_url: str = ''
    upload_dir: str = './private-uploads'
    smtp_host: str = ''
    smtp_port: int = 587
    smtp_username: str = ''
    smtp_password: str = ''
    smtp_from: str = 'flowops@example.com'
    smtp_starttls: bool = True
    mfa_encryption_key: str = ''
    require_mfa: bool = False
    require_malware_scan: bool = False
    clamav_host: str = 'clamav'
    demo_password: str = ''
    @property
    def secure(self): return self.environment in {'production','staging'}

@lru_cache
def settings():
    s = Settings()
    if len(s.jwt_secret) < 32: raise RuntimeError('JWT_SECRET must be at least 32 random characters.')
    if s.environment == 'production' and (not s.frontend_origin.startswith('https://') or not s.redis_url or not s.mfa_encryption_key or not s.require_mfa or not s.require_malware_scan):
        raise RuntimeError('Production requires HTTPS, Redis, MFA key, REQUIRE_MFA=true and REQUIRE_MALWARE_SCAN=true.')
    return s
