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

    with open(fichier_html, 'w', encoding='utf-8') as html_file:
        html_file.write("<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"UTF-8\">\n<title>Texte Structuré</title>\n<link rel=\"stylesheet\" href=\"style.css\">\n")  # En-tête du document
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
        # Ajouter la dépendance pour les icônes Font Awesome
        html_file.write("""<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">\n""")
        
        # Ajouter un bouton pour afficher/masquer le panneau d'arborescence avec icône Font Awesome
        html_file.write("""<button id="toggle-panneau" style="position: fixed; top: 20px; right: 20px; background: #3498db; color: #fff; padding: 10px; border: none; border-radius: 5px; font-size: 1em; cursor: pointer; transition: background-color 0.3s ease;">
        <i class="fas fa-bars" style="font-size: 24px;"></i>
        </button>\n""")
        
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
