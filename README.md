# amex-to-hledger

A Python script to convert American Express CSV exports into `hledger`-compatible journal files.

Amex exports charges as positive numbers and payments/credits as negative. That's the inverse of standard double-entry convention, where a charge against a liability account is a credit (negative). This script flips the signs, normalizes the date format, and writes hledger transactions to stdout.

---

## Requirements

Python 3.8+. No external dependencies.

---

## Usage

Point it at your Amex activity CSV. Output goes to stdout so you can pipe directly to a journal file:

```bash
python amex_convert.py activity.csv > amex_new.journal
```

Override the default liability account with `--account`:

```bash
python amex_convert.py activity.csv --account "liabilities:amex-gold" > amex_new.journal
```

Default account if not specified: `liabilities:credit-cards:amex`

The balancing account is hardcoded to `expenses:unclassified`. The expectation is you'll do a second pass in hledger or with a rules file to categorize from there.

---

## Verifying your export

The script checks for four columns on startup: `Date`, `Description`, `Amount`, `Reference`. If your export is missing any of them it will exit with an error listing what it found vs. what it expected.

Run against `sample_amex.csv` first to confirm your export format matches before touching real data:

```bash
python amex_convert.py sample_amex.csv
```

Expected output:

```
2023/10/04 * AMAZON WEB SERVICES
    liabilities:credit-cards:amex               $-12.55
    expenses:unclassified

2023/10/05 * PAYMENT - THANK YOU
    liabilities:credit-cards:amex               $100.00
    expenses:unclassified

2023/10/06 * LOCAL COFFEE SHOP
    liabilities:credit-cards:amex               $-4.50
    expenses:unclassified
```

The pending row in the sample (no Reference value) is intentionally skipped.

---

## Known limitations

- **Pending transactions**: Amex includes pending charges at the top of some exports without a `Reference` value. The script skips any row with an empty Reference to avoid duplicate imports when the charge settles. If you have a legitimate transaction with no reference ID, you'll need to add it manually.

- **Date format inconsistency**: Amex switches between `MM/DD/YYYY` and `MM/DD/YY` without warning. The parser tries both. If they introduce a third format, it will throw a `ValueError` with the raw string so you know which row broke.

- **Card scope**: Only tested on US personal Amex cards (Gold and Platinum). Business/corporate card exports may use different column headers.

- **Categorization**: All transactions land in `expenses:unclassified`. There's no rules engine here. Use hledger's [`--rules-file`](https://hledger.org/hledger.html#csv-format) to handle categorization after import if you want it automated.
