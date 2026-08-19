"""
Production entry point for hosting PharmaTrack's API.

This does NOT launch the desktop pywebview window - that only happens
when someone runs `python app.py` directly for local pharmacy use.
A real WSGI server (Waitress on Windows, Gunicorn on Linux) imports
the `app` object from here to serve it publicly.
"""
from app import app

if __name__ == '__main__':
    # Quick manual check only - real hosting should use a proper WSGI
    # server instead of this (see README "Hosting" section).
    app.run()