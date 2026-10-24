import json
import re

from astro.calc import engine

ARGS = dict(date="1990-05-17", time="06:30", tz=5.5, lat=19.07, lon=72.88, on="2026-01-01", extras=False)


def _write(tmp_path, **kw):
    out = tmp_path / kw.pop("d", "a")
    engine.write_outputs(engine.compute(**{**ARGS, **kw}), str(out))
    return out


def test_stamp_in_all_outputs_and_tracks_inputs(tmp_path):
    a, b = _write(tmp_path), _write(tmp_path, d="b", time="06:45")
    stamp = json.loads((a / "calc.json").read_text())["stamp"]
    assert re.fullmatch(rf"astro {re.escape(engine.ENGINE_VERSION)}; inputs sha256:[0-9a-f]{{12}}", stamp)
    assert json.loads((a / "chart.json").read_text())["_stamp"] == stamp
    assert (a / "calc.md").read_text().startswith(f"<!-- {stamp} -->\n")
    assert json.loads((b / "calc.json").read_text())["stamp"] != stamp
    assert engine.input_stamp(engine.compute(**ARGS)) == stamp   # deterministic: no timestamp in the hash
