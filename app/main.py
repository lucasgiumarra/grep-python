import sys

# import pyparsing - available if you need it!
# import lark - available if you need it!


def match(pattern, input_line):
    for i in range(len(input_line) + 1):
        if pattern[0] == "^":
            return matchhere(pattern[1:], input_line)
        if matchhere(pattern, input_line[i:]):
            return True
    return False


def matchhere(pattern, input_line):
    if not pattern:
        return True
    if len(pattern) == 1:
        return pattern in input_line
    if pattern.startswith("["):
        group, rest, negate_char_group = parse_char_group(pattern)
        if not input_line:
            return False
        if (input_line[0] in group) != negate_char_group:
            return matchhere(rest, input_line[1:])
        return False
    if pattern.startswith("\d"):
        if input_line and input_line[0].isdigit():
            return matchhere(pattern[2:], input_line[1:])
        return False
    if pattern.startswith("\w"):
        if input_line and input_line[0].isalpha():
            return matchhere(pattern[2:], input_line[1:])
        return False
    if pattern[0] == "$" and pattern[1] == "":
        return input_line == ""
    if pattern[0] == input_line[0]:
        print("pattern[0]: " + pattern[0], file=sys.stderr)
        return matchhere(pattern[1:], input_line[1:])
    return False

# def matchstar():
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

    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    # Uncomment this block to pass the first stage
    # if match_pattern(input_line, pattern):
    if match(pattern, input_line):
        print("pattern: " + pattern, file=sys.stderr)
        print("exit 0", file=sys.stderr)
        exit(0)
    else:
        print("exit 1", file=sys.stderr)
        exit(1)


if __name__ == "__main__":
    main()
