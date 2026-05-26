from datetime import date

from app import create_app
from app.models import (
    Departamento, Familia, Marca, Obra, Patrimonio,
    PerfilFuncional, Produto, Sku, Tipo, User, db,
)

ADMIN_EMAIL = 'admin@estoque.com'
ADMIN_PASSWORD = 'Estoque32$'
ADMIN_USERNAME = 'Administrador'


def get_or_create(model, defaults=None, **kwargs):
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = dict(kwargs)
    if defaults:
        params.update(defaults)
    instance = model(**params)
    db.session.add(instance)
    return instance, True


def seed_all():
    app = create_app()
    with app.app_context():
        print('=== Seed iniciado ===')

        # ── Admin ─────────────────────────────────────────────────────────────
        admin, _ = get_or_create(
            User, email=ADMIN_EMAIL,
            defaults=dict(
                username=ADMIN_USERNAME,
                classe='admin',
                active=True,
                first_login_completed=True,
            )
        )
        admin.username = ADMIN_USERNAME
        admin.classe = 'admin'
        admin.active = True
        admin.first_login_completed = True
        admin.set_password(ADMIN_PASSWORD)
        print(f'Admin: {ADMIN_EMAIL}  senha: {ADMIN_PASSWORD}')

        db.session.flush()

        # ── Departamentos ─────────────────────────────────────────────────────
        dept_ti, _      = get_or_create(Departamento, nome='TI')
        dept_almox, _   = get_or_create(Departamento, nome='Almoxarifado')
        dept_logist, _  = get_or_create(Departamento, nome='Logística')
        db.session.flush()
        print('Departamentos: TI, Almoxarifado, Logística')

        # ── Obras ─────────────────────────────────────────────────────────────
        obra_sede, _  = get_or_create(Obra, nome='Obra Sede')
        get_or_create(Obra, nome='Obra Filial Norte')
        db.session.flush()
        print('Obras: Obra Sede, Obra Filial Norte')

        # ── Perfis Funcionais ─────────────────────────────────────────────────
        perfil_gestor, _ = get_or_create(
            PerfilFuncional, nome='Gestor de Balanço',
            defaults=dict(
                descricao='Distribui e acompanha as tarefas de balanço da equipe.',
                nivel_hierarquico=3,
                pode_atribuir_balanco=True,
                pode_executar_balanco=False,
                pode_validar_balanco=False,
            )
        )
        perfil_operador, _ = get_or_create(
            PerfilFuncional, nome='Operador de Balanço',
            defaults=dict(
                descricao='Executa as conferências e endereçamentos do estoque.',
                nivel_hierarquico=1,
                pode_atribuir_balanco=False,
                pode_executar_balanco=True,
                pode_validar_balanco=False,
            )
        )
        get_or_create(
            PerfilFuncional, nome='Supervisor',
            defaults=dict(
                descricao='Delega, executa e valida qualquer operação de balanço.',
                nivel_hierarquico=5,
                pode_atribuir_balanco=True,
                pode_executar_balanco=True,
                pode_validar_balanco=True,
            )
        )
        db.session.flush()
        print('Perfis: Gestor de Balanço, Operador de Balanço, Supervisor')

        # ── Marcas ────────────────────────────────────────────────────────────
        marca_dell, _   = get_or_create(Marca, nome='Dell')
        marca_hp, _     = get_or_create(Marca, nome='HP')
        marca_bosch, _  = get_or_create(Marca, nome='Bosch')
        db.session.flush()
        print('Marcas: Dell, HP, Bosch')

        # ── Famílias e Tipos ──────────────────────────────────────────────────
        fam_eletro, _   = get_or_create(Familia, nome='Eletrônicos')
        fam_ferramentas, _ = get_or_create(Familia, nome='Ferramentas')
        db.session.flush()

        tipo_notebooks, _   = get_or_create(Tipo, nome='Notebooks',  defaults=dict(familia_id=fam_eletro.id))
        tipo_monitores, _   = get_or_create(Tipo, nome='Monitores',  defaults=dict(familia_id=fam_eletro.id))
        tipo_manuais, _     = get_or_create(Tipo, nome='Ferramentas Manuais', defaults=dict(familia_id=fam_ferramentas.id))
        db.session.flush()
        print('Famílias/Tipos: Eletrônicos (Notebooks, Monitores), Ferramentas (Ferramentas Manuais)')

        # ── SKUs ──────────────────────────────────────────────────────────────
        sku_notebook, _ = get_or_create(
            Sku, codigo='DELL-NB-001',
            defaults=dict(
                nome='Notebook Dell Inspiron 15',
                familia_id=fam_eletro.id,
                tipo_id=tipo_notebooks.id,
                marca_id=marca_dell.id,
            )
        )
        sku_monitor, _ = get_or_create(
            Sku, codigo='HP-MON-001',
            defaults=dict(
                nome='Monitor HP 24"',
                familia_id=fam_eletro.id,
                tipo_id=tipo_monitores.id,
                marca_id=marca_hp.id,
            )
        )
        sku_furadeira, _ = get_or_create(
            Sku, codigo='BOSCH-FUR-001',
            defaults=dict(
                nome='Furadeira Bosch Professional 650W',
                familia_id=fam_ferramentas.id,
                tipo_id=tipo_manuais.id,
                marca_id=marca_bosch.id,
            )
        )
        db.session.flush()
        print('SKUs: DELL-NB-001, HP-MON-001, BOSCH-FUR-001')

        # ── Produtos ──────────────────────────────────────────────────────────
        if not Produto.query.filter_by(sku_id=sku_notebook.id).first():
            db.session.add(Produto(
                sku_id=sku_notebook.id, quantidade=5.0,
                corredor='A', prateleira='01',
                preco=3500.00, data_validade=None, ativo=True,
            ))
        if not Produto.query.filter_by(sku_id=sku_monitor.id).first():
            db.session.add(Produto(
                sku_id=sku_monitor.id, quantidade=10.0,
                corredor='B', prateleira='02',
                preco=850.00, data_validade=None, ativo=True,
            ))
        if not Produto.query.filter_by(sku_id=sku_furadeira.id).first():
            db.session.add(Produto(
                sku_id=sku_furadeira.id, quantidade=3.0,
                corredor=None, prateleira=None,
                preco=450.00, data_validade=None, ativo=True,
            ))
        db.session.flush()
        print('Produtos: 5x Notebook A-01, 10x Monitor B-02, 3x Furadeira (recebimento)')

        # ── Usuários ──────────────────────────────────────────────────────────
        # Vitor – delega balanço (Gestor de Balanço)
        vitor, _ = get_or_create(User, email='vitor@estoque.com',
            defaults=dict(username='Vitor', active=True, first_login_completed=True))
        vitor.username = 'Vitor'
        vitor.classe = 'user'
        vitor.active = True
        vitor.first_login_completed = True
        vitor.cargo = 'Analista de TI'
        vitor.perfil_funcional_id = perfil_gestor.id
        vitor.departamento_id = dept_ti.id
        vitor.obra_id = obra_sede.id
        vitor.set_password('Vitor123@')
        db.session.flush()

        # Daniel – executa balanço (Operador), subordinado do Vitor
        daniel, _ = get_or_create(User, email='daniel@estoque.com',
            defaults=dict(username='Daniel', active=True, first_login_completed=True))
        daniel.username = 'Daniel'
        daniel.classe = 'user'
        daniel.active = True
        daniel.first_login_completed = True
        daniel.cargo = 'Auxiliar de Almoxarifado'
        daniel.perfil_funcional_id = perfil_operador.id
        daniel.departamento_id = dept_almox.id
        daniel.obra_id = obra_sede.id
        daniel.gestor_id = vitor.id
        daniel.set_password('Daniel123@')
        db.session.flush()

        # Silva – faz tudo (admin)
        silva, _ = get_or_create(User, email='silva@estoque.com',
            defaults=dict(username='Silva', active=True, first_login_completed=True))
        silva.username = 'Silva'
        silva.classe = 'admin'
        silva.active = True
        silva.first_login_completed = True
        silva.cargo = 'Supervisor de Estoque'
        silva.departamento_id = dept_logist.id
        silva.obra_id = obra_sede.id
        silva.set_password('Silva123@')
        db.session.flush()

        print('Usuários:')
        print('  vitor@estoque.com   | Vitor123@ | Gestor de Balanço (delega)')
        print('  daniel@estoque.com  | Daniel123@ | Operador de Balanço (executa)')
        print('  silva@estoque.com   | Silva123@  | Admin (faz tudo)')

        # ── Patrimônios ───────────────────────────────────────────────────────
        if not Patrimonio.query.filter_by(codigo_patrimonio='TI-00001').first():
            db.session.add(Patrimonio(
                codigo_patrimonio='TI-00001',
                numero_serie='SN-DELL-001',
                sku_id=sku_notebook.id,
                user_id=vitor.id,
                status='Em Uso',
                data_compra=date(2024, 3, 10),
                fim_garantia=date(2027, 3, 10),
                valor_compra=3500.00,
                observacoes='Notebook do Vitor – TI',
            ))
        if not Patrimonio.query.filter_by(codigo_patrimonio='TI-00002').first():
            db.session.add(Patrimonio(
                codigo_patrimonio='TI-00002',
                numero_serie='SN-HP-001',
                sku_id=sku_monitor.id,
                user_id=None,
                status='Disponível',
                data_compra=date(2024, 1, 15),
                fim_garantia=date(2026, 1, 15),
                valor_compra=850.00,
                observacoes='Monitor HP reserva',
            ))
        if not Patrimonio.query.filter_by(codigo_patrimonio='ALM-00001').first():
            db.session.add(Patrimonio(
                codigo_patrimonio='ALM-00001',
                numero_serie='SN-BOSCH-001',
                sku_id=sku_furadeira.id,
                user_id=None,
                status='Disponível',
                data_compra=date(2023, 8, 5),
                fim_garantia=date(2025, 8, 5),
                valor_compra=450.00,
                observacoes='Furadeira almoxarifado',
            ))
        db.session.flush()
        print('Patrimônios: TI-00001 (Notebook/Vitor), TI-00002 (Monitor), ALM-00001 (Furadeira)')

        db.session.commit()
        print('=== Seed concluído com sucesso ===')


if __name__ == '__main__':
    seed_all()
