"""python scripts/make_admin_hash.py -> prints a hash for ADMIN_PASSWORD_HASH (never store the password)."""
import getpass
from werkzeug.security import generate_password_hash
p = getpass.getpass("Admin password (min 12 chars): ")
assert len(p) >= 12, "too short"; print(generate_password_hash(p))
