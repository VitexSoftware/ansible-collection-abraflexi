# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from ansible_collections.vitexus.abraflexi.plugins.module_utils import abraflexi as m


@pytest.mark.parametrize("wanted,current,ptype,name,equal", [
    (True, "true", "logic", "a", True),
    (False, "", "logic", "a", True),
    (True, "false", "logic", "a", False),
    (10, "10.0", "numeric", "a", True),
    ("1 000.50", "1000.5", "numeric", "a", True),
    (0, "", "integer", "a", False),
    ("2024-12-10", "2024-12-10+01:00", "date", "a", True),
    ("2024-12-11", "2024-12-10+01:00", "date", "a", False),
    ("2024-12-10T10:00:00+00:00", "2024-12-10T11:00:00.000+01:00", "datetime", "a", True),
    ("CZ", "code:CZ", "relation", "stat", True),
    ("code:CZ", "code:SK", "relation", "stat", False),
    (39, "code:CZ", "relation", "stat", True),
    (38, "code:CZ", "relation", "stat", False),
    (["VIP", "code:A"], "A, VIP", "string", "stitky", True),
    ([], "", "string", "stitky", True),
    (None, "", "string", "a", True),
    ("1.0", "1", "string", "a", False),
])
def test_values_equal(wanted, current, ptype, name, equal):
    record = {"stat@ref": "/c/x/stat/39.json"}
    assert m.values_equal(wanted, current, ptype, record, name) is equal


def test_check_fields():
    props = {"kod": {"isWritable": "true"}, "sum": {"isWritable": "false"}}
    problems = m.check_fields({"kod": "x", "sum": 1, "foo": 1, "id": 2, "kod@x": 1, "bad": [{"a": 1}]}, props, [])
    assert len(problems) == 5


def test_items():
    current = [{"id": "1", "nazev": "A", "mnozMj": "1.0"}]
    out = m.diff_items([{"nazev": "A", "mnozMj": 1}, {"nazev": "B"}], current, "nazev", "p")
    assert out == [{"nazev": "B"}]
    assert m.diff_items([{"nazev": "A", "mnozMj": 2}], current, "nazev", "p") == [{"mnozMj": "2", "id": "1"}]
    with pytest.raises(ValueError):
        m.diff_items([{"nazev": "A"}], current * 2, "nazev", "p")
    with pytest.raises(ValueError):
        m.diff_record({"p": [{"nazev": "A"}]}, {}, {})


def test_payload_replaces_labels():
    assert m.build_payload({"stitky": ["B", "A"], "x": True}) == {
        "stitky@removeAll": "true", "stitky": "A,B", "x": "true"}


def test_client_tls_and_key(monkeypatch):
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    monkeypatch.setenv("ABRAFLEXI_AUTHSESSID", "leak")
    params = dict(url="https://x/", company="c", login="u", password="p")
    client = m.make_client(params, "faktura-vydana", "code:A/1")
    assert client.session.verify is True
    assert client.api_url == "https://x/c/c/faktura-vydana/code:A%2F1.json"
    assert "X-authSessionId" not in client.default_http_headers
    assert m.make_client(dict(params, validate_certs=False)).session.verify is False
