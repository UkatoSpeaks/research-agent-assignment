import ast
import operator
import time

from app.schemas import ToolResult


class CalculatorTool:
    """Safely evaluates basic arithmetic expressions."""

    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def run(self, expression: str) -> ToolResult:
        start_time = time.perf_counter()

        try:
            if not expression.strip():
                raise ValueError("Expression cannot be empty.")

            tree = ast.parse(expression, mode="eval")
            result = self._evaluate(tree.body)

            execution_time = (
                time.perf_counter() - start_time
            ) * 1000

            return ToolResult(
                tool_name="calculator",
                success=True,
                output={
                    "expression": expression,
                    "result": result,
                },
                execution_time_ms=round(
                    execution_time,
                    2,
                ),
            )

        except Exception as exc:
            execution_time = (
                time.perf_counter() - start_time
            ) * 1000

            return ToolResult(
                tool_name="calculator",
                success=False,
                error=str(exc),
                execution_time_ms=round(
                    execution_time,
                    2,
                ),
            )

    def _evaluate(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numbers are allowed.")

        if isinstance(node, ast.BinOp):
            operation = self.OPERATORS.get(type(node.op))

            if operation is None:
                raise ValueError("Unsupported operator.")

            left = self._evaluate(node.left)
            right = self._evaluate(node.right)

            return operation(left, right)

        if isinstance(node, ast.UnaryOp):
            operation = self.OPERATORS.get(type(node.op))

            if operation is None:
                raise ValueError("Unsupported unary operator.")

            return operation(self._evaluate(node.operand))

        raise ValueError(
            "Invalid expression. Only arithmetic is supported."
        )