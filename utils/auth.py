"""utils/auth.py — SHA-256 igual ao Factoring"""
import hashlib, streamlit as st
from utils.db import Q1, X


def _h(s): return hashlib.sha256(s.encode()).hexdigest()


def login(email, senha):
    email = email.lower().strip()
    if email == "admin@grupolle.com.br":
        ok = _h(senha) == st.secrets.get("admin", {}).get("senha_hash", "")
        if ok:
            return {"id": "admin", "nome": "Administrador", "email": email,
                    "perfil": "admin", "empresa_id": None, "empresa_nome": None}
        return None
    u = Q1("SELECT * FROM usuarios WHERE email=%s", (email,))
    if not u: return None
    if u["status"] == "pendente": return {"erro": "pendente"}
    if u["status"] == "inativo":  return {"erro": "inativo"}
    if u["senha_hash"] != _h(senha): return None
    emp = Q1("SELECT nome FROM empresas WHERE id=%s", (u["empresa_id"],)) if u.get("empresa_id") else None
    r = dict(u)
    r["id"] = str(r["id"])
    r["empresa_nome"] = emp["nome"] if emp else None
    return r


def cadastrar(nome, email, senha):
    email = email.lower().strip()
    if Q1("SELECT id FROM usuarios WHERE email=%s", (email,)):
        return "E-mail já cadastrado."
    try:
        X("INSERT INTO usuarios (nome,email,senha_hash) VALUES (%s,%s,%s)",
          (nome.strip(), email, _h(senha)))
        return None
    except Exception as e:
        return str(e)


def salvar(u): st.session_state.u = u; st.session_state.ok = True
def sair():    st.session_state.clear(); st.rerun()
def eu():      return st.session_state.get("u") if st.session_state.get("ok") else None


def requer_login():
    if not eu(): st.switch_page("app.py")


def requer_perfil(*perfis):
    u = eu()
    if not u or u["perfil"] not in perfis:
        st.error("⛔ Acesso não autorizado.")
        st.stop()
