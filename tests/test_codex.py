"""The Codex plugin on fake answers: it loads as an assistant plugin, its tables hold together, its
requests are the Responses API's with the key and the account's digest (never the email), OpenAI's
errors are mapped with the quota ones final, Connect reads the tier from the x-ratelimit headers,
and the free tier sends (OpenAI lists it as a usage tier)."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import pytest

from liminal_lib.assistants import Answer, Question, Usage, evaluate
from liminal_lib.errors import NotEntitled, SourceError, Unauthorized
from liminal_lib.ratelimit import fingerprint

import platform_plugin_codex as codex
from platform_plugin_codex import ASSISTANT, MODELS, PLANS, SOURCES, CodexPlugin

from conftest import FakeResponse, FakeSession

NOW = datetime(2026, 11, 3, 15, 0, tzinfo=timezone.utc)
KEY, EMAIL = "sk-proj-test-key-000", "me@example.com"


def answer(text, model="gpt-5-nano", in_=120, out=30, cached=20, reasoning=8, status="completed", reason=None, headers=None,
           refusal=None):
    content = [{"type": "output_text", "text": text, "annotations": []}] if refusal is None else [{"type": "refusal", "refusal": refusal}]
    body = {"id": "resp_1", "object": "response", "model": model, "status": status,
            "output": [{"type": "reasoning", "summary": []}, {"type": "message", "role": "assistant", "status": "completed", "content": content}],
            "usage": {"input_tokens": in_, "output_tokens": out, "total_tokens": in_ + out,
                      "input_tokens_details": {"cached_tokens": cached}, "output_tokens_details": {"reasoning_tokens": reasoning}}}
    if reason:
        body["incomplete_details"] = {"reason": reason}
    return FakeResponse(200, body, headers or {"x-request-id": "req_o"})


def models(*ids, headers=None):
    return FakeResponse(200, {"object": "list", "data": [{"id": i, "object": "model", "owned_by": "openai"} for i in ids]}, headers or {})


def error(status, msg, code=None, kind=None):
    return FakeResponse(status, {"error": {"message": msg, "type": kind or "invalid_request_error", "code": code, "param": None}})


def test_it_loads_as_an_assistant_plugin(installed):
    found = installed(ASSISTANT)
    p = found["codex"]
    assert isinstance(p, CodexPlugin) and p.KIND == "assistant" and p.SYSTEM == "platform" and p.api == "2.0" and p.vendor == "OpenAI"
    assert [k.name for k in p.keys] == ["CODEX_API_KEY", "CODEX_ACCOUNT"] and p.keys[0].aliases == ("OPENAI_API_KEY",)
    assert p.options == ("CODEX_MAX_OUTPUT_TOKENS", "CODEX_EFFORT") and p.plan_choices["CODEX_EFFORT"][:3] == ("", "none", "minimal")
    from liminal_lib.sources import registry

    assert registry.errors() == [] and set(registry.variables()) >= {"CODEX_API_KEY", "OPENAI_API_KEY", "CODEX_PLAN", "CODEX_MODEL"}


def test_the_tables_hold_together():
    assert PLANS[0].name == "free" and PLANS[0].api_access and "$100" in PLANS[0].note
    assert [p.name for p in PLANS] == ["free", "build", "launch", "grow"]
    assert all(m.input_usd > 0 and m.output_usd > 0 and m.cached_usd > 0 for m in MODELS)
    assert MODELS[0].id == ASSISTANT.default_model == "gpt-5-nano" and "gpt-5.3-codex" in {m.id for m in MODELS}
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", codex.VERIFIED) and all(s.url.startswith("https://developers.openai.com/") for s in SOURCES)
    assert ASSISTANT.cost("gpt-5-nano", Usage(1_000_000, 1_000_000, 0, 0)) == 0.45
    assert sorted(p.rpm for p in PLANS if p.rpm) == [5000, 10000, 15000]


def test_the_request_carries_the_key_and_the_digest_and_the_free_tier_sends(installed, settings_for):
    installed(ASSISTANT)
    settings = settings_for(OPENAI_API_KEY=KEY, CODEX_ACCOUNT=EMAIL, CODEX_EFFORT="minimal")
    assert settings.plugin("codex").plan == "free" and ASSISTANT.served(settings) and ASSISTANT.free_note(settings) == ""
    session = FakeSession(answer("Closed.\nVerdict: no"))
    q = Question("Is the market open?", answer=Answer("verdict", scale=("yes", "no")))
    ev = evaluate(q, settings, assistant="codex", session=session, now=lambda: NOW)
    method, url, _, body, headers = session.calls[0]
    assert method == "POST" and url == "https://api.openai.com/v1/responses" and headers["Authorization"] == f"Bearer {KEY}"
    assert body["model"] == "gpt-5-nano" and body["max_output_tokens"] == 1024 and body["store"] is False
    assert body["safety_identifier"] == fingerprint(EMAIL) and body["reasoning"] == {"effort": "minimal"}
    assert "user" not in body and "temperature" not in body and EMAIL not in json.dumps(body)
    assert ev.verdict == "no" and ev.usage == Usage(120, 30, 20, 8) and ev.request_id == "resp_1" and ev.provider == "OpenAI"
    assert ev.cost_usd == pytest.approx(MODELS[0].cost(Usage(120, 30, 20, 8)))
    fields = Question("Score it", answer=Answer("fields", fields=("verdict", "score")))
    session = FakeSession(answer('{"verdict": "bearish", "score": 3}'))
    out = evaluate(fields, settings, assistant="codex", session=session, now=lambda: NOW)
    assert session.calls[0][3]["text"] == {"format": {"type": "json_object"}} and out.fields == {"verdict": "bearish", "score": 3}
    declined = evaluate(q, settings, assistant="codex", session=FakeSession(answer("", refusal="I cannot help with that")), now=lambda: NOW)
    assert declined.stop == "refusal" and not declined.ok


def test_openais_errors_are_mapped_and_the_quota_ones_are_final(installed, settings_for):
    installed(ASSISTANT)
    settings = settings_for(CODEX_API_KEY=KEY, CODEX_PLAN="build")

    def run(*responses):
        session = FakeSession(*responses)
        a = ASSISTANT.build(settings, session=session, now=lambda: NOW)
        a.client._sleep = lambda s: None
        try:
            a.evaluate(Question("x"))
        except SourceError as e:
            return type(e), e.message, len(session.calls)
        return None, "", len(session.calls)

    kind, msg, n = run(error(401, f"Incorrect API key provided: {KEY}", "invalid_api_key"))
    assert kind is Unauthorized and KEY not in msg and n == 1
    for code in ("insufficient_quota", "credit_balance_exhausted", "organization_spend_limit_exceeded"):
        kind, msg, n = run(error(429, "You exceeded your current quota", code))
        assert kind is NotEntitled and "no credit" in msg and n == 1  # final: not tried again
    kind, msg, n = run(error(404, "The model `gpt-9` does not exist", "model_not_found"))
    assert kind is NotEntitled and "Connect's list" in msg
    kind, msg, n = run(FakeResponse(200, {"id": "resp_f", "status": "failed", "error": {"code": "server_error", "message": "boom"}, "output": []}))
    assert kind is SourceError and "boom" in msg


def test_connect_reads_the_tier_from_the_headers(installed, settings_for):
    installed(ASSISTANT)
    settings = settings_for(CODEX_API_KEY=KEY)
    limits = {"x-ratelimit-limit-requests": "5000", "x-ratelimit-limit-tokens": "1000000", "x-request-id": "req_9"}
    session = FakeSession(models("gpt-5-nano", "gpt-5-mini", "gpt-6-astra", "gpt-7-preview"),
                          answer("OK", in_=10, out=2, cached=0, reasoning=0, headers=limits))
    scanned = ASSISTANT.run_scan(ASSISTANT.build(settings, session=session, now=lambda: NOW))
    rows = {w: (ok, d) for w, ok, d in scanned.results}
    assert rows["the key"][0] and rows["the model gpt-5-nano"][0] and rows["models not in the table"] == (True, "gpt-7-preview")
    assert not rows["the table's models"][0] and "gpt-5.3-codex" in rows["the table's models"][1]
    assert rows["its plan"] == (True, "the server allows 5,000 requests a minute and 1,000,000 tokens a minute: the Build plan")
    assert scanned.plan == {"CODEX_PLAN": "build"}
    from liminal_lib.config import with_detected

    assert with_detected(settings, scanned.plan).plugin("codex").plan == "build"  # the free default gives way to the tier found
