---
description: An allegory on serialization, schemas, value equality versus object identity, and why copying state creates real-world data leaks.
---

# The Princess Who Became a Scroll

*An allegory on serialization, schemas, and the difference between copying and moving.*

The Bridge of Ash let nothing living cross. Not bird, not breath, not girl — only paper, only things that lay flat and still and told the truth about themselves in ink. The Sentinels who guarded it had one rule, and they had never once broken it: *if it has a pulse, it stays on its own side of the river.*

Princess Liora of Windmere loved Prince Kato of the far bank, and the river had never cared.

So she went to Vesna, the Royal Scribe, who kept a thousand kingdoms' secrets in a single drawer.

"I can send you across," Vesna said. "But not *you*. A telling of you. Every line, in order: your laugh here, the scar on your knuckle there, the exact five words you say when you're afraid. Nothing skipped. Nothing reordered. Skip a line and you arrive missing a piece of yourself. Swap two lines and you might arrive loving the wrong thing first."

"Then don't skip," said Liora. "And don't reorder."

"I never do," said Vesna. "That is the whole of my craft."

For three nights Vesna wrote, flattening Liora onto the scroll field by field — hair, black, curled at the ends; the scar from the day she'd punched Kato's cousin and laughed about it *after*, not before, because order matters; the letter she never sent. When she finished, the scroll was thin enough to fold four times and light enough for one raven to carry. It had no pulse. It had no breath. The Sentinels waved it through without a glance — the same way they waved through tax ledgers and grocery lists — because a *description* of a girl is not a girl, and everyone at that bridge knew it.

That was the whole trick. It worked precisely because it wasn't a trick at all.

On the far bank, Kato's own scribe unrolled the scroll and read it back, in the same order, by the same rules Vesna had used to write it. Line by line, Liora came together again — the laugh, the scar, the fear-words, the memory of the mill where she and Kato first met — until she opened her eyes and threw her arms around him.

It should have ended there, in the ink-smell of new parchment.

Three days later, a second raven came. Not a message. A confession.

Vesna, being a careful scribe, had done what careful scribes always do before sending anything irreplaceable across water she didn't control: she had kept a copy. A checkpoint, in case the raven was lost. She had never burned the first draft.

Which meant the *real* Liora — skin, breakfast, unwritten mornings — had never left Windmere at all. She was still there, asleep at the scribing table, exactly as she'd been the instant the copying finished. When she woke, days later, she remembered no bridge, no Sentinel, no embrace on the far bank. Why would she? That Liora had never lived a single hour of it. Only the scroll had crossed. Only the *reading* had continued the story.

Two Lioras now existed — identical in every particular up to Vesna's last written line, and diverging forever after it.

When Kato rode back across the bridge to demand an explanation, Vesna only shrugged.

"I told you what my craft could do. Nothing skipped, nothing reordered — I kept that promise perfectly. I never once told you I would *move* her. I told you I would describe her. A perfect description is still not the thing it describes. You asked me to send your princess across a river that kills anything with a pulse, and I did exactly that. I never promised there'd only be one of her waiting on the other side."

Kato had no answer for that.

Neither, this tale finds, does anyone who has ever pressed "save" and forgotten what was still sitting in memory.

---

!!! note "Technical note"
    Converting a structured object into an ordered, flat representation is **serialization**; reconstructing an equivalent object by applying the same rules in reverse is **deserialization**. The shared contract defining fields and order is the **schema** — both scribes must agree on it for reconstruction to succeed.

    The privacy implication is operational rather than metaphorical: serialization **copies** state rather than moving it. Two artifacts can be equal in value while existing as independent copies across storage, caches, logs, and memory. Reversible pseudonymization (see [Lecture 9: System Case Study](../101/how-different.md#3-reversible-pseudonymization-and-the-mapping-engine)) relies on managing that boundary explicitly: a stand-in representation crosses the trust boundary, while the mapping required for reconstruction remains controlled locally.
