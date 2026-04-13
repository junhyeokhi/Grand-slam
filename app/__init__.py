from flask import Flask, render_template
from sqlalchemy import MetaData
import config  # config.py 임포트
from constants import KBO_TEAMS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

naming_convention = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(column_0_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}

db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
migrate = Migrate()

from . import models


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    app.secret_key = "key"

    # ORM 초기화
    db.init_app(app)
    migrate.init_app(app, db)


    # 블루프린트 등록
    from .views import main_views
    app.register_blueprint(main_views.bp)

    # auth_views 등록
    from .views import auth_views
    app.register_blueprint(auth_views.bp)

    # 티켓 페이지(구단 선택 → 리스트 페이지) 라우트 연결
    from .views import ticket_views
    app.register_blueprint(ticket_views.bp)

    # 모든 HTML 파일에서 KBO_TEAMS 불러오기
    @app.context_processor
    def inject_teams():
        return dict(teams=KBO_TEAMS)

    return app
