# Project Instructions

## Notebook / UTF-8 Encoding Rule

When editing notebooks or other JSON/Markdown files that contain Chinese text, preserve UTF-8 end to end.

What went wrong before:

- A Markdown cell was appended to `learning/learn_coding_myself.ipynb` through a shell/Python write path that did not preserve Chinese characters correctly.
- The Chinese text was converted into literal `?` characters inside the notebook JSON.
- Git also showed `?? learning/learn_coding_myself.ipynb`, but that `??` had a different meaning: it only meant the notebook was an untracked Git file.

Rules to avoid repeating this:

- Prefer `apply_patch` for manual edits that include Chinese text.
- Do not write Chinese notebook content through an ad hoc PowerShell here-string or shell pipeline unless UTF-8 preservation has been verified.
- After editing `.ipynb`, `.md`, `.yaml`, or `.json` files containing Chinese text, read the changed content back with UTF-8 and check for accidental literal `?` replacement.
- Treat Git status `?? path` as unrelated to text corruption; it means "untracked file", not notebook content damage.
