import json
from collections import defaultdict

from flask import Blueprint, render_template
from sqlalchemy import func

from app.auth import login_required
from app.models import LoteRecebimento, Patrimonio, Produto, Sku, TarefaBalanco, db

relatorios = Blueprint('relatorios', __name__, url_prefix='/relatorios')


@relatorios.route('/')
@login_required
def index():
    # KPIs financeiros
    total_gasto = db.session.query(
        func.coalesce(func.sum(LoteRecebimento.preco_custo * LoteRecebimento.quantidade_esperada), 0)
    ).filter(LoteRecebimento.status == 'confirmado').scalar() or 0

    valor_estoque = db.session.query(
        func.coalesce(func.sum(Produto.quantidade * Produto.preco), 0)
    ).scalar() or 0

    valor_patrimonios = db.session.query(
        func.coalesce(func.sum(Patrimonio.valor_compra), 0)
    ).scalar() or 0

    # Tarefas de balanço
    tarefas_concluidas = TarefaBalanco.query.filter_by(status='concluido').count()
    tarefas_pendentes = TarefaBalanco.query.filter_by(status='pendente').count()
    tarefas_canceladas = TarefaBalanco.query.filter_by(status='cancelado').count()

    # Tempo médio de conclusão (horas)
    tarefas_com_tempo = TarefaBalanco.query.filter(
        TarefaBalanco.status == 'concluido',
        TarefaBalanco.concluido_em.isnot(None)
    ).all()
    tempo_medio_horas = 0.0
    if tarefas_com_tempo:
        tempos = [
            (t.concluido_em - t.created_at).total_seconds() / 3600
            for t in tarefas_com_tempo
            if t.concluido_em and t.created_at
        ]
        if tempos:
            tempo_medio_horas = round(sum(tempos) / len(tempos), 1)

    # Entradas por mês (Python-level grouping — DB-agnóstico)
    lotes_confirmados = LoteRecebimento.query.filter(
        LoteRecebimento.status == 'confirmado',
        LoteRecebimento.confirmado_em.isnot(None)
    ).all()
    # chave de ordenação: 'YYYY-MM', label de exibição: 'MM/YYYY'
    meses_dict = defaultdict(lambda: {'label': '', 'qtd': 0, 'valor': 0.0})
    for lote in lotes_confirmados:
        chave = lote.confirmado_em.strftime('%Y-%m')
        meses_dict[chave]['label'] = lote.confirmado_em.strftime('%m/%Y')
        meses_dict[chave]['qtd'] += 1
        meses_dict[chave]['valor'] += (lote.preco_custo or 0) * lote.quantidade_esperada
    meses_sorted = sorted(meses_dict.items(), key=lambda x: x[0])
    meses_labels = [m[1]['label'] for m in meses_sorted]
    meses_qtd = [m[1]['qtd'] for m in meses_sorted]
    meses_valor = [round(m[1]['valor'], 2) for m in meses_sorted]

    # Top 5 SKUs por valor em estoque
    top_rows = db.session.query(
        Produto.sku_id,
        func.sum(Produto.quantidade * Produto.preco).label('valor_total'),
        func.sum(Produto.quantidade).label('quantidade_total')
    ).group_by(Produto.sku_id).order_by(
        func.sum(Produto.quantidade * Produto.preco).desc()
    ).limit(5).all()

    top_skus = []
    for row in top_rows:
        sku = db.session.get(Sku, row.sku_id)
        if sku:
            top_skus.append({
                'nome': sku.nome,
                'codigo': sku.codigo,
                'valor': round(float(row.valor_total or 0), 2),
                'quantidade': float(row.quantidade_total or 0),
            })

    # Patrimônios por status
    pat_rows = db.session.query(
        Patrimonio.status,
        func.count(Patrimonio.id)
    ).group_by(Patrimonio.status).all()
    pat_status_labels = [r[0] or 'Sem status' for r in pat_rows]
    pat_status_qtd = [r[1] for r in pat_rows]

    return render_template(
        'relatorios.html',
        total_gasto=float(total_gasto),
        valor_estoque=float(valor_estoque),
        valor_patrimonios=float(valor_patrimonios),
        tarefas_concluidas=tarefas_concluidas,
        tarefas_pendentes=tarefas_pendentes,
        tarefas_canceladas=tarefas_canceladas,
        tempo_medio_horas=tempo_medio_horas,
        meses_labels=json.dumps(meses_labels),
        meses_qtd=json.dumps(meses_qtd),
        meses_valor=json.dumps(meses_valor),
        top_skus=top_skus,
        pat_status_labels=json.dumps(pat_status_labels),
        pat_status_qtd=json.dumps(pat_status_qtd),
    )
