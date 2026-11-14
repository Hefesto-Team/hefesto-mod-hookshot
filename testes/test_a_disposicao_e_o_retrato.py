from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from conftest import jogo_compilado

import hookshot


@pytest.fixture()
def pasta(lar: Path) -> Path:
    alvo = jogo_compilado(lar / "Games" / "Hookshot")
    (alvo / hookshot.OPCOES).write_text("[Controls]\npad_a=1\npad_b=0\nlanguage=pt\n",
                                        encoding="utf-8")
    return alvo


def _valores(ini: Path) -> dict[str, str]:
    linhas = ini.read_text(encoding="utf-8").splitlines()
    return dict(ln.split("=", 1) for ln in linhas if ln.startswith("pad_"))


def test_a_nintendo_poe_o_a_no_circulo(pasta: Path) -> None:
    hookshot.preparar_controles(pasta, disposicao=hookshot.NINTENDO)
    valores = _valores(pasta / hookshot.OPCOES)
    assert (valores["pad_a"], valores["pad_b"], valores["pad_x"], valores["pad_y"]) == (
        "1", "0", "3", "2")


def test_trocar_a_disposicao_respeita_o_que_quem_joga_mudou(pasta: Path) -> None:
    original = (pasta / hookshot.OPCOES).read_bytes()
    assert hookshot.preparar_controles(pasta) == "escrito"
    ini = pasta / hookshot.OPCOES
    ini.write_text(ini.read_text(encoding="utf-8").replace("pad_x=2", "pad_x=9"),
                   encoding="utf-8")
    assert hookshot.preparar_controles(pasta, disposicao=hookshot.NINTENDO) == "trocado"
    valores = _valores(ini)
    assert (valores["pad_a"], valores["pad_b"], valores["pad_x"], valores["pad_y"]) == (
        "1", "0", "9", "2")
    assert hookshot.preparar_controles(pasta, disposicao=hookshot.NINTENDO) == "ja-preparado"
    assert hookshot.preparar_controles(pasta) == "trocado"
    assert _valores(ini)["pad_a"] == "0"
    ini.write_text(ini.read_text(encoding="utf-8").replace("pad_x=9", "pad_x=2"),
                   encoding="utf-8")
    assert hookshot.desfazer_controles(pasta) == "desfeito"
    assert ini.read_bytes() == original


@pytest.mark.parametrize("gravado, esperado", [
    ({"botoes": "Nintendo"}, "Nintendo"), ({"botoes": "Posição"}, "Posição"),
    ({"botoes": "Xbox"}, "Posição"), ([], "Posição"), (None, "Posição")])
def test_a_escolha_da_janela_vem_do_opcoes_json(tmp_path: Path, gravado: object,
                                               esperado: str) -> None:
    if gravado is not None:
        (tmp_path / "opcoes.json").write_text(json.dumps(gravado), encoding="utf-8")
    assert hookshot.disposicao_escolhida(tmp_path) == esperado


def test_a_pasta_de_dados_e_a_do_hefesto(lar: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HEFESTO_MOD_DADOS", raising=False)
    assert hookshot.pasta_de_dados() == (
        lar / ".local" / "state" / "hefesto-dualsense4unix" / "mods" / "hookshot")
    monkeypatch.setenv("HEFESTO_MOD_DADOS", str(lar / "outra"))
    assert hookshot.pasta_de_dados() == lar / "outra"


def _dados(lar: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    dados = lar / "dados"
    dados.mkdir()
    monkeypatch.setenv("HEFESTO_MOD_DADOS", str(dados))
    return dados


def test_o_retrato_diz_o_que_falta_sem_a_pasta_do_hefesto(lar: Path,
                                                        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HEFESTO_MOD_DADOS", raising=False)
    assert hookshot.gravar_retrato() == "sem-dados"
    dados = _dados(lar, monkeypatch)
    assert hookshot.gravar_retrato() == "escrito"
    lido = json.loads((dados / hookshot.RETRATO).read_text(encoding="utf-8"))
    assert (lido["jogo"], lido["pasta"], lido["appimage"]) == ("falta", None, None)


def test_o_retrato_confere_o_appimage_e_nao_refaz_a_soma(lar: Path, pasta: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    dados = _dados(lar, monkeypatch)
    (lar / "Applications").mkdir()
    app = lar / "Applications" / "Hookshot-v2.1.0-x86_64.AppImage"
    app.write_bytes(b"um appimage de mentira")
    assert hookshot.gravar_retrato() == "escrito"
    lido = json.loads((dados / hookshot.RETRATO).read_text(encoding="utf-8"))
    assert lido["jogo"] == "compilado" and lido["pasta"] == str(pasta)
    assert lido["appimage"]["sha256"] == hashlib.sha256(b"um appimage de mentira").hexdigest()
    somas: list[Path] = []

    def _contar(caminho: Path) -> str:
        somas.append(caminho)
        return "x"

    monkeypatch.setattr(hookshot, "_sha256", _contar)
    assert hookshot.gravar_retrato() == "igual"
    assert somas == []
    (pasta / hookshot.DANIFICADOS).write_text("exefs/main\n", encoding="utf-8")
    assert hookshot.gravar_retrato() == "escrito"
    assert json.loads((dados / hookshot.RETRATO).read_text(encoding="utf-8"))[
        "jogo"] == "danificado"


def test_abrir_grava_o_retrato_e_aplica_a_disposicao(lar: Path, pasta: Path,
                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    dados = _dados(lar, monkeypatch)
    (dados / "opcoes.json").write_text(json.dumps({"botoes": "Nintendo"}), encoding="utf-8")
    lancados: list[list[str]] = []
    monkeypatch.setattr("hookshot.os.execve", lambda a, argv, amb: lancados.append(argv))
    monkeypatch.setattr("hookshot.os.chdir", lambda _p: None)
    hookshot.abrir([], proc=lar / "sem-proc")
    assert lancados and (dados / hookshot.RETRATO).is_file()
    assert _valores(pasta / hookshot.OPCOES)["pad_a"] == "1"
