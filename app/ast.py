import sys
import os

class Node:
    def __repr__(self):
        # A generic representation, can be overwritten by subclasses
        return self.__class__.__name__
    @property
    def children(self):
        return []
    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()

class DotNode(Node):
    def __repr__(self):
        return "DotNode()"

class LiteralNode(Node):
    def __init__(self, char):
        self.char = char
    def __repr__(self):
        return f"LiteralNode('{self.char}')"

class CaptureGroupNode(Node):
    def __init__(self, child, index):
        self._child = child # A single Node representing the group's content
        self.index = index # The index of this capturing
    @property
    def children(self):
        return [self._child]
    def __repr__(self):
        return f"CaptureGroupNode(index={self.index}, child={self.children[0]!r})"
       
class CharClassNode(Node): # For /d, /w, etc.
    def __init__(self, type):
        self.type = type # 'digit', 'word', etc.
    def __repr__(self):
        return f"CharClassNode(type='{self.type}')"

class CharSetNode(Node): # For [...]
    def __init__(self, chars, negated):
        self.chars = chars
        self.negated = negated
        # self.rest = rest
    def __repr__(self):
        return f"CharSetNode(chars={self.chars}, negated={self.negated})"
        # return f"CharSetNode(chars={self.chars}, negated={self.negated}, rest={self.rest})"

class ConcatenationNode(Node):
    def __init__(self, children):
        self._children = children # List of Nodes
    @property
    def children(self):
        return self._children
    def __repr__(self):
        return f"ConcatenationNode('{self.children!r}')"
        

class BackreferenceNode(Node):
    def __init__(self, index):
        self.index = index # The number of the group to refer to (e.g., 1 for \1)
    def __repr__(self):
        return f"BackreferenceNode(index={self.index})"


class AnchorNode(Node):
    def __init__(self, type):
        self.type = type # 'start', 'end'
    def __repr__(self):
        return f"AnchorNode(type='{self.type}')"

class AlternationNode(Node):
    def __init__(self, branches):
        self._branches = branches # List of Nodes (each a branch)
    @property
    def children(self):
        return self._branches
    def __repr__(self):
        return f"AlternationNode(branches='{self.children!r}')"

class QuantifierNode(Node):
    def __init__(self, child, type, greedy=True):
        self._child = child
        self.type = type # e.g., 'ONE_OR_MORE', 'ZERO_OR_MORE', 'ZERO_OR_ONE'
        self.greedy = greedy # For future non-greedy support
    @property
    def children(self):
        return [self._child]
    def __repr__(self):
        return f"QuantifierNode(child={self.children[0]!r}, type='{self.type}', greedy={self.greedy})"


class RegexParser: 
    def __init__(self, pattern):
        self.pattern = pattern
        self.pos = 0 # current position in pattern string
        self.group_count = 0 # Add a counter for capturing groups
    
    def parse(self):
        # Top-level parsing: handles alternation
        node = self._parse_alternation()
        if self.pos != len(self.pattern):
            raise ValueError(f"Unexpected characters at end of pattern: {self.pattern[self.pos:]}")
        return node

    def _parse_alternation(self):
        # A | B | C
        left_node = self._parse_concatenation()
        if self._peek() == '|':
            self._consume('|')
            right_node = self._parse_alternation()
            return AlternationNode([left_node, right_node])
        return left_node
    
    def _parse_concatenation(self):
        # A B C (implicit)
        nodes = []
        while True: # Changed loop condition
            current_char = self._peek()
            if current_char is None or current_char in '|)': # Explicitly check for None or '|' or ')'
                break
            
            atom = self._parse_atom() # _parse_atom will handle consuming the char
            if atom:
                nodes.append(atom)
            else:
                # This might happen if _parse_atom consumes a char but returns None (e.g., empty group () is not handled here)
                # Or if it fails to parse a valid atom, we should stop
                break 
        
        if not nodes: 
            return None # Handle cases where no valid concatenation atoms were found
        if len(nodes) == 1: 
            return nodes[0]
        return ConcatenationNode(nodes)

    def _parse_atom(self):
        # Literal, ., [], (), \d, \w, followed by optional quantifier
        char = self._peek()
        # print(f"char in _parse_atom: {char}", file=sys.stderr)
        if char is None:
            return None # Reached end of pattern, no atom found

        node = None
        if char == '(':
            self._consume('(')
            self.group_count += 1 # Increment for a new capture
            group_index = self.group_count
            node = CaptureGroupNode(self._parse_alternation(), group_index) # Group can contain an alternation
            self._expect(')')
        elif char == '[':
            node = self._parse_char_set()
        elif char == '\\':
            node = self._parse_escape_sequence()
        elif char == '.':
            node = DotNode()
            self._consume('.')
        elif char in '^$': # Anchors are atoms
            node = AnchorNode('start' if char == '^' else 'end')
            self._consume(char)
        else: # Literal character
            node = LiteralNode(char)
            self._consume(char)

        # Check for quantifiers only if a node was successfully parsed AND
        # if there's a next character to peek at which is a quantifier.
        if node: # Ensure 'node' was successfully created
            next_char = self._peek() # Get the next character after the atom
            if next_char is not None and next_char in '+*?': # Safely check if it's a quantifier
                quantifier_type = next_char
                self._consume(quantifier_type)
                if quantifier_type == '+':
                    return QuantifierNode(node, 'ONE_OR_MORE')
                elif quantifier_type == '*':
                    return QuantifierNode(node, 'ZERO_OR_MORE')
                elif quantifier_type == '?':
                    return QuantifierNode(node, 'ZERO_OR_ONE')
        
        return node # Return the atom node (possibly quantified)

    def _parse_char_set(self):
        self._consume('[')
        negated = False
        if self._peek() == '^':
            self._consume('^')
            negated = True 
        chars = set()
        while self.pos < len(self.pattern) and self._peek() != ']':
            # Add range support here: e.g., [a-z] 
            chars.add(self._peek())
            self._consume(self._peek())
        self._expect(']')
        # rest = self[i+1:]
        return CharSetNode(chars, negated)

    def _parse_escape_sequence(self):
        self._consume('\\')
        escaped_char = self._peek()
        print(f"escaped_char: {escaped_char}", file=sys.stderr)
        if escaped_char is None:
            raise ValueError("Incomplete escape sequence")

        if escaped_char.isdigit():
            self._consume(escaped_char)
            return BackreferenceNode(int(escaped_char))

        self._consume(escaped_char)
        if escaped_char == 'd':
            print("digit", file=sys.stderr)
            return CharClassNode('digit')
        elif escaped_char == 'w':
            return CharClassNode('word')
        # Add more escape sequences as needed: \s, \S, \D, \W, \. etc.
        return LiteralNode(escaped_char) # For escaped literal chars like '\+'

    def _peek(self):
        if self.pos < len(self.pattern):
            return self.pattern[self.pos]
        return None

    def _consume(self, expected_char=None):
        if expected_char and self._peek() != expected_char:
            raise ValueError(f"Expected '{expected_char}' but found '{self._peek()}' at pos {self.pos}")
        self.pos += 1 

    def _expect(self, char):
        if self.pos >= len(self.pattern) or self.pattern[self.pos] != char:
            raise ValueError(f"Expected '{char}' but found '{self._peek()}' at pos {self.pos}")
        self.pos += 1

def print_ast(node, level=0, prefix=""):
        """
        Recursively prints the AST in a human-readable, indented format.
        """
        indent = "  " * level
        if prefix:
            print(f"{indent}{prefix}{node!r}")
        else:
            print(f"{indent}{node!r}")

        # Define how to access children for different node types
        children_to_print = []
        if isinstance(node, (ConcatenationNode, AlternationNode)):
            children_to_print.extend(node.children if hasattr(node, 'children') else node.branches)
        elif isinstance(node, (CaptureGroupNode, QuantifierNode)):
            if hasattr(node, 'child') and node.child is not None:
                children_to_print.append(node.child)

        for i, child in enumerate(children_to_print):
            # Determine appropriate prefix for child nodes
            child_prefix = f"├── " if i < len(children_to_print) - 1 else "└── "
            print_ast(child, level + 1, prefix=child_prefix)

# Helper to check single char match (from previous turns, can be reused/adapted)
def _is_digit(char):
    return char.isdigit()

def _is_word_char(char):
    return char.isalnum() or char == '_'

def match_possibilities(ast_node, input_line, start_idx, captures):
    """
    Return a list of (end_idx, captures_snapshot) representing all ways ast_node can match input_line[start_idx:].
    """
    results = []

    # Literal
    if isinstance(ast_node, LiteralNode):
        if start_idx < len(input_line) and input_line[start_idx] == ast_node.char:
            results.append((start_idx+1, captures[:]))
        return results

    # CharClassNode
    if isinstance(ast_node, CharClassNode):
        if start_idx < len(input_line):
            ch = input_line[start_idx]
            ok = (ast_node.type == 'digit' and _is_digit(ch)) or (ast_node.type == 'word' and _is_word_char(ch))
            if ok:
                results.append((start_idx+1, captures[:]))
        return results

    # CharSetNode
    if isinstance(ast_node, CharSetNode):
        if start_idx < len(input_line):
            ch = input_line[start_idx]
            is_in = ch in ast_node.chars
            if is_in != ast_node.negated:
                results.append((start_idx+1, captures[:]))
        return results

    # Dot
    if isinstance(ast_node, DotNode):
        if start_idx < len(input_line):
            results.append((start_idx+1, captures[:]))
        return results

    # Backreference
    if isinstance(ast_node, BackreferenceNode):
        if ast_node.index < len(captures) and captures[ast_node.index] is not None:
            text = captures[ast_node.index]
            if input_line.startswith(text, start_idx):
                results.append((start_idx + len(text), captures[:]))
        return results

    # Anchor
    if isinstance(ast_node, AnchorNode):
        if ast_node.type == 'start':
            if start_idx == 0:
                results.append((start_idx, captures[:]))
            return results
        elif ast_node.type == 'end':
            if start_idx == len(input_line):
                results.append((start_idx, captures[:]))
            return results

    # Capture group
    if isinstance(ast_node, CaptureGroupNode):
        child_poss = match_possibilities(ast_node._child, input_line, start_idx, captures)
        for end_idx, cap_snap in child_poss:
            new_snap = cap_snap[:]
            while len(new_snap) <= ast_node.index:
                new_snap.append(None)
            new_snap[ast_node.index] = input_line[start_idx:end_idx]
            results.append((end_idx, new_snap))
        return results

    if isinstance(ast_node, QuantifierNode):
        results = []

        # ZERO_OR_ONE
        if ast_node.type == 'ZERO_OR_ONE':
            # Zero occurrences
            results.append((start_idx, captures[:]))
            # One occurrence
            for end_idx, cap_snapshot in match_possibilities(ast_node._child, input_line, start_idx, captures):
                results.append((end_idx, cap_snapshot[:]))
            return results

        # ONE_OR_MORE
        elif ast_node.type == 'ONE_OR_MORE':
            # First, get the first match
            first_matches = match_possibilities(ast_node._child, input_line, start_idx, captures)
            for end_idx, cap_snapshot in first_matches:
                results.append((end_idx, cap_snapshot[:]))  # at least one occurrence
                # Now try more matches recursively
                more_matches = match_possibilities(ast_node, input_line, end_idx, cap_snapshot)
                for more_end_idx, more_cap_snapshot in more_matches:
                    results.append((more_end_idx, more_cap_snapshot[:]))
            return results

        # ZERO_OR_MORE
        elif ast_node.type == 'ZERO_OR_MORE':
            # Zero occurrences
            results.append((start_idx, captures[:]))
            # One or more occurrences
            first_matches = match_possibilities(ast_node._child, input_line, start_idx, captures)
            for end_idx, cap_snapshot in first_matches:
                results.append((end_idx, cap_snapshot[:]))
                more_matches = match_possibilities(ast_node, input_line, end_idx, cap_snapshot)
                for more_end_idx, more_cap_snapshot in more_matches:
                    results.append((more_end_idx, more_cap_snapshot[:]))
            return results

    # Concatenation
    if isinstance(ast_node, ConcatenationNode):
        results = []
        # print(f"ast_node: {ast_node}", file=sys.stderr)
        def match_from_child(child_idx, pos, caps):
            if child_idx == len(ast_node.children):
                results.append((pos, caps[:]))
                return

            child = ast_node.children[child_idx]
            matches = match_possibilities(child, input_line, pos, caps)

            # --- FIX 1: IMPLEMENT GREEDY MATCHING ---
            # For greedy quantifiers, try the longest possible match first.
            # We reverse the list of matches because they are generated from
            # shortest to longest.
            if isinstance(child, QuantifierNode) and child.greedy:
                matches.reverse()

            for end_idx, cap_snapshot in matches:
                match_from_child(child_idx + 1, end_idx, cap_snapshot)
        # print(f"captures: {captures}", file=sys.stderr)
        match_from_child(0, start_idx, captures)
        # print(f"results: {results}", file=sys.stderr)
        return results


    # Alternation
    if isinstance(ast_node, AlternationNode):
        for branch in ast_node._branches:
            branch_poss = match_possibilities(branch, input_line, start_idx, captures)
            for end_idx, cap_snap in branch_poss:
                results.append((end_idx, cap_snap))
        return results

    return results

def match_entire_ast(ast, input_line, parser):
    # Try to match the pattern starting from every position in the input string.
    # If the pattern starts with '^', we only try from the beginning.
    if parser.pattern.startswith('^'):
        start_positions = [0]
    else:
        start_positions = range(len(input_line) + 1)

    for pos in start_positions:
        initial_caps = [None] * (parser.group_count + 1)
        
        # Get all possible ways the pattern can match from the current position `pos`.
        possibilities = match_possibilities(ast, input_line, pos, initial_caps)

        # --- FIX 2: ACCEPT ANY VALID MATCH ---
        # If the list of possibilities is not empty, a match has been found.
        # The logic within AnchorNode handles the '$' anchor, so if a pattern
        # must match to the end, 'possibilities' will only be populated if it does.
        if possibilities:
            # We found a match, so we can exit successfully.
            return True, possibilities[0][0], possibilities[0][1]

    # If we've tried all starting positions and found no match.
    return False, None, None

def search_file(filename, ast, parser, print_filenames):
    """
    Searches a single file for the pattern defined by the AST.

    Returns:
        True if a match was found in this file, False otherwise.
    """
    file_had_match = False
    try:
        with open(filename, 'r') as f:
            for line in f:
                clean_line = line.strip()
                success, _, _ = match_entire_ast(ast, clean_line, parser)
                if success:
                    if print_filenames:
                        # Prepend the filename to the matched line.
                        print(f"{filename}:{clean_line}")
                    else:
                        print(clean_line)
                    file_had_match = True
    except Exception as e:
        # Silently skip files that can't be read (e.g., binary files, permissions errors).
        # You could print an error to stderr here if you prefer.
        pass
    
    return file_had_match

def main():
    # --- 1. Argument Parsing ---
    args = sys.argv[1:]
    recursive = False
    pattern_str = None
    paths = []

    # Handle flags that can appear anywhere, like -r
    if '-r' in args:
        recursive = True
        args.remove('-r')
    
    # The -E flag must be followed by the pattern
    try:
        if '-E' in args:
            e_index = args.index('-E')
            pattern_str = args[e_index + 1]
            # Remove both -E and the pattern from the list
            args.pop(e_index)
            args.pop(e_index)
        else:
            if len(args) >= 2:
                 pattern_str = args[0]
                 args.pop(0)

        paths = args
    except IndexError:
        print("Usage: python3 ast.py [-r] -E <pattern> [path1] [path2] ...", file=sys.stderr)
        exit(2)

    # --- THIS IS THE FIX ---
    # Only exit if the pattern is missing. It's okay if 'paths' is empty.
    if not pattern_str:
        print("Usage: python3 ast.py [-r] -E <pattern> [path1] [path2] ...", file=sys.stderr)
        exit(2)
    
    # --- 2. Main Logic ---
    any_match_found = False
    try:
        parser = RegexParser(pattern_str)
        ast = parser.parse()

        print_filenames = recursive or len(paths) > 1

        if paths:
            for path in paths:
                if recursive and os.path.isdir(path):
                    for dirpath, _, filenames in os.walk(path):
                        for filename in filenames:
                            full_path = os.path.join(dirpath, filename)
                            if search_file(full_path, ast, parser, print_filenames=True):
                                any_match_found = True
                elif os.path.isfile(path):
                    if search_file(path, ast, parser, print_filenames):
                        any_match_found = True
                elif not os.path.isdir(path):
                     print(f"Error: '{path}' is not a valid file or directory.", file=sys.stderr)
        
        else:
            input_text = sys.stdin.read().strip()
            for line in input_text.splitlines():
                clean_line = line.strip()
                success, _, _ = match_entire_ast(ast, clean_line, parser)
                if success:
                    print(clean_line)
                    any_match_found = True

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        exit(1)

    # --- 3. Exit Status ---
    if any_match_found:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()