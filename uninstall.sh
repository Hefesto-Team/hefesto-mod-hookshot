#!/usr/bin/env bash
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/comum.sh
. "$RAIZ/lib/comum.sh"

for arg in "$@"; do
    case "$arg" in
        --yes) ;;
        -h|--help) echo "Uso: ./uninstall.sh  (desfaz o que o ./install.sh preparou)"; exit 0 ;;
        *) falha "opção desconhecida: $arg" ;;
    esac
done

recusar_root_e_sudo

echo "uninstall.sh: controles: $(python3 -I "$RAIZ/hookshot.py" desfazer)"

if [ -f "$MANIFESTO" ]; then
    while read -r tipo marca alvo; do
        [ "$tipo" = "arq" ] || continue
        [ -e "$alvo" ] || continue
        if [ "$(impressao "$alvo")" = "$marca" ]; then
            rm -f -- "$alvo"
            echo "uninstall.sh: removido $alvo"
        else
            echo "uninstall.sh: $alvo mudou depois do install; fica como está."
        fi
    done < "$MANIFESTO"
    rm -f -- "$MANIFESTO"
fi
rmdir -- "$DADOS" 2>/dev/null || true
echo "uninstall.sh: retrato: $(python3 -I "$RAIZ/hookshot.py" sem-retrato)"
