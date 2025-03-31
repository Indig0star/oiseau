import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io

########################################
# Fonctions utilitaires
########################################

def load_font(font_size, bold=False):
    """
    Charge une police TrueType (Arial) avec la taille donnée.
    Si indisponible, fallback sur load_default().
    """
    try:
        if bold:
            return ImageFont.truetype("arialbd.ttf", font_size)
        else:
            return ImageFont.truetype("arial.ttf", font_size)
    except:
        return ImageFont.load_default()

def get_line_height(font, line_spacing=0):
    """
    Calcule la hauteur réelle d'une ligne de texte (en pixels),
    en tenant compte des métriques de la police + un éventuel espacement personnalisé.
    """
    ascent, descent = font.getmetrics()
    return ascent + descent + line_spacing

def split_long_word(word, draw, font, max_width):
    """
    Découpe un mot trop long en segments qui tiennent chacun dans max_width.
    Retourne une liste de segments.
    """
    segments = []
    current_segment = ""
    current_width = 0

    for char in word:
        char_width = draw.textlength(char, font=font)
        if current_width + char_width <= max_width:
            # On ajoute le caractère au segment courant
            current_segment += char
            current_width += char_width
        else:
            # On valide le segment courant
            segments.append(current_segment)
            # On démarre un nouveau segment
            current_segment = char
            current_width = char_width

    if current_segment:
        segments.append(current_segment)

    return segments

def wrap_text_by_pixels(draw, text, font, max_width):
    """
    Retourne une liste de lignes (strings) telles qu'aucune ne dépasse max_width en pixels.
    Gère également les mots trop longs (sans espaces) en les fractionnant.
    """
    words = text.split()  # Séparation sur les espaces
    lines = []
    current_line = ""
    current_width = 0

    for w in words:
        # On teste la largeur d'un mot + un espace
        w_test = w + " "
        w_width = draw.textlength(w_test, font=font)

        # Si le mot lui-même dépasse max_width (long mot sans espace),
        # on va le découper en segments plus petits.
        if w_width > max_width:
            # Si on a déjà du texte dans la ligne courante, on la pousse dans lines
            if current_line:
                lines.append(current_line.rstrip())  # retire l'espace final
                current_line = ""
                current_width = 0

            # On fractionne le mot
            sub_parts = split_long_word(w, draw, font, max_width)
            for i, part in enumerate(sub_parts):
                part_test = part + " "
                part_width = draw.textlength(part_test, font=font)

                # Chaque segment part dans sa propre ligne si c'est large
                if part_width > max_width:
                    # Cas extrême, on ajoute quand même la ligne
                    lines.append(part)
                else:
                    # On crée une nouvelle ligne pour chaque segment
                    lines.append(part)
            # On remet un espace après le mot
        else:
            # Cas normal : le mot tient dans la largeur
            if current_width + w_width <= max_width:
                # On peut ajouter ce mot à la ligne courante
                current_line += w + " "
                current_width += w_width
            else:
                # On doit passer à la ligne suivante
                lines.append(current_line.rstrip())  # On retire l'espace en fin
                current_line = w + " "
                current_width = w_width

    # Dernière ligne si pas vide
    if current_line.strip():
        lines.append(current_line.rstrip())

    return lines

def get_text_bubble_height(draw, text, font, bubble_width, margin, line_spacing):
    """
    Calcule la hauteur totale (en pixels) que prendra la bulle de texte
    (avec marges + wraps). Ne dessine rien, juste un calcul.
    """
    max_text_width = bubble_width - 2 * margin
    lines = wrap_text_by_pixels(draw, text, font, max_text_width)
    line_h = get_line_height(font, line_spacing)
    total_text_height = len(lines) * line_h
    return margin + total_text_height + margin

def draw_text_bubble(draw, text, x, y, bubble_width,
                     text_font, text_color,
                     bubble_color, corner_radius,
                     margin, line_spacing):
    """
    Dessine un bloc de texte (wrap automatique) dans une bulle arrondie,
    en partant des coordonnées (x, y).
    Retourne la coordonnée Y juste en-dessous de la bulle.
    """
    max_text_width = bubble_width - 2*margin
    lines = wrap_text_by_pixels(draw, text, text_font, max_text_width)
    line_h = get_line_height(text_font, line_spacing)
    total_text_height = len(lines) * line_h
    total_height = margin + total_text_height + margin

    # Dessin de la bulle
    draw.rounded_rectangle((x, y, x + bubble_width, y + total_height),
                           radius=corner_radius, fill=bubble_color)

    # Écriture du texte
    current_y = y + margin
    for line in lines:
        draw.text((x + margin, current_y), line, font=text_font, fill=text_color)
        current_y += line_h

    return y + total_height + 10

def draw_label_and_content(draw, label, content,
                           x, y, bubble_width,
                           label_font, content_font,
                           label_color, content_color,
                           bubble_color, corner_radius,
                           margin, label_content_gap,
                           line_spacing):
    """
    Dessine un label (ex: "Nom scientifique") en gras + un contenu
    dans une bulle arrondie. Gère le wrap automatique selon la largeur.
    Retourne la coordonnée Y après dessin de la bulle.
    """
    max_text_width = bubble_width - 2*margin

    # On wrap le label et le contenu
    label_lines = wrap_text_by_pixels(draw, label, label_font, max_text_width)
    content_lines = wrap_text_by_pixels(draw, content, content_font, max_text_width)

    label_line_height = get_line_height(label_font, line_spacing)
    content_line_height = get_line_height(content_font, line_spacing)

    label_height_total = len(label_lines) * label_line_height
    content_height_total = len(content_lines) * content_line_height

    total_height = margin + label_height_total + label_content_gap + content_height_total + margin

    # Dessin de la bulle
    draw.rounded_rectangle((x, y, x + bubble_width, y + total_height),
                           radius=corner_radius, fill=bubble_color)

    # Position de départ pour écrire le texte
    current_y = y + margin

    # Label
    for line in label_lines:
        draw.text((x + margin, current_y), line, font=label_font, fill=label_color)
        current_y += label_line_height

    current_y += label_content_gap

    # Contenu
    for line in content_lines:
        draw.text((x + margin, current_y), line, font=content_font, fill=content_color)
        current_y += content_line_height

    return y + total_height + 10

########################################
# Interface Streamlit
########################################

st.set_page_config(page_title="Fiche d'oiseau", layout="centered")
st.title("🐦 Bienvenue Mélanie")
st.subheader("Crée une fiche personnalisée pour chaque oiseau")

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    fiche_num = st.text_input("Numéro de fiche", placeholder="Ex : 1")
    nom = st.text_input("Nom de l'oiseau", placeholder="Ex : Rougegorge familier")
    nom_sci = st.text_input("Nom scientifique", placeholder="Ex : Erithacus rubecula")
    dimensions = st.text_input("Dimensions", placeholder="Ex : 14 cm / 18 grammes")
    habitat = st.text_input("Habitat", placeholder="Ex : Jardin, haies, sous-bois")
    alimentation = st.text_input("Alimentation", placeholder="Ex : Insectes, graines, fruits")

with col2:
    comportement = st.text_input("Comportement", placeholder="Ex : Solitaire, territorial")
    trait = st.text_input("Trait particulier", placeholder="Ex : Tache orange sur le torse")
    confusion = st.text_input("Risques de confusion", placeholder="Ex : Rougequeue, bouvreuil")
    texte = st.text_area("Texte explicatif", placeholder="Décris son comportement, son chant, sa relation avec l'humain...")
    image = st.file_uploader("Image de l'oiseau", type=["jpg", "jpeg", "png"])

# Palette de couleurs douces
soft_styles_dict = {
    "Carnet": ((250, 245, 235), (195, 215, 180), (210, 230, 200), (50, 50, 50)),
    "Classique": ((255, 255, 255), (130, 190, 240), (255, 170, 80), (40, 40, 40)),
    "Ludique": ((255, 250, 235), (255, 200, 80), (130, 200, 255), (60, 60, 60)),
    "Épuré": ((245, 245, 245), (220, 220, 220), (235, 235, 235), (30, 30, 30)),
    "Douceur": ((255, 250, 255), (240, 210, 230), (250, 235, 245), (80, 40, 70)),
    "Automne": ((255, 250, 240), (190, 150, 100), (230, 190, 150), (60, 40, 30))
}

style = st.selectbox("Choix du style de fiche :", [
    "🌿 Carnet naturaliste (beige & vert pastel)",
    "📘 Classique (bleu & orange)",
    "🎨 Ludique & coloré",
    "⬜ Épuré moderne (gris clair)",
    "🌸 Douceur florale (rose poudré & lavande)",
    "🍂 Automne vintage (ocre & brun)"
])

with st.expander("⚙️ Options de police avancées"):
    titre_taille = st.slider("Taille du titre principal", 30, 80, 56)
    etiquette_taille = st.slider("Taille des titres de section", 16, 36, 22)
    texte_taille = st.slider("Taille du texte général", 14, 30, 18)
    line_spacing = st.slider("Espacement entre lignes", 0, 20, 5)
    corner_radius = st.slider("Arrondi des bulles", 0, 50, 20)
    margin_bulle = st.slider("Marge interne (padding) des bulles", 5, 30, 10)
    label_content_gap = st.slider("Espace entre le titre de section et le texte", 5, 50, 10)

if st.button("🎨 Générer la fiche") and nom:
    # 1) Récupération des couleurs
    fond, accent, bande, texte_couleur = soft_styles_dict["Carnet"]
    for key in soft_styles_dict:
        if key in style:
            fond, accent, bande, texte_couleur = soft_styles_dict[key]
            break

    # 2) Création de l'image
    width, height = 1000, 1400
    fiche = Image.new("RGB", (width, height), fond)
    draw = ImageDraw.Draw(fiche)

    # 3) Chargement des polices
    titre_font = load_font(titre_taille, bold=True)         # Titre en gras
    etiquette_font = load_font(etiquette_taille, bold=True) # Sections en gras
    contenu_font = load_font(texte_taille, bold=False)
    num_font = load_font(20, bold=False)

    # 4) Titre principal (centré)
    title_text = nom.upper()
    title_bbox = draw.textbbox((0, 0), title_text, font=titre_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_x = (width - title_w) // 2
    draw.text((title_x, 60), title_text, font=titre_font, fill=texte_couleur)

    # 5) Cercle pour le numéro de fiche
    circle_left, circle_top = width - 90, 40
    circle_right, circle_bottom = width - 40, 90
    draw.ellipse((circle_left, circle_top, circle_right, circle_bottom), fill=(180, 210, 230))

    # Centrage du texte dans le cercle
    circle_center_x = (circle_left + circle_right) // 2
    circle_center_y = (circle_top + circle_bottom) // 2
    num_bbox = draw.textbbox((0, 0), fiche_num, font=num_font)
    num_w = num_bbox[2] - num_bbox[0]
    num_h = num_bbox[3] - num_bbox[1]
    text_x = circle_center_x - num_w/2
    text_y = circle_center_y - num_h/2
    draw.text((text_x, text_y), fiche_num, font=num_font, fill=(0, 0, 0))

    # 6) Position de départ pour les bulles
    y = 150

    # 7) Image de l'oiseau (facultative)
    img_w, img_h = 320, 280
    img_x = width - img_w - 60
    img_y = y
    if image:
        draw.rounded_rectangle((img_x - 8, img_y - 8, img_x + img_w + 8, img_y + img_h + 8),
                               radius=corner_radius, fill=fond, outline=accent, width=3)
        bird_img = Image.open(image).convert("RGB")
        bird_img = bird_img.resize((img_w, img_h), Image.LANCZOS)
        fiche.paste(bird_img, (img_x, img_y))

    info_x_end = img_x - 30
    bubble_width = info_x_end - 60  # Largeur pour la bulle

    # 8) Champs à afficher
    infos = [
        ("Nom scientifique", nom_sci),
        ("Dimensions", dimensions),
        ("Habitat", habitat),
        ("Alimentation", alimentation),
        ("Comportement", comportement),
        ("Trait particulier", trait),
        ("Confusions", confusion),
    ]

    # 9) Dessin de chaque champ
    for label, content in infos:
        y = draw_label_and_content(
            draw=draw,
            label=label,
            content=content,
            x=60, y=y,
            bubble_width=bubble_width,
            label_font=etiquette_font,
            content_font=contenu_font,
            label_color=texte_couleur,
            content_color=texte_couleur,
            bubble_color=bande,
            corner_radius=corner_radius,
            margin=margin_bulle,
            label_content_gap=label_content_gap,
            line_spacing=line_spacing
        )

    # 10) Positionnement de la bulle finale (texte explicatif)
    #    On s'assure de ne pas chevaucher l'image.
    y = max(y, img_y + img_h + 60)
    large_width = width - 120  # 60 px de marge de chaque côté
    bubble_height = get_text_bubble_height(draw, texte, contenu_font, large_width, margin_bulle, line_spacing)

    # Espace jusqu'à la frise en bas (la frise est à ~50 px du bas)
    bottom_margin_for_frise = 50
    space_for_bubble = (height - bottom_margin_for_frise) - y

    # Facteur de placement : ajustez si vous voulez le bloc plus ou moins haut
    placement_factor = 0.1
    if bubble_height < space_for_bubble:
        final_y = y + (space_for_bubble - bubble_height) * placement_factor
    else:
        final_y = y

    # Dessin du bloc final (texte explicatif)
    y = draw_text_bubble(
        draw=draw,
        text=texte,
        x=60, y=final_y,
        bubble_width=large_width,
        text_font=contenu_font,
        text_color=texte_couleur,
        bubble_color=bande,
        corner_radius=corner_radius,
        margin=margin_bulle,
        line_spacing=line_spacing
    )

    # 11) Frise décorative en bas
    frise_y = height - 50
    draw.line((80, frise_y, width - 80, frise_y), fill=accent, width=3)
    for i in range(80, width - 80, 30):
        draw.arc((i, frise_y - 10, i + 30, frise_y + 30), start=0, end=180, fill=accent, width=2)

    # 12) Export / affichage
    buffer = io.BytesIO()
    fiche.save(buffer, format="JPEG")
    st.image(fiche, caption="Fiche générée")
    st.download_button("📥 Télécharger la fiche JPEG",
                       buffer.getvalue(),
                       file_name=f"fiche_{nom.lower().replace(' ', '_')}.jpeg",
                       mime="image/jpeg")
