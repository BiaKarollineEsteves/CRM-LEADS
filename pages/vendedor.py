"""pages/vendedor.py — Painel Vendedor"""
import streamlit as st, pandas as pd, hashlib, io
from datetime import datetime
from components.layout import css, header, sidebar
from components.charts import funil
from utils.auth import requer_login, requer_perfil, eu
from utils.db import Q, Q1, X
from utils.contatos import widget_contatos_extras

st.set_page_config(page_title="Vendedor | CRM Grupo LLE", page_icon="🎯", layout="wide")
css(); requer_login(); requer_perfil("vendedor","gestor","admin")
u = eu()

if "pg_v" not in st.session_state: st.session_state.pg_v = "🎯 Minha Carteira"
menu=[
    ("🎯 Minha Carteira",    "🎯 Minha Carteira"),
    ("📊 Análise",           "📊 Análise"),
    ("🏆 Carteira Completa", "🏆 Carteira Completa"),
    ("👤 Minha Conta",       "👤 Minha Conta"),
]
nova=sidebar(u,st.session_state.pg_v,menu)
if nova!=st.session_state.pg_v: st.session_state.pg_v=nova; st.rerun()
pg=st.session_state.pg_v

sts=Q("SELECT * FROM status_leads WHERE ativo=TRUE ORDER BY ordem")


# ══════════════════════════════════════════════════════════════════════════════
# MINHA CARTEIRA — com filtro de status inline
# ══════════════════════════════════════════════════════════════════════════════
if pg=="🎯 Minha Carteira":
    header("Minha Carteira",f"{u['nome']} — {u.get('empresa_nome') or ''}")

    # ── Notificações de novos números ────────────────────────────────────────
    notifs = Q("SELECT n.id, n.mensagem, n.criado_em FROM notificacoes n WHERE n.usuario_id=%s AND n.lida=FALSE ORDER BY n.criado_em DESC", (u["id"],))
    if notifs:
        with st.container():
            st.markdown(f'<div style="background:#FEF9C3;border:1px solid #F59E0B;border-left:4px solid #F59E0B;border-radius:8px;padding:12px 16px;margin-bottom:16px;">'
                        f'<strong>🔔 {len(notifs)} nova(s) notificação(ões)</strong></div>', unsafe_allow_html=True)
            for n in notifs:
                ts = str(n.get("criado_em",""))[:16].replace("T"," ")
                c1,c2 = st.columns([5,1])
                c1.markdown(f"🔔 {n['mensagem']} <span style='color:#94a3b8;font-size:12px;'>— {ts}</span>", unsafe_allow_html=True)
                if c2.button("✅ Li", key=f"notif_{n['id']}"):
                    X("UPDATE notificacoes SET lida=TRUE WHERE id=%s", (n["id"],))
                    st.rerun()
        st.divider()

    # ── Filtros no topo da página ────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns(3)
    f_status = fc1.selectbox("🏷️ Filtrar por Status", ["Todos"]+[s["nome"] for s in sts], key="cart_status")
    f_regiao_cart = fc2.selectbox("📍 Filtrar por Região",
        ["Todas"]+sorted([r["nome"] for r in Q("SELECT DISTINCT r.nome FROM leads l LEFT JOIN regioes r ON l.regiao_id=r.id WHERE l.vendedor_id=%s AND r.nome IS NOT NULL ORDER BY r.nome",(u["id"],))]),
        key="cart_regiao")
    busca = fc3.text_input("🔍 Buscar", placeholder="Nome, CNPJ, cidade...", key="cart_busca")

    # ── Busca leads com filtro ───────────────────────────────────────────────
    sql="""SELECT l.id,l.razao_social,l.cnpj,l.ramo,l.endereco,l.cidade,l.estado,l.telefone,l.email,
                  r.nome regiao, s.nome status, s.cor status_cor, s.id status_id
           FROM leads l
           LEFT JOIN regioes r      ON l.regiao_id=r.id
           LEFT JOIN status_leads s ON l.status_id=s.id
           WHERE l.vendedor_id=%s"""
    p=[u["id"]]
    if f_status!="Todos": sql+=" AND s.nome=%s"; p.append(f_status)
    if f_regiao_cart!="Todas": sql+=" AND r.nome=%s"; p.append(f_regiao_cart)
    sql+=" ORDER BY l.razao_social"
    leads=Q(sql,tuple(p))

    # Filtra por busca texto
    if busca:
        leads=[l for l in leads if busca.lower() in str(l.values()).lower()]

    # ── Métricas ─────────────────────────────────────────────────────────────
    todos_leads=Q("SELECT s.nome status FROM leads l LEFT JOIN status_leads s ON l.status_id=s.id WHERE l.vendedor_id=%s",(u["id"],))
    tot_geral=len(todos_leads)
    cad_geral=sum(1 for l in todos_leads if l.get("status")=="Cadastrado")
    sc_geral =sum(1 for l in todos_leads if l.get("status")=="Sem contato")

    c1,c2,c3,c4=st.columns(4)
    c1.metric("📋 Total carteira", tot_geral)
    c2.metric("🔍 Exibindo agora", len(leads))
    c3.metric("🏆 Cadastrados",    cad_geral)
    c4.metric("⏳ Sem Contato",    sc_geral)
    st.divider()

    if not leads:
        st.info("Nenhum lead encontrado com esses filtros.")
    else:
        st.caption(f"{len(leads)} lead(s)")
        for row in leads:
            ic={"Cadastrado":"✅","Contato realizado":"🔵","Tentativa de contato":"🟡"}.get(row.get("status",""),"⚪")
            with st.expander(f"{ic} **{row['razao_social']}** — {row.get('status','—')}"):
                c1,c2=st.columns([2,1])
                with c1:
                    # Contatos extras
                    extras = Q("SELECT telefone, observacao FROM contatos_extras WHERE lead_id=%s ORDER BY criado_em", (row["id"],))
                    tel_extras = "".join([f"<br>📞 {e['telefone']}{' (' + e['observacao'] + ')' if e.get('observacao') else ''}" for e in extras])
                    st.markdown(f"""
| | |
|---|---|
|**CNPJ**|{row.get('cnpj') or '—'}|
|**Ramo**|{row.get('ramo') or '—'}|
|**Endereço**|{row.get('endereco') or '—'}|
|**Cidade/UF**|{row.get('cidade') or '—'} / {row.get('estado') or '—'}|
|**Telefone**|{row.get('telefone') or '—'}|
|**E-mail**|{row.get('email') or '—'}|
|**Região**|{row.get('regiao') or '—'}|
""")
                    if extras:
                        st.markdown(f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:8px 12px;font-size:13px;margin-top:4px;">📞 <strong>Números adicionais:</strong>{tel_extras}</div>', unsafe_allow_html=True)
                with c2:
                    st.markdown("**Alterar Status**")
                    nomes=[s["nome"] for s in sts]
                    idx=nomes.index(row.get("status")) if row.get("status") in nomes else 0
                    nst=st.selectbox("",nomes,index=idx,key=f"st{row['id']}",label_visibility="collapsed")
                    ano=st.text_area("Anotação",key=f"an{row['id']}",height=80,placeholder="Ex: Ligar amanhã...")
                    if st.button("💾 Salvar",key=f"sv{row['id']}",type="primary"):
                        nsid=next((s["id"] for s in sts if s["nome"]==nst),None)
                        if nsid:
                            uid_val = u["id"] if u["id"] != "admin" else None
                            try:
                                X("UPDATE leads SET status_id=%s WHERE id=%s",(nsid,row["id"]))
                            except Exception as e:
                                st.error(f"Erro ao atualizar status: {e}"); st.stop()
                            try:
                                X("INSERT INTO historico_status(lead_id,status_id,usuario_id,anotacao) VALUES(%s,%s,%s,%s)",
                                  (row["id"],nsid,uid_val,ano or None))
                            except Exception as e:
                                st.error(f"Erro ao salvar histórico: {e}"); st.stop()
                            st.success("✅ Salvo!"); st.rerun()
                st.divider()
                t1,t2,t3=st.tabs(["💬 Comentários","📋 Histórico","📞 Telefones Extras"])
                with t1:
                    cs=Q("SELECT c.texto,c.criado_em,u.nome autor FROM comentarios c LEFT JOIN usuarios u ON c.usuario_id=u.id WHERE c.lead_id=%s ORDER BY c.criado_em",(row["id"],))
                    for c in cs:
                        ts=str(c.get("criado_em",""))[:16].replace("T"," ")
                        st.markdown(f'<div class="tl"><strong>{c.get("autor","—")}</strong> <span style="color:#94a3b8;font-size:12px">{ts}</span><br>{c["texto"]}</div>',unsafe_allow_html=True)
                    nc=st.text_input("",placeholder="Novo comentário...",key=f"nc{row['id']}",label_visibility="collapsed")
                    if st.button("📤 Enviar",key=f"ev{row['id']}") and nc.strip():
                        uid_val = u["id"] if u["id"] != "admin" else None
                        X("INSERT INTO comentarios(lead_id,usuario_id,texto) VALUES(%s,%s,%s)",(row["id"],uid_val,nc.strip()))
                        st.rerun()
                with t2:
                    hs=Q("SELECT h.anotacao,h.criado_em,s.nome st,s.cor cor,u.nome autor FROM historico_status h LEFT JOIN status_leads s ON h.status_id=s.id LEFT JOIN usuarios u ON h.usuario_id=u.id WHERE h.lead_id=%s ORDER BY h.criado_em DESC",(row["id"],))
                    if not hs: st.caption("Sem histórico.")
                    for h in hs:
                        ts=str(h.get("criado_em",""))[:16].replace("T"," ")
                        st.markdown(f'<div class="tl" style="border-color:{h.get("cor","#6B7280")}"><strong style="color:{h.get("cor","#6B7280")}">{h.get("st","—")}</strong> <span style="color:#94a3b8;font-size:12px">por {h.get("autor","—")} em {ts}</span>{"<br><em>"+h["anotacao"]+"</em>" if h.get("anotacao") else ""}</div>',unsafe_allow_html=True)
                with t3:
                    widget_contatos_extras(row["id"], u)


# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISE
# ══════════════════════════════════════════════════════════════════════════════
elif pg=="📊 Análise":
    header("Minha Análise","Desempenho da sua carteira")
    todos=Q("SELECT l.*,s.nome status FROM leads l LEFT JOIN status_leads s ON l.status_id=s.id WHERE l.vendedor_id=%s",(u["id"],))
    if not todos: st.info("Sem dados ainda.")
    else:
        df=pd.DataFrame(todos)
        tot=len(df); cad=len(df[df["status"]=="Cadastrado"]); cont=len(df[df["status"]=="Contato realizado"])
        tent=len(df[df["status"]=="Tentativa de contato"]); sc=tot-cad-cont-tent
        c1,c2,c3,c4,c5=st.columns(5)
        c1.metric("Total",tot); c2.metric("Sem Contato",sc); c3.metric("Tentativas",tent)
        c4.metric("Contatados",cont); c5.metric("🏆 Cadastrados",cad)
        st.divider()
        df_f=df.groupby("status").size().reset_index(name="total"); df_f.columns=["status","total"]
        st.plotly_chart(funil(df_f),use_container_width=True)
        st.divider()
        st.subheader("⚠️ Leads sem contato")
        df_sc=df[df["status"]=="Sem contato"]
        if df_sc.empty: st.success("✅ Todos foram contatados!")
        else: st.dataframe(df_sc[["razao_social","cidade","ramo","telefone"]].rename(columns={"razao_social":"Lead","cidade":"Cidade","ramo":"Ramo","telefone":"Telefone"}),use_container_width=True,hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# CARTEIRA COMPLETA — filtros + exportação
# ══════════════════════════════════════════════════════════════════════════════
elif pg=="🏆 Carteira Completa":
    header("Carteira Completa","Filtros, visualização e exportação")

    todos=Q("""SELECT l.razao_social, l.cnpj, l.ramo, l.endereco, l.cidade,
                      l.estado, l.telefone, l.email,
                      r.nome AS regiao, s.nome AS status, s.cor AS status_cor
               FROM leads l
               LEFT JOIN status_leads s ON l.status_id=s.id
               LEFT JOIN regioes r      ON l.regiao_id=r.id
               WHERE l.vendedor_id=%s
               ORDER BY l.razao_social""", (u["id"],))

    if not todos:
        st.info("Você ainda não tem leads atribuídos.")
    else:
        df_todos=pd.DataFrame(todos)

        # ── Filtros ──────────────────────────────────────────────────────────
        c1,c2,c3=st.columns(3)
        f_status=c1.selectbox("🏷️ Status", ["Todos"]+sorted(df_todos["status"].dropna().unique().tolist()), key="cc_status")
        f_ramo  =c2.selectbox("🏭 Ramo",   ["Todos"]+sorted(df_todos["ramo"].dropna().unique().tolist()),   key="cc_ramo")
        f_regiao=c3.selectbox("📍 Região", ["Todas"]+sorted(df_todos["regiao"].dropna().unique().tolist()), key="cc_regiao")
        busca_cc=st.text_input("🔍 Buscar", placeholder="Nome, CNPJ, cidade, e-mail...", key="cc_busca")

        # Aplica filtros
        df_f=df_todos.copy()
        if f_status!="Todos": df_f=df_f[df_f["status"]==f_status]
        if f_ramo  !="Todos": df_f=df_f[df_f["ramo"]  ==f_ramo]
        if f_regiao!="Todas": df_f=df_f[df_f["regiao"]==f_regiao]
        if busca_cc:
            mask=df_f.apply(lambda row: busca_cc.lower() in str(row.values).lower(), axis=1)
            df_f=df_f[mask]

        # ── Métricas ─────────────────────────────────────────────────────────
        st.divider()
        c1,c2,c3,c4=st.columns(4)
        c1.metric("📋 Total carteira",  len(df_todos))
        c2.metric("🔍 Filtrados",       len(df_f))
        c3.metric("🏆 Cadastrados",     len(df_todos[df_todos["status"]=="Cadastrado"]))
        c4.metric("⏳ Sem contato",      len(df_todos[df_todos["status"]=="Sem contato"]))

        # ── Exportar Excel ────────────────────────────────────────────────────
        st.divider()
        if not df_f.empty:
            df_exp=df_f[["razao_social","cnpj","ramo","endereco","cidade","estado",
                          "telefone","email","regiao","status"]].rename(columns={
                "razao_social":"Razão Social","cnpj":"CNPJ","ramo":"Ramo",
                "endereco":"Endereço","cidade":"Cidade","estado":"UF",
                "telefone":"Telefone","email":"E-mail","regiao":"Região","status":"Status"
            })
            buf=io.BytesIO()
            with pd.ExcelWriter(buf,engine="xlsxwriter") as w:
                df_exp.to_excel(w,index=False,sheet_name="Leads")
                wb=w.book; ws=w.sheets["Leads"]
                fmt=wb.add_format({"bold":True,"bg_color":"#041747","font_color":"#FAC319","border":1})
                for i,col in enumerate(df_exp.columns):
                    ws.write(0,i,col,fmt); ws.set_column(i,i,22)
            st.download_button(
                f"⬇️ Exportar Excel ({len(df_f)} leads)",
                buf.getvalue(),
                f"leads_{u['nome'].replace(' ','_')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )

        st.divider()

        # ── Lista ─────────────────────────────────────────────────────────────
        if df_f.empty:
            st.info("Nenhum lead encontrado com esses filtros.")
        else:
            st.markdown(f"**{len(df_f)}** lead(s) encontrado(s)")
            for _,row in df_f.iterrows():
                cor=row.get("status_cor","#6B7280")
                with st.container(border=True):
                    ca,cb=st.columns([3,1])
                    with ca:
                        st.markdown(f"**{row['razao_social']}**")
                        st.caption(
                            f"CNPJ: {row.get('cnpj') or '—'}  |  "
                            f"Ramo: {row.get('ramo') or '—'}  |  "
                            f"Região: {row.get('regiao') or '—'}"
                        )
                        st.caption(
                            f"📞 {row.get('telefone') or '—'}  "
                            f"✉️ {row.get('email') or '—'}  "
                            f"📍 {row.get('cidade') or '—'}/{row.get('estado') or '—'}"
                        )
                    with cb:
                        st.markdown(
                            f'<div style="text-align:right;padding-top:8px;">'
                            f'<span style="background:{cor}20;color:{cor};border:1px solid {cor}50;'
                            f'padding:4px 12px;border-radius:20px;font-size:13px;font-weight:600;">'
                            f'{row.get("status","—")}</span></div>',
                            unsafe_allow_html=True
                        )


# ══════════════════════════════════════════════════════════════════════════════
# MINHA CONTA
# ══════════════════════════════════════════════════════════════════════════════
elif pg=="👤 Minha Conta":
    def _h(s): return hashlib.sha256(s.encode()).hexdigest()
    header("Minha Conta",u["nome"])
    st.subheader("🔑 Trocar senha")
    with st.form("fv"):
        atual=st.text_input("Senha atual",type="password")
        n1=st.text_input("Nova senha",type="password",placeholder="Mínimo 6 caracteres")
        n2=st.text_input("Confirmar",type="password")
        ok=st.form_submit_button("💾 Salvar",type="primary")
    if ok:
        row=Q1("SELECT senha_hash FROM usuarios WHERE id=%s",(u["id"],))
        if not row or row["senha_hash"]!=_h(atual): st.error("❌ Senha atual incorreta.")
        elif len(n1)<6: st.error("Mínimo 6 caracteres.")
        elif n1!=n2: st.error("Senhas não coincidem.")
        else: X("UPDATE usuarios SET senha_hash=%s WHERE id=%s",(_h(n1),u["id"])); st.success("✅ Senha alterada!")
