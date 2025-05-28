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
both `path/to/unimnim/data/Latn.toml` and
`~/path/to/unimnim-config/Latn.toml`.

*mnemonic*: Key sequence that a user types.

*result*: Text that results from typing a mnemonic.

*prefix*: Prefix for all of a group's mnemonics.

*map*: A map from mnemonic to result.

*combining*: Mnemonics that modify other mnemonics. E.g., for the Latin script's
group, the combining `'` modifies the `la` mnemonic to create the mnemonic `la'`
with the result `á`. Combining mnemonics can stack, e.g., the mnemonic `le^'`
has the result `ế`.

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

After the code points, there can optionally be comma-separated flags in square
brackets.

*   `combining`: Affects how the expected string (see below) is matched.
*   `precomposed`: The string is
    [precomposed](https://en.wikipedia.org/wiki/Precomposed_character). A
    precomposed string without this flag is an error to prevent accidentally
    adding it when a separate base and combining mnemonic would be better, but
    sometimes it does make sense to add a precomposed string directly.

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
U+2260 NOT EQUAL TO [precomposed]: ≠
```

### Data files

Data files are in [TOML](https://toml.io/) format:

```toml
# See "pefix" in Terminology section above.
prefix = "l"

# Map from mnemonic (regular string) to result (explicit string) to show how the
# group works.
[examples]
"A" = "U+0041 LATIN CAPITAL LETTER A: A"
"A`" = "U+00C0 LATIN CAPITAL LETTER A WITH GRAVE: À"

# Maps from mnemonic (regular string) to result (explicit string). Must be
# sorted by result, then mnemonic. This defines a map named "main":
[maps.main]
"A" = "U+0041 LATIN CAPITAL LETTER A: A"

# Combining mnemonics as a map from partial mnemonic (regular string) to a
# combining code point (explicit string). The partial mnemonic is appended to an
# existing mnemonic and the code point is appended to that existing mnemonic's
# result, then normalized. Must be sorted by result, then mnemonic. The original
# map itself is not included in the result of combining by default. However, an
# empty entry like `"" = ""` combines with the original map to produce that same
# map, which is useful to produce both the original map and other things
# combined with it. This defines a combining config named "main":
[combining.main.append]
"" = ""
"`" = "U+0300 COMBINING GRAVE ACCENT [combining]: à"

# Combining mnemonics as a map from partial mnemonic to an array of regex and
# replacement strings. If a regex matches the code point name of an existing
# result and the replacement is a valid code point name or alias, the partial
# mnemonic is appended to the existing result's mnemonic and the normalized
# replacement is used as the new result. See
# https://docs.python.org/3/library/re.html for the regex and replacement
# syntaxes. See
# https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-2/#G27986 for
# why some mnemonics use this instead of `append`. Must be sorted by mnemonic.
# This adds to the combining config named "main":
[combining.main.name_regex_replace]
"/" = [['.*', '\g<0> WITH STROKE']]

# Expressions for how the above definitions are combined. The elements in the
# outer array are unioned together. ["map", name] results in the cartesian
# product of the given map with whatever comes before, or just the given map if
# there's nothing before it. ["combining", name] applies the given combining
# config. ["expression", name] behaves like ["map", name], but references a
# previously defined expression instead of a map. See the next example below for
# now ["name_maps", ...] works. The "main" expression is used as the final map
# of the group.
[expressions]
main = [
  [["map", "main"], ["combining", "main"]],
]
```

```toml
# This example shows how name_maps works. The name_maps tables are maps from
# mnemonic (regular string) to part of a character name (regular string). The
# name_maps expression takes the cartesian product of the given name maps, so
# this example would product the mnemonics lCa -> A, lCb -> B, lsa -> a, and lsb
# -> b. Which is not very useful for Latin, since it's designed for syllabaries.

prefix = "l"

[name_maps.prefixes]
"C" = "LATIN CAPITAL LETTER "
"s" = "LATIN SMALL LETTER "

[name_maps.letters]
"a" = "A"
"b" = "B"

[expressions]
main = [
  [["name_maps", "prefixes", "letters"]],
]
```

## Prefixes

https://en.wikipedia.org/wiki/Script_(Unicode) says "Unicode 16.0 defines 168
separate scripts, including 99 modern scripts and 69 ancient or historic
scripts." Each script can't get its own single-key prefix, but two keys should
be enough for the foreseeable future. To keep mnemonics both as short and as
memorable as possible without causing conflicts between scripts, here are some
general principles for picking a prefix, in descending order of importance:

1.  Ideally the prefix should be based on the script's [ISO
    15924](https://en.wikipedia.org/wiki/ISO_15924) 4-letter code, but other
    options can make sense too if many scripts have similar codes.
1.  One-letter prefixes should be lower case. Two-letter prefixes should start
    with an uppercase letter.
1.  More common scripts should generally get shorter prefixes, and
    ancient/historic scripts should generally get longer prefixes.
    https://en.wikipedia.org/wiki/List_of_writing_systems#List_of_writing_systems_by_adoption
    has a table that can be sorted by how many people actively use a script.
1.  The information density of each mnemonic in a script can be used to decide
    between a one- or two-key prefix. E.g., a small alphabet could get a shorter
    prefix than a large logography. Each single-logograph mnemonic encodes more
    information than each single-letter mnemonic, so the overhead of typing the
    prefix is less significant for the logography.

This is still going to be far from perfect, with lots of extra keystrokes for a
user who regularly types in a small alphabet with a 2-key prefix. One of the
reasons that the prefix is its own field in data files is to hopefully make it
easier to add per-user configuration later. E.g., maybe users could configure
prefix overrides, or maybe an input method could use a different starter key
combination to start a mnemonic with a prefix already filled in. Please file a
feature request if that's something you want.

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

### Amount (`amount`)

A `>` suffix can be used to indicate a greater amount and `<` for a lesser
amount, where "amount" can be interpreted very liberally.

```toml
"s>" = "U+017F LATIN SMALL LETTER LONG S: ſ"  # amount
"e<" = "U+0259 LATIN SMALL LETTER SCHWA: ə"  # aka="reduced vowel" amount
```

It can also be used for upper or lower case:

```toml
"?>" = "U+0241 LATIN CAPITAL LETTER GLOTTAL STOP: Ɂ"  # amount
"?<" = "U+0242 LATIN SMALL LETTER GLOTTAL STOP: ɂ"  # amount
"?" = "U+0294 LATIN LETTER GLOTTAL STOP: ʔ"
```

Or for earlier or later forms of characters:

```toml
"6>" = "U+2185 ROMAN NUMERAL SIX LATE FORM: ↅ"  # amount
"50<" = "U+2186 ROMAN NUMERAL FIFTY EARLY FORM: ↆ"  # amount
```

### Character category (`category`)

Sometimes a character of one category is based on a character of another
category, e.g., U+02BC MODIFIER LETTER APOSTROPHE is a letter based on the
punctuation character U+0027 APOSTROPHE. To convert a mnemonic from one category
to another, these suffixes can be used:

| Suffix | Meaning | Example |
| --- | --- | --- |
| `l` or `L` | letter | `"l" = [['.*', 'MODIFIER LETTER \g<0>']]` |
| `$` | symbol | `"$" = [['HEBREW LETTER (.*)', '\g<1> SYMBOL']]` |

### Mnemonics with empty results (`empty-for-combining`)

Groups with combining characters can have a mnemonic with an empty result to
make it possible to type raw combining characters. Both of the following
examples provide mnemonics to type a combining acute character, `l_'` in the
first and `l'` in the second.

```toml
prefix = "l"
[maps.main]
"_" = ""  # empty-for-combining
[combining.main.append]
"'" = "U+0301 COMBINING ACUTE ACCENT"
```

```toml
prefix = "l"
[maps.main]
"" = ""  # empty-for-combining
[combining.main.append]
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
| `R` | reversed | `"ER" = "U+018E LATIN CAPITAL LETTER REVERSED E: Ǝ"` |
| `T` | turned | `"eT" = "U+01DD LATIN SMALL LETTER TURNED E: ǝ"` |

To include an orientation in a mnemonic, use one of these affixes. Note that
these characters are not
[mirrored](https://www.unicode.org/reports/tr9/#Mirroring), so left, right, top,
and bottom mean the same thing regardless of text direction.

| Affix | Meaning | Example |
| --- | --- | --- |
| `-` | horizontal | `"-" = "U+2194 LEFT RIGHT ARROW: ↔"` |
| `\|` | vertical | `"\|" = "U+2195 UP DOWN ARROW: ↕"` |
| `/` | diagonal, bottom left to top right | |
| `\` | diagonal, top left to bottom right | |

To include a position relative to the center of a character, use one of these
affixes based on a [numeric
keypad](https://en.wikipedia.org/wiki/Numeric_keypad):

| Affix | Meaning | Example |
| --- | --- | --- |
| `1` | bottom left | `"1" = "U+2199 SOUTH WEST ARROW: ↙"` |
| `2` | bottom center | `"2" = "U+2193 DOWNWARDS ARROW: ↓"` |
| `3` | bottom right | `"3" = "U+2198 SOUTH EAST ARROW: ↘"` |
| `4` | center left | `"4" = "U+2190 LEFTWARDS ARROW: ←"` |
| `5` | center | |
| `6` | center right | `"6" = "U+2192 RIGHTWARDS ARROW: →"` |
| `7` | top left | `"7" = "U+2196 NORTH WEST ARROW: ↖"` |
| `8` | top center | `"8" = "U+2191 UPWARDS ARROW: ↑"` |
| `9` | top right | `"9" = "U+2197 NORTH EAST ARROW: ↗"` |

### Logical order (`logical-order`)

Mnemonics can be based on the logical order of text, i.e., the order the text is
written or read in, not the direction it appears on screen. For example, some
punctuation has different forms based on whether it's opening or closing, and
some letters have different forms based on whether they're the initial, medial,
final, or isolated letter in a word.

| Suffix | Meaning | Example |
| --- | --- | --- |
| `[` | opening/initial | |
| no suffix | medial | |
| `]` | closing/final | `"s]" = "U+03C2 GREEK SMALL LETTER FINAL SIGMA: ς"` |
| `[]` | isolated | |

Note that the opening `[` is always used for initial and the closing `]` for
final, even if they appear
[mirrored](https://www.unicode.org/reports/tr9/#Mirroring).

### SI prefix (`si-prefix`)

[SI prefixes](https://en.wikipedia.org/wiki/Metric_prefix) can be used for
number-related mnemonics.

```toml
"5k" = "U+2181 ROMAN NUMERAL FIVE THOUSAND: ↁ"  # si-prefix
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
[maps.main]
"i" = "U+0069 LATIN SMALL LETTER I: i"
"i-." = "U+0131 LATIN SMALL LETTER DOTLESS I: ı"  # uncombine
[combining.main.append]
"." = "U+0307 COMBINING DOT ABOVE"
```
