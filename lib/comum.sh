# shellcheck shell=bash disable=SC2034
DADOS="${XDG_DATA_HOME:-$HOME/.local/share}/hefesto-mod-hookshot"
MANIFESTO="$DADOS/instalado.txt"
COMANDO="$HOME/.local/bin/hefesto-hookshot"
ATALHO="${XDG_DATA_HOME:-$HOME/.local/share}/applications/hefesto-hookshot.desktop"
PERFIL="${XDG_CONFIG_HOME:-$HOME/.config}/hefesto-dualsense4unix/profiles/hookshot.json"

falha() {
    echo "${0##*/}: $*" >&2
    exit 1
}

recusar_root_e_sudo() {
    if [ "$(id -u)" = 0 ] || [ -n "${SUDO_USER:-}" ]; then
        falha "rode como você, sem sudo: tudo vai para a sua pasta pessoal."
    fi
}

impressao() {
    sha256sum "$1" | cut -d' ' -f1
}

do_manifesto() {
    [ -f "$MANIFESTO" ] || return 1
    awk -v alvo="$1" '$1 == "arq" && substr($0, length($1) + length($2) + 3) == alvo { print $2 }' "$MANIFESTO"
}
