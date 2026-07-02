import os, json

brain_dir = r"C:\Users\Rudraaksh\.gemini\antigravity\brain"
search_terms = ["ngrok", "free.app", "localtunnel", "friend", "colleague", "http://", "https://"]

if os.path.exists(brain_dir):
    for d in os.listdir(brain_dir):
        transcript_path = os.path.join(brain_dir, d, ".system_generated", "logs", "transcript_full.jsonl")
        if os.path.exists(transcript_path):
            with open(transcript_path, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    low = line.lower()
                    if any(term in low for term in search_terms):
                        try:
                            obj = json.loads(line)
                            content = obj.get("content", "")
                            # If it matches ngrok or free.app, print it
                            if content and any(term in content.lower() for term in ["ngrok", "free.app", "localtunnel", "colleague", "friend"]):
                                print(f"Conv {d} Line {idx+1}: {content[:300]}")
                        except Exception:
                            pass
else:
    print("Brain directory does not exist")
