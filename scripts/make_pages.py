"""Write data/pages/*.md: the 60 pages of the sample help center (57 current, 3 retired).

Each page has a title, an updated date and a status, and one or two sections under `##` headings. Three retired
pages contradict a current one (an old return window, an old shipping fee, an old return fee); ten pages each
explain one error code. Deterministic: running it twice writes the same files.
"""

from __future__ import annotations

from pathlib import Path

CURRENT = "current"
RETIRED = "retired"

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
    print(f"wrote {len(PAGES)} pages ({len(PAGES) - retired} current, {retired} retired) to {out}")


if __name__ == "__main__":
    main()
