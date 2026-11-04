"""Codex (OpenAI) for Liminal: an AI assistant plugin (liminal_lib.assistants, plugin API 2.0) that
evaluates standardized arguments through OpenAI's Responses API on your own API key ("ChatGPT
Codex" here: the codex and GPT models on an API key, a ChatGPT subscription being no key), with the
usage tiers, models and prices written in, dated, and checked against OpenAI's pages.

A Liminal plugin released on its own, registered under the entry point group `liminal.providers` as
`codex`: the plugin `CodexPlugin` (ASSISTANT below), its assistant `CodexAssistant` (assistant.py).
It relies on plugin API 2.0 and nothing of the apps.

What the user sets (the Plugins view's Setup, or the app's key script): `CODEX_API_KEY` (read as
`OPENAI_API_KEY` too), `CODEX_ACCOUNT` (the email or account name the key belongs to: shown with its
evaluations, sent to OpenAI only as a digest, the `safety_identifier`); its plan `CODEX_PLAN` (free:
the Free usage tier; build, launch, grow by credits bought), its model `CODEX_MODEL` (GPT-5 nano by
default: the cheapest), its caps on this machine `CODEX_REQUESTS_PER_DAY` (50), `CODEX_TOKENS_PER_DAY`
(200,000), `CODEX_MAX_OUTPUT_TOKENS` (1,024), and `CODEX_EFFORT` (the API's reasoning effort; the
model's default when unset).

The user, 2026-11-03: "the ai plugins should support free, and if that means they have no API access,
then so be it": OpenAI lists a Free usage tier (a $100 monthly usage limit, allowed geographies),
so the free plan sends; its per-model limits are not published and a key without credit is refused
with a quota error, which is shown as such. "every time any of the three vendors changes their
plans/rates there will have to be a way to query through the plugin to update itself, or worst
case, just version up every time w/ CI catching the disparity between code and latest rates through
unit testing": Connect reads the limits OpenAI's servers send (x-ratelimit-*) and names the tier
they show, and compares the models listed with the table; the weekly CI run reads the pricing and
rate-limit pages (SOURCES) and fails when a written-in figure is gone, which is a new release of
this plugin.
"""
from __future__ import annotations

from liminal_lib.assistants import AssistantPlugin, Caps, Model, Plan, Source

from .assistant import API, CodexAssistant

__all__ = ["ASSISTANT", "CodexPlugin", "CodexAssistant", "PLANS", "MODELS", "SOURCES", "VERIFIED", "API"]

VERIFIED = "2026-11-03"  # the day the tables below were checked against SOURCES

# OpenAI's usage tiers (developers.openai.com/api/docs/guides/rate-limits, 2026-11-03): by credits bought,
# each a monthly usage limit and, per model group, requests and tokens a minute. The figures here are
# the Astra, Sol and Terra groups' (the Luna group has more tokens a minute).
PLANS = (
    Plan("free", "Free tier", price="an account in an allowed geography, nothing bought", spend_cap="$100 a month",
         note="the Free usage tier: a $100 monthly usage limit; its per-model limits are not published; a key without "
              "credit is refused with a quota error"),
    Plan("build", "Build", rpm=5_000, tpm=1_000_000, price="$5 in credits bought", spend_cap="$500 a month",
         note="5,000 requests and 1,000,000 tokens a minute (Luna models: 2,000,000)"),
    Plan("launch", "Launch", rpm=10_000, tpm=4_000_000, price="$100 in credits bought", spend_cap="$5,000 a month",
         note="10,000 requests and 4,000,000 tokens a minute (Luna models: 10,000,000)"),
    Plan("grow", "Grow", rpm=15_000, tpm=40_000_000, price="$500 in credits bought", spend_cap="$200,000 a month",
         note="15,000 requests and 40,000,000 tokens a minute (Luna models: 30,000 and 180,000,000)"),
)

# The text models (developers.openai.com/api/docs/pricing, 2026-11-03, the Standard tier, short context):
# prices per million tokens (input, output, a cached input token); the cheapest first.
MODELS = (
    Model("gpt-5-nano", "GPT-5 nano", 0.05, 0.40, 0.005, reasoning=True, note="the cheapest"),
    Model("gpt-5-mini", "GPT-5 mini", 0.25, 2.00, 0.025, reasoning=True),
    Model("gpt-5.4-nano", "GPT-5.4 nano", 0.20, 1.25, 0.02, reasoning=True),
    Model("gpt-5.4-mini", "GPT-5.4 mini", 0.75, 4.50, 0.075, reasoning=True),
    Model("gpt-6-luna", "GPT-6 Luna", 0.10, 0.50, 0.01, reasoning=True, note="the Luna group: higher rate limits"),
    Model("gpt-6.1-terra", "GPT-6.1 Terra", 1.00, 5.00, 0.05, reasoning=True),
    Model("gpt-6.1-sol", "GPT-6.1 Sol", 2.00, 10.00, 0.10, reasoning=True),
    Model("gpt-5.3-codex", "GPT-5.3 Codex", 1.75, 14.00, 0.175, reasoning=True, note="the codex model: agentic coding"),
    Model("gpt-5.5", "GPT-5.5", 5.00, 30.00, 0.50, reasoning=True),
    Model("gpt-6-astra", "GPT-6 Astra", 10.00, 50.00, 1.00, reasoning=True, note="the flagship"),
)

# Where the tables come from, with what each page must still show (verify.check_sources, weekly in CI).
SOURCES = (
    Source("https://developers.openai.com/api/docs/pricing", "the models' prices", "Prices per 1M tokens",
           ("gpt-5-nano", "0.05", "0.40", "gpt-5-mini", "0.25", "2.00", "gpt-5.3-codex", "1.75", "14.00", "gpt-6-luna",
            "gpt-6-astra", "10.00", "50.00")),
    Source("https://developers.openai.com/api/docs/guides/rate-limits", "the usage tiers",
           "Rate limits are restrictions that our API imposes",
           ("Free", "Build", "Launch", "Grow", "$5", "$100", "$500", "5,000", "10,000", "15,000")),
)


class CodexPlugin(AssistantPlugin):
    """Codex: the plugin (see the module's docstring)."""

    name = "codex"
    title = "Codex"
    about = "OpenAI's codex and GPT models through the Responses API: evaluations of standardized arguments on your key"
    vendor = "OpenAI"
    signup = "https://platform.openai.com/"
    order = 502
    api = "2.0"
    assistant = CodexAssistant
    plans = PLANS
    models = MODELS
    default_model = "gpt-5-nano"
    verified = VERIFIED
    sources = SOURCES
    caps = Caps()  # 50 requests and 200,000 tokens a day on this machine, 1,024 output tokens an answer
    efforts = ("", "none", "minimal", "low", "medium", "high", "xhigh", "max")  # reasoning.effort; "" leaves the model's default
    key_aliases = ("OPENAI_API_KEY",)
    account_hint = "the email or account name the key belongs to: shown with its evaluations, sent to OpenAI only as a digest (safety_identifier)"


ASSISTANT = CodexPlugin()
