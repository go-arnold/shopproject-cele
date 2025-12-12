import re


def supprimer_commentaires_js_html(fichier):
    """Supprime les commentaires dans les fichiers JavaScript et HTML, puis modifie le fichier original."""

    # Lire le contenu du fichier source
    with open(fichier, 'r', encoding='utf-8') as f:
        code = f.read()

    # Supprimer les commentaires JavaScript :
    # - Les commentaires sur une ligne : // commentaire
    # - Les commentaires multi-lignes : /* commentaire */
    # code_sans_js_commentaires = re.sub(r'//.*?$|/\*.*?\*/', '', code, flags=re.DOTALL | re.MULTILINE)

    # Supprimer les commentaires HTML : <!-- commentaire -->
    code_sans_html_commentaires = re.sub(
        r'<!--.*?-->', '', code, flags=re.DOTALL)

    # Réécrire le fichier sans les commentaires
    with open(fichier, 'w', encoding='utf-8') as f:
        f.write(code_sans_html_commentaires)

    print(
        f"Le fichier {fichier} a été modifié pour supprimer les commentaires.")


# Exemple d'utilisation
fichier = input("entrez chemin: > ")  # Remplace par ton fichier JS ou HTML
supprimer_commentaires_js_html(fichier)
