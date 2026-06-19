# History of Anonymization

Data anonymization has evolved from early statistical disclosure control in censuses to modern privacy-preserving technologies used in AI and data sharing.

## Key Milestones

- **1850s–1970s**: U.S. Census and statisticians (e.g. Fellegi, Dalenius) develop methods to publish aggregate data without revealing individuals.
- **1981**: David Chaum introduces mix networks for anonymous communication (foundational for Tor).
- **1997–1998**: Latanya Sweeney re-identifies Governor Weld’s “anonymized” medical data and, with Pierangela Samarati, formalizes *k*-anonymity.
- **2003**: U.S. HIPAA Privacy Rule codifies Safe Harbor de-identification (removal of 18 identifiers).
- **2006**: Cynthia Dwork et al. introduce Differential Privacy. Machanavala et al. propose *ℓ*-diversity.
- **2007–2008**: Narayanan & Shmatikov demonstrate large-scale de-anonymization on the Netflix Prize dataset. Paul Ohm publishes “Broken Promises of Privacy”.
- **2016–2018**: GDPR (EU) recognizes pseudonymization but treats truly anonymized data as outside its scope. Differential privacy adopted by the U.S. Census and companies like Apple.
- **2020s**: Rise of synthetic data, membership inference attacks, and privacy-preserving machine learning. Growing focus on LLM memorization and safe data sharing for AI.

## Important Concepts & Trade-offs

No anonymization technique offers perfect privacy and full utility at the same time. Traditional methods (masking, *k*-anonymity and variants, differential privacy) work well for structured data but struggle with free text, context, and complex documents.

This is why modern LLM-based approaches (like PDF Anonymizer) that understand semantics and produce reversible placeholder mappings have become attractive for unstructured documents.

For deeper reading see the [Contemporary Techniques](techniques.md) page and academic references linked from the original research papers (Sweeney, Dwork, Narayanan/Shmatikov, etc.).

---

**In this course:**  
[← Previous: Why Anonymize?](why-anonymization.md) | [Course Overview](index.md) | [Next: Where is it Needed?](where-needed.md)
