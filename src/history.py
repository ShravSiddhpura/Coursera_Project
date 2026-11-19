"""
ReelLore AI — History Store Alias / Bridge
===========================================
Re-exports history methods from src.history_store for backwards compatibility.
"""

from src.history_store import save_run, list_runs, load_run, delete_run

__all__ = ["save_run", "list_runs", "load_run", "delete_run"]
