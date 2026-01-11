import secrets
import string


def generer_code():
    caracteres = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(caracteres) for _ in range(4))


# print(generer_code())
