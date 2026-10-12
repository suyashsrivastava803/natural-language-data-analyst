# Contributing to Natural Language Data Analyst

Thank you for your interest in contributing to **Natural Language Data Analyst (Fieldnote)**! We welcome contributions, whether they are bug reports, feature suggestions, documentation improvements, or pull requests.

## Code of Conduct

Please be respectful and constructive in all interactions within this project.

## How to Contribute

### Reporting Bugs
1. Check the [Issues](https://github.com/suyashsrivastava803/natural-language-data-analyst/issues) tab to see if your bug has already been reported.
2. If not, open a new issue detailing:
   - Steps to reproduce
   - Expected behavior vs. actual behavior
   - Python version and OS
   - Screenshots or error logs (ensure sensitive data is sanitized)

### Suggesting Enhancements
1. Open an issue describing the proposed feature and why it would be beneficial.
2. Provide example use cases or mockups if applicable.

### Making Code Changes
1. Fork the repository and clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/natural-language-data-analyst.git
   cd natural-language-data-analyst
   ```
2. Create a feature branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```
3. Make your modifications following these guidelines:
   - Keep dependencies minimal (the core server aims to run on Python standard library alone).
   - Maintain the local-first, privacy-by-design model (never expose raw rows or upload them to external endpoints).
   - Ensure clean code and descriptive commit messages.
4. Test your changes locally:
   ```bash
   python server.py
   ```
5. Commit and push your changes to your fork:
   ```bash
   git commit -m "feat: describe your change"
   git push origin feature/my-new-feature
   ```
6. Submit a Pull Request targeting the `main` branch.

---
Thank you for helping make local, natural-language data exploration accessible and secure!
