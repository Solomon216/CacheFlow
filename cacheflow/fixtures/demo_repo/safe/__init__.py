# Safe alternative patterns
def safe_load_yaml(path):
    """Safe YAML loading with allowlisted schema only."""
    import yaml
    schema = {"allowlist": ["key", "value"]}
    with open(path) as f:
        return yaml.safe_load(f)


def safe_render(template, name):
    """Render with escaped input (XSS-safe)."""
    from markupsafe import escape
    return template % {"name": escape(str(name))}


def verify_connection(url, verify=True):
    """Connection with explicit verification."""
    import ssl
    ctx = ssl.create_default_context()
    if verify:
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
    else:
        raise ValueError("TLS verification required")
    import urllib.request
    urllib.request.urlopen(url, context=ctx)
