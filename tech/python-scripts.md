# Python source, the data-generating scripts

## What it is

The scripts under `scripts/` are small standalone Python programs. Each one **writes a data file** of the repository (prompts, emails, help-center pages, calendar or order seed data, tasks). They are not part of the installed package and the program never runs them; they exist so the data is reproducible and its rules are visible.

This note walks through every script line by line.

## Why this repository uses it

Synthetic data is only trustworthy when you can see how it was made. A fixed random seed and plain code mean the same command always writes the same file, so the data can be regenerated, audited and changed on purpose. The committed copies are the ones the tests and the measured numbers use.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `scripts/make_pages.py` | 773 non-blank lines |
| `scripts/make_questions.py` | 451 non-blank lines |
| `scripts/make_seed_sql.py` | 23 non-blank lines |

## How it works underneath

A script starts with its imports, defines the data it draws from (lists of names, templates, rules), builds the records with a *seeded* random generator (`random.Random(seed)`: the same seed gives the same sequence of numbers), checks the result against rules, and writes it with `json.dumps` or plain text. Because nothing depends on the date or the machine, the output is identical every time.

The explanations follow the same format as the source notes.

## Walkthrough of this repository's use

### `scripts/make_pages.py`

In its own words: "Write data/pages/*.md: the 60 pages of the sample help center (57 current, 3 retired)."

773 non-blank lines; it defines `main`.

`scripts/make_pages.py`, lines 1 to 13:

```python
"""Write data/pages/*.md: the 60 pages of the sample help center (57 current, 3 retired).

Each page has a title, an updated date and a status, and one or two sections under `##` headings. Three retired
pages contradict a current one (an old return window, an old shipping fee, an old return fee); ten pages each
explain one error code. Deterministic: running it twice writes the same files.
"""

from __future__ import annotations

from pathlib import Path

CURRENT = "current"
RETIRED = "retired"
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Path` from the standard library module `pathlib`.
- Stores the text `current` under the name `CURRENT`.
- Stores the text `retired` under the name `RETIRED`.

`scripts/make_pages.py`, lines 15 to 763:

```python
PAGES: list[tuple[str, str, str, str, list[tuple[str, str]]]] = [
    # ---- orders
    (
        "p-order-place",
        "How to place an order",
        "2026-08-12",
        CURRENT,
        [
            (
                "Checkout",
                "Add items to your cart, open the cart and choose Checkout. Enter your delivery address, pick a shipping speed and pay. You receive an order confirmation email within five minutes.",
            ),
            (
                "Guest checkout",
                "You can check out without an account. Create one afterwards from the confirmation email to follow the order.",
            ),
        ],
    ),
    (
        "p-order-track",
        "Track an order",
        "2026-08-12",
        CURRENT,
        [
            (
                "Where to look",
                "Open Orders in your account and choose the order, or use the tracking link in the shipping confirmation email. Tracking updates appear within 24 hours of dispatch.",
            ),
            (
                "No updates",
                "If tracking shows no new scan for 5 business days, contact support with your order number.",
            ),
        ],
    ),
    (
        "p-order-change-address",
        "Change the delivery address",
        "2026-07-30",
        CURRENT,
        [
            (
                "Before the order is packed",
                "You can change the delivery address in Orders under Change address for up to 2 hours after you place the order. After that the parcel is packed and the address is locked.",
            ),
            (
                "After it is locked",
                "Contact support right away. If the parcel has not left our warehouse we will try to redirect it, but we cannot promise it.",
            ),
        ],
    ),
    (
        "p-order-cancel",
        "Cancel an order",
        "2026-07-30",
        CURRENT,
        [
            (
                "Self-service cancellation",
                "You can cancel an order yourself for up to 1 hour after placing it, as long as it has not been packed. Open the order and choose Cancel order. The money returns to your original payment method.",
            ),
            ("Too late to cancel", "Once the order is packed, wait for delivery and start a return instead."),
        ],
    ),
    (
        "p-order-confirmation-email",
        "The order confirmation email",
        "2026-06-18",
        CURRENT,
        [
            (
                "What it contains",
                "The email lists your items, the delivery address, the shipping speed and the total. It arrives within five minutes of ordering.",
            ),
            (
                "It did not arrive",
                "Check your spam folder first. If it is not there, look in Orders in your account. If the order is missing there too, the payment did not go through and you were not charged.",
            ),
        ],
    ),
    (
        "p-order-invoice",
        "Download an invoice",
        "2026-06-18",
        CURRENT,
        [
            (
                "Where",
                "Open Orders, choose the order and select Download invoice. The invoice is a PDF and is available as soon as the order ships.",
            ),
            (
                "Company details",
                "Add your company name and VAT number under Settings before you order. An invoice cannot be edited after it is issued.",
            ),
        ],
    ),
    (
        "p-order-history",
        "Your order history",
        "2026-05-02",
        CURRENT,
        [
            (
                "How far back",
                "Orders shows every order placed with your account since you registered. Guest orders are not listed; use the link in their confirmation email.",
            ),
        ],
    ),
    (
        "p-order-combine",
        "Combine two orders",
        "2026-05-02",
        CURRENT,
        [
            (
                "Not possible after ordering",
                "We cannot merge two orders once they are placed. To save shipping, place the second order within the 1-hour cancellation window and cancel the first, then add its items to a single new order.",
            ),
        ],
    ),
    (
        "p-order-gift-message",
        "Add a gift message",
        "2026-09-10",
        CURRENT,
        [
            (
                "At checkout",
                "Tick Add a gift message at checkout and type up to 150 characters. The message is printed on a card and the price is left off the packing slip.",
            ),
        ],
    ),
    (
        "p-order-preorder",
        "Pre-orders",
        "2026-09-10",
        CURRENT,
        [
            (
                "How they work",
                "A pre-order is charged when you place it and ships on the release date shown on the product page. If the date moves, we email you and you can cancel for a full refund.",
            ),
        ],
    ),
    # ---- shipping
    (
        "p-ship-times",
        "Shipping times",
        "2026-09-01",
        CURRENT,
        [
            (
                "Standard shipping",
                "Standard shipping takes 3 to 5 business days inside the United States. Orders placed before 2 pm Eastern on a business day are dispatched the same day.",
            ),
            ("Business days", "Weekends and public holidays do not count as business days."),
        ],
    ),
    (
        "p-ship-costs",
        "Shipping costs",
        "2026-09-01",
        CURRENT,
        [
            ("Standard", "Standard shipping is free on orders over $50. On orders of $50 or less it costs $4.99."),
            (
                "Express",
                "Express shipping costs $12.99 on any order. See the express shipping page for delivery times.",
            ),
        ],
    ),
    (
        "p-ship-costs-old",
        "Shipping costs (old)",
        "2025-01-01",
        RETIRED,
        [
            ("Flat fee", "Shipping costs a flat $6.99 on every order, whatever the total."),
        ],
    ),
    (
        "p-ship-countries",
        "Where we ship",
        "2026-08-20",
        CURRENT,
        [
            (
                "Countries",
                "We ship to the United States, Canada, the United Kingdom, all European Union member states and Australia. We cannot ship to PO boxes.",
            ),
            ("Delivery time abroad", "International parcels take 7 to 14 business days."),
        ],
    ),
    (
        "p-ship-international-duties",
        "Duties and import taxes",
        "2026-08-20",
        CURRENT,
        [
            (
                "Who pays",
                "Duties and import taxes on international parcels are paid by the recipient on delivery. They are not included in the price you pay at checkout.",
            ),
        ],
    ),
    (
        "p-ship-express",
        "Express shipping",
        "2026-09-01",
        CURRENT,
        [
            (
                "Delivery time",
                "Express shipping delivers in 1 to 2 business days within the United States. It is not available to PO boxes or parcel lockers.",
            ),
            ("Cut-off", "Order before 2 pm Eastern for same-day dispatch."),
        ],
    ),
    (
        "p-ship-tracking-delay",
        "Parcel is late",
        "2026-07-14",
        CURRENT,
        [
            (
                "When to worry",
                "A parcel is late once it is more than 2 business days past the delivery window you were quoted. Check tracking first; carriers sometimes rescan a parcel late.",
            ),
            (
                "What we do",
                "Contact support with the order number. We open a trace with the carrier, which takes up to 3 business days.",
            ),
        ],
    ),
    (
        "p-ship-damaged",
        "Damaged parcel",
        "2026-07-14",
        CURRENT,
        [
            (
                "Report it within 7 days",
                "If your parcel arrives damaged, report it within 7 days of delivery and attach photos of the box and the item. We then send a replacement or refund you, whichever you prefer.",
            ),
        ],
    ),
    (
        "p-ship-lost",
        "Lost parcel",
        "2026-07-14",
        CURRENT,
        [
            (
                "When we step in",
                "If a parcel has not arrived 10 business days after it shipped, we treat it as lost and either send a new one or refund you in full.",
            ),
        ],
    ),
    (
        "p-ship-pickup-point",
        "Pickup lockers",
        "2026-06-05",
        CURRENT,
        [
            (
                "How it works",
                "In the United States and the United Kingdom you can have a parcel sent to a pickup locker. You get a code by email when it arrives, and the parcel is held for 5 days.",
            ),
        ],
    ),
    (
        "p-ship-holiday",
        "Holiday delivery",
        "2026-10-01",
        CURRENT,
        [
            (
                "Order by",
                "Orders placed after December 18 may not arrive before December 25. Express orders placed by December 21 usually do.",
            ),
        ],
    ),
    # ---- returns
    (
        "p-return-window",
        "Return window",
        "2026-09-01",
        CURRENT,
        [
            (
                "30 days",
                "You can return items bought at full price within 30 days of delivery for a full refund. The days are counted from the delivery date shown in tracking.",
            ),
        ],
    ),
    (
        "p-return-window-old",
        "Return window (old)",
        "2025-01-01",
        RETIRED,
        [
            ("14 days", "You can return any item within 14 days of delivery for a full refund."),
        ],
    ),
    (
        "p-return-how",
        "How to return an item",
        "2026-09-01",
        CURRENT,
        [
            (
                "Steps",
                "Open Orders, choose the order and select Start a return. Print the prepaid label, pack the item and drop it at any carrier location.",
            ),
        ],
    ),
    (
        "p-return-refund-time",
        "When you get your refund",
        "2026-09-01",
        CURRENT,
        [
            (
                "Timing",
                "We refund you 5 to 7 business days after the parcel reaches our warehouse. The refund goes to your original payment method.",
            ),
        ],
    ),
    (
        "p-return-exchange",
        "Exchanges",
        "2026-08-03",
        CURRENT,
        [
            (
                "One exchange per order",
                "You can exchange an item for a different size or colour once per order, within 30 days of delivery. Choose Exchange instead of Return when you start the return.",
            ),
        ],
    ),
    (
        "p-return-condition",
        "Condition of returned items",
        "2026-08-03",
        CURRENT,
        [
            (
                "What we accept",
                "Items must be unused, in their original packaging and with tags attached. We cannot refund items that show signs of wear.",
            ),
        ],
    ),
    (
        "p-return-fee",
        "Return shipping fee",
        "2026-09-01",
        CURRENT,
        [
            (
                "Free returns",
                "Returns are free within the United States: the prepaid label costs you nothing. Outside the United States you pay the return postage.",
            ),
        ],
    ),
    (
        "p-return-fee-old",
        "Return shipping fee (old)",
        "2025-01-01",
        RETIRED,
        [
            ("A fee", "Returns carry a $5 fee, deducted from your refund."),
        ],
    ),
    (
        "p-return-warranty",
        "Warranty on electronics",
        "2026-04-15",
        CURRENT,
        [
            (
                "12 months",
                "Electronics are covered for 12 months from delivery against defects. Contact support with the order number and a short description of the fault; this is separate from the 30-day return window.",
            ),
        ],
    ),
    # ---- accounts
    (
        "p-account-create",
        "Create an account",
        "2026-06-01",
        CURRENT,
        [
            (
                "Sign up",
                "Choose Sign up, enter your email and a password of at least 10 characters, then confirm the email we send you. The link works for 24 hours.",
            ),
        ],
    ),
    (
        "p-account-reset-password",
        "Reset your password",
        "2026-06-01",
        CURRENT,
        [
            (
                "Reset link",
                "Choose Forgot password on the login page and enter your email. The reset link we send is valid for 1 hour. If it expires, request a new one.",
            ),
        ],
    ),
    (
        "p-account-change-email",
        "Change your email address",
        "2026-06-01",
        CURRENT,
        [
            (
                "Steps",
                "Open Settings, choose Email and enter the new address. You must type your password to confirm, and we send a confirmation link to the new address.",
            ),
        ],
    ),
    (
        "p-account-delete",
        "Delete your account",
        "2026-06-01",
        CURRENT,
        [
            (
                "Request deletion",
                "Open Settings, then Privacy, then Delete my account. Deletion finishes within 30 days. Order records needed for tax law are kept in anonymised form.",
            ),
        ],
    ),
    (
        "p-account-2fa",
        "Two-factor sign-in",
        "2026-07-07",
        CURRENT,
        [
            (
                "Turn it on",
                "Open Settings, then Security, and scan the code with an authenticator app. Save the ten backup codes; each works once.",
            ),
        ],
    ),
    (
        "p-account-locked",
        "Account locked",
        "2026-07-07",
        CURRENT,
        [
            (
                "After failed attempts",
                "Five wrong passwords in a row lock the account for 15 minutes. You can wait, or reset your password to unlock it at once.",
            ),
        ],
    ),
    (
        "p-account-addresses",
        "Saved addresses",
        "2026-05-20",
        CURRENT,
        [
            (
                "Up to 10",
                "You can save up to 10 delivery addresses under Settings, then Addresses, and choose one as the default.",
            ),
        ],
    ),
    (
        "p-account-newsletter",
        "Emails and newsletter",
        "2026-05-20",
        CURRENT,
        [
            (
                "Unsubscribe",
                "Every marketing email has an unsubscribe link at the bottom. Order and shipping emails cannot be turned off because they carry your receipts.",
            ),
        ],
    ),
    # ---- payments
    (
        "p-pay-methods",
        "Payment methods",
        "2026-08-28",
        CURRENT,
        [
            (
                "What we accept",
                "We accept Visa, Mastercard, American Express, PayPal and Apple Pay. The card is charged when the order is placed.",
            ),
        ],
    ),
    (
        "p-pay-declined",
        "My card was declined",
        "2026-08-28",
        CURRENT,
        [
            (
                "What to do",
                "Check the card number, expiry and billing address, then try again. If it still fails, try another card or contact your bank: declines come from the card issuer, not from us.",
            ),
        ],
    ),
    (
        "p-pay-double-charge",
        "I was charged twice",
        "2026-08-28",
        CURRENT,
        [
            (
                "Pending authorisations",
                "A failed or repeated checkout can leave a pending authorisation next to the real charge. The extra hold drops off by itself within 3 to 5 business days. If both stay after that, contact support.",
            ),
        ],
    ),
    (
        "p-pay-invoice-company",
        "Paying as a company",
        "2026-05-14",
        CURRENT,
        [
            (
                "VAT and company name",
                "Add the company name and VAT number under Settings before you order so they appear on the invoice. We do not offer payment by bank transfer.",
            ),
        ],
    ),
    (
        "p-pay-gift-cards",
        "Gift cards",
        "2026-09-10",
        CURRENT,
        [
            (
                "Amounts",
                "Gift cards come in amounts from $10 to $200. They do not expire and can be used on the whole shop, but only one gift card can be applied per order.",
            ),
        ],
    ),
    (
        "p-pay-promo-codes",
        "Promo codes",
        "2026-09-10",
        CURRENT,
        [
            (
                "Rules",
                "Enter a promo code at checkout. Only one promo code works per order, and promo codes cannot be combined with each other. A gift card can be added on top of a promo code.",
            ),
        ],
    ),
    (
        "p-pay-currency",
        "Prices and currency",
        "2026-05-14",
        CURRENT,
        [
            (
                "US dollars",
                "All prices are in US dollars. If your card is in another currency, your bank converts the amount and may add a fee.",
            ),
        ],
    ),
    (
        "p-pay-refund-method",
        "How refunds are paid",
        "2026-09-01",
        CURRENT,
        [
            (
                "Same way back",
                "Refunds go back to the payment method you used. Orders paid with a gift card are refunded as store credit on the same card.",
            ),
        ],
    ),
    (
        "p-pay-installments",
        "Pay in installments",
        "2026-10-05",
        CURRENT,
        [
            (
                "Three payments",
                "Orders between $50 and $1,000 can be split into 3 equal monthly payments at checkout, with no interest. The first payment is taken when you order.",
            ),
        ],
    ),
    # ---- error codes
    (
        "p-error-e1042",
        "Error PR-E1042",
        "2026-08-01",
        CURRENT,
        [
            (
                "Meaning",
                "Error PR-E1042 means your payment method was declined by the card issuer. Try another card or contact your bank.",
            ),
        ],
    ),
    (
        "p-error-e1043",
        "Error PR-E1043",
        "2026-08-01",
        CURRENT,
        [
            (
                "Meaning",
                "Error PR-E1043 means the billing address does not match the one your card issuer has on file. Correct the address at checkout and try again.",
            ),
        ],
    ),
    (
        "p-error-e1100",
        "Error PR-E1100",
        "2026-08-01",
        CURRENT,
        [
            (
                "Meaning",
                "Error PR-E1100 means your session expired while you were checking out. Sign in again; the items in your cart are kept for 7 days.",
            ),
        ],
    ),
    (
        "p-error-e2091",
        "Error PR-E2091",
        "2026-08-01",
        CURRENT,
        [
            (
                "Meaning",
                "Error PR-E2091 means we could not create a shipping label for the address you entered. Check the street and postcode, or choose a pickup locker.",
            ),
        ],
    ),
    (
        "p-error-e2092",
        "Error PR-E2092",
        "2026-08-01",
        CURRENT,
        [
            (
                "Meaning",
                "Error PR-E2092 means the pickup locker you chose is full or closed. Pick another locker in the list and place the order again.",
            ),
        ],
    ),
    (
        "p-error-e3001",
        "Error PR-E3001",
        "2026-08-01",
        CURRENT,
        [
            (
                "Meaning",
                "Error PR-E3001 means the promo code has expired. Promo codes show their end date in the email that carried them.",
            ),
        ],
    ),
    (
        "p-error-e3002",
        "Error PR-E3002",
        "2026-08-01",
        CURRENT,
        [
            (
                "Meaning",
                "Error PR-E3002 means the promo code was already used on your account. Each code works once per customer.",
            ),
        ],
    ),
    (
        "p-error-e4004",
        "Error PR-E4004",
        "2026-08-01",
        CURRENT,
        [
            (
                "Meaning",
                "Error PR-E4004 means an item sold out while it was in your cart. Remove it, or choose another size or colour.",
            ),
        ],
    ),
    (
        "p-error-e5000",
        "Error PR-E5000",
        "2026-08-01",
        CURRENT,
        [
            (
                "Meaning",
                "Error PR-E5000 means a temporary problem on our side. Wait 5 minutes and try again; your card is not charged when this error appears.",
            ),
        ],
    ),
    (
        "p-error-e5101",
        "Error PR-E5101",
        "2026-08-01",
        CURRENT,
        [
            (
                "Meaning",
                "Error PR-E5101 means your account is locked after too many failed sign-in attempts. It unlocks by itself after 15 minutes, or at once if you reset your password.",
            ),
        ],
    ),
    # ---- other
    (
        "p-contact-support",
        "Contact support",
        "2026-09-15",
        CURRENT,
        [
            (
                "Chat and email",
                "Chat with us from 8:00 to 20:00 Eastern, Monday to Saturday. Email replies arrive within 1 business day. Always include your order number.",
            ),
        ],
    ),
    (
        "p-privacy-cookies",
        "Cookies",
        "2026-03-10",
        CURRENT,
        [
            (
                "What we use",
                "We set only essential cookies, which keep your cart and your login, until you accept analytics cookies in the banner. You can change your choice at any time under Settings, then Privacy.",
            ),
        ],
    ),
    (
        "p-sizing-guide",
        "Sizing guide",
        "2026-04-02",
        CURRENT,
        [
            (
                "Measure yourself",
                "Measure your chest at the widest point and your waist at the narrowest. Compare the numbers with the chart on each product page; if you are between two sizes, choose the larger one.",
            ),
        ],
    ),
]
```

- Declares `PAGES` as a list of a fixed list of text, text, text, text, a list of a fixed list of text, text and sets it to a list of 60 item(s).
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`scripts/make_pages.py`, lines 766 to 777:

```python
def main() -> None:
    out = Path(__file__).resolve().parent.parent / "data" / "pages"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.md"):
        old.unlink()
    for page_id, title, updated, status, sections in PAGES:
        body = "\n\n".join(f"## {heading}\n\n{text}" for heading, text in sections)
        (out / f"{page_id}.md").write_text(
            f"---\nid: {page_id}\ntitle: {title}\nupdated: {updated}\nstatus: {status}\n---\n# {title}\n\n{body}\n",
            encoding="utf-8",
        )
    retired = sum(p[3] == RETIRED for p in PAGES)
```

- Defines the function `main`. It returns nothing (None).
- It takes no parameters.
- Stores the result of `Path(__file__).resolve().parent.parent / 'data' / 'pages'` under the name `out`.
  - `/` is divide.
  - `.resolve(...)` turns a path into a full absolute path.
  - `Path` from the standard library module `pathlib`, which a file or folder location.
- Calls `.mkdir(...)` creates a folder with 2 argument(s); the result is not kept.
  - `.mkdir(...)` creates a folder.
- Loop: the indented lines below run once for each item of `out.glob('*.md')`; `old` names the current item.
  - `.glob(...)` finds files whose names match a pattern.
- Calls `.unlink(...)` deletes a file; the result is not kept.
  - `.unlink(...)` deletes a file.
- Loop: the indented lines below run once for each item of `PAGES`; `(page_id, title, updated, s...` names the current item.
- Stores the result of calling `'\n\n'.join` under the name `body`.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Calls `.write_text(...)` writes text to a file, replacing it with 2 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `/` is divide.
- Stores the result of calling `sum` under the name `retired`.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`scripts/make_pages.py`, lines 778 to 782:

```python
    print(f"wrote {len(PAGES)} pages ({len(PAGES) - retired} current, {retired} retired) to {out}")


if __name__ == "__main__":
    main()
```

- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).
  - `-` is subtract.
- Decision: the indented lines below run only when `__name__ == '__main__'` is true.
  - `==` means equal.
- Calls `main`, a function of this file; the result is not kept.
  - `main`, a function of this file.

### `scripts/make_questions.py`

In its own words: "Write data/questions/dev.jsonl (30) and data/questions/test.jsonl (120, frozen)."

451 non-blank lines; it defines `take`, `main`.

`scripts/make_questions.py`, lines 1 to 11:

```python
"""Write data/questions/dev.jsonl (30) and data/questions/test.jsonl (120, frozen).

Types: `answerable` (a gold page and the fact that answers it), `exact` (the answer hinges on an error code or a
number), `unanswerable` (plausible, but no page answers it; some sit close to a real page on purpose).
Mix of the test set: 70 answerable, 30 unanswerable, 20 exact. The dev set has the same mix in 17, 8 and 5.
"""

from __future__ import annotations

import json
from pathlib import Path
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Brings in `Path` from the standard library module `pathlib`.

`scripts/make_questions.py`, lines 13 to 320:

```python
# (question, gold page, the fact a correct answer states)
ANSWERABLE = [
    (
        "How do I place an order without creating an account?",
        "p-order-place",
        "you can check out as a guest and create an account afterwards",
    ),
    ("How soon after ordering does the confirmation email arrive?", "p-order-place", "within five minutes"),
    (
        "Where do I see the tracking information for my parcel?",
        "p-order-track",
        "Orders in your account or the tracking link in the shipping email",
    ),
    (
        "My tracking has not moved for a week. What should I do?",
        "p-order-track",
        "contact support with the order number after 5 business days without a scan",
    ),
    (
        "Can I change the delivery address after I ordered?",
        "p-order-change-address",
        "yes, for up to 2 hours after placing the order",
    ),
    (
        "The address is locked already. Is there anything you can do?",
        "p-order-change-address",
        "contact support right away; we may redirect it if it has not left the warehouse",
    ),
    (
        "How can I cancel an order myself?",
        "p-order-cancel",
        "choose Cancel order on the order within 1 hour if it is not packed",
    ),
    ("I want to cancel but my order was already packed.", "p-order-cancel", "wait for delivery and start a return"),
    (
        "I never got an order confirmation email. What should I check?",
        "p-order-confirmation-email",
        "the spam folder, then Orders in your account",
    ),
    (
        "My order is missing from my account and I got no email. Was I charged?",
        "p-order-confirmation-email",
        "the payment did not go through and you were not charged",
    ),
    ("Where can I download an invoice?", "p-order-invoice", "Orders, choose the order, Download invoice"),
    (
        "How do I get my company name and VAT number onto the invoice?",
        "p-order-invoice",
        "add them under Settings before you order",
    ),
    (
        "Do orders I placed as a guest show up in my account?",
        "p-order-history",
        "no, use the link in the guest order's confirmation email",
    ),
    ("Can you merge two orders into one parcel?", "p-order-combine", "no, not once they are placed"),
    (
        "Is the price shown on the gift card message?",
        "p-order-gift-message",
        "no, the price is left off the packing slip",
    ),
    ("When am I charged for a pre-order?", "p-order-preorder", "when you place it"),
    (
        "What if the release date of my pre-order moves?",
        "p-order-preorder",
        "we email you and you can cancel for a full refund",
    ),
    ("How long does standard shipping take within the US?", "p-ship-times", "3 to 5 business days"),
    (
        "Do weekends count as business days for shipping?",
        "p-ship-times",
        "no, weekends and public holidays do not count",
    ),
    (
        "Which countries do you deliver to?",
        "p-ship-countries",
        "the US, Canada, the UK, EU member states and Australia",
    ),
    ("Can you deliver to a PO box?", "p-ship-countries", "no, we cannot ship to PO boxes"),
    ("How long do parcels to other countries take?", "p-ship-countries", "7 to 14 business days"),
    (
        "Who pays customs duties on an international parcel?",
        "p-ship-international-duties",
        "the recipient, on delivery",
    ),
    ("Are import taxes included in the price at checkout?", "p-ship-international-duties", "no, they are not included"),
    ("How fast is express delivery?", "p-ship-express", "1 to 2 business days within the United States"),
    (
        "Can I choose express shipping to a parcel locker?",
        "p-ship-express",
        "no, it is not available to PO boxes or parcel lockers",
    ),
    (
        "When do you call a parcel late?",
        "p-ship-tracking-delay",
        "more than 2 business days past the quoted delivery window",
    ),
    (
        "I told support my parcel is late. What happens next?",
        "p-ship-tracking-delay",
        "we open a trace with the carrier, which takes up to 3 business days",
    ),
    ("My parcel arrived damaged. What do I do?", "p-ship-damaged", "report it within 7 days with photos"),
    (
        "Can I get a replacement instead of a refund for a damaged item?",
        "p-ship-damaged",
        "yes, a replacement or a refund, whichever you prefer",
    ),
    (
        "What do you do if a parcel never arrives?",
        "p-ship-lost",
        "after 10 business days we send a new one or refund you in full",
    ),
    (
        "How do I know my parcel is waiting in a locker?",
        "p-ship-pickup-point",
        "you get a code by email when it arrives",
    ),
    (
        "Can I still get my order before the holidays if I order late?",
        "p-ship-holiday",
        "orders placed after December 18 may not arrive before December 25",
    ),
    ("Where do I drop off a parcel I am returning?", "p-return-how", "at any carrier location, with the prepaid label"),
    ("How do I begin a return?", "p-return-how", "Orders, choose the order, Start a return, print the prepaid label"),
    (
        "When does the money for a returned item come back?",
        "p-return-refund-time",
        "5 to 7 business days after the parcel reaches the warehouse",
    ),
    ("Which payment method does the refund go to?", "p-pay-refund-method", "the payment method you used"),
    ("Can I swap a pair of shoes for another size?", "p-return-exchange", "once per order, within 30 days of delivery"),
    (
        "In what state do returned items need to be?",
        "p-return-condition",
        "unused, in original packaging, tags attached",
    ),
    ("Can I return something I have worn?", "p-return-condition", "no, items showing signs of wear cannot be refunded"),
    (
        "Do I pay to send something back from the US?",
        "p-return-fee",
        "no, the prepaid label is free within the United States",
    ),
    (
        "What if my headphones stop working after four months?",
        "p-return-warranty",
        "electronics are covered for 12 months; contact support",
    ),
    ("How do I confirm my new account?", "p-account-create", "confirm the email we send; the link works for 24 hours"),
    (
        "I forgot my password. What now?",
        "p-account-reset-password",
        "choose Forgot password on the login page and use the reset link",
    ),
    (
        "How do I change the email address of my account?",
        "p-account-change-email",
        "Settings, Email, type your password; confirm via the link sent to the new address",
    ),
    (
        "How do I delete my account?",
        "p-account-delete",
        "Settings, Privacy, Delete my account; it finishes within 30 days",
    ),
    (
        "What happens to my order records when I delete my account?",
        "p-account-delete",
        "records needed for tax law are kept in anonymised form",
    ),
    (
        "How do I set up two-factor sign-in?",
        "p-account-2fa",
        "Settings, Security, scan the code with an authenticator app",
    ),
    (
        "My account is locked. How do I get back in right away?",
        "p-account-locked",
        "reset your password to unlock it at once",
    ),
    (
        "Can I turn off the shipping notification emails?",
        "p-account-newsletter",
        "no, order and shipping emails cannot be turned off",
    ),
    (
        "How do I stop getting marketing emails?",
        "p-account-newsletter",
        "use the unsubscribe link at the bottom of any marketing email",
    ),
    ("Which cards can I pay with?", "p-pay-methods", "Visa, Mastercard, American Express, PayPal and Apple Pay"),
    ("When is my card charged?", "p-pay-methods", "when the order is placed"),
    (
        "My card was declined. What should I do?",
        "p-pay-declined",
        "check the details and try again, try another card or contact your bank",
    ),
    ("Who declines a payment, you or my bank?", "p-pay-declined", "the card issuer"),
    (
        "Why do I see two charges for one order?",
        "p-pay-double-charge",
        "a pending authorisation that drops off by itself in 3 to 5 business days",
    ),
    ("Can a company pay by bank transfer?", "p-pay-invoice-company", "no, we do not offer payment by bank transfer"),
    ("Do gift cards expire?", "p-pay-gift-cards", "no, they do not expire"),
    ("Can I use two gift cards on one order?", "p-pay-gift-cards", "no, only one gift card per order"),
    ("Can I stack two promo codes?", "p-pay-promo-codes", "no, only one promo code works per order"),
    (
        "Can I use a gift card together with a promo code?",
        "p-pay-promo-codes",
        "yes, a gift card can be added on top of a promo code",
    ),
    ("In which currency are prices shown?", "p-pay-currency", "US dollars"),
    (
        "Who converts the price if my card is in euros?",
        "p-pay-currency",
        "your bank converts the amount and may add a fee",
    ),
    ("I paid with a gift card. How will I be refunded?", "p-pay-refund-method", "as store credit on the same card"),
    (
        "Can I buy something now and pay for it over several months?",
        "p-pay-installments",
        "yes, split into 3 equal monthly payments with no interest",
    ),
    ("How quickly do you answer emails?", "p-contact-support", "within 1 business day"),
    ("Which days is the chat open?", "p-contact-support", "Monday to Saturday"),
    ("Which cookies do you set before I accept anything?", "p-privacy-cookies", "only essential cookies"),
    ("How can I change my cookie choice later?", "p-privacy-cookies", "Settings, then Privacy"),
    ("I am between two sizes. Which one do I take?", "p-sizing-guide", "choose the larger one"),
    (
        "How should I measure myself for the size chart?",
        "p-sizing-guide",
        "chest at the widest point and waist at the narrowest",
    ),
    (
        "Is it possible to ship a gift with a handwritten note from you?",
        "p-order-gift-message",
        "tick Add a gift message at checkout; it is printed on a card",
    ),
    ("Do I need to be signed in to check out?", "p-order-place", "no, you can check out as a guest"),
    ("What do I do when a promo code shows an error?", "p-error-e3001", "PR-E3001 means the promo code has expired"),
    (
        "Does a failed checkout cost me money?",
        "p-pay-double-charge",
        "a pending authorisation may appear and drops off by itself",
    ),
    ("What does the return label cost for a US return?", "p-return-fee", "nothing, it is free"),
    (
        "What happens to the tracking of my order when the carrier rescans late?",
        "p-ship-tracking-delay",
        "carriers sometimes rescan a parcel late, so check tracking first",
    ),
    ("Does the invoice exist before my order ships?", "p-order-invoice", "it is available as soon as the order ships"),
    (
        "Can I change the shipping speed after placing an order?",
        "p-order-place",
        "you pick the shipping speed at checkout",
    ),
    (
        "When does a standard order leave the warehouse?",
        "p-ship-times",
        "orders placed before 2 pm Eastern on a business day are dispatched the same day",
    ),
    ("What can I do if I do not want a replacement for a damaged item?", "p-ship-damaged", "ask for a refund"),
    (
        "Is there a time limit to report a lost parcel?",
        "p-ship-lost",
        "a parcel is treated as lost 10 business days after it shipped",
    ),
    ("What if the locker I picked is not available?", "p-error-e2092", "pick another locker and place the order again"),
    (
        "How do I know my items will not disappear from my cart while I sign in again?",
        "p-error-e1100",
        "items in the cart are kept for 7 days",
    ),
    (
        "Are the cookies used for analytics switched on by default?",
        "p-privacy-cookies",
        "no, only essential cookies until you accept analytics",
    ),
    (
        "Are orders paid in installments charged in full upfront?",
        "p-pay-installments",
        "no, the first payment is taken when you order",
    ),
    (
        "Do I have to pay VAT on an order for my company?",
        "p-pay-invoice-company",
        "add the VAT number under Settings so it appears on the invoice",
    ),
    ("Where do I tick the gift message option?", "p-order-gift-message", "at checkout"),
    ("What happens to a cart after my session expires?", "p-error-e1100", "the items are kept for 7 days"),
    ("What does an expired-session error ask me to do?", "p-error-e1100", "sign in again"),
    (
        "I got a message that the billing address is wrong. What does it mean?",
        "p-error-e1043",
        "the billing address does not match the one your card issuer has on file",
    ),
    (
        "An item sold out while I was shopping and checkout stopped. What should I do?",
        "p-error-e4004",
        "remove it or choose another size or colour",
    ),
    (
        "The checkout failed with a temporary problem. Am I charged?",
        "p-error-e5000",
        "no, your card is not charged when this error appears",
    ),
]
```

- Stores a list of 93 item(s) under the name `ANSWERABLE`.

`scripts/make_questions.py`, lines 322 to 353:

```python
# Questions that hinge on an exact code or number.
EXACT = [
    ("What does error PR-E1042 mean?", "p-error-e1042", "the payment method was declined by the card issuer"),
    ("What is PR-E1043?", "p-error-e1043", "the billing address does not match the one the card issuer has on file"),
    ("What does PR-E1100 mean?", "p-error-e1100", "the session expired during checkout"),
    ("What's E2091 about?", "p-error-e2091", "no shipping label could be created for the address"),
    ("I see error PR-E2092 at checkout. What is wrong?", "p-error-e2092", "the pickup locker is full or closed"),
    ("What does PR-E3001 mean?", "p-error-e3001", "the promo code has expired"),
    ("Why did I get PR-E3002?", "p-error-e3002", "the promo code was already used on your account"),
    ("What does error PR-E4004 mean?", "p-error-e4004", "an item sold out while it was in your cart"),
    ("What is error PR-E5000?", "p-error-e5000", "a temporary problem on our side"),
    (
        "What does PR-E5101 say about my account?",
        "p-error-e5101",
        "the account is locked after too many failed sign-in attempts",
    ),
    ("Explain E1042 please.", "p-error-e1042", "the card issuer declined the payment method"),
    ("How long does PR-E5101 last?", "p-error-e5101", "it unlocks by itself after 15 minutes"),
    ("How much do I have to spend to get free standard shipping?", "p-ship-costs", "more than $50"),
    ("How much does standard shipping cost on a $30 order?", "p-ship-costs", "$4.99"),
    ("What does express shipping cost?", "p-ship-costs", "$12.99"),
    ("How many days do I have to return an item?", "p-return-window", "30 days from delivery"),
    ("What is the smallest and largest gift card amount?", "p-pay-gift-cards", "$10 to $200"),
    ("For which order totals can I pay in installments?", "p-pay-installments", "between $50 and $1,000"),
    ("How many characters must a password have?", "p-account-create", "at least 10"),
    ("How long is a password reset link valid?", "p-account-reset-password", "1 hour"),
    ("For how long does my account stay locked after five wrong passwords?", "p-account-locked", "15 minutes"),
    ("How many addresses can I save?", "p-account-addresses", "up to 10"),
    ("What is the character limit of a gift message?", "p-order-gift-message", "150 characters"),
    ("How many days is a parcel held at a locker?", "p-ship-pickup-point", "5 days"),
    ("For how many months is electronics covered by the warranty?", "p-return-warranty", "12 months"),
]
```

- Stores a list of 25 item(s) under the name `EXACT`.

`scripts/make_questions.py`, lines 355 to 394:

```python
UNANSWERABLE = [
    ("What is your return window for sale items specifically?", True),
    ("Do you ship to Antarctica?", False),
    ("Do you have a loyalty rewards program?", False),
    ("Do you have physical stores I can visit?", False),
    ("Do you price match competitors?", False),
    ("Can I add an item to an order I already placed?", True),
    ("What is your phone number?", True),
    ("Do you offer gift wrapping?", True),
    ("How do I become an affiliate partner?", False),
    ("Are your products tested on animals?", False),
    ("What is the weight limit for a parcel?", True),
    ("Do you offer student discounts?", False),
    ("Can I pick the exact day my parcel is delivered?", True),
    ("How long is the warranty on clothing?", True),
    ("Can I return an item to a physical shop?", True),
    ("What is your best-selling product?", False),
    ("Do you sell physical gift cards?", True),
    ("Can I change my username?", True),
    ("Is there a mobile app?", False),
    ("How long do you keep my order data?", True),
    ("Can I get a refund on a pre-order after it has shipped?", True),
    ("Do you deliver on Sundays?", True),
    ("Why was my product review not published?", False),
    ("Can I split a payment between two credit cards?", True),
    ("What are your support hours on public holidays?", True),
    ("How do I change the language of the website?", False),
    ("Do you ship hazardous goods?", False),
    ("Who is the CEO of the company?", False),
    ("Is the yoga mat machine washable?", False),
    ("What is the return policy for custom engraved items?", True),
    ("Can I get my invoice in another language?", True),
    ("How do I track a pre-order before it ships?", True),
    ("Do you give free samples?", False),
    ("How can I leave feedback about your website?", False),
    ("Do you adjust the price if an item goes on sale after I bought it?", True),
    ("Do you have a recycling program for old electronics?", False),
    ("Can I choose a two-hour delivery window?", True),
    ("Do you offer cash on delivery?", True),
]
```

- Stores a list of 38 item(s) under the name `UNANSWERABLE`.

`scripts/make_questions.py`, lines 397 to 408:

```python
def take(items: list, indexes: list[int]) -> list:
    return [items[i] for i in indexes]


def main() -> None:
    assert len(ANSWERABLE) >= 87, len(ANSWERABLE)
    assert len(EXACT) == 25
    assert len(UNANSWERABLE) >= 38
    dev_a_idx = list(range(0, 87, 5))[:17]
    test_a_idx = [i for i in range(87) if i not in dev_a_idx][:70]
    dev_x_idx = [0, 6, 12, 15, 20]
    test_x_idx = [i for i in range(25) if i not in dev_x_idx]
```

- Defines the function `take`. It returns a list.
- Its parameters:
    - `items` holds a list.
    - `indexes` holds a list of a whole number.
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `main`. It returns nothing (None).
- It takes no parameters.
- Checks that `len(ANSWERABLE) >= 87` is true; if it is not, the test fails with an `AssertionError` and the message `len(ANSWERABLE)`.
  - `>=` means greater than or equal.
  - `len` counts the items in a collection (or the characters in text).
- Checks that `len(EXACT) == 25` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Checks that `len(UNANSWERABLE) >= 38` is true; if it is not, the test fails with an `AssertionError`.
  - `>=` means greater than or equal.
  - `len` counts the items in a collection (or the characters in text).
- Stores the part of `list(range(0, 87, 5))` picked by `:17` under the name `dev_a_idx`.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - `list` makes a list (a copy when given a collection).
  - `range` makes the numbers from 0 up to (not including) the given one.
- Stores the part of `[i for i in range(87) if i ...` picked by `:70` under the name `test_a_idx`.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `range` makes the numbers from 0 up to (not including) the given one.
  - `not in` means is not contained in.
- Stores a list of 5 item(s) under the name `dev_x_idx`.
- Stores a list built by looping under the name `test_x_idx`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `range` makes the numbers from 0 up to (not including) the given one.
  - `not in` means is not contained in.

`scripts/make_questions.py`, lines 409 to 418:

```python
    dev_u_idx = [1, 5, 9, 14, 22, 27, 31, 35]
    test_u_idx = [i for i in range(38) if i not in dev_u_idx][:30]
    assert (len(test_x_idx), len(test_u_idx), len(test_a_idx)) == (20, 30, 70)
    rows = {"dev": [], "test": []}

    def add(split: str, kind: str, item) -> None:
        number = len(rows[split]) + 1
        prefix = "d" if split == "dev" else "t"
        if kind == "unanswerable":
            question, near = item
```

- Stores a list of 8 item(s) under the name `dev_u_idx`.
- Stores the part of `[i for i in range(38) if i ...` picked by `:30` under the name `test_u_idx`.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `range` makes the numbers from 0 up to (not including) the given one.
  - `not in` means is not contained in.
- Checks that `(len(test_x_idx), len(test_u_idx), len(test_a_idx)) == (20, 30, 70)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Stores a dictionary with 2 entries under the name `rows`.
- Defines the function `add`. It returns nothing (None).
- Its parameters:
    - `split` holds text.
    - `kind` holds text.
    - `item`.
- Stores the result of `len(rows[split]) + 1` under the name `number`.
  - `+` is add.
  - `len` counts the items in a collection (or the characters in text).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores one of two values, chosen by a condition under the name `prefix`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `==` means equal.
- Decision: the indented lines below run only when `kind == 'unanswerable'` is true.
  - `==` means equal.
- Stores the value named `item` under the name `(question, near)`.

`scripts/make_questions.py`, lines 419 to 430:

```python
            rows[split].append(
                {
                    "id": f"q-{prefix}{number:03d}",
                    "type": kind,
                    "question": question,
                    "gold_page": None,
                    "fact": None,
                    "near_miss": near,
                }
            )
        else:
            question, page, fact = item
```

- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- `else:` — the indented lines below run when none of the conditions above were true.
- Stores the value named `item` under the name `(question, page, fact)`.

`scripts/make_questions.py`, lines 431 to 444:

```python
            rows[split].append(
                {
                    "id": f"q-{prefix}{number:03d}",
                    "type": kind,
                    "question": question,
                    "gold_page": page,
                    "fact": fact,
                    "near_miss": False,
                }
            )

    for i in dev_a_idx:
        add("dev", "answerable", ANSWERABLE[i])
    for i in dev_x_idx:
```

- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Loop: the indented lines below run once for each item of `dev_a_idx`; `i` names the current item.
- Calls `add`, a function defined in this file or passed in with 3 argument(s); the result is not kept.
  - `add`, a function defined in this file or passed in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `dev_x_idx`; `i` names the current item.

`scripts/make_questions.py`, lines 445 to 456:

```python
        add("dev", "exact", EXACT[i])
    for i in dev_u_idx:
        add("dev", "unanswerable", UNANSWERABLE[i])
    for i in test_a_idx:
        add("test", "answerable", ANSWERABLE[i])
    for i in test_x_idx:
        add("test", "exact", EXACT[i])
    for i in test_u_idx:
        add("test", "unanswerable", UNANSWERABLE[i])
    out = Path(__file__).resolve().parent.parent / "data" / "questions"
    out.mkdir(parents=True, exist_ok=True)
    for split, items in rows.items():
```

- Calls `add`, a function defined in this file or passed in with 3 argument(s); the result is not kept.
  - `add`, a function defined in this file or passed in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `dev_u_idx`; `i` names the current item.
- Calls `add`, a function defined in this file or passed in with 3 argument(s); the result is not kept.
  - `add`, a function defined in this file or passed in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `test_a_idx`; `i` names the current item.
- Calls `add`, a function defined in this file or passed in with 3 argument(s); the result is not kept.
  - `add`, a function defined in this file or passed in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `test_x_idx`; `i` names the current item.
- Calls `add`, a function defined in this file or passed in with 3 argument(s); the result is not kept.
  - `add`, a function defined in this file or passed in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `test_u_idx`; `i` names the current item.
- Calls `add`, a function defined in this file or passed in with 3 argument(s); the result is not kept.
  - `add`, a function defined in this file or passed in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of `Path(__file__).resolve().parent.parent / 'data' / 'questi...` under the name `out`.
  - `/` is divide.
  - `.resolve(...)` turns a path into a full absolute path.
  - `Path` from the standard library module `pathlib`, which a file or folder location.
- Calls `.mkdir(...)` creates a folder with 2 argument(s); the result is not kept.
  - `.mkdir(...)` creates a folder.
- Loop: the indented lines below run once for each item of `rows.items()`; `(split, items)` names the current item.
  - `.items(...)` gives the key and value pairs of a dictionary.

`scripts/make_questions.py`, lines 457 to 465:

```python
        (out / f"{split}.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in items), encoding="utf-8"
        )
        kinds = {k: sum(r["type"] == k for r in items) for k in ("answerable", "exact", "unanswerable")}
        print(split, len(items), kinds)


if __name__ == "__main__":
    main()
```

- Calls `.write_text(...)` writes text to a file, replacing it with 2 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - `/` is divide.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `+` is add.
  - `json.dumps` turns Python data into JSON text.
- Stores a dictionary built by looping under the name `kinds`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `sum` adds up all the numbers.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Calls `print` writes text to the screen with 3 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - `len` counts the items in a collection (or the characters in text).
- Decision: the indented lines below run only when `__name__ == '__main__'` is true.
  - `==` means equal.
- Calls `main`, a function of this file; the result is not kept.
  - `main`, a function of this file.

### `scripts/make_seed_sql.py`

In its own words: "Write sql/002_seed.sql: one INSERT per help-center page, generated from data/pages so the two never drift apart."

23 non-blank lines; it defines `quote`, `render`.

`scripts/make_seed_sql.py`, lines 1 to 13:

```python
"""Write sql/002_seed.sql: one INSERT per help-center page, generated from data/pages so the two never drift apart."""

from __future__ import annotations

from pathlib import Path

from cited_answers.domain.pages import parse_page

root = Path(__file__).resolve().parent.parent


def quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Path` from the standard library module `pathlib`.
- Brings in `parse_page` (Parse a page file: front matter (id, title, updated, status) and a body split on its headings.) from the project module `cited_answers.domain.pages`.
- Stores the `parent` of `Path(__file__).resolve().parent` under the name `root`.
  - `.resolve(...)` turns a path into a full absolute path.
  - `Path` from the standard library module `pathlib`, which a file or folder location.
- Defines the function `quote`. It returns text.
- Its parameters:
    - `value` holds text.
- Ends the function and gives back the result of `"'" + value.replace("'", "''") + "'"` to the caller.
  - `+` is add.
  - `.replace(...)` replaces every occurrence of one piece of text with another.

`scripts/make_seed_sql.py`, lines 16 to 21:

```python
def render() -> str:
    pages = [parse_page(p.read_text(encoding="utf-8")) for p in sorted((root / "data" / "pages").glob("*.md"))]
    rows = ",\n".join(
        f"    ({quote(p.id)}, {quote(p.title)}, DATE {quote(p.updated.isoformat())}, {quote(p.status.value)})"
        for p in pages
    )
```

- Defines the function `render`. It returns text.
- It takes no parameters.
- Stores a list built by looping under the name `pages`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `parse_page` from the project's `cited_answers.domain.pages` (Parse a page file: front matter (id, title, updated, status) and a body split on its headings.).
  - `.read_text(...)` reads a whole file as text.
  - `sorted` returns a new list with the items in order.
  - `.glob(...)` finds files whose names match a pattern.
  - `/` is divide.
- Stores the result of calling `',\n'.join` under the name `rows`.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `quote`, a function of this file.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).

`scripts/make_seed_sql.py`, lines 22 to 33:

```python
    return (
        "-- DML: the pages of the sample help center (generated by scripts/make_seed_sql.py from data/pages).\n"
        "-- The chunks and their embeddings are written by `cited ingest`, which leaves retired pages out.\n\n"
        "INSERT INTO pages (id, title, updated, status) VALUES\n"
        f"{rows}\n"
        "ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title, updated = EXCLUDED.updated, status = EXCLUDED.status;\n"
    )


if __name__ == "__main__":
    (root / "sql" / "002_seed.sql").write_text(render(), encoding="utf-8")
    print("wrote sql/002_seed.sql")
```

- Ends the function and gives back a text built from pieces (an f-string) to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `__name__ == '__main__'` is true.
  - `==` means equal.
- Calls `.write_text(...)` writes text to a file, replacing it with 2 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `render`, a function of this file.
  - `/` is divide.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.

## Try it yourself

1. Check that `scripts/make_pages.py` is valid Python without running it (running it rewrites a committed data file).

```bash
.venv/bin/python -m py_compile scripts/make_pages.py && echo 'compiles: scripts/make_pages.py'
```

What you should see (captured from this repository):

```text
compiles: scripts/make_pages.py
```

2. Check that `scripts/make_questions.py` is valid Python without running it (running it rewrites a committed data file).

```bash
.venv/bin/python -m py_compile scripts/make_questions.py && echo 'compiles: scripts/make_questions.py'
```

What you should see (captured from this repository):

```text
compiles: scripts/make_questions.py
```

3. Check that `scripts/make_seed_sql.py` is valid Python without running it (running it rewrites a committed data file).

```bash
.venv/bin/python -m py_compile scripts/make_seed_sql.py && echo 'compiles: scripts/make_seed_sql.py'
```

What you should see (captured from this repository):

```text
compiles: scripts/make_seed_sql.py
```

## Mistakes people make

- **Editing a generated file by hand.** The next run of the script would overwrite it. Change the script and run it again.
- **Using unseeded randomness.** Two runs would differ. The scripts create `random.Random(seed)` objects.
- **Letting the script read the clock.** A date inside the output would change every day; the scripts use fixed dates.
- **Forgetting to commit the output.** The tests read the committed file, not a fresh one.

## Check yourself

1. What does `scripts/make_pages.py` do?

   *Answer:* Write data/pages/*.md: the 60 pages of the sample help center (57 current, 3 retired).

2. What does `scripts/make_questions.py` do?

   *Answer:* Write data/questions/dev.jsonl (30) and data/questions/test.jsonl (120, frozen).

3. What does `scripts/make_seed_sql.py` do?

   *Answer:* Write sql/002_seed.sql: one INSERT per help-center page, generated from data/pages so the two never drift apart.

4. Why are the data files generated by scripts and then committed?

   *Answer:* So a reader can see exactly how they were made, and a rerun gives the same bytes; the committed copy is what the tests and the README numbers rely on.

5. Why are the data files generated by scripts and then committed?

   *Answer:* So a reader can see exactly how they were made, and a rerun gives the same bytes; the committed copy is what the tests and the README numbers rely on.

## Further reading

- Python `random` module, https://docs.python.org/3/library/random.html (Python 3.13).
