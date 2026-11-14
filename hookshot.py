#!/usr/bin/env python3
from __future__ import annotations

import configparser
import contextlib
import hashlib
import json
import os
import re
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypedDict

PROGRAMA = "hookshot"
JANELA = "hookshot"
CHAVE_DO_JOGO = "hookshot-ocarina-of-time"
NOME_DO_JOGO = "The Legend of Zelda: Ocarina of Time (Hookshot)"
PASTA_PADRAO = Path("Games") / "Hookshot"
OPCOES = "hookshot_options.ini"
SUFIXO_DO_REGISTRO = ".hefesto.json"
SUFIXO_DA_COPIA = ".antes-do-hefesto"

ID_DA_EXTENSAO = "hookshot"
RETRATO = "retrato.json"
DANIFICADOS = "hookshot_damaged_files.txt"
POSICAO = "Posição"
NINTENDO = "Nintendo"
DISPOSICOES = (POSICAO, NINTENDO)

POSICAO_DO_BOTAO: dict[str, int] = {
    "a": 0,
    "b": 1,
    "x": 2,
    "y": 3,
    "minus": 4,
    "plus": 6,
    "ls": 7,
    "rs": 8,
    "l": 9,
    "r": 10,
    "up": 11,
    "down": 12,
    "left": 13,
    "right": 14,
    "zl": 15,
    "zr": 16,
}

AMBIENTE_DA_JANELA: dict[str, str] = {
    "SDL_APP_ID": JANELA,
    "SDL_VIDEO_X11_WMCLASS": JANELA,
    "SDL_VIDEO_WAYLAND_WMCLASS": JANELA,
}

_LINHA_DO_PAD = re.compile(r"^(\s*)(pad_[a-z]+)(\s*=\s*)(.*?)(\s*)$")


def _lar(lar: Path | None) -> Path:
    return Path(os.environ.get("HOME", str(Path.home()))) if lar is None else lar


def _xdg(variavel: str, padrao: Path) -> Path:
    valor = os.environ.get(variavel, "").strip()
    return Path(valor) if os.path.isabs(valor) else padrao


def ini_do_builder(lar: Path | None = None) -> Path:
    return _xdg("XDG_CONFIG_HOME", _lar(lar) / ".config") / "hookshot" / "builder.ini"


def _caminhos_do_builder(ini: Path, casa: Path) -> list[Path]:
    cfg = configparser.ConfigParser(strict=False, interpolation=None)
    try:
        texto = ini.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    try:
        cfg.read_string(texto if texto.lstrip().startswith("[") else "[geral]\n" + texto)
    except configparser.Error:
        return []
    achados: list[Path] = []
    for secao in cfg.sections():
        for _, valor in cfg.items(secao):
            limpo = valor.strip().strip('"')
            if limpo.startswith("~/"):
                limpo = str(casa / limpo[2:])
            if os.path.isabs(limpo) and "\x00" not in limpo:
                achados.append(Path(limpo))
    return achados


def pastas_candidatas(lar: Path | None = None) -> list[Path]:
    casa = _lar(lar)
    vistas: list[Path] = []
    for pasta in [*_caminhos_do_builder(ini_do_builder(casa), casa), casa / PASTA_PADRAO]:
        if pasta not in vistas:
            vistas.append(pasta)
    return vistas


def e_pasta_do_jogo(pasta: Path) -> bool:
    return (pasta / "bin" / PROGRAMA).is_file()


def pasta_do_jogo(lar: Path | None = None) -> Path | None:
    return next((p for p in pastas_candidatas(lar) if e_pasta_do_jogo(p)), None)


def executavel(pasta: Path) -> Path:
    lancador = pasta / PROGRAMA
    if lancador.is_file() and os.access(lancador, os.X_OK):
        return lancador
    return pasta / "bin" / PROGRAMA


class Leitura(TypedDict):
    jogos: list[dict[str, object]]
    pastas: list[str]


def ler(lar: Path | None = None) -> Leitura:
    casa = _lar(lar)
    jogos: list[dict[str, object]] = []
    pastas: list[str] = []
    for pasta in pastas_candidatas(casa):
        for olhada in (pasta, pasta / "bin"):
            if olhada.is_dir() and str(olhada) not in pastas:
                pastas.append(str(olhada))
        if not jogos and e_pasta_do_jogo(pasta):
            jogos.append({"chave": CHAVE_DO_JOGO, "nome": NOME_DO_JOGO, "caminho": str(pasta),
                          "janela": JANELA, "instalado": True})
    return {"jogos": jogos, "pastas": pastas[:64]}


def _valores_do_pad(linhas: Sequence[str]) -> dict[str, str]:
    valores: dict[str, str] = {}
    for linha in linhas:
        casou = _LINHA_DO_PAD.match(linha)
        if casou:
            valores[casou.group(2)] = casou.group(4)
    return valores


TROCA_DA_NINTENDO: dict[str, int] = {"a": 1, "b": 0, "x": 3, "y": 2}


def mapa_desejado(disposicao: str = POSICAO) -> dict[str, str]:
    posicoes = dict(POSICAO_DO_BOTAO)
    if disposicao == NINTENDO:
        posicoes.update(TROCA_DA_NINTENDO)
    return {f"pad_{botao}": str(posicao) for botao, posicao in posicoes.items()}


def pasta_de_dados(lar: Path | None = None) -> Path:
    dada = os.environ.get("HEFESTO_MOD_DADOS", "").strip()
    if os.path.isabs(dada):
        return Path(dada)
    estado = _xdg("XDG_STATE_HOME", _lar(lar) / ".local" / "state")
    return estado / "hefesto-dualsense4unix" / "mods" / ID_DA_EXTENSAO


def disposicao_escolhida(dados: Path) -> str:
    try:
        opcoes = json.loads((dados / "opcoes.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return POSICAO
    escolha = opcoes.get("botoes") if isinstance(opcoes, dict) else None
    return escolha if escolha in DISPOSICOES else POSICAO


def _com_os_valores(linhas: list[str], valores: Mapping[str, str | None]) -> list[str]:
    restantes = dict(valores)
    novas: list[str] = []
    ultimo_pad = -1
    for linha in linhas:
        casou = _LINHA_DO_PAD.match(linha)
        if casou and casou.group(2) in restantes:
            valor = restantes.pop(casou.group(2))
            if valor is None:
                continue
            linha = f"{casou.group(1)}{casou.group(2)}{casou.group(3)}{valor}"
        novas.append(linha)
        if casou:
            ultimo_pad = len(novas) - 1
    extras = [f"{chave}={valor}" for chave, valor in restantes.items() if valor is not None]
    if extras:
        ponto = ultimo_pad + 1 if ultimo_pad >= 0 else len(novas)
        novas[ponto:ponto] = extras
    return novas


def _texto(linhas: Sequence[str]) -> str:
    return "".join(f"{linha}\n" for linha in linhas)


def _gravar(alvo: Path, texto: str) -> None:
    descritor, temporario = tempfile.mkstemp(prefix=f".{alvo.name}.", dir=alvo.parent)
    try:
        with os.fdopen(descritor, "w", encoding="utf-8") as saida:
            saida.write(texto)
        if alvo.exists():
            os.chmod(temporario, alvo.stat().st_mode & 0o777)
        os.replace(temporario, alvo)
    except BaseException:
        Path(temporario).unlink(missing_ok=True)
        raise


def registro(pasta: Path) -> Path:
    return pasta / (OPCOES + SUFIXO_DO_REGISTRO)


def copia(pasta: Path) -> Path:
    return pasta / (OPCOES + SUFIXO_DA_COPIA)


def _ler_registro(pasta: Path) -> dict[str, object] | None:
    try:
        dados = json.loads(registro(pasta).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dados if isinstance(dados, dict) else None


def _anteriores(guardado: Mapping[str, object]) -> dict[str, str | None]:
    bruto = guardado.get("antes")
    if not isinstance(bruto, dict):
        return {}
    return {str(k): (None if v is None else str(v)) for k, v in bruto.items()}


def _escrito(guardado: Mapping[str, object]) -> dict[str, str]:
    bruto = guardado.get("escrito")
    return {str(k): str(v) for k, v in bruto.items()} if isinstance(bruto, dict) else {}


def _trocar_a_disposicao(pasta: Path, guardado: Mapping[str, object],
                         desejado: dict[str, str]) -> str:
    ini = pasta / OPCOES
    original = ini.read_text(encoding="utf-8", errors="surrogateescape") if ini.is_file() else ""
    linhas = original.splitlines()
    atuais = _valores_do_pad(linhas)
    escrito = _escrito(guardado)
    troca = {chave: valor for chave, valor in desejado.items()
             if atuais.get(chave) == escrito.get(chave)}
    novo = _texto(_com_os_valores(linhas, troca))
    if novo != original:
        _gravar(ini, novo)
    _gravar(registro(pasta), json.dumps(
        {"escrito": desejado, "antes": _anteriores(guardado),
         "existia": bool(guardado.get("existia", True))},
        ensure_ascii=False, indent=1) + "\n")
    return "trocado"


def preparar_controles(pasta: Path, *, forcar: bool = False,
                       disposicao: str = POSICAO) -> str:
    if not e_pasta_do_jogo(pasta):
        return "sem-jogo"
    guardado = _ler_registro(pasta)
    desejado = mapa_desejado(disposicao)
    if guardado is not None and not forcar:
        if _escrito(guardado) == desejado:
            return "ja-preparado"
        return _trocar_a_disposicao(pasta, guardado, desejado)
    ini = pasta / OPCOES
    existia = ini.is_file()
    original = ini.read_text(encoding="utf-8", errors="surrogateescape") if existia else ""
    linhas = original.splitlines()
    if guardado is None:
        atuais = _valores_do_pad(linhas)
        guardado = {"antes": {chave: atuais.get(chave) for chave in desejado},
                    "existia": existia}
    if existia and not copia(pasta).exists():
        copia(pasta).write_bytes(ini.read_bytes())
    novo = _texto(_com_os_valores(linhas, desejado))
    mudou = novo != original
    if mudou:
        _gravar(ini, novo)
    _gravar(registro(pasta), json.dumps(
        {"escrito": desejado, "antes": _anteriores(guardado),
         "existia": bool(guardado.get("existia", existia))},
        ensure_ascii=False, indent=1) + "\n")
    return "escrito" if mudou else "igual"


def desfazer_controles(pasta: Path) -> str:
    guardado_em = registro(pasta)
    if not guardado_em.is_file():
        return "nada"
    guardado = _ler_registro(pasta) or {}
    escrito = _escrito(guardado)
    anteriores = _anteriores(guardado)
    ini = pasta / OPCOES
    if ini.is_file():
        texto = ini.read_text(encoding="utf-8", errors="surrogateescape")
        linhas = texto.splitlines()
        atuais = _valores_do_pad(linhas)
        volta = {chave: anteriores.get(chave) for chave, valor in escrito.items()
                 if atuais.get(chave) == valor}
        novo = _texto(_com_os_valores(linhas, volta))
        if not novo.strip() and not guardado.get("existia", True):
            ini.unlink()
        elif novo != texto:
            _gravar(ini, novo)
    if copia(pasta).is_file() and ini.is_file() and copia(pasta).read_bytes() == ini.read_bytes():
        copia(pasta).unlink()
    guardado_em.unlink()
    return "desfeito"


def _caminhos_do_appimage(casa: Path, pasta: Path | None) -> list[Path]:
    achados = [p for p in _caminhos_do_builder(ini_do_builder(casa), casa)
               if p.suffix.lower() == ".appimage"]
    for onde in ([pasta] if pasta else []) + [casa / "Applications", casa / "Downloads", casa]:
        try:
            soltos = [p for p in onde.iterdir()
                      if p.suffix.lower() == ".appimage" and "hookshot" in p.name.lower()]
        except OSError:
            continue
        achados += sorted(soltos, key=lambda p: p.stat().st_mtime_ns, reverse=True)
    return [p for p in achados if p.is_file()]


def _sha256(caminho: Path) -> str:
    soma = hashlib.sha256()
    with caminho.open("rb") as entrada:
        for bloco in iter(lambda: entrada.read(1 << 20), b""):
            soma.update(bloco)
    return soma.hexdigest()


def _appimage(casa: Path, pasta: Path | None,
              antes: Mapping[str, object] | None) -> dict[str, object] | None:
    for caminho in _caminhos_do_appimage(casa, pasta):
        try:
            info = caminho.stat()
        except OSError:
            continue
        marca = {"caminho": str(caminho), "tamanho": info.st_size, "mtime_ns": info.st_mtime_ns}
        if antes and all(antes.get(k) == v for k, v in marca.items()) \
                and isinstance(antes.get("sha256"), str):
            return {**marca, "sha256": antes["sha256"]}
        try:
            return {**marca, "sha256": _sha256(caminho)}
        except OSError:
            continue
    return None


def _ler_retrato(dados: Path) -> dict[str, object]:
    try:
        lido = json.loads((dados / RETRATO).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return lido if isinstance(lido, dict) else {}


def retrato(lar: Path | None = None, antes: Mapping[str, object] | None = None
            ) -> dict[str, object]:
    casa = _lar(lar)
    pasta = pasta_do_jogo(casa)
    if pasta is None:
        jogo = "falta"
    elif (pasta / DANIFICADOS).is_file():
        jogo = "danificado"
    else:
        jogo = "compilado"
    velho = (antes or {}).get("appimage")
    return {"versao": 1, "casa": str(casa), "pasta": str(pasta) if pasta else None, "jogo": jogo,
            "appimage": _appimage(casa, pasta, velho if isinstance(velho, dict) else None)}


def gravar_retrato(lar: Path | None = None) -> str:
    dados = pasta_de_dados(lar)
    if not dados.is_dir():
        return "sem-dados"
    novo = json.dumps(retrato(lar, _ler_retrato(dados)), ensure_ascii=False, indent=1) + "\n"
    alvo = dados / RETRATO
    try:
        if alvo.read_text(encoding="utf-8") == novo:
            return "igual"
    except OSError:
        pass
    _gravar(alvo, novo)
    return "escrito"


def processos_do_jogo(proc: Path = Path("/proc")) -> list[int]:
    achados: list[int] = []
    try:
        entradas = list(proc.iterdir())
    except OSError:
        return achados
    for entrada in entradas:
        if not entrada.name.isdigit():
            continue
        try:
            nome = (entrada / "comm").read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        if nome == PROGRAMA:
            achados.append(int(entrada.name))
    return sorted(achados)


def linha_de_abrir(pasta: Path, argumentos: Sequence[str] = (),
                   ambiente: Mapping[str, str] | None = None) -> tuple[list[str], dict[str, str]]:
    base = dict(os.environ if ambiente is None else ambiente)
    for nome, valor in AMBIENTE_DA_JANELA.items():
        base.setdefault(nome, valor)
    return [str(executavel(pasta)), *argumentos], base


def abrir(argumentos: Sequence[str], lar: Path | None = None,
          proc: Path = Path("/proc")) -> int:
    pasta = pasta_do_jogo(lar)
    if pasta is None:
        print(f"hefesto-hookshot: o jogo não foi achado; compile-o com o Hookshot em "
              f"~/{PASTA_PADRAO} (o guia está no README da extensão).", file=sys.stderr)
        return 2
    if processos_do_jogo(proc):
        print("hefesto-hookshot: o jogo já está aberto.", file=sys.stderr)
        return 0
    with contextlib.suppress(OSError):
        gravar_retrato(lar)
    preparar_controles(pasta, disposicao=disposicao_escolhida(pasta_de_dados(lar)))
    argv, ambiente = linha_de_abrir(pasta, argumentos)
    os.chdir(pasta)
    os.execve(argv[0], argv, ambiente)
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("uso: hookshot.py leitor | abrir [args] | controles [--forcar] | desfazer | "
              "aberto | onde | retrato | sem-retrato", file=sys.stderr)
        return 2
    pedido, resto = args[0], args[1:]
    if pedido == "leitor":
        json.dump(ler(), sys.stdout, ensure_ascii=False)
        return 0
    if pedido == "abrir":
        return abrir(resto)
    if pedido == "aberto":
        pids = processos_do_jogo()
        json.dump({"aberto": bool(pids), "pids": pids}, sys.stdout)
        return 0 if pids else 1
    if pedido == "retrato":
        print(gravar_retrato())
        return 0
    if pedido == "sem-retrato":
        alvo = pasta_de_dados() / RETRATO
        existia = alvo.is_file()
        alvo.unlink(missing_ok=True)
        print("removido" if existia else "nada")
        return 0
    pasta = pasta_do_jogo()
    if pedido == "onde":
        print(pasta if pasta is not None else "")
        return 0 if pasta is not None else 1
    if pedido == "controles":
        print(preparar_controles(pasta, forcar="--forcar" in resto,
                                 disposicao=disposicao_escolhida(pasta_de_dados()))
              if pasta else "sem-jogo")
        return 0
    if pedido == "desfazer":
        feitos = [desfazer_controles(p) for p in pastas_candidatas() if registro(p).is_file()]
        print("desfeito" if feitos else "nada")
        return 0
    print(f"hookshot.py: pedido desconhecido: {pedido}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
