# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Vitex Software <info@vitexsoftware.cz>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)
"""Shared code of the vitexus.abraflexi modules."""
from __future__ import annotations

import datetime
import logging
import os
import traceback
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib

try:
    from python_abraflexi import ReadWrite
    from python_abraflexi.exceptions import AbraFlexiException, NotFoundException
    HAS_LIB = True
    LIB_ERROR = None
except ImportError:
    HAS_LIB = False
    LIB_ERROR = traceback.format_exc()
    ReadWrite = object

    class AbraFlexiException(Exception):
        pass

    class NotFoundException(AbraFlexiException):
        pass

# The library logs every 404 as an error, which would end up on stderr.
logging.getLogger("ReadWrite").addHandler(logging.NullHandler())
logging.getLogger("ReadWrite").propagate = False

# Sub-item collections accepted on import but not named so in relations.json
ITEM_ALIASES = ("polozkyFaktury", "polozkyDokladu", "kontakty", "mistaUrceni")


def connection_spec(company=True):
    spec = dict(
        url=dict(type="str", required=True, fallback=(env_fallback, ["ABRAFLEXI_URL"])),
        login=dict(type="str", fallback=(env_fallback, ["ABRAFLEXI_LOGIN"])),
        password=dict(type="str", no_log=True, fallback=(env_fallback, ["ABRAFLEXI_PASSWORD"])),
        auth_session_id=dict(type="str", no_log=True, fallback=(env_fallback, ["ABRAFLEXI_AUTHSESSID"])),
        timeout=dict(type="int", default=60),
        validate_certs=dict(type="bool", default=True),
    )
    if company:
        spec["company"] = dict(type="str", required=True, fallback=(env_fallback, ["ABRAFLEXI_COMPANY"]))
    return spec


def identity_spec():
    return dict(
        id=dict(type="int"),
        code=dict(type="str"),
        external_id=dict(type="str"),
    )


def make_module(argument_spec=None, company=True, **kwargs):
    spec = connection_spec(company)
    spec.update(argument_spec or {})
    kwargs.setdefault("supports_check_mode", True)
    module = AnsibleModule(argument_spec=spec, **kwargs)
    require_lib(module.fail_json)
    if not module.params["auth_session_id"] and not (module.params["login"] and module.params["password"]):
        module.fail_json(msg="Either auth_session_id or both login and password are required")
    return module


def require_lib(fail):
    if not HAS_LIB:
        fail(msg=missing_required_lib("python_abraflexi", url="https://github.com/VitexSoftware/python-abraflexi"),
             exception=LIB_ERROR)


def make_client(params, evidence=None, key=None, query=None, filter_expr=None, company=None):
    """Create a client; *key* is an unencoded identifier such as C(code:ABC/1)."""
    options = {
        "url": params["url"].rstrip("/"),
        "company": company or params.get("company"),
        "user": params.get("login"),
        "password": params.get("password"),
        # explicit value keeps the library away from its environment lookup
        "authSessionId": params.get("auth_session_id"),
        "timeout": params.get("timeout") or 60,
        "throwException": True,
        "native_types": False,
        "autoload": False,
        "defaultUrlParams": dict(query or {}),
    }
    if evidence:
        options["evidence"] = evidence
    client = ReadWrite(None, options)
    verify = params.get("validate_certs")
    verify = True if verify is None else verify
    if verify:
        # requests lets the CA bundle variables win only for verify=True
        verify = os.environ.get("REQUESTS_CA_BUNDLE") or True
    # The library hardcodes verify=False
    client.session.verify = verify
    if filter_expr:
        client.filter = filter_expr
    if key is not None:
        client.my_key = quote(str(key), safe=":")
    client._update_api_url()
    return client


def jsonable(value):
    if isinstance(value, dict):
        return dict((str(k), jsonable(v)) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value


def run(module, func):
    """Run *func* turning library errors into module failures."""
    try:
        return func()
    except (AbraFlexiException, ValueError) as exc:
        result = dict(msg="AbraFlexi: %s" % exc, error_type=type(exc).__name__)
        errors = getattr(exc, "errors", None)
        if errors:
            result["errors"] = jsonable(errors)
        module.fail_json(**result)


def as_list(value):
    if not value or value is True:
        return []
    return value if isinstance(value, list) else [value]


def record_key(params):
    """Return the candidate identifiers of a record, most specific first."""
    keys = []
    if params.get("id") is not None:
        keys.append(str(params["id"]))
    if params.get("external_id"):
        ext = params["external_id"]
        keys.append(ext if ext.startswith("ext:") else "ext:" + ext)
    if params.get("code"):
        code = params["code"]
        keys.append(code if code.startswith("code:") else "code:" + code)
    return keys


def fetch_record(params, evidence, keys, detail="full", relations=None):
    """Return the first record found under *keys* or None."""
    query = {"detail": detail}
    if relations:
        query["relations"] = ",".join(relations)
    for key in keys:
        try:
            rows = make_client(params, evidence, key, query).perform_request()
        except NotFoundException:
            continue
        if isinstance(rows, list) and rows:
            return rows[0]
    if not keys:
        raise ValueError("No record identifier given")
    # A missing record and a missing evidence both answer 404: tell them apart.
    make_client(params, evidence, query={"limit": 1, "detail": "id"}).perform_request()
    return None


def must_fetch(module, evidence, **kwargs):
    keys = record_key(module.params)
    record = run(module, lambda: fetch_record(module.params, evidence, keys, **kwargs))
    if record is None:
        module.fail_json(msg="Record %s not found in evidence %s" % (" / ".join(keys), evidence))
    return record


def get_properties(params, evidence):
    data = make_client(params, evidence).get_properties()
    rows = as_list(data.get("properties", {}).get("property"))
    return dict((row["propertyName"], row) for row in rows)


def get_relations(params, evidence):
    data = make_client(params, evidence).get_relations_list()
    rows = as_list((data.get("relations") or {}).get("relation")) if isinstance(data, dict) else []
    return [row["url"] for row in rows if "url" in row]


def labels(value):
    if not value:
        return []
    if not isinstance(value, (list, tuple)):
        value = str(value).split(",")
    cleaned = [str(v).strip() for v in value]
    return sorted(set(v[5:] if v.startswith("code:") else v for v in cleaned if v))


def to_bool(value):
    text = str(value).strip().lower()
    if text in ("true", "1", "yes", "on"):
        return True
    if text in ("false", "0", "no", "off", "", "none"):
        return False
    raise ValueError("%r is not a boolean" % (value,))


def to_api(value):
    """Convert a playbook value into what the API expects."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, dict):
        return dict((k, to_api(v)) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return [to_api(v) for v in value]
    if isinstance(value, (int, float)):
        return str(value)
    return jsonable(value)


def _number(value):
    text = str(value).strip().replace(" ", "")
    return Decimal(text if text else "0")


def _datetime(value):
    text = str(value).strip().replace("Z", "+00:00")
    parsed = datetime.datetime.fromisoformat(text)
    return parsed


def values_equal(wanted, current, ptype=None, record=None, name=None):
    """Compare a desired value with the one read from the API."""
    wanted = to_api(wanted)
    current = "" if current is None else current
    if name == "stitky":
        return labels(wanted) == labels(current)
    if isinstance(wanted, (list, dict)) or isinstance(current, (list, dict)):
        return wanted == current
    if ptype == "logic":
        return to_bool(wanted) == to_bool(current)
    if ptype in ("numeric", "integer"):
        if (wanted == "") != (str(current) == ""):
            return False
        try:
            return _number(wanted) == _number(current)
        except InvalidOperation:
            return str(wanted) == str(current)
    if ptype == "date":
        # values look like 2024-12-10+01:00
        return str(wanted)[:10] == str(current)[:10]
    if ptype == "datetime":
        try:
            left, right = _datetime(wanted), _datetime(current)
            if (left.tzinfo is None) != (right.tzinfo is None):
                left, right = left.replace(tzinfo=None), right.replace(tzinfo=None)
            return left == right
        except ValueError:
            return str(wanted) == str(current)
    if ptype in ("relation", None) and str(wanted) != str(current):
        record = record or {}
        if str(wanted).isdigit() and name:
            # relations come back as code:X with the id in <name>@ref
            ref = record.get(name + "@ref")
            if ref:
                return ref.rsplit("/", 1)[-1].split(".")[0] == str(wanted)
        for left, right in ((str(wanted), str(current)), (str(current), str(wanted))):
            if left == "code:" + right:
                return True
        if ptype is None:
            try:
                return _number(wanted) == _number(current)
            except InvalidOperation:
                return False
        return False
    return str(wanted) == str(current)


def check_fields(data, properties, relations):
    """Return a list of problems; the server silently ignores unknown fields."""
    problems = []
    for name, value in data.items():
        if "@" in name:
            problems.append("%s: attributes are not supported in data" % name)
        elif name == "id":
            problems.append("id: use the id, code or external_id option instead")
        elif is_items(value) or name in ITEM_ALIASES or name in relations:
            if not is_items(value):
                problems.append("%s: a list of dictionaries is expected" % name)
            elif name not in relations and name not in ITEM_ALIASES:
                problems.append("%s: unknown sub-item collection" % name)
        elif name not in properties:
            problems.append("%s: unknown field" % name)
        elif properties[name].get("isWritable") == "false":
            problems.append("%s: field is read only" % name)
    return problems


def is_items(value):
    return isinstance(value, list) and all(isinstance(v, dict) for v in value) and bool(value)


def diff_items(wanted, current, match, name):
    """Return the sub-items to send (matched by field *match*)."""
    seen = {}
    for item in current:
        key = str(item.get(match, ""))
        if key in seen:
            raise ValueError("%s: existing items are not unique by %s=%s" % (name, match, key))
        seen[key] = item
    out = []
    used = set()
    for item in wanted:
        if match not in item:
            raise ValueError("%s: item without the matching field %s" % (name, match))
        key = str(to_api(item[match]))
        if key in used:
            raise ValueError("%s: duplicate item %s=%s" % (name, match, key))
        used.add(key)
        existing = seen.get(key)
        if existing is None:
            out.append(to_api(item))
            continue
        changed = dict((k, to_api(v)) for k, v in item.items()
                       if not values_equal(v, existing.get(k), None, existing, k))
        if changed:
            changed["id"] = existing["id"]
            out.append(changed)
    return out


def diff_record(data, current, properties, items_match=None):
    """Return the fields of *data* which differ from *current*."""
    changes = {}
    for name, value in data.items():
        if is_items(value):
            match = (items_match or {}).get(name)
            if not match:
                raise ValueError(
                    "%s: set subitems_match for this collection to update an existing record "
                    "(otherwise the items would be duplicated)" % name)
            items = diff_items(value, as_list(current.get(name)), match, name)
            if items:
                changes[name] = items
        elif not values_equal(value, current.get(name), properties.get(name, {}).get("type"), current, name):
            changes[name] = value
    return changes


def build_payload(changes):
    """Convert a change set to the import format."""
    payload = {}
    for name, value in changes.items():
        if name == "stitky":
            # labels are additive on the server: replace the whole set
            payload["stitky@removeAll"] = "true"
            payload["stitky"] = ",".join(labels(value))
        else:
            payload[name] = to_api(value)
    return payload
