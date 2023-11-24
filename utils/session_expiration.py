from flask import session
from datetime import timedelta

def session_expiration(app):
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=1)
    return app.permanent_session_lifetime