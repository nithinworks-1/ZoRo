import asyncio
import hmac
import os
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from . import agent, config, db, tools


def owner_only(fn):
    async def w(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user is None or not config.OWNER_ID or user.id != config.OWNER_ID:
            return
        await fn(update, ctx)
    return w


@owner_only
async def on_text(update, ctx):
    reply = await asyncio.to_thread(agent.respond, update.message.text)
    await update.message.reply_text(reply)


_FAILS = {}  # user_id -> [timestamps of wrong passwords]
MAX_FAILS, LOCK_SECS = 5, 900


async def on_guest(update, ctx):
    """Anyone who is not the owner: password gate, then a limited tool-less chat."""
    user = update.effective_user
    if user is None or update.message is None or not config.GUEST_PASSWORD:
        return  # no password configured: stay silent, as before
    uid, text = user.id, update.message.text or ""
    if db.q("SELECT 1 FROM guests WHERE user_id=?", (uid,)):
        reply = await asyncio.to_thread(agent.respond_guest, uid, text)
        return await update.message.reply_text(reply)
    now = time.time()
    fails = [t for t in _FAILS.get(uid, []) if now - t < LOCK_SECS]
    _FAILS[uid] = fails
    if len(fails) >= MAX_FAILS:
        return  # locked out; don't even reply
    if hmac.compare_digest(text.strip().encode(), config.GUEST_PASSWORD.encode()):
        db.x("INSERT OR REPLACE INTO guests(user_id, ts) VALUES(?,?)", (uid, now))
        _FAILS.pop(uid, None)
        try:
            await update.message.delete()  # don't leave the password in the chat
        except Exception:
            pass
        return await ctx.bot.send_message(uid, "Access granted. You can chat now (limited guest mode).")
    fails.append(now)
    await update.message.reply_text("This bot is private. Send the password to continue.")


@owner_only
async def pending(update, ctx):
    rows = db.q("SELECT * FROM pending WHERE status='pending'")
    await update.message.reply_text("\n\n".join(f"#{r['id']} {r['kind']}: {r['payload']}" for r in rows) or "Nothing pending.")


@owner_only
async def approve(update, ctx):
    pid = int(ctx.args[0])
    rows = db.q("SELECT * FROM pending WHERE id=? AND status='pending'", (pid,))
    if not rows:
        return await update.message.reply_text("Not found.")
    db.x("UPDATE pending SET status='approved' WHERE id=?", (pid,))
    await update.message.reply_text("Running…")
    out = await asyncio.to_thread(tools.execute_approved, rows[0])
    await update.message.reply_text(out or "(no output)")


@owner_only
async def reject(update, ctx):
    db.x("UPDATE pending SET status='rejected' WHERE id=?", (int(ctx.args[0]),))
    await update.message.reply_text("Rejected.")


@owner_only
async def good_bad(update, ctx):
    """/good or /bad rates the last reply; feeds your eval/training set."""
    score = 1 if update.message.text.startswith("/good") else -1
    db.x("UPDATE interactions SET rating=? WHERE id=(SELECT MAX(id) FROM interactions)", (score,))
    await update.message.reply_text("Noted.")


@owner_only
async def teach(update, ctx):
    """/teach <issue> | <fix>  — adds an entry to the issues knowledge base."""
    title, sep, solution = " ".join(ctx.args).partition("|")
    if not sep or not title.strip() or not solution.strip():
        return await update.message.reply_text("Usage: /teach <issue> | <fix>")
    from . import tools_ext
    r = tools_ext.save_issue(title.strip(), solution.strip())
    await update.message.reply_text(f"Learned issue #{r['id']}.")


async def tick(ctx: ContextTypes.DEFAULT_TYPE):
    for r in db.q("SELECT * FROM reminders WHERE sent=0 AND fire_at<=?", (time.time(),)):
        await ctx.bot.send_message(config.OWNER_ID, f"⏰ {r['text']}")
        db.x("UPDATE reminders SET sent=1 WHERE id=?", (r["id"],))


def main():
    if not config.OWNER_ID:
        raise SystemExit("TELEGRAM_OWNER_ID is not set; refusing to start (bot would be unrestricted).")
    app = Application.builder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()
    # Drop every update not from the owner before any handler sees it.
    me = filters.User(user_id=config.OWNER_ID)
    app.add_handler(CommandHandler("pending", pending, filters=me))
    app.add_handler(CommandHandler("approve", approve, filters=me))
    app.add_handler(CommandHandler("reject", reject, filters=me))
    app.add_handler(CommandHandler(["good", "bad"], good_bad, filters=me))
    app.add_handler(CommandHandler("teach", teach, filters=me))
    app.add_handler(MessageHandler(me & filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(MessageHandler(~me & filters.TEXT, on_guest))
    app.job_queue.run_repeating(tick, interval=30, job_kwargs={"misfire_grace_time": 120})
    app.run_polling()


if __name__ == "__main__":
    main()
