import sys

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
        print(f"char in _parse_atom: {char}", file=sys.stderr)
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

def match_ast(ast_node, input_line, captures):
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
        if not input_line:
            return False, None
        
        char_to_check = input_line[0]

        # 2. Determine if the character matches the set based on `negated` flag
        #    If `negated` is True, the character should NOT be in the set.
        #    If `negated` is False, the character SHOULD be in the set.
        is_in_set = char_to_check in ast_node.chars

        # The condition (is_in_set != ast_node.negated) correctly combines these:
        # If negated is False (meaning we want chars IN the set):
        #   (is_in_set != False) -> is_in_set -> True if char is in set
        # If negated is True (meaning we want chars NOT IN the set):
        #   (is_in_set != True) -> not is_in_set -> True if char is NOT in set
        if is_in_set != ast_node.negated:
            return True, input_line[1:]
        else:
            return False, None

    if isinstance(ast_node, ConcatenationNode):
        # For a concatenation (like 'abc'), we match a sequence of nodes.
        # This requires a backtracking mechanism to handle greedy quantifiers
        # like `+` and `*` which might consume too many characters.
        def match_concatenation_recursive(child_nodes, current_input, captures):
            # Base case: If we've matched all child nodes, the concatenation is a success.
            if not child_nodes:
                return True, current_input

            first_node = child_nodes[0]
            rest_of_nodes = child_nodes[1:]

            # print(f"first node: {first_node}", file=sys.stderr)
            # print(f"rest of nodes: {rest_of_nodes}", file=sys.stderr)

            # Special logic for greedy quantifiers (`+`, `*`) which need to backtrack
            if isinstance(first_node, QuantifierNode) and first_node.type in ['ONE_OR_MORE', 'ZERO_OR_MORE']:
                
                # Step 1: Collect all possible ways the quantifier can match.
                # `possible_inputs_for_next_node` will store the remaining string
                # after each potential match length of the quantifier.
                possible_inputs_for_next_node = []
                
                # For `*`, a zero-length match is possible. The next node would start
                # from the same place.
                if first_node.type == 'ZERO_OR_MORE':
                    possible_inputs_for_next_node.append(current_input)
                
                # Now, match the quantifier's child pattern one or more times.
                temp_input = current_input
                while True:
                    matched, temp_input_after_match = match_ast(first_node._child, temp_input, captures)
                    
                    # We only continue if a match occurred AND it consumed characters.
                    # This prevents infinite loops on patterns like `(a*)*`.
                    if matched and len(temp_input_after_match) < len(temp_input):
                        possible_inputs_for_next_node.append(temp_input_after_match)
                        temp_input = temp_input_after_match
                    else:
                        break
                
                # Step 2: Backtrack. Try each possibility, starting from the longest (greediest) match.
                for input_for_next_node in reversed(possible_inputs_for_next_node):
                    # Recursively try to match the rest of the nodes in the concatenation.
                    # NOTE: A failed branch might leave partial captures. So we pass a copy.
                    matched_rest, final_input = match_concatenation_recursive(rest_of_nodes, input_for_next_node, captures.copy())
                    if matched_rest:
                        # We found a full match!
                        return True, final_input
                
                # If we've tried all possibilities for the quantifier and none allowed the rest
                # of the pattern to match, then this path fails.
                return False, None

            else: # For any other node (literal, `?`, group, etc.)
                # Match the first node normally.
                matched, input_after_first = match_ast(first_node, current_input, captures)
                if matched:
                    # If it matched, recursively try to match the rest of the nodes.
                    return match_concatenation_recursive(rest_of_nodes, input_after_first, captures)
                else:
                    return False, None

        return match_concatenation_recursive(ast_node._children, input_line, captures)    

    # Example for AlternationNode:
    if isinstance(ast_node, AlternationNode):
        for branch_node in ast_node._branches:
            # Pass a copy of captures to prevent a failed branch from altering the state for the next branch.
            matched, remaining = match_ast(branch_node, input_line, captures.copy())
            if matched:
                return True, remaining
        return False, None

    if isinstance(ast_node, QuantifierNode) and ast_node.type == 'ZERO_OR_ONE':
        # Match the child once
        matched_once, remaining_after_one = match_ast(ast_node._child, input_line, captures)
        if matched_once:
            return True, remaining_after_one
        # Since it failed once this means there are zero matches.
        # So just return True and the original input
        # The subsequent node in the concatenation will be called with the original input
        return True, input_line

    if isinstance(ast_node, DotNode):
        if not input_line:
            return False, None
        return True, input_line[1:]

    # Handle a CaptureGroupNode (e.g., (abc))
    if isinstance(ast_node, CaptureGroupNode):
        matched, remaining_input = match_ast(ast_node._child, input_line, captures)
        if matched:
            # If the child matched, calculate the text that was consumed
            consumed_length = len(input_line) - len(remaining_input)
            captured_text = input_line[:consumed_length]

            # Store the captrued text in our state array at the correct index
            # Ensure captures list is long enough
            while len(captures) <= ast_node.index:
                captures.append(None)
            captures[ast_node.index] = captured_text
        # A group node simply executes the match for its child node.
        # Quantifiers on a group are handled by the QuantifierNode itself.
        return matched, remaining_input 

    if isinstance(ast_node, BackreferenceNode):
        # Look up the text that was previously captured by this group.
        if ast_node.index < len(captures) and captures[ast_node.index] is not None:
            text_to_match = captures[ast_node.index]
            # Check if the current input starts with that exact text.
            if input_line.startswith(text_to_match):
                # If so, consume that text and return success.
                return True, input_line[len(text_to_match):]

        # If the group hasn't captured anything yet or the text doesn't match.
        return False, None

    # Handle AnchorNode (e.g., ^ or $)
    if isinstance(ast_node, AnchorNode):
        if ast_node.type == 'start':
            # The ^ anchor is implicitly handled by the top-level 'match' function
            # and should not be a standalone node in this recursive function.
            # If it is, something is wrong with the parser.
            return True, input_line
        elif ast_node.type == 'end':
            # The $ anchor matches only if the input is exhausted.
            if not input_line:
                return True, input_line
            return False, None

    # Add a base case for unhandled nodes or simple success (e.g. empty node)
    return False, None # Fallback if node type not handled


def main():
    # input_str = sys.argv[1]
    pattern_str = sys.argv[2]
    input_line = sys.stdin.read()
    #.strip() # Use strip() to remove trailing newline

    if sys.argv[1] != "-E":
        print("Expected first argument to be '-E'", file=sys.stderr)
        exit(1)

    print("\nLogs from your program will appear here!", file=sys.stderr)
    print(f"\ninput_line: {input_line}", file=sys.stderr)
    print(f"pattern string: {pattern_str}\n", file=sys.stderr)
    

    try:
        # Phase 1: Parse the regex string into an AST
        parser = RegexParser(pattern_str)
        ast = parser.parse()

        # Initialize the captures list. It needs space for all potential groups.
        # Use parser.group_count. Index 0 is unused, so add 1.
        initial_captures = [None] * (parser.group_count + 1)
        print("AST built successfully!", file=sys.stderr)

        print("\n--- AST Node Walkthrough ---", file=sys.stderr)
        for node in ast.walk():
            # This will print each node in a depth-first (pre-order) traversal
            print(f"- {node!r}", file=sys.stderr)
        print("----------------------------\n", file=sys.stderr)

        # Phase 2: Match the AST against the input line
        if pattern_str.startswith("^"):
            # If pattern starts with '^', match only from the beginning of the input
            captures_for_this_attempt = [None] * (parser.group_count + 1)
            matched, _ = match_ast(ast, input_line, captures_for_this_attempt) # match_ast would start from pattern[1:] for the ^ logic
            if matched:
                print("exit 0", file=sys.stderr)
                exit(0)
        elif pattern_str.endswith("$"):
            # If pattern ends with '$', match only to the end of the input
            # This is complex with match_ast. You'd need a separate final check.
            # For simplicity for now, the `$` anchor node should handle this.
            # The general match loop below will try at all positions.
            for i in range(len(input_line) + 1):
                captures_for_this_attempt = [None] * (parser.group_count + 1)
                matched, remaining_input = match_ast(ast, input_line[i:], captures_for_this_attempt)
                if matched and not remaining_input: # Match entire pattern, and input must be exhausted
                    print("exit 0", file=sys.stderr)
                    exit(0)

        else: # General match anywhere
            for i in range(len(input_line) + 1):
                captures_for_this_attempt = [None] * (parser.group_count + 1)
                matched, _ = match_ast(ast, input_line[i:], captures_for_this_attempt)
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