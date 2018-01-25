import secrets
import string


def gen_seed():
    return ''.join(secrets.choice(string.ascii_uppercase + '9') for _ in range(81))
