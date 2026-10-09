# -*- coding: utf-8 -*-
"""Catalog dock tree expansion (delta-tribe/gridradar#186).

Run with QGIS's Python: QT_QPA_PLATFORM=offscreen /usr/bin/python3 -m unittest discover -s tests
"""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from qgis.PyQt.QtWidgets import QApplication  # noqa: E402

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_plugin_package():
    # The checkout directory may not be a valid package name (worktrees, CI).
    name = "gridradar_qgis_plugin"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            name, os.path.join(_REPO, "__init__.py"), submodule_search_locations=[_REPO]
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return importlib.import_module(f"{name}.gui.catalog_dock")


catalog_dock = _load_plugin_package()
_app = QApplication.instance() or QApplication([])

CATALOG = {
    "sources": [
        {
            "id": "terna",
            "name": "Terna",
            "subgroups": [{"name": "Linee", "layers": [{"id": "terna_linee", "name": "Linee AT"}]}],
            "layers": [{"id": "terna_cabine", "name": "Cabine"}],
        },
        {"id": "ispra", "name": "ISPRA", "layers": [{"id": "ispra_frane", "name": "Frane"}]},
        {"id": "sinfi", "name": "SINFI", "integration_type": "sinfi"},
    ]
}
SINFI_LAYERS = {"cantieri": [{"id": "sinfi_cantieri", "name": "Cantieri SINFI"}]}
WORKSPACE = {
    "personal": [{"id": 1, "name": "Raccolta A"}],
    "organization": [{"id": 2, "name": "Raccolta B"}],
    "traces": [{"id": 10, "collection_id": 1, "name": "Traccia 1", "kind": "line"}],
}
SELECTIONS = {
    "personal": [{"id": 5, "name": "Mia selezione", "layer_ids": ["terna_linee"]}],
    "organization": [],
}


def _all_items(tree):
    stack = [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())]
    while stack:
        item = stack.pop()
        yield item
        stack.extend(item.child(i) for i in range(item.childCount()))


def _expanded_labels(tree):
    return {item.text(0) for item in _all_items(tree) if item.isExpanded()}


def _top_level(tree, label):
    for i in range(tree.topLevelItemCount()):
        if tree.topLevelItem(i).text(0) == label:
            return tree.topLevelItem(i)
    raise AssertionError(label)


class CatalogDockExpansionTest(unittest.TestCase):
    def setUp(self):
        self.dock = catalog_dock.CatalogDockWidget()
        self.dock.populate_catalog(CATALOG)
        self.dock.populate_sinfi_layers(SINFI_LAYERS)
        self.dock.populate_draw_workspace(WORKSPACE)
        self.dock.populate_layer_selections(SELECTIONS)

    def test_all_trees_start_collapsed(self):
        for tree in (self.dock.tree, self.dock.draw_tree, self.dock.selections_tree):
            self.assertEqual(_expanded_labels(tree), set())

    def test_catalog_refresh_keeps_only_user_opened_groups(self):
        terna = _top_level(self.dock.tree, "Terna")
        terna.setExpanded(True)
        terna.child(0).setExpanded(True)
        self.dock.populate_catalog(CATALOG)
        self.dock.populate_sinfi_layers(SINFI_LAYERS)
        self.assertEqual(_expanded_labels(self.dock.tree), {"Terna", "Linee"})

    def test_catalog_refresh_keeps_user_closed_groups_closed(self):
        _top_level(self.dock.tree, "Terna").setExpanded(True)
        self.dock.populate_catalog(CATALOG)
        _top_level(self.dock.tree, "Terna").setExpanded(False)
        self.dock.populate_catalog(CATALOG)
        self.assertEqual(_expanded_labels(self.dock.tree), set())

    def test_sinfi_layers_do_not_force_open_sinfi_node(self):
        self.dock.populate_sinfi_layers(SINFI_LAYERS)
        self.assertFalse(_top_level(self.dock.tree, "SINFI").isExpanded())

    def test_sinfi_reload_keeps_opened_subgroup(self):
        sinfi = _top_level(self.dock.tree, "SINFI")
        sinfi.setExpanded(True)
        sinfi.child(0).setExpanded(True)
        self.dock.populate_sinfi_layers(SINFI_LAYERS)
        sinfi = _top_level(self.dock.tree, "SINFI")
        self.assertTrue(sinfi.isExpanded())
        self.assertTrue(sinfi.child(0).isExpanded())

    def test_draw_and_selection_refresh_keep_user_opened_groups(self):
        _top_level(self.dock.draw_tree, "Personali").setExpanded(True)
        _top_level(self.dock.selections_tree, "Personali").setExpanded(True)
        self.dock.populate_draw_workspace(WORKSPACE)
        self.dock.populate_layer_selections(SELECTIONS)
        self.assertEqual(_expanded_labels(self.dock.draw_tree), {"Personali"})
        self.assertEqual(_expanded_labels(self.dock.selections_tree), {"Personali"})

    def test_search_opens_groups_containing_matches(self):
        self.dock.search_edit.setText("linee")
        self.assertEqual(_expanded_labels(self.dock.tree), {"Terna", "Linee"})


if __name__ == "__main__":
    unittest.main()
