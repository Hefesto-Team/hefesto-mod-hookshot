from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from porta_de_mentira import (
    AZUL,
    BRANCO,
    MESA_MISTA,
    ROXO,
    VERMELHO,
    PortaDeMentira,
    ate,
    rodar_com_a_porta,
)

import janela

NA_CENA: dict[str, Any] = {"perfil": "Hookshot", "jogo": None, "controles": [
    {"jogador": n, "perfil": "Hookshot", "jogo": None} for n in (1, 2, 3, 4)]}
FORA_DE_CENA: dict[str, Any] = {"perfil": "Padrão", "jogo": None, "controles": []}


def _cartao(estado: dict[str, Any], nome: str) -> dict[str, Any]:
    return next(a for a in estado["aparelhos"] if a["nome"] == nome)


def _valores(cartao: dict[str, Any]) -> dict[str, Any]:
    return {c["id"]: c["valor"] for c in cartao["controles"]}


def test_cada_controle_aparece_pela_cor_do_plastico(tmp_path: Path,
                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    async def corpo(porta: PortaDeMentira, _ext: Any) -> None:
        await ate(lambda: bool(porta.de("acessorios.estado")))

    porta = rodar_com_a_porta(tmp_path, monkeypatch, corpo)
    estado = porta.ultimo_estado()
    assert [a["nome"] for a in estado["aparelhos"]] == [
        "Starlight Blue", "White", "Cosmic Red", "Galactic Purple"]
    assert all(a["estado"] == "ligado" for a in estado["aparelhos"])
    assert all(_valores(a) == {"luz": None, "gatilhos": "leve", "vibracao": "jogo", "giro": True}
               for a in estado["aparelhos"])
    texto = json.dumps(estado, ensure_ascii=False)
    for proibido in ("P1", "P2", "P3", "P4", AZUL, BRANCO, VERMELHO, ROXO):
        assert proibido not in texto


def test_sem_a_cor_o_controle_e_dualsense_e_o_repetido_ganha_numero() -> None:
    nomes = janela.nomes([{"uniq": "u1", "jogador": 1}, {"uniq": "u2", "jogador": 2},
                          {"uniq": "u3", "jogador": None, "cor": "white"}])
    assert nomes == {"u1": "DualSense", "u2": "DualSense 2", "u3": "White"}


@pytest.mark.parametrize("uniq, cor", [(c["uniq"], c["cor"]) for c in MESA_MISTA])
def test_o_clique_na_luz_de_um_controle_so_muda_aquele(tmp_path: Path,
                                                       monkeypatch: pytest.MonkeyPatch,
                                                       uniq: str, cor: str) -> None:
    alvo = janela.ident(uniq)

    async def corpo(porta: PortaDeMentira, _ext: Any) -> None:
        await porta.evento("perfil.trocou", NA_CENA, "perfil.jogo")
        await porta.evento("extensao.acao", {"mod": "hookshot", "acao": "luz",
                                             "alvo": alvo, "valor": "zora"})
        await ate(lambda: bool(porta.de("luz.set")))
        await ate(lambda: _valores(_cartao(porta.ultimo_estado(), cor))["luz"] == "zora")

    porta = rodar_com_a_porta(tmp_path, monkeypatch, corpo, dados=tmp_path)
    assert porta.de("luz.set")[0] == {"uniq": uniq, "rgb": [0x2a, 0x6f, 0xd0], "ate_ms": 300000}
    estado = porta.ultimo_estado()
    assert [_valores(a)["luz"] for a in estado["aparelhos"] if a["nome"] != cor] == [None] * 3
    gravado = json.loads((tmp_path / "controles.json").read_text(encoding="utf-8"))
    assert gravado == {alvo: {"luz": "zora", "gatilhos": "leve", "vibracao": "jogo", "giro": True}}


def test_o_segundo_clique_na_mesma_luz_devolve_a_do_hefesto(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    alvo = janela.ident(BRANCO)

    async def corpo(porta: PortaDeMentira, _ext: Any) -> None:
        await porta.evento("perfil.trocou", NA_CENA, "perfil.jogo")
        for _ in range(2):
            await porta.evento("extensao.acao", {"mod": "hookshot", "acao": "luz",
                                                 "alvo": alvo, "valor": "goron"})
        await ate(lambda: len(porta.de("luz.set")) == 2)

    porta = rodar_com_a_porta(tmp_path, monkeypatch, corpo, dados=tmp_path)
    assert [p["rgb"] for p in porta.de("luz.set")] == [[0xc8, 0x40, 0x2a], [0, 0, 0]]
    assert _valores(_cartao(porta.ultimo_estado(), "White"))["luz"] is None


def test_a_luz_e_o_gatilho_so_valem_com_o_jogo_em_cena(tmp_path: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    alvo = janela.ident(VERMELHO)

    async def corpo(porta: PortaDeMentira, _ext: Any) -> None:
        await porta.evento("extensao.acao", {"mod": "hookshot", "acao": "gatilhos",
                                             "alvo": alvo, "valor": "firme"})
        await porta.evento("extensao.acao", {"mod": "hookshot", "acao": "luz",
                                             "alvo": alvo, "valor": "kokiri"})
        await ate(lambda: _valores(_cartao(porta.ultimo_estado(), "Cosmic Red"))["luz"]
                  == "kokiri")
        assert porta.de("gatilho.set") == [] and porta.de("luz.set") == []
        await porta.evento("perfil.trocou", NA_CENA, "perfil.jogo")
        await ate(lambda: len(porta.de("gatilho.set")) == 2)
        await porta.evento("perfil.trocou", FORA_DE_CENA, "perfil.jogo")
        await ate(lambda: len(porta.de("gatilho.set")) == 4)

    porta = rodar_com_a_porta(tmp_path, monkeypatch, corpo, dados=tmp_path)
    gatilhos = porta.de("gatilho.set")
    assert {g["uniq"] for g in gatilhos} == {VERMELHO}
    assert [(g["lado"], g["modo"], g["params"]) for g in gatilhos] == [
        ("esquerdo", "Feedback", [2, 7]), ("direito", "Feedback", [2, 7]),
        ("esquerdo", "Off", []), ("direito", "Off", [])]
    assert [p["rgb"] for p in porta.de("luz.set")] == [[0x2e, 0x9e, 0x44], [0, 0, 0]]


def test_a_vibracao_forte_reforca_so_o_controle_escolhido(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def corpo(porta: PortaDeMentira, ext: Any) -> None:
        await porta.evento("extensao.acao", {"mod": "hookshot", "acao": "vibracao",
                                             "alvo": janela.ident(ROXO), "valor": "forte"})
        await ate(lambda: _valores(_cartao(porta.ultimo_estado(), "Galactic Purple"))[
            "vibracao"] == "forte")
        await porta.evento("perfil.trocou", NA_CENA, "perfil.jogo")
        await ate(lambda: ext.em_cena)
        relogio = [0.0]
        ext.relogio = lambda: relogio[0]
        for quando, uniq, pedido in ((1.0, AZUL, [100, 200]), (1.0, ROXO, [100, 200]),
                                     (1.05, ROXO, [100, 200]), (1.1, ROXO, [110, 210]),
                                     (1.2, ROXO, [120, 220]), (1.25, ROXO, [0, 0]),
                                     (1.3, ROXO, [0, 0])):
            relogio[0] = quando
            await ext.vibracao_do_jogo({"uniq": uniq}, {"uniq": uniq, "pedido": pedido})

    porta = rodar_com_a_porta(tmp_path, monkeypatch, corpo, dados=tmp_path)
    assert porta.de("vibracao.set") == [
        {"uniq": ROXO, "fraco": 150, "forte": 255},
        {"uniq": ROXO, "fraco": 180, "forte": 255},
        {"uniq": ROXO, "fraco": 0, "forte": 0}]



def test_a_vibracao_forte_nao_toca_outro_jogo_e_solta_ao_sair_do_hookshot(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def corpo(porta: PortaDeMentira, ext: Any) -> None:
        await porta.evento("extensao.acao", {"mod": "hookshot", "acao": "vibracao",
                                             "alvo": janela.ident(ROXO), "valor": "forte"})
        await ate(lambda: _valores(_cartao(porta.ultimo_estado(), "Galactic Purple"))[
            "vibracao"] == "forte")
        relogio = [0.0]
        ext.relogio = lambda: relogio[0]
        for quando in (1.0, 1.5, 2.0):
            relogio[0] = quando
            await ext.vibracao_do_jogo({"uniq": ROXO}, {"uniq": ROXO, "pedido": [100, 200]})
        assert porta.de("vibracao.set") == []
        await porta.evento("perfil.trocou", NA_CENA, "perfil.jogo")
        await ate(lambda: ext.em_cena)
        relogio[0] = 3.0
        await ext.vibracao_do_jogo({"uniq": ROXO}, {"uniq": ROXO, "pedido": [100, 200]})
        await porta.evento("perfil.trocou", FORA_DE_CENA, "perfil.jogo")
        await ate(lambda: not ext.em_cena)
        for quando in (3.5, 4.0):
            relogio[0] = quando
            await ext.vibracao_do_jogo({"uniq": ROXO}, {"uniq": ROXO, "pedido": [100, 200]})

    porta = rodar_com_a_porta(tmp_path, monkeypatch, corpo, dados=tmp_path)
    assert porta.de("vibracao.set") == [
        {"uniq": ROXO, "fraco": 150, "forte": 255},
        {"uniq": ROXO, "fraco": 0, "forte": 0}]

def test_a_escolha_errada_nao_grava_e_o_estado_volta(tmp_path: Path,
                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    async def corpo(porta: PortaDeMentira, _ext: Any) -> None:
        antes = len(porta.de("acessorios.estado"))
        for pedido in ({"acao": "luz", "alvo": janela.ident(AZUL), "valor": "rosa"},
                       {"acao": "giro", "alvo": janela.ident(AZUL), "valor": "sim"},
                       {"acao": "tremor", "alvo": janela.ident(AZUL), "valor": True},
                       {"acao": "luz", "alvo": "c0000000000", "valor": "zora"}):
            await porta.evento("extensao.acao", {"mod": "hookshot", **pedido})
        await ate(lambda: len(porta.de("acessorios.estado")) == antes + 4)

    rodar_com_a_porta(tmp_path, monkeypatch, corpo, dados=tmp_path)
    assert not (tmp_path / "controles.json").exists()


def test_a_escolha_volta_depois_de_reabrir(tmp_path: Path,
                                          monkeypatch: pytest.MonkeyPatch) -> None:
    alvo = janela.ident(AZUL)
    (tmp_path / "controles.json").write_text(json.dumps(
        {alvo: {"luz": "fada", "gatilhos": "firme", "vibracao": "forte"}}), encoding="utf-8")

    async def corpo(porta: PortaDeMentira, _ext: Any) -> None:
        await ate(lambda: bool(porta.de("acessorios.estado")))

    porta = rodar_com_a_porta(tmp_path, monkeypatch, corpo, dados=tmp_path)
    assert _valores(_cartao(porta.ultimo_estado(), "Starlight Blue")) == {
        "luz": "fada", "gatilhos": "firme", "vibracao": "forte", "giro": True}


@pytest.mark.parametrize("quantos", [1, 2, 3, 4])
def test_de_um_a_quatro_controles_cada_um_tem_o_seu_cartao(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, quantos: int) -> None:
    async def corpo(porta: PortaDeMentira, _ext: Any) -> None:
        await ate(lambda: bool(porta.de("acessorios.estado")))

    porta = rodar_com_a_porta(tmp_path, monkeypatch, corpo, controles=MESA_MISTA[:quantos])
    aparelhos = porta.ultimo_estado()["aparelhos"]
    assert len(aparelhos) == quantos
    assert len({a["id"] for a in aparelhos}) == quantos


def test_o_controle_que_chega_ganha_cartao(tmp_path: Path,
                                          monkeypatch: pytest.MonkeyPatch) -> None:
    async def corpo(porta: PortaDeMentira, _ext: Any) -> None:
        await ate(lambda: bool(porta.de("acessorios.estado")))
        porta.controles.append(MESA_MISTA[1])
        await porta.evento("conexao", {"uniq": BRANCO}, "conexao", BRANCO)
        await ate(lambda: len(porta.ultimo_estado()["aparelhos"]) == 2)

    rodar_com_a_porta(tmp_path, monkeypatch, corpo, controles=MESA_MISTA[:1])
