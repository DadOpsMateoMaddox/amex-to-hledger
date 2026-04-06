"""
Golden-output test. Runs the converter against sample_amex.csv and checks
that the output matches what we expect line-for-line.

Not a unit test framework -- just subprocess + assert. Run with:
    python test_convert.py
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SCRIPT = HERE / "amex_convert.py"
SAMPLE = HERE / "sample_amex.csv"

EXPECTED = """\
2023/10/04 * AMAZON WEB SERVICES
    liabilities:credit-cards:amex             $-12.55
    expenses:unclassified

2023/10/05 * PAYMENT - THANK YOU
    liabilities:credit-cards:amex             $100.00
    expenses:unclassified

2023/10/06 * LOCAL COFFEE SHOP
    liabilities:credit-cards:amex             $-4.50
    expenses:unclassified

"""


def test_golden_output():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(SAMPLE)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Non-zero exit: {result.stderr}"
    assert result.stdout == EXPECTED, (
        f"Output mismatch.\n\nGot:\n{result.stdout!r}\n\nExpected:\n{EXPECTED!r}"
    )
    print("ok  golden output matches")


def test_pending_row_skipped():
    # The sample CSV contains one row with no Reference value. It should not
    # appear in the output at all.
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(SAMPLE)],
        capture_output=True,
        text=True,
    )
    assert "PENDING CHARGE" not in result.stdout
    print("ok  pending row skipped")


def test_missing_file_exits_nonzero():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "does_not_exist.csv"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "not found" in result.stderr
    print("ok  missing file exits nonzero")


def test_custom_account_flag():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(SAMPLE), "--account", "liabilities:amex-gold"],
        capture_output=True,
        text=True,
    )
    assert "liabilities:amex-gold" in result.stdout
    assert "liabilities:credit-cards:amex" not in result.stdout
    print("ok  custom --account flag")


if __name__ == "__main__":
    tests = [
        test_golden_output,
        test_pending_row_skipped,
        test_missing_file_exits_nonzero,
        test_custom_account_flag,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"FAIL  {t.__name__}: {e}")
            failed += 1
    if failed:
        sys.exit(1)
    print(f"\n{len(tests)} tests passed")
