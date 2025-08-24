# Project Roadmap

This document outlines the future direction and goals for the PDF Anonymizer project. Our vision is to make this a powerful, user-friendly, and trustworthy tool for protecting privacy in documents. This roadmap is a living document and will evolve based on community feedback and contributions.

## Near-Term Goals (Next Steps)

These are features and improvements that build directly on the current foundation of the tool.

*   **Improved Redaction Quality:** Enhance the text replacement logic to better match the original font, size, and style, making the anonymized document look more seamless.
*   **Granular PII Control:** Allow users to specify which categories of PII they want to anonymize (e.g., only names and emails, but not locations). This could be a command-line flag like `--pii-types NAME,EMAIL`.
*   **Expanded Model Support:** Add support for more local and cloud-based LLMs to give users more choice in terms of speed, cost, and privacy.
*   **Performance Optimization:** Investigate ways to speed up the anonymization process for very large documents.

## Mid-Term Goals (Future Features)

These are more ambitious features that would significantly expand the capabilities of the tool.

*   **Image Redaction:** Integrate computer vision (CV) models to automatically detect and redact sensitive information within images embedded in PDFs, such as faces or license plates.
*   **Support for More File Formats:** Extend the anonymization logic to handle other common file types, such as Microsoft Word (`.docx`), PowerPoint (`.pptx`), and plain text (`.txt`) files.
*   **Batch Processing:** Implement a feature to anonymize an entire folder of documents at once from the command line.

## Long-Term Vision (Ambitious Ideas)

These are high-level concepts that represent the long-term vision for the project.

*   **Interactive Anonymization Tool:** A more advanced GUI or TUI (Text-based User Interface) that allows users to review all detected PII, and then approve, reject, or edit each change before saving the final document.
*   **Secure, Self-Hosted Cloud Version:** A version of the tool that can be easily deployed to a private cloud or on-premise server, allowing teams and organizations to use it as a shared, secure service.

## Contributing

This project thrives on community contributions! If you are interested in helping to implement any of these features or have ideas of your own, please feel free to open an issue on our GitHub page to start a discussion. We welcome all contributors, from developers to documentation writers.
