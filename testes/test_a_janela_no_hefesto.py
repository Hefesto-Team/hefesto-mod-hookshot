from __future__ import annotations

import json
import re
from typing import Any

import pytest
from conftest import RAIZ
from porta_de_mentira import MESA_MISTA

import janela

pytest.importorskip("hefesto_dualsense4unix")

SHA_OUTRO = "0" * 64
CASA = "/home/quem"
COMPILADO = {"casa": CASA, "pasta": f"{CASA}/Games/Hookshot", "jogo": "compilado",
             "appimage": {"caminho": f"{CASA}/Applications/Hookshot-v2.1.0-x86_64.AppImage",
                          "sha256": janela.SHA_DO_APPIMAGE_CONHECIDO}}


def _bruto() -> dict[str, Any]:
    carga: dict[str, Any] = json.loads((RAIZ / "hefesto-mod.json").read_text(encoding="utf-8"))
    return carga


def _validado(retrato: dict[str, Any], escolhas: dict[str, Any] | None = None) -> dict[str, Any]:
    from hefesto_dualsense4unix.mods.porta import estado_dos_acessorios

    validado: dict[str, Any] = estado_dos_acessorios(
        "hookshot", janela.estado(MESA_MISTA, escolhas or {}, retrato))
    return validado


def test_as_abas_sao_jogo_controles_e_dump() -> None:
    from hefesto_dualsense4unix.mods.manifesto import ler_manifesto

    m = ler_manifesto(RAIZ)
    assert [o.grupo for o in m.opcoes] == ["Jogo"]
    assert m.aparelhos_controles is not None and m.aparelhos_controles.grupo == "Controles"
    assert m.pagina is not None and (m.pagina.rotulo, m.pagina.arquivo) == (
        "Dump", "pagina/dump.html")
    assert m.agora == ["conexoes", "linhas", "aparelhos"]
    assert m.versao == "1.2.0"


def _rotulos_da_janela() -> list[str]:
    estado = janela.estado(MESA_MISTA, {}, COMPILADO)
    rotulos: list[str] = [o["rotulo"] for o in _bruto()["opcoes"]]  # (noqa-acento): chave
    rotulos += [c["rotulo"] for c in estado["aparelhos"][0]["controles"]]
    rotulos += [o["rotulo"] for c in estado["aparelhos"][0]["controles"]
                for o in c.get("opcoes", [])]
    rotulos += [a["rotulo"] for a in _bruto()["acoes"]]
    rotulos += [c["tipo"] for c in estado["conexoes"]] + [ln["rotulo"] for ln in estado["linhas"]]
    rotulos += re.findall(r"<span>([^<]+)</span>",
                          (RAIZ / "pagina" / "dump.html").read_text(encoding="utf-8"))
    return rotulos


@pytest.mark.parametrize("rotulo", _rotulos_da_janela())
def test_todo_rotulo_tem_uma_ou_duas_palavras_e_comeca_maiusculo(rotulo: str) -> None:
    assert 1 <= len(rotulo.split()) <= 2, rotulo
    assert rotulo[:1].isupper(), rotulo


def test_a_explicacao_mora_na_dica() -> None:
    estado = janela.estado(MESA_MISTA, {}, COMPILADO)
    assert all(c.get("dica") for c in estado["aparelhos"][0]["controles"])
    assert all(c["motivo"] for c in estado["conexoes"])
    assert all(len(o.get("dica", "")) <= 120 for o in _bruto()["opcoes"])  # (noqa-acento)


@pytest.mark.parametrize("retrato, hookshot, jogo", [
    ({}, "desligado", "desligado"),
    (COMPILADO, "ligado", "ligado"),
    ({**COMPILADO, "appimage": {"caminho": "/a/b.AppImage", "sha256": SHA_OUTRO}}, "falhou",
     "ligado"),
    ({**COMPILADO, "appimage": None, "jogo": "danificado"}, "desligado", "falhou"),
    ({**COMPILADO, "pasta": None, "jogo": "falta"}, "ligado", "desligado"),
])
def test_o_hookshot_e_o_jogo_tem_estado_em_cor(retrato: dict[str, Any], hookshot: str,
                                              jogo: str) -> None:
    from hefesto_dualsense4unix.interface.desenho_da_experimental import (
        COR_DO_ESTADO,
        agora_html,
        estado_html,
    )

    validado = _validado(retrato)
    assert [(c["id"], c["estado"]) for c in validado["conexoes"]] == [
        ("hookshot", hookshot), ("jogo", jogo)]
    html = agora_html(["conexoes", "linhas", "aparelhos"], validado)
    for c in validado["conexoes"]:
        linha = re.search(rf'<div class="cx-linha" data-dica="[^"]+">.*?{c["tipo"]}</span>'
                          rf"(<span class=\"est[^<]+<i></i>[^<]+</span>)", html)
        assert linha is not None, c["tipo"]
        assert linha.group(1) == estado_html(c["estado"])
        assert f"c-{COR_DO_ESTADO[c['estado']]}" in html


def test_as_linhas_mostram_a_pasta_curta_e_o_sha() -> None:
    linhas = {ln["rotulo"]: ln["valor"] for ln in _validado(COMPILADO)["linhas"]}
    assert linhas == {"Pasta": "~/Games/Hookshot",
                      "AppImage": "Hookshot-v2.1.0-x86_64.AppImage",
                      "SHA-256": "c0b2e958ae00dc56…"}
    assert all(len(v) <= 40 for v in linhas.values())


def test_os_cartoes_do_hefesto_tem_os_quatro_controles_pela_cor() -> None:
    from hefesto_dualsense4unix.interface.desenho_da_experimental import (
        controles_dos_aparelhos_html,
    )

    validado = _validado(COMPILADO, {janela.ident(MESA_MISTA[2]["uniq"]): {"luz": "goron"}})
    html = controles_dos_aparelhos_html("hookshot", validado, frozenset(), False)
    for nome in ("Starlight Blue", "White", "Cosmic Red", "Galactic Purple"):
        assert html.count(nome) >= 1, nome
    for rotulo in ("Luz", "Gatilhos", "Vibração", "Leve", "Firme", "Jogo", "Forte"):
        assert rotulo in html, rotulo
    assert html.count("#c8402a") >= 4
    assert not re.search(r"\bP[1-4]\b", html)


def test_a_pagina_do_dump_cabe_sem_rolagem_e_nao_sai_da_caixa() -> None:
    texto = (RAIZ / "pagina" / "dump.html").read_text(encoding="utf-8")
    assert "overflow:hidden" in texto
    assert not re.search(r"(src|href)=\"https?:", texto)
    assert janela.SHA_DO_APPIMAGE_CONHECIDO in texto
    assert "e0f3ccfa" in texto and "v131072" in texto
