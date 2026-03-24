import streamlit as st
from query_engine import get_query_engine
from pptx import Presentation
from pptx.util import Inches, Pt
import io, os

st.set_page_config(page_title="ACENOS Knowledge Agent", page_icon="🏦", layout="wide")
st.title("🏦 ACENOS Knowledge Agent")
st.caption("Interroge la base de connaissances ACENOS • Sources citées automatiquement")

# Initialisation de l'agent (en cache pour ne pas recharger à chaque requête)
@st.cache_resource
def load_engine():
    return get_query_engine()

engine = load_engine()

# Historique de conversation
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Choix du format de sortie
format_sortie = st.sidebar.selectbox(
    "Format de réponse",
    ["Texte", "Générer un PPT", "Rédiger un mail"]
)

# Zone de saisie
if question := st.chat_input("Ex : Quelles sont nos meilleures pratiques ESG en banque ?"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    # Adaptation du prompt selon le format demandé
    if format_sortie == "Générer un PPT":
        prompt = f"{question}\n\nStructure ta réponse comme un plan de présentation PowerPoint avec des titres de slides et des bullet points."
    elif format_sortie == "Rédiger un mail":
        prompt = f"{question}\n\nFormule ta réponse sous forme d'un mail professionnel prêt à envoyer, avec objet, corps et signature ACENOS."
    else:
        prompt = question

    with st.chat_message("assistant"):
        with st.spinner("Recherche dans la base ACENOS..."):
            response = engine.query(prompt)
            st.write(str(response))

            # Sources
            with st.expander("📎 Sources utilisées"):
                for node in response.source_nodes:
                    st.write(f"• `{node.metadata.get('file_name', 'inconnu')}` — score : {node.score:.2f}")

            # Export PPT
            if format_sortie == "Générer un PPT":
                prs = Presentation()
                slide = prs.slides.add_slide(prs.slide_layouts[1])
                slide.shapes.title.text = question[:80]
                slide.placeholders[1].text = str(response)[:1500]
                buf = io.BytesIO()
                prs.save(buf)
                st.download_button("⬇️ Télécharger le PPT", buf.getvalue(),
                                   file_name="acenos_reponse.pptx",
                                   mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")

    st.session_state.messages.append({"role": "assistant", "content": str(response)})