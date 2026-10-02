# Security

- The MCP and REST servers bind to **127.0.0.1** by default. Listening on any other address requires
  `allow_remote = true` **and** an `api_token` in `~/.config/astrology-consultation/config.toml`; requests must then
  carry `Authorization: Bearer <token>`.
- No access logs are written and birth data is never logged. Tool errors return only the reason for a refusal.
- `skill://` resources and report paths are confined to their folders; only skill documents can be read.
- Default privacy mode is `private`: no calculation leaves the computer. The optional VedAstro cross-check runs only
  in `hybrid` mode and records what it sends.
- The plugin's launcher installs Python packages from PyPI into the plugin's own data folder; it runs nothing else.

Report a vulnerability privately through GitHub's "Report a vulnerability" (Security tab) rather than a public issue.
