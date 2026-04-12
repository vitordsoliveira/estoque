from app import create_app
from app.models import User, db


ADMIN_EMAIL = 'admin@estoque.com'
ADMIN_PASSWORD = 'Estoque32$'
ADMIN_USERNAME = 'Administrador'


def seed_admin_user():
    app = create_app()

    with app.app_context():
        admin = User.query.filter_by(email=ADMIN_EMAIL).first()

        if admin is None:
            admin = User(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                classe='admin',
                active=True,
                first_login_completed=True
            )
            admin.set_password(ADMIN_PASSWORD)
            db.session.add(admin)
            action = 'criado'
        else:
            admin.username = ADMIN_USERNAME
            admin.classe = 'admin'
            admin.active = True
            admin.first_login_completed = True
            admin.set_password(ADMIN_PASSWORD)
            action = 'atualizado'

        db.session.commit()
        print(f'Usuário admin {action} com sucesso: {ADMIN_EMAIL}')


if __name__ == '__main__':
    seed_admin_user()