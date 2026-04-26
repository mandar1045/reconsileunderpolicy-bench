# Middleware 2026 Submission Checklist

Target track: `Experimentation and Deployment`

Official call:
- https://middleware-conf.github.io/2026/calls/call-for-research-papers/

Submission system:
- Summer cycle HotCRP: https://middleware2026c2.hotcrp.com/

Important dates:
- Abstract registration: `May 29, 2026`
- Full paper submission: `June 5, 2026`
- Rebuttal window: `August 12-14, 2026`

Files prepared in this repository:
- Anonymized submission source: `paper/reconcileunderpolicy_middleware2026_submission.tex`
- Anonymized submission PDF: `paper/reconcileunderpolicy_middleware2026_submission.pdf`
- Plain abstract text: `paper/middleware2026_abstract.txt`
- Non-anonymized draft: `paper/reconcileunderpolicy_study.tex`

Middleware-specific checks already handled:
- ACM `sigconf` formatting path enabled
- Paper subtitle set to `[Experimentation and Deployment]`
- Author names, affiliations, and email omitted from the submission build
- Double-anonymous ACM build path separated from the named draft build

Checks to do before upload:
- Do not link the public GitHub repository in the submitted PDF
- Upload the anonymized PDF, not the named draft PDF
- Keep artifact links for the post-acceptance or artifact phase unless the
  venue explicitly allows anonymous artifact links
- Confirm the HotCRP title matches the PDF title and track
- Paste the abstract from `paper/middleware2026_abstract.txt`

Build commands:
```sh
cd paper
pdflatex -interaction=nonstopmode -halt-on-error reconcileunderpolicy_middleware2026_submission.tex
bibtex reconcileunderpolicy_middleware2026_submission
pdflatex -interaction=nonstopmode -halt-on-error reconcileunderpolicy_middleware2026_submission.tex
pdflatex -interaction=nonstopmode -halt-on-error reconcileunderpolicy_middleware2026_submission.tex
```
