# Recommender using external API response directly
API_URL = "https://external.example.com/api/"


def greet(name):
    """Greet via external API response (dependency not directly imported)."""
    import urllib.request
    resp = urllib.request.urlopen(API_URL + str(name))
    return resp.read().decode("utf-8")
