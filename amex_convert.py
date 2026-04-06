#!/usr/bin/env python3
import csv
import sys
import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert Amex CSV exports to hledger journal format."
    )
    parser.add_argument("infile", help="Path to the Amex activity CSV file")
    parser.add_argument(
        "--account",
        default="liabilities:credit-cards:amex",
        help="hledger account name for this card (default: liabilities:credit-cards:amex)",
    )
    return parser.parse_args()


def parse_date(date_str):
    # Amex occasionally drops the century from the year (MM/DD/YY vs MM/DD/YYYY).
    for fmt in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y/%m/%d")
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {date_str!r}")


def process_csv(filepath, account_name):
    try:
        f = open(filepath, "r", encoding="utf-8-sig")
    except FileNotFoundError:
        print(f"Error: file '{filepath}' not found.", file=sys.stderr)
        sys.exit(1)

    with f:
        reader = csv.DictReader(f)

        expected = {"Date", "Description", "Amount", "Reference"}
        actual = set(reader.fieldnames or [])
        if not expected.issubset(actual):
            missing = expected - actual
            print(f"Error: missing expected columns: {missing}", file=sys.stderr)
            print(f"Found columns: {list(actual)}", file=sys.stderr)
            sys.exit(1)

        for row in reader:
            # Amex includes pending transactions without a Reference value.
            # Skip them -- they'll appear as settled charges in the next export.
            if not row.get("Reference", "").strip():
                continue

            try:
                date = parse_date(row["Date"])
            except ValueError as e:
                print(f"Warning: skipping row -- {e} (description: {row.get('Description', '?')!r})", file=sys.stderr)
                continue

            desc = row["Description"].strip().replace('"', "")

            # Amex exports charges as positive and payments/credits as negative.
            # hledger expects a liability increase (charge) to be negative on the
            # liability account, so we invert.
            # Decimal avoids binary float representation issues in financial output.
            try:
                amount = Decimal(row["Amount"].strip()) * -1
            except InvalidOperation:
                print(f"Warning: skipping row -- could not parse amount {row['Amount']!r} (description: {desc!r})", file=sys.stderr)
                continue

            print(f"{date} * {desc}")
            print(f"    {account_name:<40}  ${amount:.2f}")
            print(f"    expenses:unclassified\n")


if __name__ == "__main__":
    args = parse_args()
    try:
        process_csv(args.infile, args.account)
    except BrokenPipeError:
        sys.exit(0)
