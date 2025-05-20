import sys

# import pyparsing - available if you need it!
# import lark - available if you need it!


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
        print("exit 0", file=sys.stderr)
        exit(0)
    else:
        print("exit 1", file=sys.stderr)
        exit(1)


if __name__ == "__main__":
    main()
