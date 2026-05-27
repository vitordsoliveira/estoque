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


def _info_cliente() -> str:
    try:
        from flask import request as req
        ip = req.headers.get('X-Forwarded-For', req.remote_addr) or '?'
        ip = ip.split(',')[0].strip()   # proxy chains → pega o IP de origem
        ua = req.headers.get('User-Agent', '')
        so = _parse_os(ua)
        browser = _parse_browser(ua)
        return f'{ip} | {so} | {browser}'
    except RuntimeError:
        return ''


def log(user, aba: str, acao: str, detalhes: str = ''):
    nome = _nome_usuario(user)
    cliente = _info_cliente()
    partes = [f'[AUDIT] {nome}', aba, acao]
    msg = ' | '.join(partes)
    if detalhes:
        msg += f' — {detalhes}'
    if cliente:
        msg += f'  [{cliente}]'
    logger.info(msg)
