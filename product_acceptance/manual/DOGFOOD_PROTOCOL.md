# Product V2 human dogfood protocol

Target time: 15–25 minutes.

This is written for a person trying the product, not for someone debugging its
internals. Use a clean test account or a deliberately disposable local home.
Do not enter real passwords, provider tokens, bank details, identity numbers,
or private documents.

## What to record

For each checkpoint, write `PASS`, `FAIL`, or `PARTIAL` and one sentence about
what you actually saw. A successful capture should feel like: “I put it in and
it was safe.” A successful later answer should show what it knows and where it
came from.

## 0–2 minutes — start and first save

1. Start Blackhole and open the Capture view.
2. Enter `Taxi za 10 minut.` and submit it once.
3. Confirm that the app says it was saved immediately. It is okay if deeper
   understanding happens later; it is not okay for the save to wait on a
   provider or disappear.

Checkpoint: `PASS` if the note is clearly saved and remains visible after a
refresh; `FAIL` if the app blocks, loses it, or demands organization first.

## 2–6 minutes — ordinary mixed captures

Submit these as separate captures, without adding labels or categories:

- `Klucze do piwnicy są u mamy.`
- `I left the spare charger in the blue suitcase.`
- `Kuba lubi ten zielony makaron z Lidla.`
- `The kettle is still leaking near the handle.`

If the app supports attachments, also submit the small image fixture by itself
and the small PDF fixture with the note `The PDF from the landlord is the new
lease.`

Checkpoint: `PASS` if every ordinary sentence saves, and the attachment gives a
clear saved or clearly recoverable limitation. `FAIL` if a rapid sequence loses
one note or silently drops the file.

## 6–9 minutes — wait, then check Attention

Wait for processing if the app has a processing indicator. Open Attention.

1. Look for the taxi as a near-term actionable item.
2. Add `My brother's flight is next month.` and `I might buy a bike next year.`
3. Check that those two statements do not become urgent tasks merely because
   they mention future time.

Checkpoint: `PASS` if Attention distinguishes something the user needs to act
on soon from background memory. `FAIL` if every future statement becomes an
urgent interruption or if the taxi is not findable.

## 9–12 minutes — inspect Memory and ask naturally

Open Memory and then ask, in your own words:

- “Where are the basement keys?”
- “What pasta does Kuba like?”
- “What did I save from the landlord?”

Checkpoint: `PASS` if answers are useful, current, and linked to the captured
source. `PARTIAL` if the fact is found but evidence or uncertainty is missing.
`FAIL` if the app confidently invents an answer or cannot retrieve ordinary
details that were just captured.

## 12–15 minutes — change a fact

Capture:

1. `PocketWave costs 9 EUR per month.`
2. `PocketWave from 1 September will cost 11 EUR.`
3. `I think the boiler warranty might expire in December, not sure.`

Ask “What am I paying for PocketWave now?” and “When does the boiler warranty
expire?”

Checkpoint: `PASS` if 11 EUR is current, 9 EUR remains history, and the boiler
answer stays uncertain. `FAIL` if the old price is shown as current or
December is presented as confirmed.

## 15–18 minutes — correction and Undo

1. Capture `The spare house key is in the hall drawer.`
2. Use Undo on that most recent capture.
3. Capture `Correction: the spare house key is in the blue suitcase.`
4. Ask where the spare house key is.

Checkpoint: `PASS` if the hall-drawer statement no longer drives active memory,
the blue-suitcase statement remains, and the original source is not silently
erased. `FAIL` if Undo does nothing, erases the later correction, or leaves two
equally current answers.

## 18–22 minutes — restart and recover

Restart the Host/app using the normal local restart action. Do not delete the
data folder. After it comes back, ask again where the charger is and inspect
Attention.

Checkpoint: `PASS` if state survives restart and no item is duplicated. If a
capture was still waiting, confirm it is still waiting or has a clear retry
state. `FAIL` if the inbox is blank, the app asks you to start over, or an
already processed item appears twice.

## 22–25 minutes — write the verdict

Record:

- the strongest thing you trusted;
- the first moment you hesitated;
- any answer that lacked evidence or showed false urgency;
- whether capture, attachments, Attention, Ask, Memory, Undo, and restart were
  each `PASS`, `FAIL`, or `PARTIAL`;
- the exact visible message for any failure.

Do not turn a pleasant demo into a pass if one of the trust checkpoints failed.
The purpose is to find product-breaking friction before release.
