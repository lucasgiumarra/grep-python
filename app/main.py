import sys


def match(pattern, input_line):
    for i in range(len(input_line) + 1):
        if pattern[0] == "^":
            return matchhere(pattern[1:], input_line)
        if matchhere(pattern, input_line[i:]):
            return True
    return False


# If returns false match() will go through the next iteration of the for loop
# If returns true then match will return true bc a match was found
def matchhere(pattern, input_line):
    print("pattern: " + pattern, file=sys.stderr)
    print("input_line: " + input_line, file=sys.stderr)

    if not pattern:
        return True
    if "+" in pattern:
        if len(input_line) < len(pattern) - 1:
            return False
        plus_index = pattern.index("+")
        try:
            assert plus_index > 0
        except AssertionError as e:
            print(f"Need a character preceeding '+': {e}")

        char_pattern = pattern[:plus_index]
        if char_pattern in input_line:
            return True

    if pattern.startswith("["):
        group, rest, negate_char_group = parse_char_group(pattern)
        if not input_line:
            return False
        if (input_line[0] in group) != negate_char_group:
            return matchhere(rest, input_line[1:])
        return False
    if pattern.startswith("\\d"):
        if input_line and input_line[0].isdigit():
            return matchhere(pattern[2:], input_line[1:])
        return False
    if pattern.startswith("\\w"):
        if input_line and input_line[0].isalpha():
            return matchhere(pattern[2:], input_line[1:])
        return False
    if pattern == "$" and input_line == "":
        return True
    if len(input_line) > 0 and pattern[0] == input_line[0]:
        return matchhere(pattern[1:], input_line[1:])
    return False


def parse_char_group(pattern):
    assert pattern[0] == "["
    negate = False
    i = 1
    if pattern[i] == "^":
        negate = True
        i += 1
    chars = set()
    while i < len(pattern) and pattern[i] != "]":
        chars.add(pattern[i])
        i += 1
    if i == len(pattern):
        raise ValueError("Unterminated character group")
    rest = pattern[i+1:]
    return chars, rest, negate


def main():
    pattern = sys.argv[2]
    input_line = sys.stdin.read()

    if sys.argv[1] != "-E":
        print("Expected first argument to be '-E'")
        exit(1)

    print("Logs from your program will appear here!", file=sys.stderr)

    if match(pattern, input_line):
        print("pattern: " + pattern, file=sys.stderr)
        print("exit 0", file=sys.stderr)
        exit(0)
    else:
        print("exit 1", file=sys.stderr)
        exit(1)


if __name__ == "__main__":
    main()
