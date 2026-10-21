"""Council 4 R3 L3 (chart_facts input), R4 L2 (REST token removed while remote), R5 comparator. Synthetic data only."""
import importlib.util
import os

import pytest
from fastapi.testclient import TestClient

from astro import config, rest, service as S

spec = importlib.util.spec_from_file_location("cf", os.path.join(config.load().skill_dir, "scripts", "chart_facts.py"))   # both editions
cf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cf)


@pytest.mark.parametrize("asc,pl", [
    ({"sign": ""}, {}),
    ({"sign": "Aries"}, {"Jupiter": {"sign": "Leo"}}),
    ({"sign": "Aries"}, {"Su": {"sign": "Leo", "deg": "10"}}),
    ({"sign": "Aries"}, {"Su": {"sign": "Leo", "deg": 45}}),
])
def test_chart_facts_rejects_bad_input(asc, pl):
    with pytest.raises(ValueError):
        cf.facts({"asc": asc, "planets": pl})


def test_rest_token_removed_while_remote_is_refused(monkeypatch):
    s = config.Settings(api_token="")
    monkeypatch.setattr(config, "load", lambda: s)
    monkeypatch.setattr(S, "REMOTE", True)
    assert TestClient(rest.app).get("/api/v1/health").status_code == 401
    monkeypatch.setattr(S, "REMOTE", False)   # localhost without a token stays open
    assert TestClient(rest.app).get("/api/v1/health").status_code == 200


def test_comparator_flags_a_perturbed_chart():
    """Council 4 R5: the comparator must also report a difference, not only agree with itself."""
    from astro.calc import engine as lc
    from astro.calc.adapters import from_local
    from astro.calc.compare import compare
    a = from_local(lc.compute("1990-05-17", "06:30", 5.5, 19.07, 72.88, on="2026-01-01"))
    b = a.model_copy(deep=True)
    b.bodies["Ju"].lon = (b.bodies["Ju"].lon + 0.5) % 360
    bad = [(x.key, x.verdict) for x in compare(a, b) if x.verdict not in ("match", "within tolerance", "not comparable")]
    assert bad and all(k == "Ju" for k, _ in bad)


def test_hybrid_mode_migrates_to_private(tmp_path, monkeypatch, capsys):
    """The removed 'hybrid' privacy mode is read as 'private' (docs/PRIVACY.md), never as an error or a cloud call."""
    p = tmp_path / "config.toml"
    p.write_text('mode = "hybrid"\n')
    monkeypatch.setattr(config, "CONFIG_PATH", str(p))
    assert config.load().mode == "private" and "no longer exists" in capsys.readouterr().err
