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
