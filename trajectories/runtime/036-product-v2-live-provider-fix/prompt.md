# Runtime smoke instruction

Faithful summary of the authorized live-smoke portion of the human task (the
full instruction is preserved in the coding trajectory prompt): use a fresh
temporary `BLACKHOLE_HOME`, launch `python -m app.host init` and the normal
`python -m app.web_app --host 127.0.0.1 --port <free-port>` entry point, make
only the two specified Polish captures, wait for the managed worker, and issue
only the two specified Ask questions. Do not call `app.product_process
process`, run G01/G02/G03, or tune semantics from wording.
