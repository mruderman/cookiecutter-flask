# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import logging
import sys

from flask import Flask, render_template

from app import commands
from app.jobs import reminder_jobs
from app.extensions import (
    bcrypt,
    cache,
    csrf_protect,
    db,
    debug_toolbar,
    flask_static_digest,
    limiter,
    login_manager,
    migrate,
    scheduler,
)
from app.api import auth as api_auth, reminders as api_reminders
from app.ui import public, user, reminders


def create_app(config_object="app.settings"):
    """Create application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__.split(".")[0])
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)
    register_jobs(app)
    configure_logger(app)
    return app


def register_extensions(app):
    """Register Flask extensions."""
    bcrypt.init_app(app)
    cache.init_app(app)
    db.init_app(app)
    csrf_protect.init_app(app)
    login_manager.init_app(app)
    debug_toolbar.init_app(app)
    migrate.init_app(app, db)
    flask_static_digest.init_app(app)
    limiter.init_app(app)
    scheduler.init_app(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    # UI blueprints
    app.register_blueprint(public.blueprint)
    app.register_blueprint(user.blueprint)
    app.register_blueprint(reminders.blueprint)

    # API blueprints
    app.register_blueprint(api_auth.blueprint)
    app.register_blueprint(api_reminders.blueprint)
    return None


def register_errorhandlers(app):
    """Register error handlers."""

    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, "code", 500)
        return render_template(f"{error_code}.html"), error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""
    from app.models import User

    def shell_context():
        """Shell context objects."""
        return {"db": db, "User": User}

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)


def register_jobs(app):
    """Register scheduled jobs."""
    with app.app_context():
        reminder_jobs.register_jobs()


def configure_logger(app):
    """Configure loggers."""
    handler = logging.StreamHandler(sys.stdout)
    if not app.logger.handlers:
        app.logger.addHandler(handler)
