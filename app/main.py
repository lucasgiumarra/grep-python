import sys

# import pyparsing - available if you need it!
# import lark - available if you need it!

def match(pattern, input_line):
    for i in range(len(input_line) + 1):
        if matchhere(pattern, input_line[i:]):
            return True
    return False


def matchhere(pattern, input_line):
    if not pattern:
        return True
    if input_line and pattern_matches(pattern[0], input_line[0]):
        return True
    return False

# def matchstar():

def pattern_matches(pattern, input_char):
    if pattern == "\d":
        for char in input_char:
            if "0" <= char <= "9":
                return True
        return False
    elif pattern == "\w":
        for char in input_char:
            if "A" <= char <= "Z" or "a" <= char <= "z" or char == "_":
                return True
        return False
    # this negative character group logic must come before the positive group
    # logic becuase otherwise a negative character group will run under a
    # positive group logic
    elif "[" in pattern and "]" in pattern and "^" in pattern:
        for p in pattern:
            if p == "[" or p == "]" or p == "^":
                continue
            if p not in input_char:
                return True
        return False
    # positive character groups
    elif "[" in pattern and "]" in pattern:
        if "^" in pattern:
            for p in pattern:
                if p == "[" or p == "]" or p == "^":
                    continue
                if p not in input_char:
                    return True
            return False
        else:
            for p in pattern:
                if p == "[" or p == "]":
                    continue
                if p in input_char:
                    return True
            return False
    return False



def match_pattern(input_line, pattern):
    if len(pattern) == 1:
        return pattern in input_line
    elif pattern == "\d":
        for char in input_line:
            if "0" <= char <= "9":
                return True
        return False
    elif pattern == "\w":
        for char in input_line:
            if "A" <= char <= "Z" or "a" <= char <= "z" or char == "_":
                return True
        return False
    # this negative character group logic must come before the positive group
    # logic becuase otherwise a negative character group will run under a
    # positive group logic
    elif "[" in pattern and "]" in pattern and "^" in pattern:
        for p in pattern:
            if p == "[" or p == "]" or p == "^":
                continue
            if p not in input_line:
                return True
        return False
    # positive character groups
    elif "[" in pattern and "]" in pattern:
        if "^" in pattern:
            for p in pattern:
                if p == "[" or p == "]" or p == "^":
                    continue
                if p not in input_line:
                    return True
            return False
        else:
            for p in pattern:
                if p == "[" or p == "]":
                    continue
                if p in input_line:
                    return True
            return False
    else:
        raise RuntimeError(f"Unhandled pattern: {pattern}")


def main():
    pattern = sys.argv[2]
    input_line = sys.stdin.read()

    if sys.argv[1] != "-E":
        print("Expected first argument to be '-E'")
        exit(1)

    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    # Uncomment this block to pass the first stage
    if match_pattern(input_line, pattern):
    # if match(pattern, input_line):
        print("pattern: " + pattern, file=sys.stderr)
        print("exit 0", file=sys.stderr)
        exit(0)
    else:
        print("exit 1", file=sys.stderr)
        exit(1)


if __name__ == "__main__":
    main()
