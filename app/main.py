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
    alternatives = split_alternatives(pattern)
    if len(alternatives) > 1: # Only proceed if there's actually an "|" at the top level
        print(f"Alteration detected: Alternatiives: {str(alternatives)}", file=sys.stderr)
        for sub_pattern in alternatives:
            if matchhere(sub_pattern, input_line):
                return True
        return False
    if len(pattern) >= 2 and pattern[1] == "+":
        # We found a pattern segment like "X+" where X is pattern[0]
        char_to_match = pattern[0]
        rest_of_pattern = pattern[2:]
        
        # Try to match the character 'X' at least once
        if not input_line or not matchchar(char_to_match, input_line[0]):
            return False

        # If it matches at least once, then try to match it one or more times
        # (greedy approach with backtracking)
        
        # Option 1: Match more 'X's (recursive call for X+)
        if matchhere(pattern, input_line[1:]):
            return True
        
        # Option 2: Stop matching 'X's and try to match the rest of the pattern
        if matchhere(rest_of_pattern, input_line[1:]):
            return True
        
        # if neither option works
        return False 
        
    
    if len(pattern) >= 2 and pattern[1] == "?":
        if len(pattern) == 2:
            included_char = pattern[0]
            excluded_char = "" 
        else:
            # We know from the first check that len(pattern) is at least two
            # so this else handles when len(pattern) > 2
            included_char = pattern[0] + pattern[2:]
            excluded_char = pattern[2:]
        print(f"included_char: {included_char}", file=sys.stderr)
        print(f"excluded_char: {excluded_char}", file=sys.stderr)
        if matchchar(included_char, input_line) or matchchar(excluded_char, input_line):
            return True 

        return False 

    if pattern.startswith("."):
        if not input_line:
            return False
        return matchhere(pattern[1:], input_line[1:])
    if pattern.startswith("("):
        try: 
            closing_paren_index = find_matching_paraenthesis(pattern, 0)
        except ValueError as e:
            raise e #Re-raise if malformed
        
        inner_pattern = pattern[1:closing_paren_index]
        remaining_pattern = pattern[closing_paren_index + 1]
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
        if input_line and (input_line[0].isalnum() or input_line[0] == "_"):
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

def split_alternatives(pattern):
    parts = []
    current_part = [] 
    depth = 0 
    for char in pattern:
        if char == '(' and depth == 0: # Start of a top-level group
            current_part.append(char)
            depth += 1
        elif char == ')' and depth > 0: # End of a top-level group
            current_part.append(char)
            depth -= 1
        elif char == '|' and depth == 0: # Top-level alternative
            parts.append("".join(current_part))
            current_part = []
        else: # Any other character or character within a group
            current_part.append(char)
    if current_part: # Add the last part
        parts.append("".join(current_part))
    return parts

def matchchar(pattern_char, input_char):
    """
    Checks if a single character pattern matches a single input character. 
    Handles '.', '\\d', '\\w', and literal characters.
    """
    if not input_char:
        return False
    if pattern_char == '.':
        return True
    if pattern_char == '\\d':
        return input_char.isdigit()
    if pattern_char == '\\w':
        return input_char.isalnum() or input_char == '_'
    return pattern_char == input_char


def find_matching_paraenthesis(pattern, start_index):
    depth = 0
    for i in range(start_index, len(pattern)):
        if pattern[i] == '(':
            depth += 1
        elif pattern[i] == ')':
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("Unmatched opening paraenthesis")

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
