# Markdown

## What it is

**Markdown** is a way to write formatted text using only plain characters. You type `# Title` and a viewer shows a big heading; you type `**word**` and it shows bold. Because the source is plain text, it is easy to write, easy to compare in version control, and readable even when nothing renders it. The dialect used by GitHub is called GitHub-Flavored Markdown (GFM) and adds tables, task lists and fenced code blocks.

## Why this repository uses it

Everything a human reads in this repository is Markdown: the README, the architecture notes, decision records, the changelog, the prompts and these technology notes. One simple format means one set of tools and nothing to install to read them.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `*.md` | 73 files outside `tech/`; the table below lists them all |

## How it works underneath

A Markdown viewer parses the text line by line. Blank lines end paragraphs. Lines starting with `#`, `-`, `1.`, `>` or a table pipe are recognized as block elements; text inside backticks is turned into code. The result is converted to HTML for display. The rules for every element are in the specification, which is why different viewers show nearly the same page.

Markdown is not a programming language: it has no variables or loops. Anything dynamic (the measured numbers in a report) is produced by a program and written into the file.

## Walkthrough of this repository's use

### The first lines of this repository's `README.md`

```markdown
# ai-cited-answers

A question-answering service over a help center: it indexes the current pages, retrieves chunks with keyword and vector search fused together, writes an answer in which every claim cites a chunk a reader can open, and says so with a fixed refusal when the pages do not hold the answer. Retrieval and answer quality are graded apart, with intervals.

| | |
| --- | --- |
| **Lesson** | `/prep/ai/project-cited-answers`, "Cited answers over a help center" (`data-structure-explainer/src/content/tracks/ai/97-project-cited-answers.md` in the Plainround app) |
| **Planned hours** | 12 |
| **Level** | Intermediate |
| **Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md), decisions in [docs/adr](docs/adr) |

## Prerequisites
```

- `# Title` (one `#` and a space) is a first-level heading, the title of the page. `##` is second level, `###` third, down to `######` for sixth level.
- A blank line separates paragraphs. A line that begins with `- ` or `* ` is a bullet; `1. ` begins a numbered list item.
- `**bold**` and `*italic*` (or `_italic_`) mark emphasis. A word between backticks, `like this`, is code. Three backticks on a line of their own open and close a **code fence**; a language name after the opening fence (```` ```bash ````) lets the viewer color it.
- A link is `[text](address)`. An image is `![alt](address)`.
- A table is rows of cells separated by `|`, with a second row of dashes (`| --- | --- |`) under the header.
- A quote starts with `>`.

### Every Markdown file in this repository

73 files. The second column is each file's own first heading.

| File | First heading |
| --- | --- |
| `ARCHITECTURE.md` | Architecture: ai-cited-answers |
| `CHANGELOG.md` | Changelog |
| `README.md` | ai-cited-answers |
| `data/pages/p-account-2fa.md` | Two-factor sign-in |
| `data/pages/p-account-addresses.md` | Saved addresses |
| `data/pages/p-account-change-email.md` | Change your email address |
| `data/pages/p-account-create.md` | Create an account |
| `data/pages/p-account-delete.md` | Delete your account |
| `data/pages/p-account-locked.md` | Account locked |
| `data/pages/p-account-newsletter.md` | Emails and newsletter |
| `data/pages/p-account-reset-password.md` | Reset your password |
| `data/pages/p-contact-support.md` | Contact support |
| `data/pages/p-error-e1042.md` | Error PR-E1042 |
| `data/pages/p-error-e1043.md` | Error PR-E1043 |
| `data/pages/p-error-e1100.md` | Error PR-E1100 |
| `data/pages/p-error-e2091.md` | Error PR-E2091 |
| `data/pages/p-error-e2092.md` | Error PR-E2092 |
| `data/pages/p-error-e3001.md` | Error PR-E3001 |
| `data/pages/p-error-e3002.md` | Error PR-E3002 |
| `data/pages/p-error-e4004.md` | Error PR-E4004 |
| `data/pages/p-error-e5000.md` | Error PR-E5000 |
| `data/pages/p-error-e5101.md` | Error PR-E5101 |
| `data/pages/p-order-cancel.md` | Cancel an order |
| `data/pages/p-order-change-address.md` | Change the delivery address |
| `data/pages/p-order-combine.md` | Combine two orders |
| `data/pages/p-order-confirmation-email.md` | The order confirmation email |
| `data/pages/p-order-gift-message.md` | Add a gift message |
| `data/pages/p-order-history.md` | Your order history |
| `data/pages/p-order-invoice.md` | Download an invoice |
| `data/pages/p-order-place.md` | How to place an order |
| `data/pages/p-order-preorder.md` | Pre-orders |
| `data/pages/p-order-track.md` | Track an order |
| `data/pages/p-pay-currency.md` | Prices and currency |
| `data/pages/p-pay-declined.md` | My card was declined |
| `data/pages/p-pay-double-charge.md` | I was charged twice |
| `data/pages/p-pay-gift-cards.md` | Gift cards |
| `data/pages/p-pay-installments.md` | Pay in installments |
| `data/pages/p-pay-invoice-company.md` | Paying as a company |
| `data/pages/p-pay-methods.md` | Payment methods |
| `data/pages/p-pay-promo-codes.md` | Promo codes |
| `data/pages/p-pay-refund-method.md` | How refunds are paid |
| `data/pages/p-privacy-cookies.md` | Cookies |
| `data/pages/p-return-condition.md` | Condition of returned items |
| `data/pages/p-return-exchange.md` | Exchanges |
| `data/pages/p-return-fee-old.md` | Return shipping fee (old) |
| `data/pages/p-return-fee.md` | Return shipping fee |
| `data/pages/p-return-how.md` | How to return an item |
| `data/pages/p-return-refund-time.md` | When you get your refund |
| `data/pages/p-return-warranty.md` | Warranty on electronics |
| `data/pages/p-return-window-old.md` | Return window (old) |
| `data/pages/p-return-window.md` | Return window |
| `data/pages/p-ship-costs-old.md` | Shipping costs (old) |
| `data/pages/p-ship-costs.md` | Shipping costs |
| `data/pages/p-ship-countries.md` | Where we ship |
| `data/pages/p-ship-damaged.md` | Damaged parcel |
| `data/pages/p-ship-express.md` | Express shipping |
| `data/pages/p-ship-holiday.md` | Holiday delivery |
| `data/pages/p-ship-international-duties.md` | Duties and import taxes |
| `data/pages/p-ship-lost.md` | Lost parcel |
| `data/pages/p-ship-pickup-point.md` | Pickup lockers |
| `data/pages/p-ship-times.md` | Shipping times |
| `data/pages/p-ship-tracking-delay.md` | Parcel is late |
| `data/pages/p-sizing-guide.md` | Sizing guide |
| `docs/adr/0001-hybrid-retrieval-by-rank-fusion.md` | 0001. Hybrid retrieval by reciprocal rank fusion |
| `docs/adr/0002-retired-pages-stay-out-of-the-index.md` | 0002. Retired pages stay out of the index, and the database enforces it |
| `docs/adr/0003-refusal-threshold-on-cosine-tuned-on-dev.md` | 0003. The refusal threshold is on cosine similarity and is tuned on dev only |
| `docs/adr/0004-citations-are-checked-in-code.md` | 0004. Citations are checked in code against what was retrieved |
| `docs/adr/0005-grade-retrieval-and-answers-apart.md` | 0005. Grade retrieval and answers apart, and split every miss by stage |
| `docs/adr/0006-recorded-models-and-a-hand-checked-judge.md` | 0006. Recorded models, and a judge checked against hand grades |
| `prompts/CHANGELOG.md` | Prompt changelog |
| `prompts/answer/v1.md` | (a prompt file: front matter `version: ...`, then the prompt text) |
| `prompts/answer/v2.md` | (a prompt file: front matter `version: ...`, then the prompt text) |
| `prompts/judge/v1.md` | (a prompt file: front matter `version: ...`, then the prompt text) |

### Special uses here

- `README.md` is shown automatically on the repository's front page by GitHub.
- `CHANGELOG.md` records what changed in each version, newest first.
- `docs/adr/*.md` (where present) are *architecture decision records*: one short file per important decision, saying the context, the decision and its consequences. Their names start with a number so they sort in the order they were made.
- `prompts/**/*.md` are the prompts sent to models. Each starts with a small block between `---` lines, the *front matter* (`version: v1`), which the program reads to learn the prompt's version; the rest of the file is the prompt text. Storing prompts as versioned files keeps them reviewable and lets an evaluation name the exact prompt it used.
- `ARCHITECTURE.md` contains diagrams written as Mermaid text inside ```` ```mermaid ```` fences. GitHub draws them as pictures.
- Pages under `data/` (where present) are the help-center articles that the program searches.
- Reports under `evals/` and `migration/` are written by the program (`.md` files that are generated from measurements); they are committed so you can read the results without running anything.

## Try it yourself

1. The title and first paragraph of the README, as plain text.

```bash
head -5 README.md
```

What you should see (captured from this repository):

```text
# ai-cited-answers

A question-answering service over a help center: it indexes the current pages, retrieves chunks with keyword and vector search fused together, writes an answer in which every claim cites a chunk a reader can open, and says so with a fixed refusal when the pages do not hold the answer. Retrieval and answer quality are graded apart, with intervals.

| | |
```

2. How many second-level sections the README has.

```bash
grep -c '^## ' README.md
```

What you should see (captured from this repository):

```text
10
```

3. Code fences are lines of three backticks: they come in pairs.

```bash
grep -n '^```' README.md | head -4
```

What you should see (captured from this repository):

```text
28:```bash
39:```
45:```bash
53:```
```

4. The Markdown files at the top of the repository.

```bash
ls *.md
```

What you should see (captured from this repository):

```text
ARCHITECTURE.md
CHANGELOG.md
README.md
```

## Mistakes people make

- **Forgetting the blank line before a list or table.** Many viewers then run the list into the paragraph above it.
- **Unbalanced code fences.** A missing closing fence turns the rest of the page into code.
- **Using Markdown for generated numbers by hand.** Numbers in reports come from the program, so they cannot drift from the code.
- **Trailing-space line breaks lost by editors.** `.editorconfig` keeps trailing whitespace in `.md` files.
- **Pipes inside table cells.** A `|` ends the cell; write `\|` to show one.

## Check yourself

1. How do you make a second-level heading?

   *Answer:* Start a line with `## ` (two hash signs and a space).

2. What marks a block of code?

   *Answer:* A fence of three backticks above and below, or four spaces of indent.

3. Why are prompts stored as Markdown files with front matter?

   *Answer:* So each prompt is versioned and reviewable, and the program can read its version.

4. What is an ADR?

   *Answer:* An architecture decision record: a short note of one decision, why it was made and what follows.

5. What is front matter?

   *Answer:* A block between two `---` lines at the top of a file that holds settings such as `version: v1`.

## Further reading

- CommonMark specification, https://spec.commonmark.org/ and the GitHub Flavored Markdown spec, https://github.github.com/gfm/ (the element list above was checked against how this repository's own files are written).
