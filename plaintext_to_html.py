import html
import re
from bs4 import BeautifulSoup

def formatter_html_beautifulsoup(html_string):
    """Formate du HTML avec Beautiful Soup."""
    soup = BeautifulSoup(html_string, 'html.parser')
    return soup.prettify()

def convertir_texte_en_html(fichier_texte, fichier_html):
    """Convertit un fichier texte structuré en HTML (gestion imbrication)."""

    try:
        with open(fichier_texte, 'r', encoding='utf-8') as f:
            contenu = f.read()
    except FileNotFoundError:
        print(f"Erreur : Fichier '{fichier_texte}' non trouvé.")
        return

    style = """<style>
    /* Reset CSS (pour uniformiser le rendu entre les navigateurs) */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box; /* Important pour la gestion des marges et des paddings */
    }

    body {
        font-family: 'Arial', sans-serif;
        background-color: #f4f4f9; /* Fond doux gris clair */
        color: #333; /* Texte sombre pour le contraste */
        padding: 30px;
        line-height: 1.6;
        margin: 0;
    }

    ::selection {
        background: #3498db; /* Couleur de sélection bleue */
        color: #fff; /* Texte blanc sur sélection bleue */
    }

    /* Thème Matte pour Highlight.js */
    .hljs {
        background: #f7f7f7; /* Fond clair doux */
        color: #333; /* Texte gris foncé */
        padding: 1px 2px; /* Espacement interne */
        border-radius: 4px; /* Coins arrondis */
        font-family: 'Fira Code', monospace; /* Police lisible pour le code */
        line-height: 1.6; /* Espacement entre les lignes */
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* Ombre douce */
        border: 1px solid #e0e0e0; /* Bordure légère */
    }

    /* Couleurs pour différents types de syntaxe */
    .hljs-keyword, .hljs-selector-tag, .hljs-name {
        color: #005cc5; /* Bleu doux pour les mots-clés */
        font-weight: bold;
    }

    .hljs-string, .hljs-meta-string {
        color: #22863a; /* Vert doux pour les chaînes */
    }

    .hljs-comment {
        color: #6a737d; /* Gris moyen pour les commentaires */
        font-style: italic;
    }

    .hljs-number, .hljs-literal, .hljs-builtin, .hljs-type {
        color: #d73a49; /* Rouge pastel pour les types et littéraux */
    }

    .hljs-attribute, .hljs-variable {
        color: #e36209; /* Orange clair pour les variables et attributs */
    }

    .hljs-title, .hljs-section, .hljs-selector-id {
        color: #005cc5; /* Bleu pour les titres et ID */
        font-weight: bold;
    }

    .hljs-emphasis {
        font-style: italic;
    }

    .hljs-strong {
        font-weight: bold;
    }

    /* Titres */
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50; /* Couleur sombre et élégante */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 600;
        text-align: left;
        margin-bottom: 20px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    h1 {
        font-size: 2.5em;
        border-bottom: 2px solid #bdc3c7;
        padding-bottom: 10px;
    }

    h2 {
        font-size: 2em;
        color: #34495e;
    }

    h3 {
        font-size: 1.75em;
        color: #7f8c8d;
    }

    h4, h5, h6 {
        font-size: 1.5em;
    }

    /* Gestion des balises <code> dans les titres */
    h1 code, h2 code, h3 code, h4 code, h5 code, h6 code {
        background-color: #ecf0f1; /* Fond clair pour le code */
        padding: 1px 2px;
        border-radius: 4px;
        display: inline-block; /* Assure que le code est inline dans les titres */
        font-size: 0.9em; /* Ajuste la taille du code pour les titres */
    }

    /* Paragraphe */
    p {
        font-size: 1.1em;
        color: #555; /* Texte gris foncé pour une lecture agréable */
        margin-bottom: 1em;
        line-height: 1.8;
    }

    p code {
        background-color: #ecf0f1; /* Fond clair pour le code */
        padding: 1px 2px;
        border-radius: 4px;
        display: inline-block; /* Assure que le code est inline dans les paragraphes */
        font-size: 0.9em; /* Ajuste la taille du code pour les paragraphes */ 
    }

    /* Liens */
    a {
        color: #3498db; /* Bleu doux pour les liens */
        text-decoration: none;
        transition: all 0.3s ease;
    }

    a:hover {
        text-decoration: underline;
        color: #2980b9; /* Bleu plus foncé au survol */
    }

    /* Listes */
    ul, ol {
        padding-left: 20px;
        margin-bottom: 1em;
    }

    li {
        margin-bottom: 10px;
        color: #666; /* Couleur douce pour les éléments de liste */
    }

    ul code, li code, ol code {
        background-color: #ecf0f1; /* Fond clair pour le code */
        padding: 1px 2px;
        border-radius: 4px;
        display: inline-block; /* Assure que le code est inline dans les listes */
        font-size: 0.9em; /* Ajuste la taille du code pour les listes */
    }

    /* Panneau d'arborescence */
    #panneau-arborescence {
        position: fixed;
        top: 65px;
        right: 20px;
        background: #fff;
        border: 1px solid #ddd;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        padding: 10px;
        max-height: 500px;
        overflow-y: auto;
        width: 250px;
    }

    #panneau-arborescence ul {
        padding: 0;
        list-style-type: none;
    }

    #panneau-arborescence li {
        padding: 5px;
        cursor: pointer;
    }

    #panneau-arborescence li:hover {
        background-color: #f4f4f4;
    }

    #panneau-arborescence a {
        text-decoration: none;
        color: #333;
    }

    #panneau-arborescence a:hover {
        color: #3498db;
    }

    /* Code */
    code {
        font-family: 'Fira Code', monospace;
        background-color: #ecf0f1; /* Fond légèrement gris pour le code */
        padding: 4px 8px;
        border-radius: 4px;
        line-height: 1.4;
        display: block; /* Affiche le code sur une ligne */
        white-space: pre-wrap; /* Préserve les sauts de ligne et les espaces */
    }

    pre {
        font-family: 'Fira Code', monospace;
        background-color: #ecf0f1;
        padding: 5px;
        border-radius: 4px;
        overflow-x: auto;
        font-size: 1em;
        display: inline-block; /* Empêche le saut de ligne */
    }

    /* Box */
    .box {
        background-color: #fff;
        padding: 20px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); /* Ombre douce */
        border-radius: 8px;
        margin-bottom: 20px;
    }

    /* Citations */
    blockquote {
        border-left: 5px solid #bdc3c7;
        padding-left: 15px;
        font-style: italic;
        margin: 20px 0;
        color: #7f8c8d;
        font-size: 1.2em;
    }

    /* Boutons */
    button {
        background-color: #3498db;
        color: #fff;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        font-size: 1em;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }

    button:hover {
        background-color: #2980b9; /* Changement de couleur au survol */
    }

    /* Formulaires */
    input, textarea {
        width: 100%;
        padding: 10px;
        font-size: 1em;
        border-radius: 5px;
        border: 1px solid #bdc3c7;
        margin-bottom: 10px;
        background-color: #f9f9f9;
    }

    input:focus, textarea:focus {
        border-color: #3498db;
        outline: none;
    }
</style>"""

    with open(fichier_html, 'w', encoding='utf-8') as html_file:
        html_file.write("<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"UTF-8\">\n<title>Texte Structuré</title>\n" + style + "\n")  # En-tête du document
        html_file.write("</head>\n<body>\n")  # Début du corps du document

        regex = r'(<(h[1-6]|p|ul|ol|code)[^>]*>.*?</\2>)'
        matches = re.finditer(regex, contenu, re.DOTALL)
        
        titres = []  # Liste pour stocker les titres trouvés
        index = 0
        for match in matches:
            tag_content = match.group(0)
            if "<code>" in tag_content:
                # Traitement des balises <code> pour éviter de les gérer une par une
                tag_content = handle_code_in_text(tag_content)
            if "<ul>" in tag_content or "<ol>" in tag_content:
                # Traitement des balises <ul> et <ol> avec des éléments entre {}
                tag_content = handle_list_items(tag_content)
            # Si c'est un titre, ajouter un ID unique
            if tag_content.startswith("<h"):
                titre_tag = re.match(r'<h([1-6])', tag_content).group(1)
                titre_id = f"section{index + 1}"  # ID unique basé sur l'ordre des titres
                tag_content = tag_content.replace(f"<h{titre_tag}>", f"<h{titre_tag} id=\"{titre_id}\">")

                # Extraire le texte brut du titre (sans les balises HTML)
                soup = BeautifulSoup(tag_content, 'html.parser')
                titre_text = soup.get_text(" ",strip=True)

                titres.append((int(titre_tag), titre_text, titre_id))  # Stocker le texte du titre et son ID avec le niveau du titre
            
            html_file.write(tag_content)

            # Mettre à jour l'index pour avancer dans le texte
            index = match.end()

        # Si des parties du texte restent non traitées, les ajouter comme paragraphes
        remaining_text = contenu[index:]
        if remaining_text.strip():
          html_file.write(f"<p>{html.escape(remaining_text.strip())}</p>\n")

        # Ajouter un bouton pour afficher/masquer le panneau d'arborescence avec icone Awesome Font
        html_file.write("""<button id="toggle-panneau" style="position: fixed; top: 20px; right: 20px; background: #3498db; color: #fff; padding: 10px; border: none; border-radius: 5px; font-size: 1em; cursor: pointer; transition: background-color 0.3s ease;"><i class="fas fa-sitemap"></i> Arborescence</button>""")
        
        # Construire le panneau d'arborescence non affiché par défaut
        html_file.write("""<div id="panneau-arborescence" style="display: none;"><ul>""")

        for titre_level, titre_text, titre_id in titres:
            padding = 20 * (titre_level - 1) + 10  # Appliquer du padding-left basé sur le niveau
            titre_text_html = html.escape(titre_text)  # Échapper les caractères spéciaux
            html_file.write(f'<li style="padding-left: {padding}px;"><a href="#{titre_id}">{titre_text_html}</a></li>\n')

        html_file.write("""</ul></div>""")

        html_file.write("""\n<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
<script>
document.addEventListener("DOMContentLoaded", () => {
    const toggleButton = document.getElementById('toggle-panneau');
    const panneauArborescence = document.getElementById('panneau-arborescence');

    toggleButton.addEventListener('click', () => {
        panneauArborescence.style.display = panneauArborescence.style.display === 'none' ? 'block' : 'none';
    });
});
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll('code').forEach((block) => {
        try {
            const result = hljs.highlightAuto(block.textContent);
            block.classList.add(result.language || 'bash'); // Appliquer le langage détecté ou bash par défaut
        } catch (e) {
            block.classList.add('bash'); // Appliquer bash par défaut
        }
        hljs.highlightElement(block);
    });
});
</script>\n</body>\n</html>\n""")
    print(f"Fichier HTML '{fichier_html}' créé.")

def handle_code_in_text(text):
    """Gère l'imbrication des balises <code> dans le texte."""
    # Si le <code> est dans un <p>, <ul> ou <ol>, ne pas ajouter <pre>
    if any(tag in text for tag in ['<p>', '<ul>', '<ol>']):
        # Remplace toutes les balises <code> sans ajouter <pre>
        return re.sub(r'(<code>)(.*?)(</code>)', lambda m: f"<code>{html.escape(m.group(2))}</code>", text)
    else:
        # Ajoute <pre> seulement si <code> est utilisé seul
        return re.sub(r'(<code>)(.*?)(</code>)', lambda m: f"<code>{html.escape(m.group(2))}</code>", text)

def handle_list_items(text):
    """Gère l'imbrication des éléments de liste dans les balises <ul> et <ol>."""
    # Remplace les éléments entre {} par des éléments de liste <li>
    # Corrige la structure de la liste en évitant l'imbrication
    text = re.sub(r'\{(.*?)\}', lambda m: f"<li>{'</li><li>'.join(m.group(1).split(','))}</li>", text)
    # Enveloppe le tout dans une balise <ul> ou <ol> s'il n'y en a pas déjà
    if "<ul>" in text or "<ol>" in text:
        return text
    else:
        return f"<ul>{text}</ul>"

def prettify_html(html_string):
    with open(html_string, "r", encoding="utf-8") as f:
        html_contenu = f.read()

    html_formate = formatter_html_beautifulsoup(html_contenu)

    with open("output.html", "w", encoding="utf-8") as f:
        f.write(html_formate)

    print("Fichier HTML formaté avec Beautiful Soup créé : output.html")

convertir_texte_en_html("input.txt", "output.html")
