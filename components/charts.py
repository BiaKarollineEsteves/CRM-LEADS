"""components/charts.py — Plotly tema Grupo LLE"""
import plotly.graph_objects as go
import pandas as pd

AM="#FAC319"; AZ="#007FE0"; VD="#0F8C3B"; AE="#041747"
PAL=[AM,AZ,VD,"#F97316","#8B5CF6","#EC4899","#14B8A6"]
BASE=dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
          font=dict(family="sans-serif",color=AE),
          margin=dict(l=20,r=20,t=40,b=20),colorway=PAL)

# Ordem e cores fixas por status
ORDEM_STATUS = [
    "Sem contato",
    "Tentativa de contato",
    "Contato realizado",
    "Cadastrado",
]
STATUS_CORES = {
    "Sem contato":           "#6B7280",
    "Tentativa de contato":  "#F59E0B",
    "Contato realizado":     "#007FE0",
    "Cadastrado":            "#0F8C3B",
}


def funil(df):
    """Funil ordenado corretamente do topo ao fundo do processo de vendas."""
    df = df.copy()
    # Ordena pela posição na ordem definida
    df["_ord"] = df["status"].apply(
        lambda x: ORDEM_STATUS.index(x) if x in ORDEM_STATUS else len(ORDEM_STATUS)
    )
    df = df.sort_values("_ord").drop(columns="_ord").reset_index(drop=True)
    cores = [STATUS_CORES.get(s, "#94A3B8") for s in df["status"]]

    fig = go.Figure(go.Funnel(
        y=df["status"],
        x=df["total"],
        textinfo="value+percent initial",
        marker=dict(
            color=cores,
            line=dict(width=2, color="rgba(255,255,255,.15)")
        ),
        textfont=dict(color="white", size=13),
        hovertemplate="<b>%{y}</b><br>Leads: %{x}<extra></extra>",
    ))
    fig.update_layout(**BASE, title="Funil de Vendas", height=370)
    return fig


def barras_h(df, x, y, titulo):
    fig = go.Figure(go.Bar(
        x=df[x], y=df[y], orientation="h",
        marker_color=AZ, text=df[x], textposition="outside",
        textfont=dict(color=AE)
    ))
    fig.update_layout(**BASE, title=titulo, height=max(250, len(df)*40),
                      xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
    return fig


def barras_v(df, x, y, titulo, y2=None):
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Leads", x=df[x], y=df[y],
                         marker_color=AZ, text=df[y], textposition="outside",
                         textfont=dict(color=AE)))
    if y2 and y2 in df.columns:
        fig.add_trace(go.Bar(name="Cadastrados", x=df[x], y=df[y2],
                             marker_color=VD, text=df[y2], textposition="outside",
                             textfont=dict(color=AE)))
    fig.update_layout(**BASE, title=titulo, barmode="group", height=320,
                      xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
    return fig


def performance_por_status(df_leads, col_vendedor="vendedor"):
    """Barras empilhadas por status com cor diferente para cada um."""
    if df_leads.empty:
        return go.Figure()

    df_pivot = (
        df_leads.groupby([col_vendedor, "status"])
        .size()
        .reset_index(name="total")
        .pivot(index=col_vendedor, columns="status", values="total")
        .fillna(0)
        .reset_index()
    )

    fig = go.Figure()

    # Empilha na ordem correta do funil
    status_cols = [s for s in ORDEM_STATUS if s in df_pivot.columns] + \
                  [s for s in df_pivot.columns if s != col_vendedor and s not in ORDEM_STATUS]

    for st in status_cols:
        cor = STATUS_CORES.get(st, "#94A3B8")
        vals = df_pivot[st].astype(int)
        textos = [str(v) if v > 0 else "" for v in vals]
        fig.add_trace(go.Bar(
            name=st,
            x=df_pivot[col_vendedor],
            y=vals,
            marker_color=cor,
            text=textos,
            textposition="inside",
            textfont=dict(color="#fff", size=12),
            hovertemplate=f"<b>%{{x}}</b><br>{st}: %{{y}}<extra></extra>",
        ))

    fig.update_layout(
        **BASE,
        title="Performance por Vendedor",
        barmode="stack",
        height=380,
        xaxis=dict(showgrid=False, tickangle=-20),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)", title="Leads"),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right",  x=1,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#dde3ef",
            borderwidth=1,
            font=dict(size=11, color=AE)
        )
    )
    return fig


def pizza(df, names, values, titulo):
    fig = go.Figure(go.Pie(
        labels=df[names], values=df[values], hole=.5,
        marker=dict(colors=PAL, line=dict(color="#fff",width=2)),
        textfont=dict(color=AE), textinfo="label+percent"
    ))
    fig.update_layout(**BASE, title=titulo, height=300, showlegend=False)
    return fig
