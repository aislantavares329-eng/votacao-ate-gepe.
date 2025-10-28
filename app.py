import streamlit as st
import pandas as pd
from pathlib import Path
from urllib.parse import urlencode, quote_plus

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Votação Mascote A.T.E. (GEPE)", layout="centered")

OPCOES = ["Pomba", "Coruja", "Gato"]

# Imagens locais (coloque arquivos pomba.png, coruja.png, gato.png no repositório)
IMGS = {
    "Pomba": "pomba.png",
    "Coruja": "coruja.png",
    "Gato": "gato.png",
}

# Arquivos “persistentes” no container do Streamlit Cloud (válido para a sessão)
BASE = Path(".")
CSV = BASE / "votos.csv"
LOCK = BASE / "winner.txt"

# =========================
# HELPERS
# =========================
def init_csv():
    if not CSV.exists():
        pd.DataFrame(columns=["escolha"]).to_csv(CSV, index=False)

def votar(opcao: str):
    df = pd.read_csv(CSV) if CSV.exists() else pd.DataFrame(columns=["escolha"])
    df.loc[len(df)] = [opcao]
    df.to_csv(CSV, index=False)

def contagem():
    if not CSV.exists():
        return {o: 0 for o in OPCOES}
    df = pd.read_csv(CSV)
    s = df["escolha"].value_counts().reindex(OPCOES, fill_value=0)
    return s.to_dict()

def vencedor_atual():
    c = contagem()
    # empate: pega o primeiro por ordem (comunica empate no título)
    v = max(c, key=c.get) if c else None
    return v, c

def fechar_votacao():
    v, c = vencedor_atual()
    if not v or sum(c.values()) == 0:
        return False, "Sem votos."
    LOCK.write_text(v, encoding="utf-8")
    return True, v

def reabrir():
    if LOCK.exists():
        LOCK.unlink()

def votacao_fechada():
    return LOCK.exists()

def vencedor_travado():
    return LOCK.read_text(encoding="utf-8").strip() if LOCK.exists() else ""

def css_limpo():
    st.markdown("""
    <style>
      header, footer, .stDeployButton, .viewerBadge_link__1S137 {display:none !important;}
      .block-container {padding-top: 1.2rem; padding-bottom: 0.2rem;}
      .stButton>button {font-size: 1.05rem;}
    </style>
    """, unsafe_allow_html=True)

def url_atual(params: dict):
    base = st.secrets.get("BASE_URL", "")  # opcional; senão usa a URL atual
    if not base:
        base = st.experimental_get_query_params()
        # sem BASE_URL em secrets, vamos só construir query; o usuário usará a URL atual + ?view=winner
    return "?" + urlencode(params, quote_via=quote_plus)

# =========================
# ROTAS POR QUERY PARAM
# =========================
qs = st.experimental_get_query_params()
view = (qs.get("view", ["vote"])[0]).lower()

init_csv()
css_limpo()

# -------------------------
# VIEW: VOTAÇÃO (QR + rádio)
# -------------------------
if view == "vote":
    st.title("Vote no Mascote do A.T.E. 🕊️🦉🐈")
    if votacao_fechada():
        st.info(f"Votação encerrada. Vencedor: **{vencedor_travado()}**")
    else:
        escolha = st.radio("Escolha 1 opção:", OPCOES, index=None, horizontal=False)
        st.button("Enviar voto", disabled=(escolha is None), on_click=lambda: votar(escolha))
        st.caption("Depois de votar, você pode voltar e ver o resultado parcial.")
    st.divider()
    v, c = vencedor_atual()
    st.subheader("Resultado parcial (ao vivo)")
    st.bar_chart(pd.DataFrame({"Votos": c}))

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link(st.experimental_get_query_params(), label="Atualizar", icon="🔄")
    with col2:
        st.link_button("Abrir tela de RESULTADO", url_atual({"view":"winner"}), use_container_width=True)
    with col3:
        st.link_button("Tela de CONTROLE", url_atual({"view":"control"}), use_container_width=True)

# -------------------------
# VIEW: RESULTADO LIMPO (para embutir no PowerPoint)
# -------------------------
elif view == "winner":
    # Tela limpa: só o vencedor (imagem grande). Sem header/footer.
    st.markdown("<h1 style='text-align:center;'>Mascote do A.T.E.</h1>", unsafe_allow_html=True)
    if not votacao_fechada():
        v, c = vencedor_atual()
        st.warning("Votação em andamento. Feche a votação para fixar o vencedor.")
        if sum(c.values()) == 0:
            st.info("Aguardando votos…")
        else:
            st.write(f"Parcial: **{v}** à frente.")
    else:
        v = vencedor_travado()
        if v:
            st.write(f"<h3 style='text-align:center;'>Vencedor: {v}</h3>", unsafe_allow_html=True)
            img_path = IMGS.get(v)
            if img_path and Path(img_path).exists():
                st.image(img_path, use_column_width=True)
            else:
                # fallback com emoji grande
                EMOJI = {"Pomba":"🕊️","Coruja":"🦉","Gato":"🐈"}.get(v,"⭐")
                st.markdown(f"<div style='font-size:200px;text-align:center;'>{EMOJI}</div>", unsafe_allow_html=True)
        else:
            st.info("Sem vencedor (winner.txt vazio).")

# -------------------------
# VIEW: CONTROLE (encerrar/reabrir)
# -------------------------
elif view == "control":
    st.header("Controle do Apresentador")
    v, c = vencedor_atual()
    st.write("Parcial:", c)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Fechar votação (travar vencedor)", use_container_width=True):
            ok, msg = fechar_votacao()
            if ok:
                st.success(f"Votação encerrada. Vencedor: {msg}")
            else:
                st.error(msg)
    with col2:
        if st.button("Reabrir votação", use_container_width=True):
            reabrir()
            st.info("Votação reaberta.")
    with col3:
        if st.button("Zerar votos", use_container_width=True):
            pd.DataFrame(columns=["escolha"]).to_csv(CSV, index=False)
            reabrir()
            st.warning("Votos zerados e vencedor limpo.")
    st.divider()
    st.link_button("Tela de Votação (QR)", url_atual({"view":"vote"}), use_container_width=True)
    st.link_button("Tela de Resultado (limpa para PPT)", url_atual({"view":"winner"}), use_container_width=True)
else:
    st.write("View inválida. Use ?view=vote | ?view=winner | ?view=control")
