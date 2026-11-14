from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import RAIZ

ALVOS = ["hookshot.py", "testes"]


def _ferramenta(nome: str) -> str:
    vizinha = Path(sys.executable).with_name(nome)
    achada = str(vizinha) if vizinha.is_file() else shutil.which(nome)
    if not achada:
        pytest.skip(f"sem o {nome} neste ambiente")
    return achada


def test_o_ruff_fecha_limpo() -> None:
    feito = subprocess.run([_ferramenta("ruff"), "check", *ALVOS], cwd=RAIZ,
                           capture_output=True, text=True, check=False)
    assert feito.returncode == 0, feito.stdout


def test_o_mypy_fecha_limpo() -> None:
    ambiente = {**os.environ, "MYPYPATH": "testes"}
    feito = subprocess.run([_ferramenta("mypy"), *ALVOS], cwd=RAIZ, env=ambiente,
                           capture_output=True, text=True, check=False)
    assert feito.returncode == 0, feito.stdout
