import pickle


def deserialize(data):
    """Pickle-deserialize user input (vulnerable: unsafe deserialization)."""
    return pickle.loads(data)


def run():
    deserialize("os")
