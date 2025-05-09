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
prefix than a group for a more common script. One of the reasons that the prefix
is its own field in data files is to hopefully make it easier for users to
override prefixes in the future, e.g., to let users who primarily type math
symbols with this input method to override a math symbol group to use a shorter
(or empty) prefix. Please file a bug if that's something you want.

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
point with a corrected name. Code points are joined together by commas and
spaces.

After the code points, there can optionally be flags in square brackets.
Currently the only flag is `combining` which affects how the expected string
(see below) is matched.

At the end, there can optionally be a colon, then a space, then a normally
encoded string to show what the explicit string actually looks like. Normally,
this string at the end must exactly match the code points. With the `combining`
flag, it instead must decompose to a sequence that ends in the code points,
which is useful to show what a combining character looks like without causing
rendering issues.

Examples:

```
U+0068 LATIN SMALL LETTER H, U+0069 LATIN SMALL LETTER I
U+0068 LATIN SMALL LETTER H, U+0069 LATIN SMALL LETTER I: hi
U+0301 COMBINING ACUTE ACCENT [combining]: á
```

In general, the first form should be used for non-printing and combining
characters, and the second form for everything else.

### Data files

Data files are in [TOML](https://toml.io/) format:

```toml
# See "pefix" in Terminology section above.
prefix = "l"

# Base mnemonics, as a map from mnemonic (regular string) to result (explicit
# string). Must be sorted by result, then mnemonic.
[base]
"A" = "U+0041 LATIN CAPITAL LETTER A: A"

# Combinining mnemonics as a map from partial mnemonic (regular string) to a
# combining code point (explicit string). The partial mnemonic is appended to an
# existing mnemonic and the code point is appended to that existing mnemonic's
# result, then normalized. Must be sorted by result, then mnemonic.
[combining.append]
"`" = "U+0300 COMBINING GRAVE ACCENT [combining]: à"

# Combining mnemonics as a map from partial mnemonic to a regex and replacement
# string. If the regex matches the code point name of an existing result and the
# replacement is a valid code point name or alias, the partial mnemonic is
# appended to the existing result's mnemonic and the normalized replacement is
# used as the new result. See https://docs.python.org/3/library/re.html for the
# regex and replacement syntaxes. See
# https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-2/#G27986 for
# why some mnemonics use this instead of combining.append. Must be sorted by
# mnemonic.
[combining.name_regex_replace]
"/" = ['.*', '\g<0> WITH STROKE']
```

## Conventions

To make the mnemonics as easy to remember as possible, the data files generally
follow a set of conventions. When a convention would generally require a comment
for a user looking at a data file to understand, it should have a tag in a
comment, which can be searched in this document in the parentheses after a
convention's title.

Additionally, some groups have their own conventions, see the comments at the
top of the file.

### Also known as (`aka="alternate name"`)

Some characters have mnemonics that are derived from alternate names other than
the name or any of the aliases in Unicode. This can be used for different
reasons.

To fit a pattern of other similar mnemonics:

```toml
"-m" = "U+2014 EM DASH: —"
"-q" = "U+2015 HORIZONTAL BAR: ―"  # aka="quotation dash"
```

To differentiate characters that would otherwise have the same mnemonic:

```toml
"DH" = "U+00D0 LATIN CAPITAL LETTER ETH: Ð"  # aka="edh"
"TH" = "U+00DE LATIN CAPITAL LETTER THORN: Þ"
```

### Based on another mnemonic (`based-on=group`)

When a mnemonic is based on another mnemonic from a different group, use
`based-on=` with the path of the other group relative to this directory, without
the `.toml` extension.

```toml
# latin.toml
prefix = "l"
[base]
"N" = "U+004E LATIN CAPITAL LETTER N: N"
```

```toml
# common/symbol/math.toml
"lN/" = "U+2115 DOUBLE-STRUCK CAPITAL N: ℕ"  # based-on=latin
```

### Base mnemonics with empty results (`empty-for-combining`)

Groups with combining characters can have a base mnemonic with an empty result
to make it possible to type raw combining characters. Both of the following
examples provide mnemonics to type a combining acute character, `l_'` in the
first and `l'` in the second.

```toml
prefix = "l"
[base]
"_" = ""  # empty-for-combining
[combining.append]
"'" = "U+0301 COMBINING ACUTE ACCENT"
```

```toml
prefix = "l"
[base]
"" = ""  # empty-for-combining
[combining.append]
"'" = "U+0301 COMBINING ACUTE ACCENT"
```

### Consistency with other systems (`from=other1,other2`)

When there isn't a good and obvious mnemonic, sometimes one is taken from
another similar system of mnemonics. E.g., an ogonek does not look much like a
semicolon, but I couldn't think of anything better.

```toml
";" = "U+0328 COMBINING OGONEK"  # from=rfc1345,xcompose
```

Other systems for use with this tag:

*   `aliases`: https://www.unicode.org/Public/UNIDATA/NameAliases.txt
*   `rfc1345`: https://datatracker.ietf.org/doc/html/rfc1345
*   `xcompose`: One of the `Compose.pre` files at
    https://gitlab.freedesktop.org/xorg/lib/libx11/-/tree/master/nls

### Geometry (`geometry`)

Mnemonics for characters that are geometrically related to another character can
use one of these suffixes:

| Suffix | Meaning | Example |
| --- | --- | --- |
| `I` | inverted | `"!I" = "U+00A1 INVERTED EXCLAMATION MARK: ¡"` |
| `R` | reversed | |
| `T` | turned | |

### Initial, medial, final, and isolated (`imfi`)

Mnemonics for characters with a specific IMFI position can use one of these
suffixes:

| Suffix | Meaning | Example |
| --- | --- | --- |
| `[` | initial | |
| no suffix | medial | |
| `]` | final | `"s]" = "U+03C2 GREEK SMALL LETTER FINAL SIGMA: ς"` |
| `[]` | isolated | |

Note that the opening `[` is always used for initial and the closing `]` for
final, even if they appear
[mirrored](https://www.unicode.org/reports/tr9/#Mirroring).

### Character length (`length`)

Long characters can use a `+` suffix and shorter characters can use a `-`
suffix.

Unfortunately, this could be somewhat confusing when `-` is used for macron,
which can also mean long in some contexts. So it's a trade-off, and ideas are
welcome.

```toml
"s+" = "U+017F LATIN SMALL LETTER LONG S: ſ"  # length
```

### Suboptimal (`suboptimal`)

Hopefully not actually a convention, but mnemonics that are less than ideal can
be tagged with this to make it clear that suggestions for improvements are
particularly welcome for them, and to make it easier to revisit them later.

### Using a combining mnemonic to remove a diacritic (`uncombine`)

For characters that are similar to other characters with a combining character
removed, the mnemonic can be based on the other character and the combining
character.

```toml
[base]
"i" = "U+0069 LATIN SMALL LETTER I: i"
"i-." = "U+0131 LATIN SMALL LETTER DOTLESS I: ı"  # uncombine
[combining.append]
"." = "U+0307 COMBINING DOT ABOVE"
```
