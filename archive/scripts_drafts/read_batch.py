import json, os, sys

batch_dir = r"C:\Users\Administrator\WorkBuddy\CyberpunkRED\solo\parse_output\mcp_insert"

# Get the batch filename from command line arg
if len(sys.argv) > 1:
    fname = sys.argv[1]
else:
    # List all batch files
    for f in sorted(os.listdir(batch_dir)):
        if f.endswith('.json') and not f.startswith('_'):
            print(f)
    sys.exit(0)

path = os.path.join(batch_dir, fname)
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Output compact JSON (no trailing newline to avoid issues)
result = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
sys.stdout.write(result)
