"""
API routes package
"""
from . import profiles
from . import tasks
from . import actions
from . import dashboard
from . import websocket

__all__ = ['profiles', 'tasks', 'actions', 'dashboard', 'websocket']
