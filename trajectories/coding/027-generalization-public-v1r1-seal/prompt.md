# Generalization public V1R1 seal — prompt record

The initiating human message was:

> /goal Referenced pasted text files:
> - pasted text file: C:\\Users\\natan\\.codex\\attachments\\81b8fdf4-1adc-4e16-a922-00507b9bf67a\\pasted-text-1.txt. Read this file before continuing.

The referenced pasted instruction was read before this branch was created. It
authorizes a new `generalization/public-v1r1` branch from
`implementation-freeze-v1`, without mutating `generalization/public-v1`, and
requires copying only the repaired public response contract, query bundle, and
three public scenario files. It also requires a safe `PUBLIC_MANIFEST.json`
with the V1R1 revision, public hashes, schema-repair provenance, and explicit
statements that no provider/model call consumed a generalization event before
the repair and that expected outputs remain absent.

The public branch must not contain the generalization generator, audit,
oracle manifest, expected outputs, defect catalog, or oracle history. A
blindness audit must distinguish the absent generalization oracle from
historical frozen development material such as `benchmark/dev/expected/**`,
which is allowed and must remain unchanged. No baseline execution, advanced
runtime execution, provider/model call, semantic scoring, or expected-output
inspection is authorized.

This file is a faithful summary of the referenced task specification, not a
fabricated transcript; the attachment is the authoritative full text.
