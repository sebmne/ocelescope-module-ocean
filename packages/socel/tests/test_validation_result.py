import unittest

from socel.validation.result import Invalid, Valid, combine


class ValidationResultTests(unittest.TestCase):
    def test_combine_accumulates_independent_errors(self) -> None:
        result = combine(
            (
                Invalid(("first",)),
                Valid(2),
                Invalid(("second", "third")),
            )
        )

        self.assertEqual(result, Invalid(("first", "second", "third")))

    def test_and_then_chains_dependent_validations(self) -> None:
        result = Valid[int, str](2).and_then(lambda value: Valid(value * 3))

        self.assertEqual(result, Valid(6))

    def test_and_then_does_not_run_after_failure(self) -> None:
        called = False

        def next_validation(value: int) -> Valid[int, str]:
            nonlocal called
            called = True
            return Valid(value)

        result = Invalid[int, str](("failed",)).and_then(next_validation)

        self.assertEqual(result, Invalid(("failed",)))
        self.assertFalse(called)


if __name__ == "__main__":
    unittest.main()
