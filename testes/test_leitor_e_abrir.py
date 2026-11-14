from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import RAIZ, jogo_compilado

import hookshot


def test_sem_o_jogo_a_lista_vem_vazia(lar: Path) -> None:
    assert hookshot.ler(lar) == {"jogos": [], "pastas": []}


def test_o_jogo_na_pasta_padrao_vira_um_jogo_com_a_janela(lar: Path) -> None:
    pasta = jogo_compilado(lar / "Games" / "Hookshot")
    lido = hookshot.ler(lar)
    assert lido["jogos"] == [{"chave": hookshot.CHAVE_DO_JOGO, "nome": hookshot.NOME_DO_JOGO,
                              "caminho": str(pasta), "janela": "hookshot", "instalado": True}]
    assert lido["pastas"] == [str(pasta), str(pasta / "bin")]


def test_a_pasta_que_o_builder_guarda_vale_antes_da_padrao(lar: Path, tmp_path: Path) -> None:
    outra = jogo_compilado(tmp_path / "disco" / "Zelda")
    jogo_compilado(lar / "Games" / "Hookshot")
    ini = lar / ".config" / "hookshot" / "builder.ini"
    ini.parent.mkdir(parents=True)
    ini.write_text(f"[Builder]\noutput_dir={outra}\nlast_nup=/naoexiste/ocarina.nup\n",
                   encoding="utf-8")
    assert hookshot.pasta_do_jogo(lar) == outra
    assert [j["caminho"] for j in hookshot.ler(lar)["jogos"]] == [str(outra)]


def test_o_builder_sem_secao_e_com_til_tambem_se_le(lar: Path) -> None:
    pasta = jogo_compilado(lar / "Jogos" / "OoT")
    ini = lar / ".config" / "hookshot" / "builder.ini"
    ini.parent.mkdir(parents=True)
    ini.write_text("out=~/Jogos/OoT\n", encoding="utf-8")
    assert hookshot.pasta_do_jogo(lar) == pasta


def test_o_builder_respeita_o_xdg_config_home(lar: Path, tmp_path: Path,
                                             monkeypatch: pytest.MonkeyPatch) -> None:
    pasta = jogo_compilado(tmp_path / "em-outro-lugar")
    config = tmp_path / "cfg"
    (config / "hookshot").mkdir(parents=True)
    (config / "hookshot" / "builder.ini").write_text(f"[a]\nb={pasta}\n", encoding="utf-8")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config))
    assert hookshot.pasta_do_jogo(lar) == pasta


def test_o_leitor_pela_linha_de_comando_imprime_o_json(lar: Path) -> None:
    jogo_compilado(lar / "Games" / "Hookshot")
    saida = subprocess.run([sys.executable, "-I", "hookshot.py", "leitor"], cwd=RAIZ,
                           env={"HOME": str(lar), "PATH": os.environ["PATH"]},
                           capture_output=True, text=True, check=True).stdout
    assert [j["chave"] for j in json.loads(saida)["jogos"]] == [hookshot.CHAVE_DO_JOGO]


def test_abrir_prefere_o_lancador_da_pasta_e_poe_o_nome_da_janela(lar: Path) -> None:
    pasta = jogo_compilado(lar / "Games" / "Hookshot")
    argv, ambiente = hookshot.linha_de_abrir(pasta, ["--fullscreen"], {"PATH": "/usr/bin"})
    assert argv == [str(pasta / "hookshot"), "--fullscreen"]
    assert ambiente["SDL_APP_ID"] == "hookshot"
    assert ambiente["SDL_VIDEO_X11_WMCLASS"] == "hookshot"
    assert ambiente["SDL_VIDEO_WAYLAND_WMCLASS"] == "hookshot"
    assert ambiente["PATH"] == "/usr/bin"


def test_sem_o_lancador_abre_o_binario(lar: Path) -> None:
    pasta = jogo_compilado(lar / "Games" / "Hookshot", com_lancador=False)
    assert hookshot.linha_de_abrir(pasta, [], {})[0] == [str(pasta / "bin" / "hookshot")]


def test_o_nome_da_janela_que_quem_usa_escolheu_vale(lar: Path) -> None:
    pasta = jogo_compilado(lar / "Games" / "Hookshot")
    ambiente = hookshot.linha_de_abrir(pasta, [], {"SDL_APP_ID": "outro"})[1]
    assert ambiente["SDL_APP_ID"] == "outro"


def _proc(raiz: Path, processos: dict[int, str]) -> Path:
    for pid, nome in processos.items():
        (raiz / str(pid)).mkdir(parents=True)
        (raiz / str(pid) / "comm").write_text(nome + "\n", encoding="utf-8")
    (raiz / "self").mkdir(parents=True, exist_ok=True)
    return raiz


def test_o_jogo_aberto_se_reconhece_pelo_processo(tmp_path: Path) -> None:
    proc = _proc(tmp_path / "proc", {10: "bash", 4321: "hookshot", 77: "hookshot-builde"})
    assert hookshot.processos_do_jogo(proc) == [4321]
    assert hookshot.processos_do_jogo(_proc(tmp_path / "vazio", {1: "systemd"})) == []
    assert hookshot.processos_do_jogo(tmp_path / "nao-existe") == []


def test_abrir_de_ponta_a_ponta_prepara_os_botoes_e_entrega_o_ambiente(lar: Path,
                                                                      tmp_path: Path) -> None:
    pasta = lar / "Games" / "Hookshot"
    jogo_compilado(pasta)
    relato = tmp_path / "relato.txt"
    (pasta / "hookshot").write_text(
        f"#!/bin/sh\n{{ pwd; echo \"$SDL_APP_ID\"; echo \"$@\"; }} > {relato}\n",
        encoding="utf-8")
    proc = _proc(tmp_path / "proc", {1: "systemd"})
    codigo = subprocess.run(
        [sys.executable, "-I", "-c",
         ("import sys; sys.path.insert(0, sys.argv[1]); import hookshot, pathlib; "
          "raise SystemExit(hookshot.abrir(['--um'], proc=pathlib.Path(sys.argv[2])))"),
         str(RAIZ), str(proc)],
        env={"HOME": str(lar), "PATH": os.environ["PATH"]}, check=False).returncode
    assert codigo == 0
    assert relato.read_text(encoding="utf-8").splitlines() == [str(pasta), "hookshot", "--um"]
    assert (pasta / hookshot.OPCOES).is_file()
    assert hookshot.registro(pasta).is_file()


def test_abrir_com_o_jogo_ja_aberto_nao_abre_outro(lar: Path, tmp_path: Path) -> None:
    pasta = jogo_compilado(lar / "Games" / "Hookshot")
    proc = _proc(tmp_path / "proc", {4321: "hookshot"})
    assert hookshot.abrir([], lar, proc) == 0
    assert not (pasta / hookshot.OPCOES).exists()


def test_abrir_sem_o_jogo_diz_onde_compilar(lar: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert hookshot.abrir([], lar, Path("/nao-existe")) == 2
    assert "Games/Hookshot" in capsys.readouterr().err
