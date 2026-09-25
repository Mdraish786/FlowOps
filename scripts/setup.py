"""Create local-only secrets. This script never overwrites an existing .env."""
from pathlib import Path
import base64,secrets,sys
root=Path(__file__).resolve().parents[1]
env=root/'.env'
if env.exists(): sys.exit('.env already exists; kept unchanged.')
password=secrets.token_urlsafe(18)
config=f'''# Generated local development configuration. Do not commit or share.
ENVIRONMENT=development
JWT_SECRET={secrets.token_urlsafe(48)}
POSTGRES_PASSWORD={secrets.token_hex(24)}
MFA_ENCRYPTION_KEY={base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()}
DEMO_PASSWORD={password}
FRONTEND_ORIGIN=http://localhost:8080
REQUIRE_MFA=false
REQUIRE_MALWARE_SCAN=false
SMTP_HOST=
SMTP_PORT=587
SMTP_FROM=flowops@example.com
SMTP_STARTTLS=true
'''
env.write_text(config)
print('Created .env with unique local secrets.')
print('Demo sign-in password: '+password)
print('For non-Docker setup: copy .env to backend/.env and set FRONTEND_ORIGIN=http://localhost:5173.')
