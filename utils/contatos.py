"""utils/contatos.py — Gestão de contatos extras e notificações"""
import streamlit as st
from datetime import timedelta
from utils.db import Q, Q1, X


def _fmt_ts(criado):
    """Converte datetime UTC para GMT-3 e formata."""
    if not criado:
        return "—"
    try:
        return (criado - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(criado)[:16].replace("T", " ")


def widget_contatos_extras(lead_id: int, usuario_atual: dict):
    """Widget reutilizável para exibir e adicionar telefones extras."""
    extras = Q(
        "SELECT ce.id, ce.telefone, ce.observacao, ce.criado_em, u.nome autor "
        "FROM contatos_extras ce LEFT JOIN usuarios u ON ce.adicionado_por=u.id "
        "WHERE ce.lead_id=%s ORDER BY ce.criado_em",
        (lead_id,)
    )

    if extras:
        st.markdown("**📞 Telefones adicionais:**")
        for e in extras:
            ts = _fmt_ts(e.get("criado_em"))
            c1, c2 = st.columns([5, 1])
            obs = f" — *{e['observacao']}*" if e.get("observacao") else ""
            c1.markdown(
                f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:7px;'
                f'padding:8px 12px;font-size:13px;margin-bottom:4px;">'
                f'📞 <strong>{e["telefone"]}</strong>{obs} '
                f'<span style="color:#94a3b8;font-size:11px;">— {e.get("autor","—")} em {ts}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
            if c2.button("🗑️", key=f"del_ct_{e['id']}_{lead_id}", help="Remover"):
                X("DELETE FROM contatos_extras WHERE id=%s", (e["id"],))
                st.rerun()
    else:
        st.caption("Nenhum telefone adicional ainda.")

    with st.form(key=f"form_ct_{lead_id}"):
        c1, c2 = st.columns([2, 3])
        novo_tel = c1.text_input("Novo telefone", placeholder="(XX) XXXXX-XXXX")
        obs_tel  = c2.text_input("Observação (opcional)", placeholder="Ex: WhatsApp, vizinho...")
        salvar   = st.form_submit_button("➕ Adicionar telefone", type="primary")

    if salvar:
        if not novo_tel.strip():
            st.error("Digite o telefone.")
        else:
            uid = usuario_atual["id"] if usuario_atual["id"] != "admin" else None
            X(
                "INSERT INTO contatos_extras (lead_id, telefone, observacao, adicionado_por) "
                "VALUES (%s, %s, %s, %s)",
                (lead_id, novo_tel.strip(), obs_tel.strip() or None, uid)
            )
            lead = Q1("SELECT vendedor_id, razao_social FROM leads WHERE id=%s", (lead_id,))
            if lead and lead.get("vendedor_id"):
                vid = str(lead["vendedor_id"])
                if vid != usuario_atual["id"]:
                    msg = f"Novo número adicionado para **{lead['razao_social']}**: {novo_tel.strip()}"
                    if obs_tel.strip():
                        msg += f" ({obs_tel.strip()})"
                    X(
                        "INSERT INTO notificacoes (usuario_id, lead_id, mensagem) VALUES (%s, %s, %s)",
                        (vid, lead_id, msg)
                    )
            st.cache_data.clear()
            st.success(f"✅ Telefone {novo_tel} adicionado!")
            st.rerun()
