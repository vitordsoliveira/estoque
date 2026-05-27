import logging
import re

logger = logging.getLogger('estoque.audit')


def _nome_usuario(user):
    if not user:
        return 'Anônimo'
    papel = 'Administrador' if user.is_admin else (user.nome_papel or 'sem papel')
    return f'{user.username} ({papel})'


def _parse_os(ua: str) -> str:
    if 'Windows NT 10.0' in ua or 'Windows NT 11.0' in ua:
        return 'Windows 10/11'
    if 'Windows NT 6.3' in ua:
        return 'Windows 8.1'
    if 'Windows NT 6.1' in ua:
        return 'Windows 7'
    if 'Mac OS X' in ua:
        return 'macOS'
    if 'Android' in ua:
        return 'Android'
    if 'iPhone' in ua or 'iPad' in ua:
        return 'iOS'
    if 'Linux' in ua:
        return 'Linux'
    return 'SO desconhecido'


def _parse_browser(ua: str) -> str:
    if m := re.search(r'Edg/(\d+)', ua):
        return f'Edge {m.group(1)}'
    if re.search(r'OPR/', ua):
        return 'Opera'
    if m := re.search(r'Chrome/(\d+)', ua):
        return f'Chrome {m.group(1)}'
    if m := re.search(r'Firefox/(\d+)', ua):
        return f'Firefox {m.group(1)}'
    if 'Safari/' in ua:
        return 'Safari'
    return 'Navegador desconhecido'



def _parse_cliente_parts():
    try:
        from flask import request as req
        ip = req.headers.get('X-Forwarded-For', req.remote_addr) or '?'
        ip = ip.split(',')[0].strip()
        ua = req.headers.get('User-Agent', '')
        return ip, _parse_os(ua), _parse_browser(ua)
    except RuntimeError:
        return None, None, None


def log(user, aba: str, acao: str, detalhes: str = ''):
    nome = _nome_usuario(user)
    ip, so, navegador = _parse_cliente_parts()
    cliente_str = f'{ip} | {so} | {navegador}' if ip else ''

    partes = [f'[AUDIT] {nome}', aba, acao]
    msg = ' | '.join(partes)
    if detalhes:
        msg += f' — {detalhes}'
    if cliente_str:
        msg += f'  [{cliente_str}]'
    logger.info(msg)

    try:
        from app.models import LogAudit, db
        papel = None
        usuario_nome = None
        if user:
            usuario_nome = user.username
            papel = 'Administrador' if user.is_admin else (user.nome_papel or None)
        entry = LogAudit(
            usuario=usuario_nome,
            papel=papel,
            ip=ip,
            so=so,
            navegador=navegador,
            aba=aba,
            acao=acao,
            detalhes=detalhes or None,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        pass
