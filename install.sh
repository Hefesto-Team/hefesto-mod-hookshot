#!/usr/bin/env bash
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/comum.sh
. "$RAIZ/lib/comum.sh"

ajuda() {
    cat <<'TEXTO'
Uso: ./install.sh [--yes | --desinstalar]

Prepara a extensão Hookshot para você, sem sudo:
  ~/.local/bin/hefesto-hookshot                            o comando que abre o jogo
  ~/.local/share/applications/hefesto-hookshot.desktop     o atalho do menu
  ~/.config/hefesto-dualsense4unix/profiles/hookshot.json  o perfil do DualSense, se você não tem um
  os botões do DualSense no hookshot_options.ini do jogo, com cópia do original

Rodar de novo não muda nada. O ./uninstall.sh desfaz tudo isso.
TEXTO
}

for arg in "$@"; do
    case "$arg" in
        --yes) ;;
        --desinstalar) exec bash "$RAIZ/uninstall.sh" ;;
        -h|--help) ajuda; exit 0 ;;
        *) falha "opção desconhecida: $arg (use --yes, --desinstalar ou --help)" ;;
    esac
done

recusar_root_e_sudo
command -v python3 >/dev/null || falha "falta o python3."
command -v sha256sum >/dev/null || falha "falta o sha256sum."

mkdir -p "$DADOS"
touch "$MANIFESTO"

registrar() {
    local alvo="$1" marca
    marca="$(impressao "$alvo")"
    awk -v alvo="$alvo" '!($1 == "arq" && substr($0, length($1) + length($2) + 3) == alvo)' \
        "$MANIFESTO" > "$MANIFESTO.novo"
    printf 'arq %s %s\n' "$marca" "$alvo" >> "$MANIFESTO.novo"
    mv "$MANIFESTO.novo" "$MANIFESTO"
}

e_da_extensao() {
    local alvo="$1" marca
    marca="$(do_manifesto "$alvo" || true)"
    [ -n "$marca" ] && [ "$marca" = "$(impressao "$alvo")" ]
}

escrever() {
    local alvo="$1" modo="$2" conteudo="$3"
    if [ -e "$alvo" ] && ! e_da_extensao "$alvo"; then
        echo "install.sh: $alvo já existe e não é da extensão; fica como está."
        return 0
    fi
    if [ -f "$alvo" ] && [ "$(cat "$alvo")" = "$conteudo" ]; then
        return 0
    fi
    mkdir -p "$(dirname "$alvo")"
    printf '%s\n' "$conteudo" > "$alvo.novo"
    chmod "$modo" "$alvo.novo"
    mv "$alvo.novo" "$alvo"
    registrar "$alvo"
    echo "install.sh: escrito $alvo"
}

escrever "$COMANDO" 755 "#!/usr/bin/env bash
exec python3 -I $(printf '%q' "$RAIZ/hookshot.py") abrir \"\$@\""

escrever "$ATALHO" 644 "[Desktop Entry]
Type=Application
Name=Ocarina of Time (Hookshot)
Comment=O Zelda recompilado pelo Hookshot, com o DualSense pelo Hefesto
Exec=$COMANDO
Icon=applications-games
Terminal=false
Categories=Game;
StartupWMClass=hookshot"

escrever "$PERFIL" 644 "$(cat "$RAIZ/perfis/hookshot.json")"

echo "install.sh: controles: $(python3 -I "$RAIZ/hookshot.py" controles)"
