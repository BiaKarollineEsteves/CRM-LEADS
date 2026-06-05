"""pages/gestor.py — Painel Gestor"""
import streamlit as st, pandas as pd, hashlib
from components.layout import css, header, sidebar
from components.charts import funil, barras_h, barras_v, performance_por_status
from utils.auth import requer_login, requer_perfil, eu
from utils.db import Q, Q1, X
from utils.contatos import widget_contatos_extras

st.set_page_config(page_title="Gestor | CRM Grupo LLE", page_icon="📊", layout="wide")
css(); requer_login(); requer_perfil("gestor","admin")
u = eu()
eid  = u.get("empresa_id")
enm  = u.get("empresa_nome","—")

if "pg_g" not in st.session_state: st.session_state.pg_g = "📊 Dashboard"
menu=[
    ("📊 Dashboard","📊 Dashboard"),("📤 Distribuir","📤 Distribuir"),
    ("🔄 Reatribuir","🔄 Reatribuir"),("👥 Equipe","👥 Equipe"),
    ("📋 Todos os Leads","📋 Todos os Leads"),("🏆 Clientes","🏆 Clientes"),
    ("👤 Minha Conta","👤 Minha Conta"),
]
nova=sidebar(u,st.session_state.pg_g,menu)
if nova!=st.session_state.pg_g: st.session_state.pg_g=nova; st.rerun()
pg=st.session_state.pg_g

with st.sidebar:
    st.divider()
    regs=Q("SELECT id,nome FROM regioes ORDER BY nome")
    fr=st.selectbox("Região",["Todas"]+[r["nome"] for r in regs])
    sts=Q("SELECT * FROM status_leads WHERE ativo=TRUE ORDER BY ordem")
    fs=st.selectbox("Status",["Todos"]+[s["nome"] for s in sts])


@st.cache_data(ttl=20)
def meus_leads(eid, reg, stat):
    sql="""SELECT l.id,l.razao_social,l.cnpj,l.ramo,l.cidade,l.estado,
                  l.telefone,l.email,l.vendedor_id,
                  r.nome regiao, u.nome vendedor, s.nome status, s.cor status_cor
           FROM leads l
           LEFT JOIN regioes r      ON l.regiao_id=r.id
           LEFT JOIN usuarios u     ON l.vendedor_id=u.id
           LEFT JOIN status_leads s ON l.status_id=s.id
           WHERE l.empresa_id=%s"""
    p=[eid]
    if reg!="Todas":
        rid=next((r["id"] for r in regs if r["nome"]==reg),None)
        if rid: sql+=" AND l.regiao_id=%s"; p.append(rid)
    if stat!="Todos": sql+=" AND s.nome=%s"; p.append(stat)
    sql+=" ORDER BY l.razao_social"
    rows=Q(sql,tuple(p))
    return pd.DataFrame(rows) if rows else pd.DataFrame()

def vs(): return {v["nome"]:str(v["id"]) for v in Q("SELECT id,nome FROM usuarios WHERE empresa_id=%s AND perfil='vendedor' AND status='aprovado' ORDER BY nome",(eid,))}


if pg=="📊 Dashboard":
    header(f"Dashboard — {enm}","Visão geral")
    df=meus_leads(eid,fr,fs)
    if df.empty: st.info("Nenhum lead ainda.")
    else:
        tot=len(df); cad=len(df[df["status"]=="Cadastrado"]) if "status" in df.columns else 0
        sv=int(df["vendedor_id"].isna().sum()) if "vendedor_id" in df.columns else 0
        tx=f"{cad/tot*100:.1f}%" if tot else "0%"
        c1,c2,c3,c4=st.columns(4)
        c1.metric("📋 Total",f"{tot:,}"); c2.metric("🏆 Cadastrados",f"{cad:,}")
        c3.metric("👤 Sem Vendedor",f"{sv:,}"); c4.metric("📊 Conversão",tx)
        st.divider()
        c1,c2=st.columns(2)
        with c1:
            if "status" in df.columns and df["status"].notna().any():
                df_f=df.groupby("status").size().reset_index(name="total"); df_f.columns=["status","total"]
                st.plotly_chart(funil(df_f),use_container_width=True)
        with c2:
            if "regiao" in df.columns and df["regiao"].notna().any():
                df_r=df[df["regiao"].notna()].groupby("regiao").size().reset_index(name="total")
                st.plotly_chart(barras_h(df_r,"total","regiao","Por Região"),use_container_width=True)

elif pg=="📤 Distribuir":
    header("Distribuir Leads")
    vm=vs()
    sem=Q("SELECT l.id,l.razao_social,r.nome regiao FROM leads l LEFT JOIN regioes r ON l.regiao_id=r.id WHERE l.empresa_id=%s AND l.vendedor_id IS NULL ORDER BY l.razao_social LIMIT 300",(eid,))
    if not sem: st.success("✅ Todos têm vendedor!")
    elif not vm: st.warning("Nenhum vendedor aprovado nesta empresa.")
    else:
        st.caption(f"{len(sem)} sem vendedor")
        vd=st.selectbox("Para:",list(vm.keys()))
        op={r["id"]:f"{r['razao_social']} — {r.get('regiao') or '—'}" for r in sem}
        sel=st.multiselect("Leads:",list(op.keys()),format_func=lambda x:op[x],default=[])
        todos=st.checkbox("Atribuir TODOS")
        if st.button("✅ Atribuir",type="primary"):
            alvo=[r["id"] for r in sem] if todos else sel
            if not alvo: st.warning("Selecione ao menos um.")
            else:
                [X("UPDATE leads SET vendedor_id=%s WHERE id=%s",(vm[vd],lid)) for lid in alvo]
                st.cache_data.clear(); st.success(f"✅ {len(alvo)} → {vd}"); st.rerun()

elif pg=="🔄 Reatribuir":
    header("Reatribuir Leads")
    vm=vs()
    com=Q("SELECT l.id,l.razao_social,u.nome vendedor FROM leads l LEFT JOIN usuarios u ON l.vendedor_id=u.id WHERE l.empresa_id=%s AND l.vendedor_id IS NOT NULL ORDER BY l.razao_social LIMIT 300",(eid,))
    if not com: st.info("Nenhum atribuído.")
    elif not vm: st.warning("Nenhum vendedor.")
    else:
        lid=st.selectbox("Lead:",[r["id"] for r in com],format_func=lambda x:next(f"{r['razao_social']} → {r['vendedor']}" for r in com if r["id"]==x))
        nv=st.selectbox("Novo:",list(vm.keys()))
        if st.button("🔄 Reatribuir",type="primary"):
            X("UPDATE leads SET vendedor_id=%s WHERE id=%s",(vm[nv],lid))
            st.cache_data.clear(); st.success("✅ Reatribuído!"); st.rerun()

elif pg=="👥 Equipe":
    header(f"Equipe — {enm}")
    vends=Q("SELECT id,nome,email FROM usuarios WHERE empresa_id=%s AND perfil='vendedor' ORDER BY nome",(eid,))
    if not vends: st.info("Nenhum vendedor.")
    for v in vends:
        lv=Q("SELECT l.razao_social,r.nome regiao,s.nome status FROM leads l LEFT JOIN status_leads s ON l.status_id=s.id LEFT JOIN regioes r ON l.regiao_id=r.id WHERE l.vendedor_id=%s",(v["id"],))
        cad_v=sum(1 for l in lv if l.get("status")=="Cadastrado")
        with st.expander(f"👤 **{v['nome']}** — {len(lv)} leads | {cad_v} cadastrados"):
            st.caption(v["email"])
            if lv: st.dataframe(pd.DataFrame(lv)[["razao_social","regiao","status"]].rename(columns={"razao_social":"Lead","regiao":"Região","status":"Status"}),use_container_width=True,hide_index=True)

elif pg=="📋 Todos os Leads":
    header(f"Leads — {enm}")
    df=meus_leads(eid,fr,fs)
    if df.empty: st.info("Nenhum lead.")
    else:
        cols=[c for c in ["razao_social","cnpj","regiao","vendedor","status","ramo","cidade","estado","telefone","email"] if c in df.columns]
        st.dataframe(df[cols].rename(columns={"razao_social":"Razão Social","cnpj":"CNPJ","regiao":"Região","vendedor":"Vendedor","status":"Status","ramo":"Ramo","cidade":"Cidade","estado":"UF","telefone":"Telefone","email":"E-mail"}),use_container_width=True,hide_index=True)
        st.divider()
        st.subheader("📞 Adicionar telefone a um lead")
        lead_opts = df["id"].tolist()
        lead_sel_g = st.selectbox("Selecionar lead", lead_opts,
            format_func=lambda x: f"{df[df['id']==x]['razao_social'].values[0]} — {df[df['id']==x]['vendedor'].values[0] or 'Sem vendedor'}",
            key="lead_ct_g")
        widget_contatos_extras(lead_sel_g, u)

elif pg=="🏆 Clientes":
    header(f"Clientes — {enm}")
    rows=Q("SELECT l.*,r.nome regiao,u.nome vendedor FROM leads l LEFT JOIN status_leads s ON l.status_id=s.id LEFT JOIN regioes r ON l.regiao_id=r.id LEFT JOIN usuarios u ON l.vendedor_id=u.id WHERE l.empresa_id=%s AND s.nome='Cadastrado' ORDER BY l.razao_social",(eid,))
    if not rows: st.info("Nenhum cliente ainda.")
    else:
        st.metric("🏆 Clientes",len(rows)); st.divider()
        for r in rows:
            with st.container(border=True):
                st.markdown(f"**{r['razao_social']}**")
                st.caption(f"CNPJ: {r.get('cnpj') or '—'} | {r.get('ramo') or '—'} | {r.get('regiao') or '—'} | Vendedor: {r.get('vendedor') or '—'}")
                st.caption(f"📞 {r.get('telefone') or '—'}  ✉️ {r.get('email') or '—'}")

elif pg=="👤 Minha Conta":
    def _h(s): return hashlib.sha256(s.encode()).hexdigest()
    header("Minha Conta",u["nome"])
    st.subheader("🔑 Trocar senha")
    with st.form("fs"):
        atual=st.text_input("Senha atual",type="password")
        n1=st.text_input("Nova senha",type="password",placeholder="Mínimo 6 caracteres")
        n2=st.text_input("Confirmar",type="password")
        ok=st.form_submit_button("💾 Salvar",type="primary")
    if ok:
        if u["id"] == "admin": st.warning("O administrador master troca a senha nos Secrets do Streamlit Cloud."); st.stop()
        row=Q1("SELECT senha_hash FROM usuarios WHERE id=%s",(u["id"],))
        if not row or row["senha_hash"]!=_h(atual): st.error("❌ Senha atual incorreta.")
        elif len(n1)<6: st.error("Mínimo 6 caracteres.")
        elif n1!=n2: st.error("Senhas não coincidem.")
        else: X("UPDATE usuarios SET senha_hash=%s WHERE id=%s",(_h(n1),u["id"])); st.success("✅ Senha alterada!")
