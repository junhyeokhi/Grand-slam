from flask_migrate import Migrate

from flask import Flask, render_template
import config  # config.py 임포트
from constants import KBO_TEAMS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    # 블루프린트 등록
    from .views import main_views
    app.register_blueprint(main_views.bp)

    # auth_views 등록
    from .views import auth_views
    app.register_blueprint(auth_views.bp)

    # 모든 HTML 파일에서 KBO_TEAMS 불러오기
    @app.context_processor
    def inject_teams():
        return dict(teams=KBO_TEAMS)

    return app
