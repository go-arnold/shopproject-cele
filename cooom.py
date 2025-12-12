import re


def supprimer_commentaires_et_docstrings(fichier):
    """Supprime les commentaires et les docstrings d'un fichier Python, puis modifie le fichier original."""

    # Ouvrir le fichier source en lecture
    with open(fichier, 'r', encoding='utf-8') as f:
        code = f.read()

    # Supprimer les docstrings ("""...""" ou '''...''')
    code_sans_docstrings = re.sub(
        r'("""(.*?)"""|\'\'\'(.*?)\'\'\')', '', code, flags=re.DOTALL)

    # Supprimer les commentaires qui commencent par #
    code_sans_commentaires = re.sub(r'#.*', '', code_sans_docstrings)

    # Ouvrir le fichier en mode écriture pour remplacer son contenu
    with open(fichier, 'w', encoding='utf-8') as f:
        f.write(code_sans_commentaires)

    print(
        f"Le fichier {fichier} a été modifié avec succès pour supprimer les commentaires et docstrings.")


# Exemple d'utilisation
fichier = input("Le chemin du fichier a modifier > ")
supprimer_commentaires_et_docstrings(fichier)
