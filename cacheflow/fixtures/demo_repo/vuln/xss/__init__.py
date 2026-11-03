from markupsafe import escape as safe_escape


def render(template, name):
    """Render template with unvalidated user-controlled name (vulnerable: XSS)."""
    return template % {name: name}
