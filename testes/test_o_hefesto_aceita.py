from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import RAIZ, jogo_compilado

pytest.importorskip("hefesto_dualsense4unix")

MANIFESTO = json.loads((RAIZ / "hefesto-mod.json").read_text(encoding="utf-8"))
PERFIL = json.loads((RAIZ / "perfis" / "hookshot.json").read_text(encoding="utf-8"))


def test_o_hefesto_aceita_o_manifesto() -> None:
    from hefesto_dualsense4unix.mods.manifesto import ler_manifesto

    lido = ler_manifesto(RAIZ)
    assert lido.id == "hookshot"
    assert lido.api_aceita()


def test_o_hefesto_aceita_o_perfil_e_o_nome_vira_o_arquivo() -> None:
    from hefesto_dualsense4unix.profiles.schema import Profile
    from hefesto_dualsense4unix.profiles.slug import slugify

    perfil = Profile.model_validate(PERFIL)
    assert slugify(perfil.name) == "hookshot"


def test_o_hefesto_le_o_jogo_pelo_leitor_do_manifesto(lar: Path,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    from hefesto_dualsense4unix.integrations.censo_dos_lancadores import (
        lancador_da_modificacao,
        ler_por_processo,
    )

    pasta = jogo_compilado(lar / "Games" / "Hookshot")
    lancador = lancador_da_modificacao("hookshot", MANIFESTO["lancador"], RAIZ)
    assert lancador.leitor is not None
    biblioteca = ler_por_processo(lancador.leitor, bwrap=False)
    jogos = list(getattr(biblioteca, "jogos", []))
    assert len(jogos) == 1
    assert getattr(jogos[0], "caminho", None) == pasta
    assert getattr(jogos[0], "janela", "") == "hookshot"
