"""app.py — CRM Grupo LLE — Login"""
import streamlit as st
from components.layout import css, logo_b64
from utils.auth import login, cadastrar, salvar, eu

st.set_page_config(page_title="CRM | Grupo LLE", page_icon="🏢",
                   layout="wide", initial_sidebar_state="collapsed")
css()

u = eu()
if u:
    p = u["perfil"]
    if p == "admin":    st.switch_page("pages/admin.py")
    elif p == "gestor": st.switch_page("pages/gestor.py")
    else:               st.switch_page("pages/vendedor.py")

b64 = logo_b64()
AE  = "#041747"

_, col, _ = st.columns([1, 1.1, 1])
with col:
    st.markdown("<br>", unsafe_allow_html=True)

    # Topo azul com logo
    logo_html = f'<img src="data:image/png;base64,{b64}" style="max-width:210px;width:100%;">' \
                if b64 else '<span style="color:#FAC319;font-weight:800;font-size:26px;">GRUPO LLE</span>'
    st.markdown(
        f'<div style="background:{AE};padding:28px 24px;border-radius:12px 12px 0 0;text-align:center;">'
        f'{logo_html}</div>', unsafe_allow_html=True)

    # Corpo cinza
    st.markdown(
        '<div style="background:#f4f7fc;border:1px solid #dde3ef;border-top:none;'
        'border-radius:0 0 12px 12px;padding:24px 24px 28px;">'
        '<p style="text-align:center;color:#666;font-size:13px;margin:0 0 20px;">Sistema de Gestão de Leads</p>',
        unsafe_allow_html=True)

    aba = st.tabs(["🔑  Entrar", "📝  Cadastrar-se"])

    with aba[0]:
        with st.form("f_login"):
            email = st.text_input("E-mail", placeholder="seu@email.com.br")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            ok    = st.form_submit_button("Entrar", type="primary", use_container_width=True)
        if ok:
            if not email or not senha:
                st.error("Preencha e-mail e senha.")
            else:
                with st.spinner("Autenticando..."):
                    try:    r = login(email, senha)
                    except Exception as e: st.error(f"Erro de conexão: {e}"); st.stop()
                if r is None:
                    st.error("❌ E-mail ou senha incorretos.")
                elif isinstance(r, dict) and r.get("erro") == "pendente":
                    st.warning("⏳ Cadastro aguardando aprovação do administrador.")
                elif isinstance(r, dict) and r.get("erro") == "inativo":
                    st.error("⛔ Acesso inativo. Contate o administrador.")
                else:
                    salvar(r)
                    p = r["perfil"]
                    if p == "admin":    st.switch_page("pages/admin.py")
                    elif p == "gestor": st.switch_page("pages/gestor.py")
                    else:               st.switch_page("pages/vendedor.py")

    with aba[1]:
        st.info("Após o cadastro, aguarde a aprovação do administrador.")
        with st.form("f_cad"):
            nome  = st.text_input("Nome completo")
            email2= st.text_input("E-mail", placeholder="seu@email.com.br")
            s1    = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres")
            s2    = st.text_input("Confirmar senha", type="password")
            sub   = st.form_submit_button("Solicitar acesso", type="primary", use_container_width=True)
        if sub:
            if not all([nome, email2, s1, s2]):  st.error("Preencha todos os campos.")
            elif len(s1) < 6:                    st.error("Senha deve ter pelo menos 6 caracteres.")
            elif s1 != s2:                       st.error("As senhas não coincidem.")
            else:
                err = cadastrar(nome, email2, s1)
                if err: st.error(err)
                else:   st.success("✅ Solicitação enviada! Aguarde a aprovação.")

    st.markdown("</div>", unsafe_allow_html=True)
