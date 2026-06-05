"""components/layout.py — CSS e helpers (idêntico ao Factoring)"""
import streamlit as st, base64
from pathlib import Path

AM="#FAC319"; VD="#0F8C3B"; AZ="#007FE0"; AE="#041747"


def logo_b64():
    for p in [Path(__file__).parent.parent/"assets"/"logo.png", Path("assets/logo.png")]:
        if p.exists(): return base64.b64encode(p.read_bytes()).decode()
    return ""


def logo_img(h=36):
    b = logo_b64()
    return f'<img src="data:image/png;base64,{b}" style="height:{h}px;">' if b \
           else '<span style="color:#fff;font-weight:700;">GRUPO LLE</span>'


def css():
    st.markdown(f"""<style>
    [data-testid="stSidebarNav"]{{display:none!important}}
    [data-testid="stSidebar"]{{min-width:240px!important;max-width:240px!important;background:{AE}!important}}
    [data-testid="stSidebar"] p,[data-testid="stSidebar"] span,[data-testid="stSidebar"] label{{color:rgba(255,255,255,.85)!important}}
    [data-testid="stSidebar"] .stButton button{{background:rgba(255,255,255,.06)!important;border:1px solid rgba(255,255,255,.12)!important;color:#fff!important;text-align:left!important;border-radius:7px!important;margin-bottom:3px!important;font-size:13px!important;padding:8px 14px!important;width:100%!important}}
    [data-testid="stSidebar"] .stButton button:hover{{background:rgba(250,195,25,.15)!important;border-color:{AM}!important}}
    [data-testid="stSidebar"] [data-testid="baseButton-primary"]{{background:{AM}!important;color:{AE}!important;border:none!important;font-weight:700!important}}
    [data-testid="baseButton-primary"]{{background:{AE}!important;color:#fff!important;border:none!important;border-radius:7px!important}}
    [data-testid="baseButton-primary"]:hover{{background:{AZ}!important}}
    [data-testid="metric-container"]{{background:#f4f7fc;border-radius:10px;padding:14px 18px;border-left:4px solid {AM};box-shadow:0 1px 4px rgba(4,23,71,.07)}}
    h1{{color:{AE}!important;font-weight:700!important}}
    h2{{color:{AE}!important;font-weight:600!important}}
    h3{{color:{AE}!important}}
    .tl{{border-left:3px solid {AM};padding:4px 0 10px 16px;margin-left:8px;font-size:13px;color:#374151}}
    .hbar{{background:{AE};padding:14px 22px;border-radius:10px;margin-bottom:22px;display:flex;align-items:center;gap:16px}}
    .hbar-t{{color:#fff;font-size:20px;font-weight:700}}
    .hbar-s{{color:{AM};font-size:12px;margin-top:2px}}
    [data-testid="stExpander"]{{border:1px solid #dde3ef!important;border-radius:9px!important}}
    hr{{border-color:{AM}!important;opacity:.25}}
    </style>""", unsafe_allow_html=True)


def header(titulo, sub=""):
    st.markdown(
        f'<div class="hbar">{logo_img(38)}'
        f'<div><div class="hbar-t">{titulo}</div>'
        f'{"<div class=hbar-s>"+sub+"</div>" if sub else ""}</div></div>',
        unsafe_allow_html=True)


def sidebar(u, pagina, menu):
    with st.sidebar:
        st.markdown(f'<div style="text-align:center;padding:18px 8px 10px">{logo_img(52)}</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="text-align:center;color:{AM};font-size:11px;letter-spacing:.06em;margin:-4px 0 14px;text-transform:uppercase">CRM — Gestão de Leads</p>', unsafe_allow_html=True)
        st.divider()
        sel = pagina
        for label, key in menu:
            if st.button(label, use_container_width=True,
                         type="primary" if pagina==key else "secondary",
                         key=f"m_{key}"):
                sel = key
        st.divider()
        pc = {"admin":AM,"gestor":AZ,"vendedor":VD}.get(u.get("perfil",""), "#fff")
        st.markdown(
            f'<p style="font-size:11px;color:rgba(255,255,255,.5);text-transform:uppercase;margin-bottom:2px">Usuário</p>'
            f'<p style="font-size:14px;font-weight:600;color:#fff;margin-bottom:2px">👤 {u["nome"]}</p>'
            f'<p style="font-size:11px;color:{pc};text-transform:uppercase;margin-bottom:2px">{u["perfil"]}</p>'
            f'<p style="font-size:11px;color:rgba(255,255,255,.4);margin-bottom:12px">{u.get("empresa_nome") or "—"}</p>',
            unsafe_allow_html=True)
        if st.button("🚪  Sair", use_container_width=True, key="m_sair"):
            from utils.auth import sair; sair()
    return sel
