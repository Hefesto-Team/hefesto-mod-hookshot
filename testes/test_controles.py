from __future__ import annotations

from pathlib import Path

import pytest
from conftest import jogo_compilado

import hookshot

ORIGINAL = (
    "language=pt\n"
    "rumble_strength=100\n"
    "pad_a=1\n"
    "pad_b=0\n"
    "pad_zl=15\n"
    "motion_controls=1\n"
)


@pytest.fixture()
def pasta(lar: Path) -> Path:
    return jogo_compilado(lar / "Games" / "Hookshot")


def _valores(ini: Path) -> dict[str, str]:
    pares = (linha.split("=", 1) for linha in ini.read_text(encoding="utf-8").splitlines()
             if "=" in linha)
    return {chave.strip(): valor.strip() for chave, valor in pares}


def test_cada_botao_do_hookshot_tem_uma_posicao_so_do_sdl() -> None:
    botoes = {"a", "b", "x", "y", "l", "r", "zl", "zr", "plus", "minus", "ls", "rs",
              "left", "up", "right", "down"}
    assert set(hookshot.POSICAO_DO_BOTAO) == botoes
    posicoes = list(hookshot.POSICAO_DO_BOTAO.values())
    assert len(set(posicoes)) == len(posicoes)
    assert all(0 <= p <= 16 for p in posicoes)
    assert 5 not in posicoes


def test_a_cruz_e_o_a_e_o_direcional_segue_a_ordem_do_sdl() -> None:
    p = hookshot.POSICAO_DO_BOTAO
    assert (p["a"], p["b"], p["x"], p["y"]) == (0, 1, 2, 3)
    assert (p["up"], p["down"], p["left"], p["right"]) == (11, 12, 13, 14)
    assert (p["l"], p["r"], p["zl"], p["zr"]) == (9, 10, 15, 16)
    assert (p["minus"], p["plus"], p["ls"], p["rs"]) == (4, 6, 7, 8)


def test_escreve_os_botoes_guarda_a_copia_e_nao_mexe_no_resto(pasta: Path) -> None:
    ini = pasta / hookshot.OPCOES
    ini.write_text(ORIGINAL, encoding="utf-8")
    assert hookshot.preparar_controles(pasta) == "escrito"
    valores = _valores(ini)
    assert {k: v for k, v in valores.items() if k.startswith("pad_")} == hookshot.mapa_desejado()
    assert valores["language"] == "pt"
    assert valores["rumble_strength"] == "100"
    assert valores["motion_controls"] == "1"
    assert hookshot.copia(pasta).read_text(encoding="utf-8") == ORIGINAL


def test_rodar_de_novo_nao_muda_nada(pasta: Path) -> None:
    ini = pasta / hookshot.OPCOES
    ini.write_text(ORIGINAL, encoding="utf-8")
    hookshot.preparar_controles(pasta)
    depois = ini.read_bytes()
    copia = hookshot.copia(pasta).read_bytes()
    registro = hookshot.registro(pasta).read_bytes()
    assert hookshot.preparar_controles(pasta) == "ja-preparado"
    assert hookshot.preparar_controles(pasta, forcar=True) == "igual"
    assert ini.read_bytes() == depois
    assert hookshot.copia(pasta).read_bytes() == copia
    assert hookshot.registro(pasta).read_bytes() == registro


def test_o_remapeamento_de_quem_joga_sobrevive_a_proxima_abertura(pasta: Path) -> None:
    ini = pasta / hookshot.OPCOES
    ini.write_text(ORIGINAL, encoding="utf-8")
    hookshot.preparar_controles(pasta)
    ini.write_text(ini.read_text(encoding="utf-8").replace("pad_a=0", "pad_a=3"),
                   encoding="utf-8")
    assert hookshot.preparar_controles(pasta) == "ja-preparado"
    assert _valores(ini)["pad_a"] == "3"


def test_a_copia_nunca_se_sobrescreve(pasta: Path) -> None:
    ini = pasta / hookshot.OPCOES
    ini.write_text(ORIGINAL, encoding="utf-8")
    hookshot.preparar_controles(pasta)
    hookshot.preparar_controles(pasta, forcar=True)
    assert hookshot.copia(pasta).read_text(encoding="utf-8") == ORIGINAL


def test_desfazer_devolve_o_arquivo_byte_a_byte(pasta: Path) -> None:
    ini = pasta / hookshot.OPCOES
    ini.write_text(ORIGINAL, encoding="utf-8")
    hookshot.preparar_controles(pasta)
    assert hookshot.desfazer_controles(pasta) == "desfeito"
    assert ini.read_text(encoding="utf-8") == ORIGINAL
    assert not hookshot.copia(pasta).exists()
    assert not hookshot.registro(pasta).exists()
    assert hookshot.desfazer_controles(pasta) == "nada"


def test_desfazer_guarda_o_que_quem_joga_mudou_depois(pasta: Path) -> None:
    ini = pasta / hookshot.OPCOES
    ini.write_text(ORIGINAL, encoding="utf-8")
    hookshot.preparar_controles(pasta)
    ini.write_text(ini.read_text(encoding="utf-8").replace("pad_x=2", "pad_x=9") + "fov=90\n",
                   encoding="utf-8")
    hookshot.desfazer_controles(pasta)
    valores = _valores(ini)
    assert valores["pad_x"] == "9"
    assert valores["pad_a"] == "1"
    assert valores["fov"] == "90"
    assert "pad_y" not in valores
    assert hookshot.copia(pasta).read_text(encoding="utf-8") == ORIGINAL


def test_sem_o_arquivo_ele_nasce_e_o_desfazer_o_tira(pasta: Path) -> None:
    ini = pasta / hookshot.OPCOES
    assert hookshot.preparar_controles(pasta) == "escrito"
    assert _valores(ini) == hookshot.mapa_desejado()
    assert not hookshot.copia(pasta).exists()
    hookshot.desfazer_controles(pasta)
    assert not ini.exists()


def test_sem_o_jogo_compilado_nada_se_escreve(lar: Path) -> None:
    pasta = lar / "Games" / "Hookshot"
    pasta.mkdir(parents=True)
    assert hookshot.preparar_controles(pasta) == "sem-jogo"
    assert list(pasta.iterdir()) == []
