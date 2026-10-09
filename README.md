# GridRadar QGIS Plugin

Plugin QGIS ufficiale per accedere al catalogo layer [GridRadar](https://gridradar.it) e all'integrazione **SINFI**.

Il plugin **non include** il catalogo layer: dopo l'autenticazione scarica metadati e risolve le connessioni GIS on-demand dal backend GridRadar.

## Requisiti

- QGIS 3.40 o superiore
- Account GridRadar con abbonamento attivo (`proxy_access`)
- Python package `requests` (installato automaticamente dal Plugin Manager quando possibile)

## Sviluppo locale (symlink)

Per iterare senza zip/reinstall, collega il repo alla cartella plugin di QGIS:

```bash
./scripts/link-qgis-plugin.sh
```

Questo crea (se manca) `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/` e un symlink:

`…/plugins/gridradar_qgis_plugin` → questa directory del repo.

Per rimuovere il symlink:

```bash
./scripts/unlink-qgis-plugin.sh
```

### Profilo QGIS diverso

```bash
QGIS_PROFILE=MyProfile ./scripts/link-qgis-plugin.sh
```

### Ciclo di test

1. Esegui `link-qgis-plugin.sh` una volta.
2. In QGIS: **Plugin → Gestione e installazione plugin → Installato** → abilita **GridRadar**.
3. Dopo modifiche ai file `.py`: disabilita e riabilita il plugin (oppure installa il plugin community [Plugin Reloader](https://plugins.qgis.org/plugins/plugin_reloader/)).
4. Dopo modifiche a `metadata.txt`: riavvia QGIS.

### Backend locale

Per testare contro un backend in sviluppo, apri **Impostazioni avanzate** nel dialogo di accesso e imposta l'URL API (es. `http://localhost:8000`). L'istanza di produzione usa `https://api.gridradar.it` per impostazione predefinita.

### Alternativa: `QGIS_PLUGINPATH`

Puoi anche avviare QGIS con un path plugin extra (utile in CI o profili isolati):

```bash
QGIS_PLUGINPATH=/home/castelli/repos/gridradar_qgis_plugin qgis
```

Con il symlink non serve: QGIS carica già la cartella dal profilo utente.

## Debug da Cursor / VS Code

Il plugin gira nel Python di QGIS (`/usr/bin/python3`), non nel conda `gis`. Il metodo standard è **debugpy attach** (come [QGIS DevTools](https://docs.nextgis.com/docs_ngqgis/source/devtools.html) e la community QGIS).

### Setup (una volta)

```bash
./scripts/install-qgis-debug.sh   # apt install python3-debugpy
./scripts/link-qgis-plugin.sh     # symlink nel profilo QGIS
```

Installa anche **Plugin Reloader** da Gestione plugin (serve per ricaricare il codice dopo l'attach).

Apri `gridradar_qgis_plugin` nel workspace Cursor (serve `.vscode/launch.json`).

### Debug con QGIS DevTools (consigliato)

Prerequisiti: `link-qgis-plugin.sh`, estensione **Python Debugger** in Cursor, plugin **Plugin Reloader** in QGIS.

1. **Chiudi** eventuali QGIS avviati con `debug-qgis.sh` o «Launch + attach».
2. Apri **QGIS normalmente** (icona applicazione, non da Cursor).
3. In QGIS: icona **bug** in basso a destra (DevTools) → **Start**.
   - Oppure: Plugin → QGIS DevTools → avvia il server.
   - Deve comparire la notifica «debugpy listening»; l'icona bug resta attiva.
4. In Cursor: breakpoint in `gui/login_dialog.py` (es. riga dentro `__init__`).
5. **Run and Debug** → **Attach to QGIS** → F5.
   - In QGIS l'icona DevTools diventa **verde** («client connected»).
   - In Cursor la barra in basso diventa arancione.
6. In QGIS: **Plugin Reloader** → ricarica **GridRadar**.
7. Clicca l'icona **GridRadar** → il breakpoint deve fermarsi su `login_dialog.py`.

Se DevTools mostra «Copy launch.json template», puoi incollarlo in `.vscode/launch.json` sostituendo `<YOUR_PLUGIN_NAME>` con `gridradar_qgis_plugin`. La config nel repo è già pronta.

**Non usare** `debug-qgis.sh` / «Launch + attach» insieme a DevTools: si contendono la porta 5678. GridRadar non avvia più debugpy da solo.

### Debug integrato (senza DevTools)

1. Breakpoint in un file `.py` (es. `gui/login_dialog.py`).
2. **Run and Debug** → **QGIS: Launch + attach** → F5.
3. Attendi `QGIS debug ready on 127.0.0.1:5678` nel terminale del task.
4. Cursor si collega (barra di stato arancione = debug attivo).
5. In QGIS: **Plugin Reloader** → ricarica **GridRadar** (obbligatorio: il primo caricamento avviene prima dell'attach).
6. Azione che passa dal breakpoint (es. clic icona GridRadar).

Flusso manuale: `./scripts/debug-qgis.sh` → **QGIS: Attach** → Plugin Reloader.

### Perché Plugin Reloader

QGIS carica i plugin all'avvio, prima che Cursor faccia attach. I breakpoint scattano solo sul codice eseguito **dopo** l'attach. Ricaricare il plugin è il workflow standard documentato da NextGIS e dalla community.

### Note tecniche

- Porta: `5678` (`GRIDRADAR_DEBUGPY_PORT`).
- `pathMappings` in `launch.json`: repo locale → `~/.local/share/QGIS/.../plugins/gridradar_qgis_plugin` (path symlink usato da QGIS).
- Workspace multi-root: usa `${workspaceFolder:gridradar_qgis_plugin}`.
- `core/debug.py`: `debugpy.listen()` al caricamento; su reload usa `connect()` se la porta è già in uso.

### Risoluzione problemi

| Sintomo | Fix |
|---|---|
| preLaunchTask bloccato | Verifica che GridRadar sia abilitato nel profilo; controlla `/tmp/gridradar-qgis-debug.log` |
| Attach OK, breakpoint grigi | Plugin Reloader dopo attach; verifica symlink `link-qgis-plugin.sh` |
| Porta già in uso | `fuser -k 5678/tcp` e riavvia |

## Build release (distribuzione protetta)

Distribuire il plugin **senza sorgente leggibile**, con un unico ZIP valido su Linux, Windows e macOS:

```bash
pip install -r scripts/requirements-build.txt
./scripts/build-release.sh
```

Output in `dist/`:

| Artefatto | Contenuto |
|---|---|
| `gridradar_qgis_plugin/` | Plugin con `.py` offuscati (python-minifier) |
| `gridradar_qgis_plugin-<versione>.zip` | Pacchetto per plugins.qgis.org o clienti |

Il build:

1. Esclude file di sviluppo (`scripts/`, `.vscode/`, `core/debug.py`, …).
2. Offusca ogni modulo: nomi locali abbreviati, docstring e annotazioni rimosse, codice compattato.
3. Verifica che `classFactory` sia importabile (opzionale: `QGIS_PYTHON=/usr/bin/python3`).

**Nessun runtime nativo**, nessun bytecode legato alla versione Python: resta codice `.py` normale, eseguibile da qualsiasi QGIS ≥ 3.40 con Python ≥ 3.10.

Non è crittografia: chi vuole può ancora rileggere la logica, ma è molto più scomodo del sorgente originale. Per protezione più forte (con vincoli OS/Python) si può valutare PyArmor separatamente.

## Utilizzo

1. Clicca l'icona **GridRadar** nella barra degli strumenti o nel menu Web.
2. Accedi con le credenziali GridRadar e seleziona l'organizzazione.
3. Nel pannello laterale, cerca un layer e attivalo con la checkbox, oppure usa il tab **Selezioni** per importare preset salvati.
4. Nel tab **Disegni**, attiva una **raccolta** per importare tutti i disegni, oppure attiva singole tracce (punti, linee, poligoni).
5. Per **SINFI**, clicca **Collega SINFI**, inserisci le credenziali personali e seleziona il gruppo.

## Architettura

| Componente | Ruolo |
|---|---|
| `core/api_client.py` | Client REST verso `/auth/*`, `/gis/catalog*`, `/orgs/{id}/map-drawings`, `/orgs/{id}/layer-selections`, `/me/integrations/sinfi/validate` |
| `core/draw/trace_layers.py` | Costruzione layer vettoriali QGIS da tracce GeoJSON |
| `core/providers/` | Costruzione layer QGIS per WMS, ArcGIS, GeoJSON, XYZ, MVT, OSM |
| `core/sinfi/` | Whitelist layer SINFI, GetCapabilities, auth Basic via QgsAuthManager |
| `gui/catalog_dock.py` | Albero catalogo, tab Selezioni e Disegni con ricerca e toggle |

Il backend companion in `gispv-mvp` espone:

- `GET /gis/catalog` — albero metadati (senza URL upstream)
- `POST /gis/catalog/resolve` — descriptor connessione QGIS on-demand
- `GET /gis/catalog/version` — hash versione per cache
- `GET /orgs/{org_id}/map-drawings` — workspace disegni (raccolte + tracce GeoJSON)
- `GET /orgs/{org_id}/layer-selections` — preset layer salvati (personali e organizzazione)

## Matrice di test manuale

| # | Scenario | Esito atteso |
|---|---|---|
| 1 | Login con credenziali valide | Dock catalogo visibile |
| 2 | Login senza abbonamento | Errore 403 dal backend |
| 3 | Toggle layer WMS (es. Campania) | Layer raster in gruppo `GridRadar · …` |
| 4 | Toggle layer ArcGIS feature (es. Lombardia PPR) | Layer vettoriale valido |
| 5 | Toggle layer ArcGIS image (es. Campania PUC) | Layer raster ArcGIS valido |
| 6 | Toggle layer MVT OpenInfraMap | Layer vector tile valido |
| 7 | Toggle basemap XYZ | Sfondo raster Carto/Esri |
| 8 | Layer SITAP / Vincoli in Rete (`requires_proxy`) | Richiesta via proxy autenticato |
| 9 | Collegamento SINFI + toggle layer INFR_RT | WMS SINFI con stile selezionato |
| 10 | Rimozione layer da legenda QGIS | Checkbox si deseleziona |
| 11 | Esci dal plugin | Layer plugin rimossi, sessione cancellata |
| 12 | Tab Selezioni + toggle preset | Layer del preset aggiunti con opacità salvata |
| 13 | Tab Disegni + toggle traccia | Layer vettoriale in `GridRadar · Disegni · {raccolta}` |
| 14 | Tab Disegni + toggle raccolta | Tutte le tracce della raccolta aggiunte/rimosse |
| 15 | Aggiorna disegni | Albero sincronizzato con workspace API |
| 16 | Ispezione ZIP plugin | Nessun file `layers/*.json` o `proxy_rules.json` |
| 17 | Apertura dock / Aggiorna catalogo | Gruppi chiusi; restano aperti solo quelli espansi dall'utente |

Test automatici (Python di QGIS, Qt offscreen; `tests/` è escluso dallo ZIP):

```bash
QT_QPA_PLATFORM=offscreen /usr/bin/python3 -m unittest discover -s tests
```

## Pubblicazione su plugins.qgis.org

1. Aggiorna `metadata.txt` (`version`, `changelog`) — la versione deve coincidere con il tag Git (`v0.2.4` → `version=0.2.4`).
2. Crea una **GitHub Release** sul tag; il workflow `.github/workflows/release.yml` genera lo ZIP offuscato e lo allega automaticamente.
3. Scarica `gridradar_qgis_plugin-<versione>.zip` dalla release e caricalo su [plugins.qgis.org](https://plugins.qgis.org) come plugin sperimentale.

Build locale (opzionale):

```bash
pip install -r scripts/requirements-build.txt
./scripts/build-release.sh
```

## Backend companion (gispv-mvp)

Dopo modifiche al catalogo frontend:

```bash
python backend/scripts/sync_catalog_order.py
python backend/scripts/sync_proxy_rules.py
```

Il deploy backend deve includere `backend/gispv_backend/data/layers/` e `catalog_order.json`.

## Licenza

Distribuito con il progetto GridRadar. Verificare i termini di servizio per l'uso commerciale del catalogo.
