#!/usr/bin/env python3
"""Discord transport.

Outbound uses plain webhooks over urllib — zero dependencies, always available.
Inbound (dev slash commands) uses a gateway bot and requires `pip install discord.py`.
If discord.py is absent the daemon still runs; only slash commands are disabled.
"""
import json
import os
import ssl
import urllib.error
import urllib.request

MAX_LEN = 1900  # leave headroom under Discord's 2000-char limit


def _chunks(text, size=MAX_LEN):
    text = text or ""
    if len(text) <= size:
        return [text]
    out, buf = [], ""
    for line in text.splitlines(keepends=True):
        if len(buf) + len(line) > size:
            out.append(buf)
            buf = ""
        # single line longer than a chunk: hard-split it
        while len(line) > size:
            out.append(line[:size])
            line = line[size:]
        buf += line
    if buf:
        out.append(buf)
    return out


class Webhook:
    """Fire-and-forget outbound messages. Never raises into the scheduler."""

    def __init__(self, url, dev_id="", trainee_id="", quiet=False):
        self.url = (url or "").strip()
        self.dev_id = str(dev_id or "").strip()
        self.trainee_id = str(trainee_id or "").strip()
        self.quiet = quiet
        self._ctx = ssl.create_default_context()

    def mention(self, who):
        uid = {"dev": self.dev_id, "trainee": self.trainee_id}.get(who, "")
        return f"<@{uid}>" if uid else ""

    def send(self, content="", embed=None, mentions=()):
        if self.quiet or not self.url:
            print(f"[discord:disabled] {content[:160]}")
            return False
        prefix = " ".join(m for m in (self.mention(w) for w in mentions) if m)
        body = (prefix + " " + content).strip() if prefix else content
        ok = True
        parts = _chunks(body)
        for i, part in enumerate(parts):
            payload = {"content": part, "allowed_mentions": {"parse": ["users"]}}
            if embed and i == len(parts) - 1:
                payload["embeds"] = [embed]
            ok &= self._post(payload)
        return ok

    def _post(self, payload):
        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json",
                     "User-Agent": "UstaadOS/1.0"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15, context=self._ctx) as r:
                return r.status in (200, 204)
        except urllib.error.HTTPError as e:
            print(f"[discord] HTTP {e.code}: {e.read()[:200]!r}")
        except Exception as e:  # network flaps must never kill the loop
            print(f"[discord] send failed: {e}")
        return False


def embed(title, description="", fields=None, color=0x5865F2, footer=None):
    e = {"title": title[:250], "description": (description or "")[:4000], "color": color}
    if fields:
        e["fields"] = [
            {"name": str(n)[:250], "value": (str(v) or "-")[:1020], "inline": bool(i)}
            for n, v, i in fields
        ][:25]
    if footer:
        e["footer"] = {"text": str(footer)[:2000]}
    return e


# --------------------------------------------------------------------------
# Inbound: gateway bot (optional)
# --------------------------------------------------------------------------
def run_bot(cfg, handlers, log=print):
    """Blocking. Runs the slash-command bot. Returns False if discord.py missing."""
    try:
        import discord
        from discord import app_commands
    except ImportError:
        log("[bot] discord.py not installed — slash commands disabled. "
            "Install with: pip install -U discord.py")
        return False

    token = (cfg.get("bot_token") or "").strip()
    guild_id = str(cfg.get("guild_id") or "").strip()
    dev_id = str(cfg.get("dev_user_id") or "").strip()
    if not token or not dev_id:
        log("[bot] bot_token or dev_user_id missing — slash commands disabled.")
        return False

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)
    guild = discord.Object(id=int(guild_id)) if guild_id.isdigit() else None

    def is_dev(inter):
        return str(inter.user.id) == dev_id

    async def deny(inter):
        await inter.response.send_message(
            "This command is restricted to the dev.", ephemeral=True)

    async def long_reply(inter, text):
        for i, part in enumerate(_chunks(text or "(no output)")):
            if i == 0:
                await inter.followup.send(part)
            else:
                await inter.channel.send(part)

    @tree.command(name="dev", description="Run a request against Ustaad in dev mode",
                  guild=guild)
    @app_commands.describe(query="What you want Ustaad to do or report on")
    async def dev_cmd(inter, query: str):
        if not is_dev(inter):
            return await deny(inter)
        await inter.response.defer(thinking=True)
        out = await client.loop.run_in_executor(None, handlers["dev_query"], query)
        await long_reply(inter, out)

    @tree.command(name="status", description="Short state digest", guild=guild)
    async def status_cmd(inter):
        if not is_dev(inter):
            return await deny(inter)
        await inter.response.defer(thinking=True)
        await long_reply(inter, handlers["status"]())

    @tree.command(name="report", description="Full progress report", guild=guild)
    async def report_cmd(inter):
        if not is_dev(inter):
            return await deny(inter)
        await inter.response.defer(thinking=True)
        await long_reply(inter, handlers["report"]())

    @tree.command(name="directive", description="Queue guidance for the trainee's next standup",
                  guild=guild)
    @app_commands.describe(text="Guidance, shown to him verbatim as from you")
    async def directive_cmd(inter, text: str):
        if not is_dev(inter):
            return await deny(inter)
        await inter.response.send_message(handlers["directive"](text), ephemeral=True)

    @tree.command(name="pause", description="Silence notifications for N hours", guild=guild)
    @app_commands.describe(hours="How many hours to stay quiet")
    async def pause_cmd(inter, hours: int = 12):
        if not is_dev(inter):
            return await deny(inter)
        await inter.response.send_message(handlers["pause"](hours), ephemeral=True)

    @tree.command(name="resume", description="Resume notifications", guild=guild)
    async def resume_cmd(inter):
        if not is_dev(inter):
            return await deny(inter)
        await inter.response.send_message(handlers["resume"](), ephemeral=True)

    @client.event
    async def on_ready():
        try:
            if guild:
                tree.copy_global_to(guild=guild)
                await tree.sync(guild=guild)
            else:
                await tree.sync()
            log(f"[bot] ready as {client.user} — slash commands synced")
        except Exception as e:
            log(f"[bot] command sync failed: {e}")

    try:
        client.run(token, log_handler=None)
    except Exception as e:
        log(f"[bot] crashed: {e}")
    return True
