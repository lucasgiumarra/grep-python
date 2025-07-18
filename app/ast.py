import sys

class Node:
    pass
class DotNode(Node):
    pass

class LiteralNode(Node):
    def __init__(self, char):
        self.char = char
       
class CharClassNode(Node): # For /d, /w, etc.
    def __init__(self, type):
        self.type = type # 'digit', 'word', etc.

class ConcatenationNode(Node):
    def __init__(self, children):
        self.children = children # List of Nodes

class AnchorNode(Node):
    def __init__(self, type):
        self.type = type # 'start', 'end'

class AlternationNode(Node):
    def __init__(self, branches):
        self.branches = branches # List of Nodes (each a branch)

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
        if char is None: return None
        
        node = Node
        # if char == '(':
        #     self._consume('(')
        #     node = GroupNode(self._parse_alternation()) # Group can contain an alternation
        #     self._expect(')')
        if char == ".":
            node = DotNode()
            self._consume('.')
        elif char in '^$': # Anchors are atoms
            node = AnchorNode('start' if char == '^' else 'end')
            self._consume(char)
        else: # Literal character
            node = LiteralNode(char)
            self._consume(char)

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

    # Example for ConcatenationNode:
    # if isinstance(ast_node, ConcatenationNode):
    #     current_input = input_line
    #     for child_node in ast_node.children:
    #         matched, current_input = match_ast(child_node, current_input)
    #         if not matched:
    #             return False, None
    #     return True, current_input

    # # Example for AlternationNode:
    # if isinstance(ast_node, AlternationNode):
    #     for branch_node in ast_node.branches:
    #         matched, remaining = match_ast(branch_node, input_line)
    #         if matched:
    #             return True, remaining
    #     return False, None

    # # Example for QuantifierNode (ONE_OR_MORE):
    # if isinstance(ast_node, QuantifierNode) and ast_node.type == 'ONE_OR_MORE':
    #     # Must match at least once
    #     first_match, current_input = match_ast(ast_node.child, input_line)
    #     if not first_match:
    #         return False, None
        
    #     # Then, recursively try to match the child zero or more times (greedy)
    #     temp_input = current_input
    #     while True:
    #         m, next_input = match_ast(ast_node.child, temp_input)
    #         if m:
    #             temp_input = next_input
    #         else:
    #             break
    #     return True, temp_input

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
        print(f"ast: {ast}", file=sys.stderr)
        # You might want to print the AST for debugging here

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