<!--
    SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>

    SPDX-License-Identifier: Apache-2.0
-->

# UNIcode MNemonic Input Method (unimnim)

unimnim is an input method that uses mnemonics to input as much of Unicode as
possible. It's inspired by [m17n's RFC1345 input
method](https://www.nongnu.org/m17n/manual-en/m17nDBData.html#mim-list) and
[compose
sequences](https://en.wikipedia.org/wiki/Compose_key#Compose_sequences).

See the [data directory](unimnim/data) and its README for information about the
mnemonics it uses.

## FAQ

### How is "unimnim" pronounced?

`uni` and `mn` are pronounced however you'd pronounce them in Unicode and
mnemonic. `im` is entirely up to you. Personally, I pronounce it the same as
[uninym](https://en.wiktionary.org/wiki/uninym#English).

### How stable is this?

The code only generates output files for other input method engines to use, so
software stability hopefully isn't an issue.

The data is α. There might still be significant changes to the mnemonics. At
this point, internal consistency is valued over stability. When adding a new
mnemonic, if it makes sense to first change other mnemonics so they can all use
the same pattern, that change should generally be made.

### Aren't these mnemonics all focused on an English (US) keyboard?

Unfortunately yes. I tried to find data on the most common keyboard layouts and
the keys shared by layouts used by the most people before starting this project,
but I didn't find much.

If you want to use this input method with another layout, please file a bug.

For small changes like changing [the currency
prefix](unimnim/data/common/symbol/currency.toml) from `C$` to `C` followed by a
currency symbol on your keyboard, I think it would be easy enough to add support
for prefix overrides.

For medium changes like adding `læ'` as a mnemonic for `ǽ` in addition to the
current `lae'` mnemonic, I think it would make sense to automatically generate
parts of `[base]`. The input method templates might need modification too. E.g.,
it looks like [m17n would need a different syntax for the
mnemonics](https://savannah.nongnu.org/bugs/?66557).

For large changes like adding mnemonics in a script other than Latin, I'm happy
to think about it more. Maybe it makes sense to have separate data directories?

## Licenses

This repo follows the [reuse](https://reuse.software/) specification. See file
headers for what license(s) each file is available under, and the
[LICENSES](LICENSES) directory for the text of the licenses.

The intent is that all of this repo can be used under the terms of Apache-2.0.
*Additionally*, [data files](unimnim/data) and [templates](unimnim/templates)
can be used under the terms of CC0-1.0, and some templates can also be used
under the terms of whatever license(s) are common for the type of input method
the template is for. If you find a file that doesn't match that intent, please
file a bug.
