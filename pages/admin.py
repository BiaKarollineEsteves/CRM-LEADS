# v2 - com telefones extras
"""pages/admin.py — Painel Administrador"""
import streamlit as st, pandas as pd, hashlib
from components.layout import css, header, sidebar
from components.charts import funil, barras_h, barras_v, pizza, performance_por_status
from utils.auth import requer_login, requer_perfil, eu
from utils.db import Q, Q1, X, XM
from utils.excel import ler, template

def widget_contatos_extras(lead_id, usuario_atual):
    extras = Q(
        "SELECT ce.id, ce.telefone, ce.observacao, ce.criado_em, u.nome autor "
        "FROM contatos_extras ce LEFT JOIN usuarios u ON ce.adicionado_por=u.id "
        "WHERE ce.lead_id=%s ORDER BY ce.criado_em", (lead_id,)
    )
    if extras:
        st.markdown("**📞 Telefones adicionais:**")
        for e in extras:
            from datetime import timezone, timedelta
        gmt3 = timezone(timedelta(hours=-3))
        criado = e.get("criado_em")
        if criado and hasattr(criado, "astimezone"):
            ts = criado.astimezone(gmt3).strftime("%d/%m/%Y %H:%M")
        else:
            ts = str(criado or "")[:16].replace("T"," ")
            c1,c2 = st.columns([5,1])
            obs = f" — *{e['observacao']}*" if e.get("observacao") else ""
            c1.markdown(
                f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:7px;'
                f'padding:8px 12px;font-size:13px;margin-bottom:4px;">'
                f'📞 <strong>{e["telefone"]}</strong>{obs} '
                f'<span style="color:#94a3b8;font-size:11px;">— {e.get("autor","—")} em {ts}</span>'
                f'</div>', unsafe_allow_html=True)
            if c2.button("🗑️", key=f"del_ct_{e['id']}_{lead_id}"):
                X("DELETE FROM contatos_extras WHERE id=%s", (e["id"],))
                st.rerun()
    else:
        st.caption("Nenhum telefone adicional ainda.")
    with st.form(key=f"form_ct_{lead_id}"):
        c1,c2 = st.columns([2,3])
        novo_tel = c1.text_input("Novo telefone", placeholder="(XX) XXXXX-XXXX")
        obs_tel  = c2.text_input("Observação", placeholder="Ex: WhatsApp, vizinho...")
        salvar   = st.form_submit_button("➕ Adicionar telefone", type="primary")
    if salvar:
        if not novo_tel.strip():
            st.error("Digite o telefone.")
        else:
            uid = usuario_atual["id"] if usuario_atual["id"] != "admin" else None
            X("INSERT INTO contatos_extras (lead_id, telefone, observacao, adicionado_por) VALUES (%s,%s,%s,%s)",
              (lead_id, novo_tel.strip(), obs_tel.strip() or None, uid))
            lead = Q1("SELECT vendedor_id, razao_social FROM leads WHERE id=%s", (lead_id,))
            if lead and lead.get("vendedor_id"):
                vid = str(lead["vendedor_id"])
                if vid != usuario_atual["id"]:
                    msg = f"Novo número adicionado para **{lead['razao_social']}**: {novo_tel.strip()}"
                    if obs_tel.strip(): msg += f" ({obs_tel.strip()})"
                    X("INSERT INTO notificacoes (usuario_id, lead_id, mensagem) VALUES (%s,%s,%s)",
                      (vid, lead_id, msg))
            st.cache_data.clear()
            st.success(f"✅ Telefone {novo_tel} adicionado!")
            st.rerun()


st.set_page_config(page_title="ADM | CRM Grupo LLE", page_icon="⚙️", layout="wide")
css(); requer_login(); requer_perfil("admin")
u = eu()

if "pg" not in st.session_state: st.session_state.pg = "📊 Dashboard"

pend = len(Q("SELECT id FROM usuarios WHERE status='pendente'"))
menu = [
    ("📊 Dashboard",      "📊 Dashboard"),
    (f"✅ Aprovações{'  🔴' if pend else ''}", "✅ Aprovações"),
    ("📥 Importar Leads", "📥 Importar Leads"),
    ("🔀 Atribuir Leads", "🔀 Atribuir Leads"),
    ("🏷️ Status",         "🏷️ Status"),
    ("🗺️ Regiões",        "🗺️ Regiões"),
    ("👥 Usuários",       "👥 Usuários"),
    ("🔑 Senhas",         "🔑 Senhas"),
]
nova = sidebar(u, st.session_state.pg, menu)
if nova != st.session_state.pg:
    st.session_state.pg = nova; st.rerun()
pg = st.session_state.pg

empresas = {e["nome"]: e["id"] for e in Q("SELECT id,nome FROM empresas ORDER BY nome")}
with st.sidebar:
    st.divider()
    st.markdown('<p style="font-size:11px;color:rgba(255,255,255,.5);text-transform:uppercase">Empresa</p>', unsafe_allow_html=True)
    fe = st.selectbox("", ["Todas"]+list(empresas.keys()), label_visibility="collapsed", key="fe")
eid = empresas.get(fe) if fe != "Todas" else None


def _h(s): return hashlib.sha256(s.encode()).hexdigest()


@st.cache_data(ttl=20)
def leads_df(empresa_id=None):
    sql = """SELECT l.id, l.razao_social, l.cnpj, l.ramo, l.cidade, l.estado,
                    l.telefone, l.email, l.vendedor_id, l.empresa_id,
                    e.nome empresa, r.nome regiao,
                    u.nome vendedor, s.nome status, s.cor status_cor
             FROM leads l
             LEFT JOIN empresas e     ON l.empresa_id=e.id
             LEFT JOIN regioes r      ON l.regiao_id=r.id
             LEFT JOIN usuarios u     ON l.vendedor_id=u.id
             LEFT JOIN status_leads s ON l.status_id=s.id"""
    p: tuple = ()
    if empresa_id: sql += " WHERE l.empresa_id=%s"; p = (empresa_id,)
    sql += " ORDER BY l.razao_social"
    rows = Q(sql, p)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if pg == "📊 Dashboard":
    header("Dashboard", f"Empresa: {fe}")
    df = leads_df(eid)
    if df.empty:
        st.info("Nenhum lead ainda. Importe em **📥 Importar Leads**.")
    else:
        tot=len(df); cad=len(df[df["status"]=="Cadastrado"]) if "status" in df.columns else 0
        sv=int(df["vendedor_id"].isna().sum()) if "vendedor_id" in df.columns else 0
        tx=f"{cad/tot*100:.1f}%" if tot else "0%"
        c1,c2,c3,c4=st.columns(4)
        c1.metric("📋 Total",f"{tot:,}"); c2.metric("🏆 Cadastrados",f"{cad:,}")
        c3.metric("👤 Sem Vendedor",f"{sv:,}"); c4.metric("📊 Conversão",tx)
        st.divider()
        col1,col2=st.columns(2)
        with col1:
            if "status" in df.columns and df["status"].notna().any():
                df_f=df.groupby("status").size().reset_index(name="total"); df_f.columns=["status","total"]
                st.plotly_chart(funil(df_f),use_container_width=True)
        with col2:
            if "regiao" in df.columns and df["regiao"].notna().any():
                df_r=df[df["regiao"].notna()].groupby("regiao").size().reset_index(name="total")
                st.plotly_chart(barras_h(df_r,"total","regiao","Leads por Região"),use_container_width=True)
        col3,col4=st.columns(2)
        with col3:
            if fe=="Todas" and "empresa" in df.columns:
                df_e=df.groupby("empresa").size().reset_index(name="total")
                st.plotly_chart(pizza(df_e,"empresa","total","Por Empresa"),use_container_width=True)
        with col4:
            if "vendedor" in df.columns and df["vendedor"].notna().any():
                df_v=df[df["vendedor"].notna()].groupby("vendedor").size().reset_index(name="total")
                df_c=(df[(df["vendedor"].notna())&(df["status"]=="Cadastrado")].groupby("vendedor").size().reset_index(name="cadastrados"))
                df_v=df_v.merge(df_c,on="vendedor",how="left").fillna(0)
                st.plotly_chart(barras_v(df_v,"vendedor","total","Performance",y2="cadastrados"),use_container_width=True)
        st.divider()
        st.subheader("Todos os Leads")

        # Busca e filtro na tabela
        bf1, bf2, bf3 = st.columns(3)
        busca_adm = bf1.text_input("🔍 Buscar", placeholder="Nome, CNPJ...", key="busca_adm")
        f_status_adm = bf2.selectbox("Status", ["Todos"]+[s["nome"] for s in Q("SELECT nome FROM status_leads ORDER BY ordem")], key="f_st_adm")
        f_vend_adm = bf3.selectbox("Vendedor", ["Todos"]+sorted(df["vendedor"].dropna().unique().tolist()) if "vendedor" in df.columns else ["Todos"], key="f_vend_adm")

        df_tab = df.copy()
        if f_status_adm != "Todos" and "status" in df_tab.columns: df_tab = df_tab[df_tab["status"]==f_status_adm]
        if f_vend_adm  != "Todos" and "vendedor" in df_tab.columns: df_tab = df_tab[df_tab["vendedor"]==f_vend_adm]
        if busca_adm:
            mask = df_tab.apply(lambda row: busca_adm.lower() in str(row.values).lower(), axis=1)
            df_tab = df_tab[mask]

        st.caption(f"{len(df_tab)} lead(s) encontrado(s)")

        cols=[c for c in ["razao_social","cnpj","empresa","regiao","vendedor","status","ramo","cidade","estado"] if c in df_tab.columns]
        df_show = df_tab[cols].copy().fillna("—").replace("nan","—").replace("NaN","—")
        st.dataframe(df_show.rename(columns={"razao_social":"Razão Social","cnpj":"CNPJ","empresa":"Empresa",
            "regiao":"Região","vendedor":"Vendedor","status":"Status","ramo":"Ramo","cidade":"Cidade","estado":"UF"}),
            use_container_width=True, hide_index=True)

        # ── Detalhes do lead com histórico ──────────────────────────────────
        st.divider()
        st.subheader("🔍 Detalhes e Histórico do Lead")

        if df_tab.empty:
            st.info("Nenhum lead para exibir com esses filtros.")
        else:
            lead_opts = df_tab["id"].tolist()
            lead_sel = st.selectbox(
                "Selecionar lead",
                lead_opts,
                format_func=lambda x: (
                    f"{df_tab[df_tab['id']==x]['razao_social'].values[0]}  —  "
                    f"{df_tab[df_tab['id']==x]['vendedor'].values[0] or 'Sem vendedor'}  |  "
                    f"{df_tab[df_tab['id']==x]['status'].values[0] or '—'}"
                ),
                key="lead_det"
            )
            row = df_tab[df_tab["id"]==lead_sel].iloc[0]

            with st.container(border=True):
                c1, c2 = st.columns([2,1])
                with c1:
                    st.markdown(f"### {row['razao_social']}")
                    st.markdown(f"""
| | |
|---|---|
|**CNPJ**|{row.get('cnpj') or '—'}|
|**Ramo**|{row.get('ramo') or '—'}|
|**Endereço**|{row.get('endereco','—') if 'endereco' in row else '—'}|
|**Cidade/UF**|{row.get('cidade') or '—'} / {row.get('estado') or '—'}|
|**Telefone**|{row.get('telefone') or '—'}|
|**E-mail**|{row.get('email') or '—'}|
|**Empresa**|{row.get('empresa') or '—'}|
|**Região**|{row.get('regiao') or '—'}|
|**Vendedor**|{row.get('vendedor') or '—'}|
""")
                with c2:
                    cor = row.get("status_cor","#6B7280")
                    st.markdown(
                        f'<div style="margin-top:12px;text-align:center;">'
                        f'<span style="background:{cor}20;color:{cor};border:1px solid {cor}50;'
                        f'padding:6px 18px;border-radius:20px;font-size:14px;font-weight:700;">'
                        f'{row.get("status","—")}</span></div>',
                        unsafe_allow_html=True
                    )

                st.divider()
                tab_hist, tab_coment, tab_ct = st.tabs(["📋 Histórico de Status", "💬 Comentários", "📞 Telefones Extras"])

                with tab_hist:
                    hs = Q("""SELECT h.anotacao, h.criado_em, s.nome st, s.cor cor, u.nome autor
                              FROM historico_status h
                              LEFT JOIN status_leads s ON h.status_id=s.id
                              LEFT JOIN usuarios u     ON h.usuario_id=u.id
                              WHERE h.lead_id=%s ORDER BY h.criado_em DESC""", (lead_sel,))
                    if not hs:
                        st.caption("Nenhuma mudança de status registrada ainda.")
                    else:
                        for h in hs:
                            ts = str(h.get("criado_em",""))[:16].replace("T"," ")
                            cor_h = h.get("cor","#6B7280")
                            st.markdown(
                                f'<div class="tl" style="border-color:{cor_h};">'
                                f'<strong style="color:{cor_h};">{h.get("st","—")}</strong> '
                                f'<span style="color:#94a3b8;font-size:12px;">por {h.get("autor","—")} em {ts}</span>'
                                f'{"<br><em style=color:#555;>"+h["anotacao"]+"</em>" if h.get("anotacao") else ""}'
                                f'</div>',
                                unsafe_allow_html=True
                            )

                with tab_coment:
                    cs = Q("""SELECT c.texto, c.criado_em, u.nome autor
                              FROM comentarios c
                              LEFT JOIN usuarios u ON c.usuario_id=u.id
                              WHERE c.lead_id=%s ORDER BY c.criado_em""", (lead_sel,))
                    if not cs:
                        st.caption("Nenhum comentário ainda.")
                    else:
                        for c in cs:
                            ts = str(c.get("criado_em",""))[:16].replace("T"," ")
                            st.markdown(
                                f'<div class="tl"><strong>{c.get("autor","—")}</strong> '
                                f'<span style="color:#94a3b8;font-size:12px;">{ts}</span>'
                                f'<br>{c["texto"]}</div>',
                                unsafe_allow_html=True
                            )
                with tab_ct:
                    widget_contatos_extras(lead_sel, u)


# ══════════════════════════════════════════════════════════════════════════════
# APROVAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
elif pg == "✅ Aprovações":
    header("Aprovações","Novos cadastros aguardando liberação")
    rows = Q("SELECT * FROM usuarios WHERE status='pendente' ORDER BY criado_em")
    if not rows:
        st.success("✅ Nenhum cadastro pendente.")
    else:
        st.info(f"**{len(rows)}** cadastro(s) aguardando.")
        for r in rows:
            with st.container(border=True):
                st.markdown(f"**{r['nome']}** — `{r['email']}`")
                c1,c2,c3=st.columns(3)
                pf=c1.selectbox("Perfil",["vendedor","gestor","admin"],key=f"pf{r['id']}")
                ep=c2.selectbox("Empresa",["(nenhuma)"]+list(empresas.keys()),key=f"ep{r['id']}")
                ca,cr=c3.columns(2)
                if ca.button("✅ Aprovar",key=f"ap{r['id']}",type="primary"):
                    X("UPDATE usuarios SET status='aprovado',perfil=%s,empresa_id=%s WHERE id=%s",
                      (pf, empresas.get(ep) if ep!="(nenhuma)" else None, r["id"]))
                    st.success(f"✅ {r['nome']} aprovado como **{pf}**!")
                    if pf == "admin":
                        st.info("Hash da senha (para secrets.toml se quiser acesso master):")
                        st.code(f'[admin]\nsenha_hash = "{r["senha_hash"]}"', language="toml")
                    st.rerun()
                if cr.button("❌ Recusar",key=f"rc{r['id']}"):
                    X("UPDATE usuarios SET status='inativo' WHERE id=%s",(r["id"],))
                    st.warning("Recusado."); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# IMPORTAR LEADS — com detecção automática de regiões
# ══════════════════════════════════════════════════════════════════════════════
elif pg == "📥 Importar Leads":
    header("Importar Leads","Cidades detectadas automaticamente do endereço")
    ci,cb=st.columns([3,1])
    with cb: st.download_button("⬇ Template",template(),"template_leads.xlsx",
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with ci: st.info("O sistema extrai a cidade do endereço e sugere as regiões para você confirmar.")

    arq = st.file_uploader("Selecionar arquivo Excel ou CSV",type=["xlsx","xls","csv"])

    if arq:
        # Cache do DataFrame no session_state para não perder ao interagir
        chave = f"imp_{arq.name}_{arq.size}"
        if st.session_state.get("imp_chave") != chave:
            df_i, err = ler(arq)
            if err: st.error(err); st.stop()
            st.session_state.imp_df = df_i
            st.session_state.imp_chave = chave

        df_i = st.session_state.imp_df
        st.success(f"**{len(df_i)}** registros encontrados.")

        # Empresa destino
        emp = st.selectbox("Empresa destino", list(empresas.keys()), key="imp_emp")
        empid = empresas[emp]

        # ── Detecção de cidades ────────────────────────────────────────────
        st.divider()
        st.subheader("🗺️ Cidades detectadas automaticamente")

        cidades = sorted(df_i["_cidade"].dropna().unique().tolist())
        sem_cidade = df_i[df_i["_cidade"].isna()]

        if not cidades:
            st.warning("⚠️ Nenhuma cidade detectada. Verifique se o endereço segue o padrão: *Rua X, 100 - Bairro, Cidade - UF, CEP*")
        else:
            regs_existentes = Q("SELECT id,nome FROM regioes ORDER BY nome")
            nomes_reg = [r["nome"] for r in regs_existentes]
            regs_map  = {r["nome"]: r["id"] for r in regs_existentes}

            st.info(f"**{len(cidades)}** cidade(s) encontrada(s). Confirme como cada uma será registrada como região:")

            mapeamento = {}  # cidade → nome da região
            for cidade in cidades:
                qtd = len(df_i[df_i["_cidade"] == cidade])
                c1, c2 = st.columns([2, 3])
                c1.markdown(f"**📍 {cidade}** &nbsp; `{qtd} lead(s)`", unsafe_allow_html=True)

                # Opção padrão: criar com o próprio nome da cidade
                opcoes = [f"🆕 Criar região: {cidade}"] + [f"🔗 Usar existente: {r}" for r in nomes_reg]
                escolha = c2.selectbox("", opcoes, key=f"r_{cidade}", label_visibility="collapsed")

                if "Criar" in escolha:
                    mapeamento[cidade] = cidade
                else:
                    mapeamento[cidade] = escolha.replace("🔗 Usar existente: ", "")

            if len(sem_cidade) > 0:
                st.warning(f"**{len(sem_cidade)}** lead(s) sem cidade detectada — importados sem região.")

            # Resumo
            st.divider()
            novas_regioes = [r for r in set(mapeamento.values()) if r not in nomes_reg]
            if novas_regioes:
                st.markdown(f"**🆕 Regiões que serão criadas:** {', '.join(novas_regioes)}")
            st.markdown(f"**Total a importar:** {len(df_i)} leads")

            # Modo de importação
            st.divider()
            modo = st.radio(
                "Como importar?",
                ["🆕 Inserir apenas novos leads", "🔄 Atualizar existentes pelo CNPJ (preserva histórico)"],
                key="modo_import"
            )
            st.caption("**Atualizar** só muda os dados cadastrais (ramo, endereço, telefone, e-mail). Não altera status nem histórico.")

            if st.button("🚀 Confirmar e Importar", type="primary", use_container_width=True):
                st0 = Q1("SELECT id FROM status_leads WHERE nome='Sem contato'")
                sid = st0["id"] if st0 else None

                # Cria regiões novas
                for rn in novas_regioes:
                    try: X("INSERT INTO regioes(nome) VALUES(%s)", (rn,))
                    except: pass

                regs_att = {r["nome"]: r["id"] for r in Q("SELECT id,nome FROM regioes")}

                novos = 0; atualizados = 0; ignorados = 0

                for _, row in df_i.iterrows():
                    cidade_row  = row.get("_cidade")
                    regiao_nome = mapeamento.get(cidade_row) if cidade_row else None
                    rid  = regs_att.get(regiao_nome) if regiao_nome else None
                    cnpj = row.get("CNPJ")
                    rs   = row.get("Razão Social")
                    ramo = row.get("Ramo de Atividade")
                    end  = row.get("Endereço")
                    tel  = row.get("Telefone")
                    email= row.get("Email")
                    est  = row.get("_estado")

                    # Sempre busca existente pelo CNPJ ou Razão Social
                    existente = None
                    if cnpj and str(cnpj).strip() not in ("", "—", "None", "nan"):
                        existente = Q1(
                            "SELECT id FROM leads WHERE cnpj=%s AND empresa_id=%s",
                            (cnpj, empid)
                        )
                    if not existente and rs:
                        existente = Q1(
                            "SELECT id FROM leads WHERE razao_social=%s AND empresa_id=%s",
                            (rs, empid)
                        )

                    if existente:
                        if "Atualizar" in modo:
                            # Atualiza dados cadastrais — preserva status, vendedor e histórico
                            X("""UPDATE leads SET
                                razao_social=%s, ramo=%s, endereco=%s, cidade=%s,
                                estado=%s, telefone=%s, email=%s, regiao_id=%s
                               WHERE id=%s""",
                              (rs, ramo, end, cidade_row, est, tel, email, rid, existente["id"]))
                            atualizados += 1
                        else:
                            # Modo "apenas novos" → pula duplicatas
                            ignorados += 1
                    else:
                        # Não existe → insere novo em qualquer modo
                        X("""INSERT INTO leads
                            (cnpj,razao_social,ramo,endereco,cidade,estado,telefone,email,empresa_id,regiao_id,status_id)
                            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                          (cnpj, rs, ramo, end, cidade_row, est, tel, email, empid, rid, sid))
                        novos += 1

                st.cache_data.clear()
                for k in ["imp_df","imp_chave"]:
                    st.session_state.pop(k, None)

                if "Atualizar" in modo:
                    st.success(f"✅ **{atualizados}** atualizado(s) | **{novos}** novo(s) inserido(s)")
                else:
                    msg = f"✅ **{novos}** lead(s) inserido(s)"
                    if ignorados > 0:
                        msg += f" | **{ignorados}** duplicata(s) ignorada(s)"
                    st.success(msg)
                if novas_regioes:
                    st.info(f"Regiões criadas: {', '.join(novas_regioes)}")
                st.balloons()


# ══════════════════════════════════════════════════════════════════════════════
# ATRIBUIR LEADS
# ══════════════════════════════════════════════════════════════════════════════
elif pg == "🔀 Atribuir Leads":
    header("Atribuir / Reatribuir Leads")
    sq="SELECT id,nome FROM usuarios WHERE status='aprovado' AND perfil='vendedor'"
    pv: tuple=()
    if eid: sq+=" AND empresa_id=%s"; pv=(eid,)
    vm={v["nome"]:str(v["id"]) for v in Q(sq,pv)}
    if not vm:
        st.warning("Nenhum vendedor aprovado. Vá em **✅ Aprovações**.")
    else:
        t1,t2=st.tabs(["📤 Sem vendedor","🔄 Reatribuir"])
        with t1:
            sq2="SELECT l.id,l.razao_social,r.nome regiao FROM leads l LEFT JOIN regioes r ON l.regiao_id=r.id WHERE l.vendedor_id IS NULL"
            if eid: sq2+=" AND l.empresa_id=%s"; pv2=(eid,)
            else: pv2=()
            sem=Q(sq2+" ORDER BY l.razao_social LIMIT 300",pv2)
            if not sem: st.success("✅ Todos os leads têm vendedor!")
            else:
                st.caption(f"{len(sem)} lead(s) sem vendedor")
                vd=st.selectbox("Atribuir para:",list(vm.keys()))
                op={r["id"]:f"{r['razao_social']} — {r.get('regiao') or '—'}" for r in sem}
                sel=st.multiselect("Selecione leads:",list(op.keys()),format_func=lambda x:op[x],default=[])
                todos=st.checkbox("Atribuir TODOS os sem vendedor")
                if st.button("✅ Atribuir",type="primary"):
                    alvo=[r["id"] for r in sem] if todos else sel
                    if not alvo: st.warning("Selecione ao menos um.")
                    else:
                        with st.spinner(f"Atribuindo {len(alvo)}..."):
                            [X("UPDATE leads SET vendedor_id=%s WHERE id=%s",(vm[vd],lid)) for lid in alvo]
                        st.cache_data.clear(); st.success(f"✅ {len(alvo)} → {vd}"); st.rerun()
        with t2:
            com=Q("SELECT l.id,l.razao_social,u.nome vendedor FROM leads l LEFT JOIN usuarios u ON l.vendedor_id=u.id WHERE l.vendedor_id IS NOT NULL"
                  +(" AND l.empresa_id=%s" if eid else "")+" ORDER BY l.razao_social LIMIT 300",(eid,) if eid else ())
            if not com: st.info("Nenhum lead atribuído.")
            else:
                lid=st.selectbox("Lead:",[r["id"] for r in com],
                    format_func=lambda x:next(f"{r['razao_social']} → {r['vendedor']}" for r in com if r["id"]==x))
                nv=st.selectbox("Novo vendedor:",list(vm.keys()),key="rv")
                if st.button("🔄 Reatribuir",type="primary"):
                    X("UPDATE leads SET vendedor_id=%s WHERE id=%s",(vm[nv],lid))
                    st.cache_data.clear(); st.success("✅ Reatribuído!"); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STATUS
# ══════════════════════════════════════════════════════════════════════════════
elif pg == "🏷️ Status":
    header("Gerenciar Status")
    for r in Q("SELECT * FROM status_leads ORDER BY ordem"):
        c1,c2,c3,c4=st.columns([4,1,1,1])
        c1.markdown(f'<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{r["cor"]};margin-right:8px;vertical-align:middle"></span>**{r["nome"]}**',unsafe_allow_html=True)
        c2.caption(f"#{r['ordem']}"); c3.caption("✅" if r["ativo"] else "❌")
        if r["nome"] not in ("Sem contato","Cadastrado"):
            if c4.button("Desativar",key=f"ds{r['id']}"):
                X("UPDATE status_leads SET ativo=FALSE WHERE id=%s",(r["id"],)); st.rerun()
    st.divider()
    st.subheader("➕ Novo status")
    c1,c2,c3=st.columns(3)
    nn=c1.text_input("Nome"); nc=c2.color_picker("Cor","#3B82F6"); no=c3.number_input("Ordem",min_value=0,value=4)
    if st.button("Adicionar",type="primary") and nn.strip():
        try: X("INSERT INTO status_leads(nome,cor,ordem) VALUES(%s,%s,%s)",(nn.strip(),nc,int(no))); st.rerun()
        except: st.error("Esse nome já existe.")


# ══════════════════════════════════════════════════════════════════════════════
# REGIÕES
# ══════════════════════════════════════════════════════════════════════════════
elif pg == "🗺️ Regiões":
    header("Gerenciar Regiões")
    regioes=Q("SELECT * FROM regioes ORDER BY nome")
    if not regioes: st.info("Nenhuma região ainda — são criadas automaticamente na importação.")
    for r in regioes:
        c1,c2=st.columns([5,1])
        c1.write(f"📍 **{r['nome']}**")
        if c2.button("Remover",key=f"rr{r['id']}"):
            X("DELETE FROM regioes WHERE id=%s",(r["id"],)); st.rerun()
    st.divider()
    nr=st.text_input("Adicionar manualmente")
    if st.button("Adicionar",type="primary") and nr.strip():
        try: X("INSERT INTO regioes(nome) VALUES(%s)",(nr.strip(),)); st.rerun()
        except: st.error("Já existe.")


# ══════════════════════════════════════════════════════════════════════════════
# USUÁRIOS
# ══════════════════════════════════════════════════════════════════════════════
elif pg == "👥 Usuários":
    header("Gerenciar Usuários")
    us=Q("SELECT u.id,u.nome,u.email,u.perfil,u.status,u.empresa_id,e.nome empresa FROM usuarios u LEFT JOIN empresas e ON u.empresa_id=e.id ORDER BY u.nome")
    if not us: st.info("Nenhum usuário ainda.")
    else:
        df_u=pd.DataFrame(us); df_u["empresa"]=df_u["empresa"].fillna("—")
        st.dataframe(df_u[["nome","email","perfil","empresa","status"]].rename(columns={
            "nome":"Nome","email":"E-mail","perfil":"Perfil","empresa":"Empresa","status":"Status"
        }),use_container_width=True,hide_index=True)
        st.divider()
        st.subheader("✏️ Editar usuário")
        sel=st.selectbox("Selecionar",[u2["email"] for u2 in us])
        row=next(u2 for u2 in us if u2["email"]==sel)
        c1,c2,c3=st.columns(3)
        np_=c1.selectbox("Perfil",["vendedor","gestor","admin"],
            index=["vendedor","gestor","admin"].index(row["perfil"]) if row["perfil"] in ["vendedor","gestor","admin"] else 0)
        el=["(nenhuma)"]+list(empresas.keys())
        ce=next((k for k,v in empresas.items() if v==row.get("empresa_id")),"(nenhuma)")
        ne=c2.selectbox("Empresa",el,index=el.index(ce))
        ns=c3.selectbox("Status",["pendente","aprovado","inativo"],
            index=["pendente","aprovado","inativo"].index(row["status"]) if row["status"] in ["pendente","aprovado","inativo"] else 1)
        cs,ca=st.columns(2)
        if cs.button("💾 Salvar",type="primary"):
            X("UPDATE usuarios SET perfil=%s,empresa_id=%s,status=%s WHERE email=%s",
              (np_,empresas.get(ne) if ne!="(nenhuma)" else None,ns,sel))
            st.success("✅ Atualizado!"); st.rerun()
        if ca.button("🗑️ Excluir"):
            st.session_state[f"del_{sel}"]=True
        if st.session_state.get(f"del_{sel}"):
            st.warning(f"⚠️ Excluir **{row['nome']}**?")
            cc1,cc2=st.columns(2)
            if cc1.button("Sim, excluir",type="primary"):
                X("DELETE FROM usuarios WHERE email=%s",(sel,))
                st.session_state.pop(f"del_{sel}",None)
                st.success("✅ Excluído!"); st.rerun()
            if cc2.button("Cancelar"):
                st.session_state.pop(f"del_{sel}",None); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SENHAS
# ══════════════════════════════════════════════════════════════════════════════
elif pg == "🔑 Senhas":
    header("Redefinir Senhas")
    us=Q("SELECT nome,email FROM usuarios ORDER BY nome")
    if not us: st.info("Nenhum usuário cadastrado.")
    else:
        sel=st.selectbox("Selecionar usuário",[u2["email"] for u2 in us],
            format_func=lambda x:next(f"{u2['nome']} ({x})" for u2 in us if u2["email"]==x))
        with st.form("form_reset"):
            n1=st.text_input("Nova senha",type="password",placeholder="Mínimo 6 caracteres")
            n2=st.text_input("Confirmar",type="password")
            ok=st.form_submit_button("🔑 Redefinir",type="primary")
        if ok:
            if not n1 or not n2:     st.error("Preencha os dois campos.")
            elif len(n1)<6:          st.error("Mínimo 6 caracteres.")
            elif n1!=n2:             st.error("Senhas não coincidem.")
            else:
                X("UPDATE usuarios SET senha_hash=%s WHERE email=%s",(_h(n1),sel))
                st.success(f"✅ Senha de **{sel}** redefinida!")
        st.divider()
        st.subheader("ℹ️ Senha do Administrador master")
        st.info("Definida nos **Secrets do Streamlit Cloud** no campo `[admin] senha_hash`.")
        st.markdown("Gerar hash: https://emn178.github.io/online-tools/sha256.html")
