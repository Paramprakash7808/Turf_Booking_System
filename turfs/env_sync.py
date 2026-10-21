"""
Credential Persistence Utility for .env file.
Automatically records newly created users, admins, managers, and staff
into the project's .env file whenever an account is created or registered.
"""
import os
import re
import datetime
import threading
from pathlib import Path
from django.conf import settings

_ENV_LOCK = threading.Lock()

def get_env_file_path() -> Path:
    """Returns the absolute path to the project .env file."""
    if hasattr(settings, 'BASE_DIR'):
        return Path(settings.BASE_DIR) / '.env'
    return Path(__file__).resolve().parent.parent / '.env'

def sanitize_identifier(value: str) -> str:
    """Sanitizes an email, username, or role into a valid UPPERCASE .env variable key."""
    if not value:
        return 'ACCOUNT'
    cleaned = re.sub(r'[^A-Za-z0-9]', '_', str(value).strip().upper())
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')
    return cleaned or 'ACCOUNT'

def format_env_value(val: str) -> str:
    """Formats value safely for .env syntax, adding quotes if spaces, #, or quotes exist."""
    val = str(val).replace('\r', '').replace('\n', '')
    if any(c in val for c in ['#', ' ', '\t', '"', "'", '$', '\\']):
        escaped = val.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    return val

def get_role_prefix(role: str) -> str:
    """Returns clean prefix for role category."""
    r = (role or '').upper().replace(' ', '_').strip()
    if r in ('PLAYER', 'CUSTOMER', 'USER'):
        return 'USER'
    if r in ('STAFF',):
        return 'STAFF'
    if r in ('MANAGER',):
        return 'MANAGER'
    if r in ('ORG_ADMIN', 'ORGANIZATION_ADMIN'):
        return 'ORG_ADMIN'
    if r in ('SUPER_ADMIN', 'SUPERADMIN'):
        return 'SUPERADMIN'
    return f"ROLE_{sanitize_identifier(r)}"

def save_credentials_to_env(
    email: str,
    password: str,
    role: str = 'PLAYER',
    username: str = None,
    name: str = None,
    organization: str = None,
    branch: str = None,
    target_file: Path = None
) -> bool:
    """
    Saves or updates account credentials in the .env file.
    Preserves all existing environment configurations.
    """
    if not email or not password:
        return False

    email = str(email).strip()
    password = str(password)
    username = str(username).strip() if username else email
    role = str(role or 'PLAYER').strip()

    prefix = get_role_prefix(role)
    ident = sanitize_identifier(email)
    var_base = f"{prefix}_{ident}"

    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    meta_parts = [f"Account: {email}", f"Role: {role}"]
    if name:
        meta_parts.append(f"Name: {name.strip()}")
    if organization:
        meta_parts.append(f"Org: {organization.strip()}")
    if branch:
        meta_parts.append(f"Branch: {branch.strip()}")
    meta_parts.append(f"Saved: {now_str}")
    meta_comment = " | ".join(meta_parts)

    formatted_password = format_env_value(password)

    keys_to_set = {
        f"{var_base}_EMAIL": email,
        f"{var_base}_USERNAME": username,
        f"{var_base}_PASSWORD": formatted_password,
        f"{var_base}_ROLE": role,
        "NEW_ACCOUNT_EMAIL": email,
        "NEW_ACCOUNT_USERNAME": username,
        "NEW_ACCOUNT_PASSWORD": formatted_password,
        "NEW_ACCOUNT_ROLE": role,
        "LATEST_CREATED_USER_EMAIL": email,
        "LATEST_CREATED_USER_USERNAME": username,
        "LATEST_CREATED_USER_PASSWORD": formatted_password,
        "LATEST_CREATED_USER_ROLE": role,
    }

    # Synchronize current process os.environ immediately
    for k, v in keys_to_set.items():
        raw_val = password if 'PASSWORD' in k else v
        os.environ[k] = raw_val

    env_path = target_file if target_file is not None else get_env_file_path()

    with _ENV_LOCK:
        try:
            if not env_path.exists():
                lines = []
            else:
                with open(env_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

            # Ensure newline termination of existing lines
            if lines and not lines[-1].endswith('\n'):
                lines[-1] += '\n'

            key_line_map = {}
            for idx, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('#') or '=' not in stripped:
                    continue
                k = stripped.split('=', 1)[0].strip()
                if k:
                    key_line_map[k] = idx

            # 1. Update or initialize the "LATEST CREATED ACCOUNT" block
            latest_keys = [
                "NEW_ACCOUNT_EMAIL",
                "NEW_ACCOUNT_USERNAME",
                "NEW_ACCOUNT_PASSWORD",
                "NEW_ACCOUNT_ROLE",
                "LATEST_CREATED_USER_EMAIL",
                "LATEST_CREATED_USER_USERNAME",
                "LATEST_CREATED_USER_PASSWORD",
                "LATEST_CREATED_USER_ROLE",
            ]

            master_header_marker = "# CREATED USERS & TEAM ACCOUNTS (Auto-saved on Account Creation)"
            content_str = "".join(lines)

            # If master section doesn't exist, append master header + LATEST block
            if master_header_marker not in content_str:
                lines.extend([
                    "\n",
                    "# " + "=" * 78 + "\n",
                    f"{master_header_marker}\n",
                    "# " + "=" * 78 + "\n",
                    "\n",
                    "# --- MOST RECENTLY CREATED ACCOUNT ---\n",
                    f"NEW_ACCOUNT_EMAIL={email}\n",
                    f"NEW_ACCOUNT_USERNAME={username}\n",
                    f"NEW_ACCOUNT_PASSWORD={formatted_password}\n",
                    f"NEW_ACCOUNT_ROLE={role}\n",
                    f"LATEST_CREATED_USER_EMAIL={email}\n",
                    f"LATEST_CREATED_USER_USERNAME={username}\n",
                    f"LATEST_CREATED_USER_PASSWORD={formatted_password}\n",
                    f"LATEST_CREATED_USER_ROLE={role}\n",
                    "\n",
                    "# --- CREATED ACCOUNTS DIRECTORY ---\n",
                ])
                # Re-index lines after appending
                key_line_map = {}
                for idx, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith('#') or '=' not in stripped:
                        continue
                    k = stripped.split('=', 1)[0].strip()
                    if k:
                        key_line_map[k] = idx
            else:
                # Update existing LATEST keys
                for lk in latest_keys:
                    if lk in key_line_map:
                        lines[key_line_map[lk]] = f"{lk}={keys_to_set[lk]}\n"
                    else:
                        lines.append(f"{lk}={keys_to_set[lk]}\n")

            # 2. Add or update the specific user's distinct keys
            user_key_prefix = f"{var_base}_EMAIL"
            user_exists = user_key_prefix in key_line_map

            user_keys = [
                f"{var_base}_EMAIL",
                f"{var_base}_USERNAME",
                f"{var_base}_PASSWORD",
                f"{var_base}_ROLE",
            ]

            if user_exists:
                # Update in place
                for uk in user_keys:
                    if uk in key_line_map:
                        lines[key_line_map[uk]] = f"{uk}={keys_to_set[uk]}\n"
                    else:
                        lines.append(f"{uk}={keys_to_set[uk]}\n")
            else:
                # Append dedicated block for this account
                lines.extend([
                    f"\n# [{meta_comment}]\n",
                    f"{var_base}_EMAIL={email}\n",
                    f"{var_base}_USERNAME={username}\n",
                    f"{var_base}_PASSWORD={formatted_password}\n",
                    f"{var_base}_ROLE={role}\n",
                ])

            # Write atomically back to disk
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except OSError:
                    pass
            return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error saving credentials to .env: {e}")
            return False
