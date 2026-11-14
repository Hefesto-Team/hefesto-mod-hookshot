from __future__ import annotations

import os
import subprocess
from pathlib import Path

from conftest import RAIZ, jogo_compilado

import hookshot

ORIGINAL = "language=pt\npad_a=1\npad_b=0\n"


def _rodar(script: str, lar: Path, *args: str) -> subprocess.CompletedProcess[str]:
    ambiente = {"HOME": str(lar), "PATH": os.environ["PATH"], "LANG": "C.UTF-8"}
    return subprocess.run(["bash", str(RAIZ / script), *args], env=ambiente,
                          capture_output=True, text=True, check=False)


def _arvore(raiz: Path) -> dict[str, bytes]:
    return {str(p.relative_to(raiz)): p.read_bytes() for p in sorted(raiz.rglob("*"))
            if p.is_file()}


def _caminhos(lar: Path) -> tuple[Path, Path, Path]:
    return (lar / ".local/bin/hefesto-hookshot",
            lar / ".local/share/applications/hefesto-hookshot.desktop",
            lar / ".config/hefesto-dualsense4unix/profiles/hookshot.json")


def test_o_install_prepara_tudo_e_rodar_de_novo_nao_muda_nada(lar: Path) -> None:
    pasta = jogo_compilado(lar / "Games" / "Hookshot")
    (pasta / hookshot.OPCOES).write_text(ORIGINAL, encoding="utf-8")
    primeira = _rodar("install.sh", lar, "--yes")
    assert primeira.returncode == 0, primeira.stderr
    comando, atalho, perfil = _caminhos(lar)
    assert os.access(comando, os.X_OK)
    assert "hookshot.py" in comando.read_text(encoding="utf-8")
    assert "StartupWMClass=hookshot" in atalho.read_text(encoding="utf-8")
    assert perfil.read_bytes().strip() == (RAIZ / "perfis/hookshot.json").read_bytes().strip()
    assert "pad_a=0" in (pasta / hookshot.OPCOES).read_text(encoding="utf-8")
    antes = _arvore(lar)
    segunda = _rodar("install.sh", lar, "--yes")
    assert segunda.returncode == 0, segunda.stderr
    assert _arvore(lar) == antes
    assert "escrito" not in segunda.stdout.replace("controles: ja-preparado", "")


def test_o_uninstall_desfaz_o_que_o_install_preparou(lar: Path) -> None:
    pasta = jogo_compilado(lar / "Games" / "Hookshot")
    (pasta / hookshot.OPCOES).write_text(ORIGINAL, encoding="utf-8")
    antes = _arvore(lar)
    assert _rodar("install.sh", lar).returncode == 0
    desfeito = _rodar("uninstall.sh", lar)
    assert desfeito.returncode == 0, desfeito.stderr
    assert _arvore(lar) == antes
    assert not (lar / ".local/share/hefesto-mod-hookshot").exists()


def test_o_perfil_que_ja_existia_e_de_quem_usa(lar: Path) -> None:
    perfil = _caminhos(lar)[2]
    perfil.parent.mkdir(parents=True)
    perfil.write_text('{"name": "Hookshot", "meu": true}\n', encoding="utf-8")
    assert _rodar("install.sh", lar).returncode == 0
    assert '"meu": true' in perfil.read_text(encoding="utf-8")
    assert _rodar("uninstall.sh", lar).returncode == 0
    assert '"meu": true' in perfil.read_text(encoding="utf-8")


def test_o_que_quem_usa_mudou_depois_do_install_fica(lar: Path) -> None:
    assert _rodar("install.sh", lar).returncode == 0
    atalho = _caminhos(lar)[1]
    atalho.write_text(atalho.read_text(encoding="utf-8") + "NoDisplay=true\n", encoding="utf-8")
    assert _rodar("uninstall.sh", lar).returncode == 0
    assert atalho.is_file()
    assert not _caminhos(lar)[0].exists()


def test_o_install_sem_o_jogo_compilado_ainda_prepara_o_comando(lar: Path) -> None:
    feito = _rodar("install.sh", lar)
    assert feito.returncode == 0, feito.stderr
    assert "controles: sem-jogo" in feito.stdout
    assert _caminhos(lar)[0].is_file()


def test_o_comando_instalado_abre_o_jogo(lar: Path, tmp_path: Path) -> None:
    pasta = jogo_compilado(lar / "Games" / "Hookshot")
    relato = tmp_path / "abriu.txt"
    (pasta / "hookshot").write_text(f"#!/bin/sh\necho \"$SDL_APP_ID $*\" > {relato}\n",
                                    encoding="utf-8")
    assert _rodar("install.sh", lar).returncode == 0
    comando = _caminhos(lar)[0]
    ambiente = {"HOME": str(lar), "PATH": os.environ["PATH"]}
    abriu = subprocess.run([str(comando), "--um"], env=ambiente, check=False)
    assert abriu.returncode == 0
    assert relato.read_text(encoding="utf-8").strip() == "hookshot --um"


def test_o_install_recusa_sudo(lar: Path) -> None:
    ambiente = {"HOME": str(lar), "PATH": os.environ["PATH"], "SUDO_USER": "alguem"}
    feito = subprocess.run(["bash", str(RAIZ / "install.sh")], env=ambiente,
                           capture_output=True, text=True, check=False)
    assert feito.returncode != 0
    assert "sem sudo" in feito.stderr
    assert not (lar / ".local").exists()


def test_o_preparo_do_hefesto_grava_o_retrato_e_o_uninstall_o_tira(lar: Path) -> None:
    jogo_compilado(lar / "Games" / "Hookshot")
    dados = lar / ".local/state/hefesto-dualsense4unix/mods/hookshot"
    dados.mkdir(parents=True)
    antes = _arvore(lar)
    feito = _rodar("install.sh", lar, "--yes")
    assert "retrato: escrito" in feito.stdout, feito.stderr
    retrato = (dados / hookshot.RETRATO).read_text(encoding="utf-8")
    assert '"jogo": "compilado"' in retrato
    assert "retrato: igual" in _rodar("install.sh", lar, "--yes").stdout
    assert "retrato: removido" in _rodar("uninstall.sh", lar).stdout
    assert _arvore(lar) == antes
