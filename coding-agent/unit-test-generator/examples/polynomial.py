class Polynomial:
    """
    Polynomial class for basic polynomial arithmetic and evaluation.
    Coefficients are in increasing order: [a0, a1, a2, ...] represents a0 + a1*x + a2*x^2 + ...
    """

    def __init__(self, coefficients):
        self.coefficients = list(coefficients)
        self._trim()

    def _trim(self):
        # Remove trailing zeros to maintain the correct degree
        while len(self.coefficients) > 1 and self.coefficients[-1] == 0:
            self.coefficients.pop()

    def degree(self):
        """Return the degree of the polynomial."""
        return len(self.coefficients) - 1

    def __repr__(self):
        terms = []
        for power, coef in enumerate(self.coefficients):
            if coef == 0:
                continue
            if power == 0:
                terms.append(f"{coef}")
            elif power == 1:
                terms.append(f"{coef}*x")
            else:
                terms.append(f"{coef}*x^{power}")
        return " + ".join(terms) if terms else "0"

    def __eq__(self, other):
        if not isinstance(other, Polynomial):
            return False
        self._trim()
        other._trim()
        return self.coefficients == other.coefficients

    def __add__(self, other):
        """Add two polynomials and return a new Polynomial."""
        max_len = max(len(self.coefficients), len(other.coefficients))
        result = [0] * max_len
        for i in range(max_len):
            a = self.coefficients[i] if i < len(self.coefficients) else 0
            b = other.coefficients[i] if i < len(other.coefficients) else 0
            result[i] = a + b
        return Polynomial(result)

    def __mul__(self, other):
        """Multiply two polynomials and return a new Polynomial."""
        result = [0] * (len(self.coefficients) + len(other.coefficients) - 1)
        for i, a in enumerate(self.coefficients):
            for j, b in enumerate(other.coefficients):
                result[i + j] += a * b
        return Polynomial(result)

    def evaluate(self, x):
        """Evaluate the polynomial at the given value x."""
        result = 0
        # Use Horner's method
        for coef in reversed(self.coefficients):
            result = result * x + coef
        return result

    def derivative(self):
        """Return the derivative of the polynomial as a new Polynomial."""
        if len(self.coefficients) <= 1:
            return Polynomial([0])
        deriv = [i * c for i, c in enumerate(self.coefficients)][1:]
        return Polynomial(deriv)
