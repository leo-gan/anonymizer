---
description: Cryptographic pitfalls in pseudonymization — unsalted hash reversal, keyed HMAC, Format-Preserving Encryption (NIST SP 800-38G), authenticated mapping envelopes, and GDPR key separation.
---

# Lecture 6: Pseudonymization and Cryptographic Hygiene

Pseudonymization replaces direct identifiers with stand-in tokens while preserving the ability to link records or restore original values under controlled conditions. Because pseudonymized data remains personal data under GDPR Art. 4(5), its security rests on **cryptographic construction and key custody**.[^gdpr] Weak cryptography turns pseudonymization into trivial obfuscation.

---

## 1. Deterministic vs. Randomized Pseudonyms

- **Randomized stand-ins (`PERSON_1`, random UUIDs):** Fresh counters or random tokens per entity/document leak nothing about values across independent releases, because two releases assign unrelated identifiers unless explicitly seeded from a shared mapping.
- **Deterministic pseudonyms ($f_K(x)$):** Mapping identical inputs to identical tokens enables cross-table joins or longitudinal tracking without decrypting values. However, determinism preserves **equality and frequency**: if one patient appears 40 times in a clinic log, their deterministic pseudonym also appears 40 times, exposing frequency-analysis and linkage attacks.

---

## 2. Why Unsalted Cryptographic Hashes Fail

A recurring engineering mistake is hashing identifiers directly with `SHA-256` or `MD5` without a secret key. Cryptographic hash functions are designed to be **fast and public**, not secret. Whenever an identifier comes from a low-entropy domain, an attacker can precompute every possible digest in seconds to hours:

| Identifier Domain | Approximate Keyspace Size | Unsalted Hash Reversal |
|---|---|---|
| U.S. 5-digit ZIP code | $10^5$ | Milliseconds on a laptop |
| U.S. 9-digit SSN | $10^9$ | Seconds on commodity GPU |
| 10-digit phone number (single country) | $\approx 10^{10}$ | Seconds–minutes on GPU |
| Structured municipal IDs (e.g., NYC taxi medallions) | $\approx 10^4\text{–}10^7$ | Seconds (demonstrated publicly in 2014)[^taxi2014] |

Because `SHA-256` is public, **even a known per-dataset salt only prevents precomputed rainbow tables** — an attacker who sees the salt simply re-hashes the $10^9$ candidates.

### Keyed Pseudonymization (HMAC)
To resist offline dictionary reversal, replace bare hashes with a keyed message authentication code such as $\text{HMAC-SHA256}_K(x)$ using a high-entropy secret key $K$ (at least 128–256 bits) kept separate from the dataset:[^rfc2104]

$$
\text{token}(x) = \text{HMAC-SHA256}_K(\text{domain} \parallel x).
$$

Without $K$, an adversary cannot test candidate inputs $x$. Note that $\text{HMAC}_K(x)$ is still deterministic (it reveals equality/frequency) and irreversible unless a separate lookup map is retained.

---

## 3. Format-Preserving Encryption (FPE)

Legacy databases and payment systems often require a pseudonym to match the original field schema (for example, a 9-digit numeric string or 16-digit card shape). **Format-Preserving Encryption** (NIST SP 800-38G) encrypts a message from a finite domain $\mathcal{X}$ into a ciphertext in the same domain $\mathcal{X}$ using a secret key $K$ and an optional **tweak** $T$:[^nist38g]

- **FF1:** A 10-round Feistel construction over AES. Remains approved in NIST SP 800-38G (Rev. 1 draft tightens minimum domain size to $\ge 10^6$ to resist small-domain attacks).
- **FF3 / FF3-1:** Formerly approved 8-round construction; cryptanalytic slide and small-domain attacks led NIST to **withdraw approval for FF3-1** in favor of FF1.
- **Operational caveats:** FPE without a per-record tweak is deterministic (leaks equality); FPE on small domains weakens security; and when format preservation is unnecessary, standard authenticated encryption (AES-256-GCM) provides simpler, stronger integrity and confidentiality guarantees.

---

## 4. Securing Reversible Mapping Tables

When a workflow relies on typed placeholders (`PERSON_1`) plus an external mapping table (`mapping.json`), **the mapping file is the re-identification key**. Leaking it collapses all privacy protection immediately. Defensive custody requires five controls:

1. **Authenticated encryption (AEAD):** Encrypt the mapping with AES-256-GCM or ChaCha20-Poly1305 so ciphertext tampering is detected before parsing.
2. **Memory-hard key derivation (KDF):** When deriving keys from a passphrase, use **Argon2id** (RFC 9106) with explicit stored parameters rather than fast hashes or weak PBKDF2 counts, and validate KDF bounds before running the KDF to prevent crafted-envelope denial-of-service.[^rfc9106]
3. **Additional Authenticated Data (AAD) binding:** Bind envelope metadata — such as the SHA-256 digest of the source document and schema version — into the AEAD tag. Without AAD, an attacker can transpose ciphertext from document A's mapping onto document B's envelope (where both documents start counting at `PERSON_1`).
4. **Least-privilege I/O and ephemerality:** Write mapping files atomically with owner-only permissions (`0600`) to avoid umask leaks on shared hosts, wipe owned key/plaintext buffers in memory where the runtime permits, and use **ephemeral in-memory mappings** whenever later restoration is not required.
5. **Organizational separation:** Under GDPR Art. 4(5) and EDPB Guidelines 01/2025, pseudonymization requires keeping the "additional information" (the mapping or secret key) **separately** under technical and organizational controls preventing unauthorized re-linking.[^edpb2025]

---

??? note "Exercises"
    1. **Hash reversal:** A company hashes customer U.S. Social Security numbers with `SHA-256("salt-2026" + ssn)` and documents `"salt-2026"` in its public data dictionary. Does the salt protect the SSNs from offline recovery? Why or why not?
    2. **Transposition attack:** Why does encrypting `mapping.json` with AES-256-GCM *without* AAD fail to stop someone from swapping Document A's encrypted mapping file into Document B's folder?

    ??? note "Solutions"
        1. **No.** Because `"salt-2026"` is known and valid SSNs number fewer than $10^9$, an attacker can compute `SHA-256("salt-2026" + ssn)` for all $10^9$ candidates in seconds on a single GPU. Protecting low-entropy identifiers requires a **secret** key (e.g., $\text{HMAC}_K$) kept strictly outside the dataset.
        2. AES-256-GCM without document-binding AAD authenticates only that the ciphertext came from the right passphrase, not *which* document it belongs to. Because independent runs reuse placeholder names (`PERSON_1`, `PERSON_2`), swapping envelopes causes decryption to succeed while injecting Document A's names into Document B.

*Next lecture: [Lecture 7 — Evaluation, Metrics, and Benchmarks](evaluation-and-benchmarks.md).*

## References

[^gdpr]: Regulation (EU) 2016/679 (GDPR), Article 4(5). <https://gdpr-info.eu/art-4-gdpr/>
[^taxi2014]: Pandurangan, V. (2014). *On Taxis and Rainbows: Lessons from NYC's Improperly Anonymized Taxi Logs*. <https://medium.com/@vijayp/of-taxis-and-rainbows-f6bc289679a1>
[^rfc2104]: Krawczyk, H., Bellare, M., & Canetti, R. (1997). *HMAC: Keyed-Hashing for Message Authentication*. IETF RFC 2104. <https://www.rfc-editor.org/rfc/rfc2104>
[^nist38g]: Dworkin, M. (2016; Rev. 1 draft). *Recommendation for Block Cipher Modes of Operation: Methods for Format-Preserving Encryption*. NIST Special Publication 800-38G. <https://csrc.nist.gov/pubs/sp/800/38/g/final>
[^rfc9106]: Biryukov, A., Dinu, D., Khovratovich, D., & Josefsson, S. (2021). *Argon2 Memory-Hard Function for Password Hashing and Proof-of-Work Applications*. IETF RFC 9106. <https://www.rfc-editor.org/rfc/rfc9106>
[^edpb2025]: European Data Protection Board (2025). *Guidelines 01/2025 on Pseudonymisation*. <https://www.edpb.europa.eu/>
