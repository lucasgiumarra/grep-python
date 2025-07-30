import sys

class Node:
    def __repr__(self):
        # A generic representation, can be overwritten by subclasses
        return self.__class__.__name__

class DotNode(Node):
    def __repr__(self):
        return "DotNode()"

class LiteralNode(Node):
    def __init__(self, char):
        self.char = char
    def __repr__(self):
        return f"LiteralNode('{self.char}')"

class GroupNode(Node):
    def __init__(self, child):
        self.child = child # A single Node representing the group's content
    def __repr__(self):
        return f"GroupNode('{self.child!r}')"
       
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
        self.children = children # List of Nodes
    def __repr__(self):
        return f"ConcatenationNode('{self.children!r}')"

class AnchorNode(Node):
    def __init__(self, type):
        self.type = type # 'start', 'end'
    def __repr__(self):
        return f"AnchorNode(type='{self.type}')"

class AlternationNode(Node):
    def __init__(self, branches):
        self.branches = branches # List of Nodes (each a branch)
    def __repr__(self):
        return f"AlternationNode(branches='{self.branches}')"

class QuantifierNode(Node):
    def __init__(self, child, type, greedy=True):
        self.child = child
        self.type = type # e.g., 'ONE_OR_MORE', 'ZERO_OR_MORE', 'ZERO_OR_ONE'
        self.greedy = greedy # For future non-greedy support
    def __repr__(self):
        return f"QuantifierNode(child={self.child!r}, type='{self.type}', greedy={self.greedy})"


class RegexParser: 
    def __init__(self, pattern):
        self.pattern = pattern
        self.pos = 0 # current position in pattern string
    
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
        print(f"char in _parse_atom: {char}", file=sys.stderr)
        if char is None:
            return None # Reached end of pattern, no atom found

        node = None
        if char == '(':
            self._consume('(')
            node = GroupNode(self._parse_alternation()) # Group can contain an alternation
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
        elif isinstance(node, (GroupNode, QuantifierNode)):
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


def match_ast(ast_node, input_line):
    """
    Attempts to match the AST node against the input_line.
    Returns (True, remaining_input) on success, (False, None) on failure.
    """
    # This is where your matchhere logic gets translated to AST traversal
    # Implement the logic for each Node type (LiteralNode, ConcatenationNode, etc.)
    # as discussed above.

    # Example for LiteralNode:
    if isinstance(ast_node, LiteralNode):
        if not input_line or input_line[0] != ast_node.char:
            return False, None
        return True, input_line[1:]
    
    if isinstance(ast_node, CharClassNode):
        if not input_line:
            return False, None
        
        char = input_line[0]
        matched = False

        if ast_node.type == 'digit':
            matched = _is_digit(char)
        elif ast_node.type == 'word':
            matched = _is_word_char(char)
        
        if matched: 
            return True, input_line[1:] # Consume the character and continue
        else: 
            return False, None

    if isinstance(ast_node, CharSetNode):
        group, rest, negate_char_group = ast_node.char, ast_node.rest, ast_node.negated
        if not input_line:
            return False, None
        
        char_to_check = input_line[0]
        # 2. Determine if the character matches the set based on `negated` flag
        #    If `negated` is True, the character should NOT be in the set.
        #    If `negated` is False, the character SHOULD be in the set.
        is_in_set = char_to_check in ast_node.chars

        if is_in_set != ast_node.negated:
            return True, input_line[1:]
        else:
            return False, None

    #Example for ConcatenationNode:
    if isinstance(ast_node, ConcatenationNode):
        current_input = input_line
        for child_node in ast_node.children:
            matched, current_input = match_ast(child_node, current_input)
            if not matched:
                return False, None
        return True, current_input

    # Example for AlternationNode:
    if isinstance(ast_node, AlternationNode):
        for branch_node in ast_node.branches:
            matched, remaining = match_ast(branch_node, input_line)
            if matched:
                return True, remaining
        return False, None

    # Example for QuantifierNode (ONE_OR_MORE):
    if isinstance(ast_node, QuantifierNode) and ast_node.type == 'ONE_OR_MORE':
        # Must match at least once
        first_match, current_input = match_ast(ast_node.child, input_line)
        if not first_match:
            return False, None
        
        # Then, recursively try to match the child zero or more times (greedy)
        temp_input = current_input
        while True:
            m, next_input = match_ast(ast_node.child, temp_input)
            if m:
                temp_input = next_input
            else:
                break
        return True, temp_input

    # ... and so on for all other node types ...

    # Add a base case for unhandled nodes or simple success (e.g. empty node)
    return False, None # Fallback if node type not handled


def main():
    pattern_str = sys.argv[2]
    input_line = sys.stdin.read()
    #.strip() # Use strip() to remove trailing newline

    if sys.argv[1] != "-E":
        print("Expected first argument to be '-E'", file=sys.stderr)
        exit(1)

    print("Logs from your program will appear here!", file=sys.stderr)

    try:
        # Phase 1: Parse the regex string into an AST
        parser = RegexParser(pattern_str)
        ast = parser.parse()
        print("AST built successfully!", file=sys.stderr)

        print("\n--- AST Representation ---", file=sys.stderr)
        print_ast(ast, prefix="")
        print("--------------------------\n", file=sys.stderr)
        # **************************************

        # Phase 2: Match the AST against the input line
        if pattern_str.startswith("^"):
            # If pattern starts with '^', match only from the beginning of the input
            matched, _ = match_ast(ast, input_line) # match_ast would start from pattern[1:] for the ^ logic
            if matched:
                print("exit 0", file=sys.stderr)
                exit(0)
        elif pattern_str.endswith("$"):
            # If pattern ends with '$', match only to the end of the input
            # This is complex with match_ast. You'd need a separate final check.
            # For simplicity for now, the `$` anchor node should handle this.
            # The general match loop below will try at all positions.
            for i in range(len(input_line) + 1):
                matched, remaining_input = match_ast(ast, input_line[i:])
                if matched and not remaining_input: # Match entire pattern, and input must be exhausted
                    print("exit 0", file=sys.stderr)
                    exit(0)

        else: # General match anywhere
            for i in range(len(input_line) + 1):
                matched, _ = match_ast(ast, input_line[i:])
                if matched:
                    print("exit 0", file=sys.stderr)
                    exit(0)

    except ValueError as e:
        print(f"Error parsing regex: {e}", file=sys.stderr)
        print("exit 1", file=sys.stderr)
        exit(1)

    print("exit 1", file=sys.stderr)
    exit(1)

if __name__ == "__main__":
    main()