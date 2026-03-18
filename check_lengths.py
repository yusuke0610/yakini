import sys

for arg in sys.argv[1:]:
    with open(arg, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            line = line.rstrip('\n')
            if len(line) > 79:
                print(f"{arg}:{i}: length {len(line)}")
