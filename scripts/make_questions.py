"""Write data/questions/dev.jsonl (30) and data/questions/test.jsonl (120, frozen).

Types: `answerable` (a gold page and the fact that answers it), `exact` (the answer hinges on an error code or a
number), `unanswerable` (plausible, but no page answers it; some sit close to a real page on purpose).
Mix of the test set: 70 answerable, 30 unanswerable, 20 exact. The dev set has the same mix in 17, 8 and 5.
"""

from __future__ import annotations

import json
from pathlib import Path

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
    dev_u_idx = [1, 5, 9, 14, 22, 27, 31, 35]
    test_u_idx = [i for i in range(38) if i not in dev_u_idx][:30]
    assert (len(test_x_idx), len(test_u_idx), len(test_a_idx)) == (20, 30, 70)
    rows = {"dev": [], "test": []}

    def add(split: str, kind: str, item) -> None:
        number = len(rows[split]) + 1
        prefix = "d" if split == "dev" else "t"
        if kind == "unanswerable":
            question, near = item
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
        (out / f"{split}.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in items), encoding="utf-8"
        )
        kinds = {k: sum(r["type"] == k for r in items) for k in ("answerable", "exact", "unanswerable")}
        print(split, len(items), kinds)


if __name__ == "__main__":
    main()
