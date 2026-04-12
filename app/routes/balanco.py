import json
from collections import defaultdict
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.auth import functional_permission_required, get_current_user, resolve_safe_redirect_target
from app.models import Produto, Sku, TarefaBalanco, User, db
from app.number_utils import parse_decimal_input

balanco = Blueprint(
    'balanco',
    __name__,
    url_prefix='/balanco'
)

TIPOS_OPERACAO_BALANCO = {
    'conferencia': 'Conferência operacional',
    'enderecamento': 'Endereçamento para prateleira',
}

STATUS_PRIORITY = {
    'pendente': 0,
    'concluido': 1,
    'cancelado': 2,
}


def normalizar_texto(valor):
    texto = (valor or '').strip()
    return texto or None


def normalizar_quantidade(valor):
    return float(valor or 0)


def produto_esta_enderecado(produto):
    return bool((produto.corredor or '').strip() or (produto.prateleira or '').strip())


def formatar_localizacao(produto):
    corredor = (produto.corredor or '').strip()
    prateleira = (produto.prateleira or '').strip()

    if corredor or prateleira:
        return f'{corredor or "-"} / {prateleira or "-"}'

    return 'Recebimento / sem endereço'


def ordenar_tarefas(tarefas):
    return sorted(tarefas, key=lambda tarefa: STATUS_PRIORITY.get(tarefa.status, 9))


def construir_redirect_balanco(sku_id=None):
    destino = resolve_safe_redirect_target(request.form.get('next') or request.args.get('next'))
    if destino:
        return redirect(destino)
    if sku_id:
        return redirect(url_for('balanco.gerenciar_balanco', sku_id=sku_id))
    return redirect(url_for('balanco.gerenciar_balanco'))


def resolver_sku_por_payload(leitura):
    texto = (leitura or '').strip()
    if not texto:
        raise ValueError('Leia um QR Code ou informe um código de SKU para iniciar o balanço.')

    payload = None
    codigo = texto

    if texto.startswith('{'):
        try:
            payload = json.loads(texto)
        except json.JSONDecodeError as exc:
            raise ValueError('O conteúdo lido do QR Code não está em um formato JSON válido.') from exc

    if payload is not None:
        if not isinstance(payload, dict):
            raise ValueError('O QR Code lido não possui um payload válido para SKU.')

        payload_type = (payload.get('type') or '').strip().lower()
        if payload_type and payload_type != 'sku':
            raise ValueError('O QR Code lido não pertence a um SKU válido.')

        sku_id = payload.get('id')
        codigo = (payload.get('codigo') or '').strip()

        sku = None
        if sku_id is not None:
            try:
                sku = db.session.get(Sku, int(sku_id))
            except (TypeError, ValueError):
                sku = None

        if not sku and codigo:
            sku = Sku.query.filter_by(codigo=codigo).first()

        if not sku:
            raise LookupError('Nenhum SKU vinculado ao QR Code foi encontrado.')

        return sku, 'qrcode'

    sku = Sku.query.filter_by(codigo=codigo).first()
    if not sku:
        raise LookupError('Nenhum SKU encontrado para o código informado.')

    return sku, 'codigo'


def resolver_sku_para_balanco(sku_id=None, leitura=None):
    if sku_id:
        sku = db.session.get(Sku, sku_id)
        if not sku:
            raise LookupError('O SKU selecionado para o balanço não foi encontrado.')
        return sku, 'atalho'

    return resolver_sku_por_payload(leitura)


def montar_resumo_balanco(sku):
    produtos = Produto.query.filter_by(sku_id=sku.id).order_by(Produto.created_at.desc(), Produto.id.desc()).all()

    quantidade_total = sum(normalizar_quantidade(produto.quantidade) for produto in produtos)
    quantidade_prateleira = sum(
        normalizar_quantidade(produto.quantidade)
        for produto in produtos
        if produto_esta_enderecado(produto)
    )
    quantidade_recebida = quantidade_total - quantidade_prateleira

    resumo_localizacoes = defaultdict(lambda: {'localizacao': '', 'quantidade': 0.0, 'registros': 0, 'enderecado': False})
    for produto in produtos:
        localizacao = formatar_localizacao(produto)
        acumulado = resumo_localizacoes[localizacao]
        acumulado['localizacao'] = localizacao
        acumulado['quantidade'] += normalizar_quantidade(produto.quantidade)
        acumulado['registros'] += 1
        acumulado['enderecado'] = produto_esta_enderecado(produto)

    mapa_localizacoes = sorted(
        resumo_localizacoes.values(),
        key=lambda item: (
            0 if item['enderecado'] else 1,
            item['localizacao'].lower()
        )
    )

    return {
        'produtos_relacionados': produtos,
        'quantidade_total': quantidade_total,
        'quantidade_prateleira': quantidade_prateleira,
        'quantidade_recebida': quantidade_recebida,
        'total_registros': len(produtos),
        'mapa_localizacoes': mapa_localizacoes,
    }


def usuario_pode_delegar_para(gestor, responsavel):
    if not gestor or not responsavel or not responsavel.active or responsavel.is_admin:
        return False

    if not responsavel.can_execute_balanco:
        return False

    if gestor.is_admin:
        return True

    if responsavel.id == gestor.id:
        return gestor.can_execute_balanco

    return responsavel.gestor_id == gestor.id


def carregar_responsaveis_delegaveis(current_user):
    if not current_user or not current_user.can_assign_balanco:
        return []

    usuarios = User.query.filter(User.active.is_(True)).order_by(User.username.asc()).all()
    delegaveis = []
    vistos = set()

    for usuario in usuarios:
        if usuario.id in vistos:
            continue
        if usuario_pode_delegar_para(current_user, usuario):
            delegaveis.append(usuario)
            vistos.add(usuario.id)

    return delegaveis


def carregar_tarefas_recebidas(current_user):
    if not current_user:
        return []
    tarefas = TarefaBalanco.query.filter_by(responsavel_id=current_user.id).order_by(TarefaBalanco.created_at.desc()).all()
    return ordenar_tarefas(tarefas)


def carregar_tarefas_delegadas(current_user):
    if not current_user or not current_user.can_assign_balanco:
        return []
    tarefas = TarefaBalanco.query.filter_by(criado_por_id=current_user.id).order_by(TarefaBalanco.created_at.desc()).all()
    return ordenar_tarefas(tarefas)


def usuario_pode_concluir_tarefa(current_user, tarefa):
    if not current_user or not tarefa:
        return False
    if current_user.is_admin:
        return True
    if tarefa.responsavel_id == current_user.id:
        return True
    if current_user.can_validate_balanco:
        return True
    return current_user.can_assign_balanco and tarefa.criado_por_id == current_user.id


def parse_data(valor):
    texto = (valor or '').strip()
    if not texto:
        return None
    return datetime.strptime(texto, '%Y-%m-%d').date()


def criar_titulo_tarefa(sku, tipo_operacao, contexto):
    base = 'Endereçar SKU' if tipo_operacao == 'enderecamento' else 'Conferir SKU'
    if contexto:
        return f'{base} {sku.codigo} · {contexto}'
    return f'{base} {sku.codigo}'


def mover_quantidade_para_destino(sku, quantidade, corredor_destino, prateleira_destino):
    corredor_destino = normalizar_texto(corredor_destino)
    prateleira_destino = normalizar_texto(prateleira_destino)

    if not corredor_destino and not prateleira_destino:
        raise ValueError('Informe o corredor ou a prateleira de destino para concluir um endereçamento.')

    if quantidade <= 0:
        raise ValueError('A quantidade realizada precisa ser maior que zero para movimentar o estoque.')

    produtos_recebidos = [
        produto for produto in Produto.query.filter_by(sku_id=sku.id).order_by(Produto.created_at.asc(), Produto.id.asc()).all()
        if not produto_esta_enderecado(produto) and normalizar_quantidade(produto.quantidade) > 0
    ]

    saldo_disponivel = sum(normalizar_quantidade(produto.quantidade) for produto in produtos_recebidos)
    if saldo_disponivel + 1e-9 < quantidade:
        raise ValueError('Não há saldo suficiente em recebimento para endereçar essa quantidade.')

    restante = quantidade
    custo_total = 0.0
    validade_mais_proxima = None

    for produto in produtos_recebidos:
        disponivel = normalizar_quantidade(produto.quantidade)
        if disponivel <= 0:
            continue

        consumir = min(disponivel, restante)
        custo_total += consumir * float(produto.preco or 0)

        if produto.data_validade and (validade_mais_proxima is None or produto.data_validade < validade_mais_proxima):
            validade_mais_proxima = produto.data_validade

        nova_quantidade = round(disponivel - consumir, 6)
        produto.quantidade = nova_quantidade
        restante = round(restante - consumir, 6)

        if nova_quantidade <= 0.000001:
            db.session.delete(produto)

        if restante <= 0.000001:
            break

    preco_medio = round(custo_total / quantidade, 2) if quantidade else 0.0
    db.session.add(
        Produto(
            sku_id=sku.id,
            quantidade=quantidade,
            preco=preco_medio,
            corredor=corredor_destino,
            prateleira=prateleira_destino,
            data_validade=validade_mais_proxima,
        )
    )


@balanco.route('/gerenciar')
def gerenciar_balanco():
    current_user = get_current_user()
    leitura = (request.args.get('leitura') or '').strip()
    sku_id = request.args.get('sku_id', type=int)

    sku = None
    origem_leitura = None
    contexto_balanco = {
        'produtos_relacionados': [],
        'quantidade_total': 0.0,
        'quantidade_prateleira': 0.0,
        'quantidade_recebida': 0.0,
        'total_registros': 0,
        'mapa_localizacoes': [],
    }

    if sku_id or leitura:
        try:
            sku, origem_leitura = resolver_sku_para_balanco(sku_id=sku_id, leitura=leitura)
            contexto_balanco = montar_resumo_balanco(sku)
            if not leitura and sku:
                leitura = sku.codigo
        except ValueError as exc:
            flash(str(exc), 'warning')
        except LookupError as exc:
            flash(str(exc), 'danger')

    minhas_tarefas = carregar_tarefas_recebidas(current_user)
    tarefas_delegadas = carregar_tarefas_delegadas(current_user)
    responsaveis_delegaveis = carregar_responsaveis_delegaveis(current_user)

    return render_template(
        'gerenciar_balanco.html',
        leitura=leitura,
        sku=sku,
        origem_leitura=origem_leitura,
        minhas_tarefas=minhas_tarefas,
        tarefas_delegadas=tarefas_delegadas,
        responsaveis_delegaveis=responsaveis_delegaveis,
        tipos_operacao=TIPOS_OPERACAO_BALANCO,
        total_tarefas_pendentes=sum(1 for tarefa in minhas_tarefas if tarefa.is_open),
        total_tarefas_delegadas=sum(1 for tarefa in tarefas_delegadas if tarefa.is_open),
        **contexto_balanco,
    )


@balanco.route('/tarefas/cadastrar', methods=['POST'])
@functional_permission_required('can_assign_balanco', 'Seu papel funcional não permite delegar balanços.')
def cadastrar_tarefa_balanco():
    current_user = get_current_user()
    sku_id = request.form.get('sku_id', type=int)
    responsavel_id = request.form.get('responsavel_id', type=int)
    tipo_operacao = (request.form.get('tipo_operacao') or 'conferencia').strip().lower()
    contexto = normalizar_texto(request.form.get('contexto'))
    titulo = normalizar_texto(request.form.get('titulo'))
    descricao = normalizar_texto(request.form.get('descricao'))
    corredor_destino = normalizar_texto(request.form.get('corredor_destino'))
    prateleira_destino = normalizar_texto(request.form.get('prateleira_destino'))

    sku = db.session.get(Sku, sku_id)
    responsavel = db.session.get(User, responsavel_id)

    if not sku:
        flash('Selecione um SKU válido para delegar o balanço.', 'warning')
        return construir_redirect_balanco()

    if tipo_operacao not in TIPOS_OPERACAO_BALANCO:
        flash('Tipo de operação inválido para a tarefa de balanço.', 'danger')
        return construir_redirect_balanco(sku.id)

    if not usuario_pode_delegar_para(current_user, responsavel):
        flash('Esse usuário não pode receber essa tarefa com base na hierarquia atual.', 'danger')
        return construir_redirect_balanco(sku.id)

    try:
        quantidade_esperada = parse_decimal_input(request.form.get('quantidade_esperada'))
        data_referencia = parse_data(request.form.get('data_referencia'))
    except ValueError as exc:
        flash(str(exc), 'danger')
        return construir_redirect_balanco(sku.id)

    if quantidade_esperada is None or quantidade_esperada <= 0:
        flash('A quantidade esperada precisa ser maior que zero.', 'warning')
        return construir_redirect_balanco(sku.id)

    if tipo_operacao == 'enderecamento' and not corredor_destino and not prateleira_destino:
        flash('Informe o destino físico quando a tarefa for de endereçamento.', 'warning')
        return construir_redirect_balanco(sku.id)

    try:
        db.session.add(
            TarefaBalanco(
                titulo=titulo or criar_titulo_tarefa(sku, tipo_operacao, contexto),
                descricao=descricao,
                contexto=contexto,
                tipo_operacao=tipo_operacao,
                status='pendente',
                data_referencia=data_referencia,
                quantidade_esperada=quantidade_esperada,
                sku_id=sku.id,
                responsavel_id=responsavel.id,
                criado_por_id=current_user.id,
                corredor_destino=corredor_destino,
                prateleira_destino=prateleira_destino,
            )
        )
        db.session.commit()
        flash('Tarefa de balanço delegada com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao delegar tarefa de balanço: {exc}', 'danger')

    return construir_redirect_balanco(sku.id)


@balanco.route('/tarefas/<int:id>/concluir', methods=['POST'])
def concluir_tarefa_balanco(id):
    tarefa = db.session.get(TarefaBalanco, id)
    if not tarefa:
        flash('Tarefa de balanço não encontrada.', 'danger')
        return construir_redirect_balanco()

    current_user = get_current_user()
    if not usuario_pode_concluir_tarefa(current_user, tarefa):
        flash('Você não tem permissão para concluir essa tarefa.', 'danger')
        return construir_redirect_balanco(tarefa.sku_id)

    if not tarefa.is_open:
        flash('Essa tarefa já foi finalizada.', 'warning')
        return construir_redirect_balanco(tarefa.sku_id)

    try:
        quantidade_realizada = parse_decimal_input(request.form.get('quantidade_realizada'))
    except ValueError as exc:
        flash(str(exc), 'danger')
        return construir_redirect_balanco(tarefa.sku_id)

    if quantidade_realizada is None:
        quantidade_realizada = tarefa.quantidade_esperada

    if quantidade_realizada < 0:
        flash('A quantidade realizada não pode ser negativa.', 'warning')
        return construir_redirect_balanco(tarefa.sku_id)

    observacoes = normalizar_texto(request.form.get('observacoes_execucao'))
    corredor_destino = normalizar_texto(request.form.get('corredor_destino')) or tarefa.corredor_destino
    prateleira_destino = normalizar_texto(request.form.get('prateleira_destino')) or tarefa.prateleira_destino

    try:
        if tarefa.tipo_operacao == 'enderecamento':
            mover_quantidade_para_destino(tarefa.sku, quantidade_realizada, corredor_destino, prateleira_destino)
            tarefa.corredor_destino = corredor_destino
            tarefa.prateleira_destino = prateleira_destino

        tarefa.quantidade_realizada = quantidade_realizada
        tarefa.observacoes_execucao = observacoes
        tarefa.status = 'concluido'
        tarefa.concluido_em = datetime.utcnow()
        db.session.commit()
        flash('Tarefa concluída com sucesso.', 'success')
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), 'danger')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao concluir tarefa: {exc}', 'danger')

    return construir_redirect_balanco(tarefa.sku_id)


@balanco.route('/tarefas/<int:id>/cancelar', methods=['POST'])
@functional_permission_required('can_assign_balanco', 'Seu papel funcional não permite cancelar tarefas de balanço.')
def cancelar_tarefa_balanco(id):
    tarefa = db.session.get(TarefaBalanco, id)
    if not tarefa:
        flash('Tarefa de balanço não encontrada.', 'danger')
        return construir_redirect_balanco()

    current_user = get_current_user()
    if not current_user.is_admin and tarefa.criado_por_id != current_user.id:
        flash('Somente quem delegou a tarefa pode cancelá-la.', 'danger')
        return construir_redirect_balanco(tarefa.sku_id)

    if not tarefa.is_open:
        flash('A tarefa já foi finalizada e não pode ser cancelada.', 'warning')
        return construir_redirect_balanco(tarefa.sku_id)

    try:
        tarefa.status = 'cancelado'
        tarefa.observacoes_execucao = normalizar_texto(request.form.get('observacoes_execucao')) or tarefa.observacoes_execucao
        db.session.commit()
        flash('Tarefa cancelada com sucesso.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Erro ao cancelar tarefa: {exc}', 'danger')

    return construir_redirect_balanco(tarefa.sku_id)