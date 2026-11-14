from __future__ import annotations

import json

from conftest import RAIZ

MANIFESTO = json.loads((RAIZ / "hefesto-mod.json").read_text(encoding="utf-8"))
PERFIL = json.loads((RAIZ / "perfis" / "hookshot.json").read_text(encoding="utf-8"))


def test_o_manifesto_declara_o_lancador_com_leitor_e_preparo() -> None:
    assert MANIFESTO["id"] == "hookshot"
    assert MANIFESTO["licenca"] == "GPL-3.0-or-later"
    assert MANIFESTO["tipos"] == ["lancador", "processo"]
    assert MANIFESTO["processo"]["executar"] == ["python3", "-I", "servidor.py"]
    assert MANIFESTO["permissoes"][0] == "lancador"
    assert MANIFESTO["preparar"] == ["bash", "install.sh", "--yes"]
    lancador = MANIFESTO["lancador"]
    assert lancador["comandos"] == ["hefesto-hookshot"]
    assert lancador["janelas"] == ["hookshot"]
    assert lancador["leitor"]["executar"][:3] == ["python3", "-I", "hookshot.py"]
    assert len(MANIFESTO["aviso"]) <= 400


def test_o_aviso_e_o_mesmo_no_readme() -> None:
    assert MANIFESTO["aviso"] in (RAIZ / "README.md").read_text(encoding="utf-8")


def test_o_perfil_reconhece_o_jogo_pela_janela_e_pelo_processo() -> None:
    assert PERFIL["match"]["type"] == "criteria"
    assert PERFIL["match"]["window_class"] == ["hookshot"]
    assert PERFIL["match"]["process_name"] == ["hookshot"]


def test_o_perfil_nao_separa_controle_modo_nem_conexao() -> None:
    assert "controllers" not in PERFIL
    assert "mode" not in PERFIL
    assert PERFIL["controles_modo"] == "extensao:hookshot"
    assert "movimento" not in PERFIL
    assert PERFIL["rumble"]["passthrough"] is True
    assert PERFIL["leds"]["auto_player_colors"] is True
    assert PERFIL["leds"]["player_leds"] == [False] * 5
