<!--
    SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>

    SPDX-License-Identifier: Apache-2.0
-->

# UNIcode MNemonic Input Method (unimnim)

This is a very early alpha stage input method for using mnemonics to input as
much of Unicode as possible. It's inspired by [m17n's RFC1345 input
method](https://www.nongnu.org/m17n/manual-en/m17nDBData.html#mim-list) and
[compose
sequences](https://en.wikipedia.org/wiki/Compose_key#Compose_sequences).

## Terminology

*group*: Group of mnemonics with common properties, e.g., the same prefix, and
the same pattern of combining characters used to generate accented results.

*mnemonic*: Key sequence that a user types.

*result*: Text that results from typing a mnemonic.

## Data format

### Explicit strings

Results are specified with strings that are explicit about all code points, to
avoid confusion over [homoglyphs](https://en.wikipedia.org/wiki/Homoglyph) and
to make it easy to see non-printing characters.

Each code point in an explicit string is represented with its number followed by
its name and/or an alias in parentheses. E.g., `U+0068 LATIN SMALL LETTER H` for
a code point with a useful name, `U+0000 (NULL)` for a code point with only an
alias, or `U+01A2 LATIN CAPITAL LETTER OI (LATIN CAPITAL LETTER GHA)` for a code
point with a corrected name.

Code points are joined together by commas and spaces. At the end, there can
optionally be a colon, then a space, then the normally encoded string. For
example, these explicit strings both encode the English word `hi`:

```
U+0068 LATIN SMALL LETTER H, U+0069 LATIN SMALL LETTER I
U+0068 LATIN SMALL LETTER H, U+0069 LATIN SMALL LETTER I: hi
```

In general, the first form should be used for non-printing and combining
characters, and the second form for everything else.
