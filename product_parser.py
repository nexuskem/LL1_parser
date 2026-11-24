"""
LL(1) Table-Driven Parser for DeKUT Product-Label Grammar
Course: Compiler Construction
"""

import re
import sys


class ParseError(Exception):
    """Custom exception raised when a syntax error occurs during LL(1) parsing."""
    def __init__(self, message, unexpected_token, position, expected_tokens):
        super().__init__(message)
        self.unexpected_token = unexpected_token
        self.position = position
        self.expected_tokens = expected_tokens


class LL1Parser:
    """Generic table-driven LL(1) parser engine."""
    def __init__(self, name, table, start_symbol, terminals, nonterminals):
        self.name = name
        self.table = table
        self.start_symbol = start_symbol
        self.terminals = terminals
        self.nonterminals = nonterminals

    def tokenize(self, text):
        """
        Tokenises the input case-insensitively, splitting compound quantity+unit tokens
        (e.g., '500ml' -> '500', 'ML') and tracking character start positions.
        """
        tokens = []
        # Find all whitespace-separated words/segments
        for match in re.finditer(r'\S+', text):
            raw_word = match.group(0)
            start_pos = match.start()

            # Check if token is a combined quantity + unit (e.g., '500ml', '250ML', '100Ml')
            compound_match = re.fullmatch(r'(\d+)([a-zA-Z]+)', raw_word)
            if compound_match:
                qty_part = compound_match.group(1)
                unit_part = compound_match.group(2)
                tokens.append((qty_part.upper(), start_pos, qty_part))
                tokens.append((unit_part.upper(), start_pos + len(qty_part), unit_part))
            else:
                tokens.append((raw_word.upper(), start_pos, raw_word))

        # Append End-of-Input marker ($)
        tokens.append(('$', len(text), '$'))
        return tokens

    def parse(self, text, verbose=False):
        """
        Parses an input string using the LL(1) parsing table and an explicit stack.
        Returns (success: bool, trace: list of trace step dictionaries).
        Raises ParseError upon encountering any syntax or lexical mismatch.
        """
        tokens = self.tokenize(text)
        stack = ['$', self.start_symbol]
        token_idx = 0
        trace = []

        while stack:
            top = stack[-1]
            curr_token, pos, raw_val = tokens[token_idx]
            remaining_tokens = [t[0] for t in tokens[token_idx:]]
            stack_snapshot = list(stack)

            if top == '$':
                if curr_token == '$':
                    stack.pop()
                    trace.append({
                        'stack': stack_snapshot,
                        'remaining': remaining_tokens,
                        'action': 'Accept (Input successfully parsed)'
                    })
                    break
                else:
                    expected = ['$']
                    raise ParseError(
                        f"Syntax Error at char position {pos}: unexpected token '{raw_val}'. "
                        f"Expected end of input ($), but found trailing tokens.",
                        curr_token, pos, expected
                    )

            elif top in self.terminals:
                if top == curr_token:
                    stack.pop()
                    token_idx += 1
                    trace.append({
                        'stack': stack_snapshot,
                        'remaining': remaining_tokens,
                        'action': f"Match terminal '{top}'"
                    })
                else:
                    raise ParseError(
                        f"Syntax Error at char position {pos}: unexpected token '{raw_val}'. "
                        f"Expected terminal '{top}'.",
                        curr_token, pos, [top]
                    )

            elif top in self.nonterminals:
                if curr_token in self.table[top]:
                    production_rhs = self.table[top][curr_token]
                    stack.pop()
                    # Push right-hand side symbols in reverse order
                    for sym in reversed(production_rhs):
                        stack.append(sym)
                    trace.append({
                        'stack': stack_snapshot,
                        'remaining': remaining_tokens,
                        'action': f"Output {top} -> {' '.join(production_rhs)}"
                    })
                else:
                    expected = sorted(list(self.table[top].keys()))
                    raise ParseError(
                        f"Syntax Error at char position {pos}: unexpected token '{raw_val}'. "
                        f"Parsing nonterminal '{top}', expected one of: {', '.join(expected)}.",
                        curr_token, pos, expected
                    )
            else:
                raise ValueError(f"Internal Error: Unknown grammar symbol on stack: '{top}'")

        if verbose:
            self._print_trace(trace)

        return True, trace

    def _print_trace(self, trace):
        print(f"\n--- Parse Trace for [{self.name}] ---")
        print(f"{'Step':<5} | {'Stack (bottom -> top)':<32} | {'Remaining Input':<36} | {'Action'}")
        print("-" * 105)
        for i, step in enumerate(trace, 1):
            stack_str = " ".join(step['stack'])
            rem_str = " ".join(step['remaining'])
            print(f"{i:<5} | {stack_str:<32} | {rem_str:<36} | {step['action']}")
        print("-" * 105)


# =====================================================================
# GRAMMAR DEFINITIONS & PREDICTIVE PARSING TABLES
# =====================================================================

# 1. Base Grammar (Tasks 1, 2, 3)
TABLE_BASE = {
    'S': {
        'DEKUT': ['BRAND', 'P', 'Q']
    },
    'BRAND': {
        'DEKUT': ['DEKUT']
    },
    'P': {
        'FLAVOURED': ['FLAVOURED', 'YOGHURT', 'F'],
        'UNFLAVOURED': ['UNFLAVOURED', 'YOGHURT']
    },
    'F': {
        'COFFEE': ['COFFEE'],
        'CHIA': ['CHIA'],
        'STRAWBERRY': ['STRAWBERRY']
    },
    'Q': {
        '100': ['M', 'ML'],
        '250': ['M', 'ML'],
        '500': ['M', 'ML']
    },
    'M': {
        '100': ['100'],
        '250': ['250'],
        '500': ['500']
    }
}

TERMINALS_BASE = {
    'DEKUT', 'FLAVOURED', 'UNFLAVOURED', 'YOGHURT',
    'COFFEE', 'CHIA', 'STRAWBERRY', '100', '250', '500', 'ML', '$'
}
NON_TERMINALS_BASE = {'S', 'BRAND', 'P', 'F', 'Q', 'M'}

parser_base = LL1Parser("Base Yoghurt Grammar", TABLE_BASE, 'S', TERMINALS_BASE, NON_TERMINALS_BASE)


# 2. Extended Grammar (Task 4: Adding Milk and Juice)
# Productions:
#   P -> FLAVOURED YOGHURT F | UNFLAVOURED YOGHURT | FRESH MILK | JUICE J
#   J -> MANGO | PASSION
TABLE_EXTENDED = {
    'S': {
        'DEKUT': ['BRAND', 'P', 'Q']
    },
    'BRAND': {
        'DEKUT': ['DEKUT']
    },
    'P': {
        'FLAVOURED': ['FLAVOURED', 'YOGHURT', 'F'],
        'UNFLAVOURED': ['UNFLAVOURED', 'YOGHURT'],
        'FRESH': ['FRESH', 'MILK'],
        'JUICE': ['JUICE', 'J']
    },
    'F': {
        'COFFEE': ['COFFEE'],
        'CHIA': ['CHIA'],
        'STRAWBERRY': ['STRAWBERRY']
    },
    'J': {
        'MANGO': ['MANGO'],
        'PASSION': ['PASSION']
    },
    'Q': {
        '100': ['M', 'ML'],
        '250': ['M', 'ML'],
        '500': ['M', 'ML']
    },
    'M': {
        '100': ['100'],
        '250': ['250'],
        '500': ['500']
    }
}

TERMINALS_EXTENDED = {
    'DEKUT', 'FLAVOURED', 'UNFLAVOURED', 'YOGHURT',
    'COFFEE', 'CHIA', 'STRAWBERRY', '100', '250', '500', 'ML',
    'FRESH', 'MILK', 'JUICE', 'MANGO', 'PASSION', '$'
}
NON_TERMINALS_EXTENDED = {'S', 'BRAND', 'P', 'F', 'J', 'Q', 'M'}

parser_extended = LL1Parser("Extended Shop Products Grammar", TABLE_EXTENDED, 'S', TERMINALS_EXTENDED, NON_TERMINALS_EXTENDED)


# =====================================================================
# TEST HARNESS & DEMONSTRATION RUNNER
# =====================================================================

def run_tests():
    print("=" * 80)
    print("TASK 3 TEST SUITE: BASE GRAMMAR (YOGHURT)")
    print("=" * 80)

    # 1. Valid test cases
    valid_test_cases = [
        ("DEKUT Flavoured yoghurt coffee 500ml", "Sample input from prompt"),
        ("DEKUT Unflavoured yoghurt 250ml", "Unflavoured yoghurt, 250ml"),
        ("dekut flavoured yoghurt chia 100ml", "Chia flavour, 100ml, all lowercase"),
        ("DEKUT flavoured yoghurt strawberry 500ML", "Strawberry flavour, 500ML"),
        ("DEKUT unflavoured yoghurt 100 ml", "Unflavoured, space-separated unit (100 ml)"),
        ("dekut flavoured yoghurt coffee 250 ml", "Coffee flavour, 250 ml"),
        ("DEKUT Unflavoured yoghurt 500ml", "Unflavoured yoghurt, 500ml")
    ]

    print("\n--- Valid Test Cases (Expected: ACCEPT) ---")
    for text, description in valid_test_cases:
        try:
            parser_base.parse(text)
            print(f"[ACCEPT] '{text}'\n         -> Description: {description}")
        except ParseError as err:
            print(f"[FAIL]   '{text}'\n         -> Unexpected ParseError: {err}")

    # 2. Invalid test cases
    invalid_test_cases = [
        ("DEKUT flavoured yoghurt vanilla 500ml", "Unknown flavour ('vanilla')"),
        ("DEKUT flavoured yoghurt coffee 750ml", "Unsupported size ('750')"),
        ("DEKUT flavoured yoghurt coffee 500", "Missing unit ('ML')"),
        ("Flavoured yoghurt coffee 500ml", "Missing brand ('DEKUT')"),
        ("DEKUT 500ml flavoured yoghurt coffee", "Tokens in wrong order (size before product)"),
        ("DEKUT flavoured yoghurt 500ml", "Flavoured yoghurt missing flavour token"),
        ("DEKUT unflavoured yoghurt coffee 500ml", "Unflavoured yoghurt containing extra flavour")
    ]

    print("\n--- Invalid Test Cases (Expected: REJECT with descriptive error) ---")
    for text, description in invalid_test_cases:
        try:
            parser_base.parse(text)
            print(f"[FAIL]   '{text}' was incorrectly accepted! ({description})")
        except ParseError as err:
            print(f"[REJECT] '{text}'\n         -> Case: {description}\n         -> Caught: {err}")

    print("\n" + "=" * 80)
    print("TASK 4 TEST SUITE: EXTENDED GRAMMAR (MILK & JUICE)")
    print("=" * 80)

    extended_test_cases = [
        ("DEKUT Fresh milk 500ml", "Valid Fresh Milk, 500ml"),
        ("dekut fresh milk 250 ml", "Valid Fresh Milk, 250 ml (lowercase)"),
        ("DEKUT juice mango 500ml", "Valid Mango Juice, 500ml"),
        ("DEKUT juice passion 250ml", "Valid Passion Juice, 250ml"),
        ("DEKUT juice orange 500ml", "Invalid juice flavour ('orange')"),
        ("DEKUT sour milk 500ml", "Invalid milk type ('sour')")
    ]

    for text, description in extended_test_cases:
        try:
            parser_extended.parse(text)
            print(f"[ACCEPT] '{text}'\n         -> Description: {description}")
        except ParseError as err:
            print(f"[REJECT] '{text}'\n         -> Case: {description}\n         -> Caught: {err}")


# =====================================================================
# MAIN ENTRY POINT (CLI / Interactive / Self-Test)
# =====================================================================

def main():
    if len(sys.argv) > 1:
        # If user passed an argument or command
        arg = sys.argv[1].strip()
        if arg in ("--test", "-t"):
            run_tests()
            print("\nDisplaying detailed step-by-step trace for the sample input:")
            parser_base.parse("DEKUT Flavoured yoghurt coffee 500ml", verbose=True)
            return
        elif arg in ("--trace", "-v"):
            input_text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "DEKUT Flavoured yoghurt coffee 500ml"
            parser_base.parse(input_text, verbose=True)
            return
        else:
            # Parse argument string directly
            input_str = " ".join(sys.argv[1:])
    else:
        # Interactive mode or stdin
        print("Enter a product label string to parse (or press Enter to run all test cases):")
        try:
            line = sys.stdin.readline()
            if not line or line.strip() == "":
                run_tests()
                print("\nDisplaying detailed step-by-step trace for the sample input:")
                parser_base.parse("DEKUT Flavoured yoghurt coffee 500ml", verbose=True)
                return
            input_str = line.strip()
        except EOFError:
            run_tests()
            return

    # Parse user input with both parsers
    print(f"\nParsing input: '{input_str}'")
    print("\n--- Trying Base Grammar (Yoghurt) ---")
    try:
        parser_base.parse(input_str, verbose=True)
        print("RESULT: VALID product label according to Base Grammar.")
    except ParseError as e:
        print(f"RESULT: REJECTED by Base Grammar.\nDetails: {e}")

    print("\n--- Trying Extended Grammar (Yoghurt, Milk, Juice) ---")
    try:
        parser_extended.parse(input_str, verbose=True)
        print("RESULT: VALID product label according to Extended Grammar.")
    except ParseError as e:
        print(f"RESULT: REJECTED by Extended Grammar.\nDetails: {e}")


if __name__ == "__main__":
    main()
