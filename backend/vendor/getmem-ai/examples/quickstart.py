"""Minimal end-to-end usage of the getmem Python SDK.

Run with a real key:
    GETMEM_API_KEY=gm_live_xxx python examples/quickstart.py
"""

import os

import getmem_ai as getmem

api_key = os.environ["GETMEM_API_KEY"]
user_id = os.environ.get("GETMEM_USER_ID", "demo_user")

with getmem.init(api_key) as mem:
    # Store a couple of conversation turns.
    result = mem.ingest(
        user_id=user_id,
        messages=[
            {"role": "user", "content": "I want to travel to Thailand in spring"},
            {"role": "assistant", "content": "Great choice! Bangkok is lovely then."},
        ],
        tags=["travel"],
    )
    print(f"stored={result.memories_stored} queued={result.extraction_queued}")

    # Retrieve assembled context for a query.
    ctx = mem.get(user_id=user_id, query="What are my travel plans?", token_budget=2000)
    print(f"context ({ctx.meta.total_ms} ms):\n{ctx.context}")
    for m in ctx.memories:
        print(f"  - [{m.type}] {m.text} ({m.relevance_score})")
