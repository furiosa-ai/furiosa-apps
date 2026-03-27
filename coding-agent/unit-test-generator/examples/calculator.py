"""
Recursive-descent parser based calculator.
Supports +, -, *, /, parentheses, and floating-point numbers.
Usage:
    from calculator import evaluate
    result = evaluate("3 + 4 * (2 - 1) / 5")
"""


class Parser:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if self.text else None

    def error(self, message: str):
        raise ValueError(f"Parse error at pos {self.pos}: {message}")

    def advance(self):
        self.pos += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def parse(self) -> float:
        value = self.expr()
        self.skip_whitespace()
        if self.current_char is not None:
            self.error(f"Unexpected character '{self.current_char}'")
        return value

    def expr(self) -> float:
        # expr := term (( '+' | '-' ) term)*
        result = self.term()
        while True:
            self.skip_whitespace()
            if self.current_char == "+":
                self.advance()
                result += self.term()
            elif self.current_char == "-":
                self.advance()
                result -= self.term()
            else:
                break
        return result

    def term(self) -> float:
        # term := factor ( ( '*' | '/' ) factor )*
        result = self.factor()
        while True:
            self.skip_whitespace()
            if self.current_char == "*":
                self.advance()
                result *= self.factor()
            elif self.current_char == "/":
                self.advance()
                denominator = self.factor()
                if denominator == 0:
                    raise ValueError("Division by zero.")
                result /= denominator
            else:
                break
        return result

    def factor(self) -> float:
        # factor := ('+' | '-') factor | number | '(' expr ')'
        self.skip_whitespace()
        char = self.current_char
        if char is None:
            self.error("Unexpected end of input")
        if char == "+":
            self.advance()
            return self.factor()
        if char == "-":
            self.advance()
            return -self.factor()
        if char.isdigit() or char == ".":
            return self.number()
        if char == "(":
            self.advance()
            result = self.expr()
            self.skip_whitespace()
            if self.current_char != ")":
                self.error("Expected ')'")
            self.advance()
            return result
        self.error(f"Invalid character '{char}'")

    def number(self) -> float:
        num_str = ""
        dot_count = 0
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == "."):
            if self.current_char == ".":
                dot_count += 1
                if dot_count > 1:
                    self.error("Invalid number format")
            num_str += self.current_char
            self.advance()
        try:
            return float(num_str)
        except ValueError:
            self.error(f"Could not parse number '{num_str}'")


def evaluate(expression: str) -> float:
    """Evaluate a mathematical expression and return the result."""
    parser = Parser(expression)
    return parser.parse()
