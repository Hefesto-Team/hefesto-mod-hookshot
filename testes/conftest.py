from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


@pytest.fixture()
def lar(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    casa = tmp_path / "casa"
    casa.mkdir()
    monkeypatch.setenv("HOME", str(casa))
    for nome in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME"):
        monkeypatch.delenv(nome, raising=False)
    return casa


def jogo_compilado(pasta: Path, *, com_lancador: bool = True) -> Path:
    (pasta / "bin").mkdir(parents=True, exist_ok=True)
    binario = pasta / "bin" / "hookshot"
    binario.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    binario.chmod(0o755)
    if com_lancador:
        lancador = pasta / "hookshot"
        lancador.write_text("#!/bin/sh\nexec \"$(dirname \"$0\")/bin/hookshot\" \"$@\"\n",
                            encoding="utf-8")
        lancador.chmod(0o755)
    return pasta
