"""gemini_client.py — the call_model(prompt)->str seam for blog_ingest.py, backed by Gemini."""
import os, time, requests

MODEL = "gemini-3.1-flash-lite"  # confirmed working + has free-tier quota (15 RPM / 500 RPD) on this key
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

def call_model(prompt, _retried=False):
    key = os.environ["GEMINI_API_KEY"]
    r = requests.post(
        URL, params={"key": key},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=60,
    )
    if r.status_code == 429 and not _retried:
        time.sleep(45)
        return call_model(prompt, _retried=True)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]
