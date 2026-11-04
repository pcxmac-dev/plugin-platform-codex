# platform-plugin-codex

Codex for [Liminal](https://github.com/pcxmac-dev/liminal-app): an AI assistant plugin (plugin API
2.0, `liminal_lib.assistants`, a platform plugin) that evaluates standardized arguments (a question
over headlines, an assessment, a report; a judge over earlier answers) through OpenAI's Responses
API on your own API key, with OpenAI's usage tiers, models and prices written in. "ChatGPT Codex"
here means the codex and GPT models on an API key: a ChatGPT subscription is not a key.

- `codex` on the Plugins view (the AI assistants group): Setup takes `CODEX_API_KEY` (read as
  `OPENAI_API_KEY` too) and `CODEX_ACCOUNT`, the email or account name the key belongs to, shown
  with its evaluations and sent to OpenAI only as a digest (the `safety_identifier`).
- Plan: `CODEX_PLAN` is `free` by default, OpenAI's Free usage tier (a $100 monthly usage limit in
  allowed geographies, per-model limits unpublished), so a key can be tried at once; a key without
  credit is refused with a quota error. `build`, `launch` and `grow` are the tiers by credits bought.
  Connect reads the limits OpenAI's servers send and names the tier they show, applied where you set
  none.
- Model: `CODEX_MODEL`, GPT-5 nano by default (the cheapest); GPT-5 mini, the 5.4 nano and mini, the
  GPT-6 Luna, Terra, Sol and Astra models, GPT-5.3 Codex and GPT-5.5 are in the table.
  `CODEX_EFFORT` sets the API's reasoning effort.
- Caps on this machine, every database together: `CODEX_REQUESTS_PER_DAY` (50),
  `CODEX_TOKENS_PER_DAY` (200,000), `CODEX_MAX_OUTPUT_TOKENS` (1,024); raised on the Plugins view.
- The tables were verified on the date the plugin says (`VERIFIED`) against OpenAI's pricing and
  rate-limit pages; the weekly CI run reads those pages again and fails when a figure is gone, which
  is a new release of this plugin.

Nothing is sent from an offline copy of the app (`LIMINAL_OFFLINE`).

## Install

Into the app's environment, from the app's folder:

```powershell
.venv\Scripts\python.exe -m pip install "platform-plugin-codex @ git+https://github.com/pcxmac-dev/platform-plugin-codex@release/0.2.0"
```

or with the app's plugins (`pip install -e ".[plugins]"` in liminal-app). The app loads it on its next
start. Save the key with the app's `tools/set-key.ps1` or on the Plugins view (it is read from your
user environment variables only, never written to a file).

## Tests

`python -m pytest -q`: fake answers, nothing sent. `LIMINAL_VENDOR_PAGES=1` adds the page check.
