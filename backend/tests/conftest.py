import pytest


@pytest.fixture(autouse=True)
def _no_irsa_wait(monkeypatch):
    """Les nouvelles tentatives IRSA n'attendent pas pendant les tests."""
    from app.core import search
    monkeypatch.setattr(search, "SIA_BACKOFF_S", (0.0, 0.0))


@pytest.fixture(autouse=True)
def _no_auto_update(monkeypatch):
    """Pas de mise à jour automatique en arrière-plan pendant les tests (sauf tests dédiés)."""
    from app.core import config
    monkeypatch.setattr(config, "AUTO_UPDATE", False)
