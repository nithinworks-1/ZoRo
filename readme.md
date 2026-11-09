# Chief of Staff (COS)

Local-model personal assistant (Ollama, no API costs), controlled from Telegram.

## Setup

    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env   # fill in Telegram token + id (@userinfobot); then: ollama pull qwen3.5:4b
    python -m cos.bot

## Chat commands

/pending, /approve <id>, /reject <id>, /good, /bad, /teach <issue> | <fix>

## Teaching it about issues

Ask about any problem ("wifi keeps dropping", "pip install fails") and the bot searches its
`issues` table first, then falls back to general knowledge. Teach it fixes with
`/teach <issue> | <fix>`, or just tell it "that worked, remember it" and it calls `save_issue`.

## Improving it with your data

Every turn is logged in `interactions`. Rate replies with /good and /bad, then
`python evals/export.py > evals/rated.jsonl` to build an eval set and few-shot examples.

## Roadmap

1. Gmail read/draft/send (OAuth) in `execute_approved`
2. Calendar, messages (WhatsApp/iMessage), morning brief via scheduler
3. Eval harness replaying rated interactions on prompt/model changes
4. LoRA fine-tune the local model (mlx-lm) on rated data once evals show a gap

## SETUP

1. install venv
2. install or use CLi and get ollama or openclaw any other model
3. open terminal and install pip install -r reqiurements.txt
4. pull the model " ollama pull qwen3.5:9b
   5.run it by python -m cos.bot

## Telegram bot Setup

1. search for botfather and select newbot
2. Get the token id
3. search for userinfonbot and get user ID
# ZoRo
