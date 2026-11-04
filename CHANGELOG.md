# Changelog

## 0.2.0 (2026-11-03)

Renamed `plugin-platform-codex` (the package `plugin_platform_codex`; it was `platform-plugin-codex`) on 2026-11-03: the naming by system (plugins are `plugin-<app>-<name>`), on liminal-libs 1.4.0 (`liminal_libs`, the library renamed with it).

The first release: `CodexPlugin` (an `AssistantPlugin`, plugin API 2.0, liminal-libs 1.3.0) and
`CodexAssistant` on OpenAI's Responses API. The plans (the Free usage tier, which sends; Build,
Launch and Grow by credits bought, with their limits and monthly usage limits), the models (GPT-5
nano by default, GPT-5 mini, the 5.4 nano and mini, GPT-6 Luna, Terra, Sol and Astra, GPT-5.3 Codex,
GPT-5.5, with their prices per million tokens) and the pages they were written from, verified
2026-11-03; Connect reads the tier from the x-ratelimit headers and compares the models listed with
the table; the weekly CI run reads the pages again. Every error scrubbed of the key and the account;
a quota refusal is final, not retried.
