<!--
    SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>

    SPDX-License-Identifier: CC0-1.0 OR Apache-2.0
-->

# UNIcode MNemonic Input Method (unimnim) data

## Terminology

*group*: Group of mnemonics with common properties, e.g., the same prefix, and
the same pattern of combining characters used to generate accented results.
Currently this maps 1:1 to files in this directory. In the future it might be
possible for users to configure overrides, so a single group could be defined in
both `path/to/unimnim/data/latin.toml` and
`~/path/to/unimnim-config/latin.toml`.

*mnemonic*: Key sequence that a user types.

*result*: Text that results from typing a mnemonic.

*prefix*: Prefix for a group's mnemonics. In general, groups where users are
likely to type more mnemonics should get shorter and easier to type prefixes
than other groups. E.g., while some users might type math symbols frequently,
they probably do not type as many math symbols at a time as a user typing in a
natural language. So a group for math symbols should probably have a longer
prefix than a group for a common script.

*base*: Mnemonics in a group that directly follow the group's prefix. E.g., for
the Latin script's group with a prefix of `l`, the base `a` creates the mnemonic
`la` with the result `a`.

*combining*: Mnemonics in a group that modify the preceding mnemonic. E.g., for
the Latin script's group, the combining `'` modifies the `la` mnemonic to create
the mnemonic `la'` with the result `á`. Combining mnemonics can stack, e.g., the
mnemonic `le^'` has the result `ế`.

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

## Conventions

To make the mnemonics as easy to remember as possible, the data files generally
follow a set of conventions. When a convention would generally require a comment
for a user looking at a data file to understand, it should have a tag in a
comment, which can be searched in this document in the parentheses after a
convention's title.

### Base mnemonics with empty results (`empty-for-combining`)

Groups with combining characters can have a base mnemonic with an empty result
to make it possible to type raw combining characters. Both of the following
examples provide mnemonics to type a combining acute character, `l_'` in the
first and `l'` in the second.

```toml
prefix = "l"
[base]
"_" = ""  # empty-for-combining
[combining]
"'" = "U+0301 COMBINING ACUTE ACCENT"
```

```toml
prefix = "l"
[base]
"" = ""  # empty-for-combining
[combining]
"'" = "U+0301 COMBINING ACUTE ACCENT"
```
