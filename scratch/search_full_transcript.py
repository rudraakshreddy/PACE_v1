import os, json

log_dir = r"C:\Users\Rudraaksh\.gemini\antigravity\brain\ba7040d6-3882-48b7-96fb-ba1cd5a95605\.system_generated\logs"
transcript_path = os.path.join(log_dir, "transcript_full.jsonl")

if not os.path.exists(transcript_path):
    print("Transcript not found at", transcript_path)
else:
    print("Transcript exists. Searching transcript_full...")
    count = 0
    with open(transcript_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            low = line.lower()
            if "ngrok" in low or "free.app" in low or "localtunnel" in low or "friend" in low or "colleague" in low or "http" in low:
                try:
                    obj = json.loads(line)
                    # Look at tools used, output, or text content
                    content = obj.get("content", "")
                    if content and ("ngrok" in content.lower() or "free.app" in content.lower() or "friend" in content.lower() or "colleague" in content.lower()):
                        print(f"Line {i+1} Content: {content[:300]}")
                        count += 1
                    tool_calls = obj.get("tool_calls", [])
                    for tc in tool_calls:
                        args = str(tc.get("arguments", ""))
                        if "ngrok" in args.lower() or "free.app" in args.lower():
                            print(f"Line {i+1} Tool Call: {tc.get('name')} -> {args[:300]}")
                            count += 1
                except Exception as e:
                    pass
    print(f"Total matching lines in transcript_full: {count}")
