"""
Local dev CLI utilities (reseed, seed state).

Autocompletion:
  python cli.py --install-completion
"""

from __future__ import annotations

import os
import sys

import typer


SRC_DIR = os.path.join(os.path.dirname(__file__), "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

import database  # noqa: E402
import models  # noqa: E402
from seed_data import seed_database  # noqa: E402


app = typer.Typer(no_args_is_help=True, add_completion=True)


@app.command("seed")
def seed() -> None:
    """Run auto-seed (same as on app startup)."""
    with database.SessionLocal() as db:
        seed_database(db)
    typer.echo("OK")


@app.command("reseed-tests")
def reseed_tests() -> None:
    """Force reseed tests from backend/tests/*.txt."""
    os.environ["FORCE_RESEED_TESTS"] = "1"
    with database.SessionLocal() as db:
        seed_database(db)
    typer.echo("OK")


@app.command("reseed-materials")
def reseed_materials() -> None:
    """Force reseed materials from backend/materials/*.txt."""
    os.environ["FORCE_RESEED_MATERIALS"] = "1"
    with database.SessionLocal() as db:
        seed_database(db)
    typer.echo("OK")


@app.command("show-seed-state")
def show_seed_state() -> None:
    """Print current seed_state key/value pairs."""
    with database.SessionLocal() as db:
        rows = db.query(models.SeedState).order_by(models.SeedState.key.asc()).all()
        for r in rows:
            typer.echo(f"{r.key}={r.value}")


if __name__ == "__main__":
    app()

