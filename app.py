import streamlit as st
import pandas as pd
from pathlib import Path

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Votação Mascote A.T.E. (GEPE)", layout="centered")

OPCOES = ["Pomba", "Coruja", "Gato"]

# Se quiser imagens, suba pomba.png / coruja.png / gato.png no repo
IMGS = {"Pomba": "pomba.png", "Coruja": "coruja.png", "Gato": "gato.png"}

BASE = Path(".")
CSV = BASE / "votos.csv"
LOCK = BASE / "winner.txt"  # quando existe, votação está encerrada e guarda o vencedor

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
    if not c or sum(c.values()) == 0:
        return None, {o: 0 for o in OPCOES}
    v = max(c, key=c.get)  # em empate, pega o primeiro por ordem
    return v, c

def fechar_votacao():
    v, c = vencedor_atual()
    if sum(c.values()) == 0:
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
      header, footer, .viewerBadge_link__1S137 {display:none !important;}
      .block-container {padding-top: 1.2rem; padding-bottom: 0.6rem;}
      .stButton>button {font-size: 1.05rem;}
    </style>
    """, unsafe_allow_html=True)

def link_relativo(view_name: str) -> str:
    # A URL base do Streamlit permanece; só trocamos a query.
    return f"?view={view_name}"

# =========================
# APP
# =========================
init_csv()
css_limpo()

qs = st.experimental_get_query_params()
view = (qs.get("view", ["vote"])[0]).lower()

# -------------------------
# TELA: VOTAÇÃO
# -------------------------
if view == "vote":
    st.title("Vote no Mascote do A.T.E. 🕊️🦉🐈")

    if votacao_fechada():
        st.info(f"Votação encerrada. Vencedor: **{vencedor_travado()}**")
    else:
        escolha = st.radio("Escolha 1 opção:", OPCOES, index=None)
        if st.button("Enviar voto", disabled=(escolha is None), use_container_width=True):
            votar(escolha)
            st.success(f"Voto confirmado: {escolha}")

    st.divider()
    st.subheader("Resultado parcial (ao vivo)")
    _, c = vencedor_atual()
    st.bar_chart(pd.DataFrame({"Votos": c}))

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Atualizar", use_container_width=True):
            st.rerun()
    with col2:
        st.link_button("Abrir RESULTADO (para o PPT)", link_relativo("winner"), use_container_width=True)
    with col3:
        st.link_button("Tela de CONTROLE", link_relativo("control"), use_container_width=True)

# -------------------------
# TELA: RESULTADO LIMPO (para embutir no PowerPoint)
# -------------------------
elif view == "winner":
    st.markdown("<h1 style='text-align:center;'>Mascote do A.T.E.</h1>", unsafe_allow_html=True)

    if not votacao_fechada():
        v, c = vencedor_atual()
        if sum(c.values()) == 0:
            st.info("Aguardando votos…")
        else:
            st.warning("Votação em andamento. Feche para fixar o vencedor.")
            st.write(f"<h3 style='text-align:center;'>Parcial: {v}</h3>", unsafe_allow_html=True)
    else:
        v = vencedor_travado()
        if v:
            st.write(f"<h2 style='text-align:center;'>Vencedor: {v}</h2>", unsafe_allow_html=True)
            img_path = IMGS.get(v)
            if img_path and Path(img_path).exists():
                st.image(img_path, use_column_width=True)
            else:
                EMOJI = {"Pomba":"🕊️","Coruja":"🦉","Gato":"🐈"}.get(v, "⭐")
                st.markdown(f"<div style='font-size:200px;text-align:center;'>{EMOJI}</div>", unsafe_allow_html=True)
        else:
            st.info("Sem vencedor definido.")

    st.divider()
    st.link_button("Ir para CONTROLE", link_relativo("control"), use_container_width=True)

# -------------------------
# TELA: CONTROLE (encerrar/reabrir)
# -------------------------
elif view == "control":
    st.header("Controle do Apresentador")
    v, c = vencedor_atual()
    st.write("Parcial:", c)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Fechar votação (travar vencedor)", use_container_width=True):
            ok, msg = fechar_votacao()
            st.success(f"Votação encerrada. Vencedor: {msg}" if ok else msg)
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
    st.link_button("Tela de VOTAÇÃO (QR)", link_relativo("vote"), use_container_width=True)
    st.link_button("Tela de RESULTADO (PPT)", link_relativo("winner"), use_container_width=True)

else:
    st.write("View inválida. Use ?view=vote | ?view=winner | ?view=control")
