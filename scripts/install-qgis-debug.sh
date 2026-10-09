#!/usr/bin/env bash
# Install debugpy (apt) for QGIS plugin debugging with VS Code/Cursor.
set -euo pipefail

if ! /usr/bin/python3 -c "import debugpy" 2>/dev/null; then
  echo "Installing python3-debugpy (requires sudo)…"
  sudo apt-get install -y python3-debugpy
fi

/usr/bin/python3 -c "import debugpy; print('debugpy', debugpy.__version__, 'ok')"

echo ""
echo "Debug install complete."
echo ""
echo "Metodo consigliato (QGIS DevTools — plugin ufficiale community):"
echo "  Plugin → Gestione plugin → QGIS DevTools → Start → copia launch.json → Attach"
echo "  https://docs.nextgis.com/docs_ngqgis/source/devtools.html"
echo ""
echo "Metodo integrato in questo repo:"
echo "  1. ./scripts/link-qgis-plugin.sh"
echo "  2. Cursor → QGIS: Launch + attach (F5)"
echo "  3. Dopo l'attach: Plugin Reloader → ricarica GridRadar"
echo "  4. I breakpoint scattano sul codice ricaricato"
