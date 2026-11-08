"""Export rated interactions as JSONL: the seed for evals / few-shot / fine-tuning."""
import json
import sys
sys.path.insert(0, ".")
from cos import db

for r in db.q("SELECT user_msg, reply, rating FROM interactions WHERE rating IS NOT NULL"):
    print(json.dumps(r))
