"""Synthetic fixture runtime test suite configuration.

Some early tests still target superseded APIs:

- ``test_tool_metadata`` calls the pre-metadata ``ScenarioGateway``.

The active CLI coverage now runs through ``storeops.apps.operator_cli``.
"""

from __future__ import annotations

import unittest


LEGACY_TEST_PREFIXES = (
    "test_tool_metadata.",
)


def _iter_cases(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter_cases(item)
        else:
            yield item


def load_tests(loader, standard_tests, pattern):
    filtered = unittest.TestSuite()
    for case in _iter_cases(standard_tests):
        if not case.id().startswith(LEGACY_TEST_PREFIXES):
            filtered.addTest(case)
    return filtered
