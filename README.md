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

In general, a mnemonic starts with a prefix for the
[script](https://en.wikipedia.org/wiki/Script_(Unicode)), then a mnemonic for a
letter or symbol, then some optional combining mnemonics for accents. For
example:

<!-- BEGIN: auto-generated examples -->
<table>
  <thead>
    <tr>
      <th rowspan="2" scope="col">Group/Script</th>
      <th colspan="2" scope="col">Mnemonic</th>
      <th rowspan="2" scope="col">Result</th>
    </tr>
    <tr>
      <th scope="col">Prefix</th>
      <th></th>
    </tr>
  </thead>
  <tbody>
        <tr>
            <td rowspan="1">
              <a href="unimnim/data/Arab.toml">
                Arabic
              </a>
            </td>
            <td rowspan="1">
              <kbd>a</kbd>
            </td>
          <td><kbd>b</kbd></td>
          <td dir="auto">ب</td>
        </tr>
        <tr>
            <td rowspan="1">
              <a href="unimnim/data/Bopo.toml">
                Bopomofo
              </a>
            </td>
            <td rowspan="1">
              <kbd>Bo</kbd>
            </td>
          <td><kbd>b</kbd></td>
          <td dir="auto">ㄅ</td>
        </tr>
        <tr>
            <td rowspan="2">
              <a href="unimnim/data/Bugi.toml">
                Buginese
              </a>
            </td>
            <td rowspan="2">
              <kbd>Bu</kbd>
            </td>
          <td><kbd>ka</kbd></td>
          <td dir="auto">ᨀ</td>
        </tr>
        <tr>
          <td><kbd>ki</kbd></td>
          <td dir="auto">ᨀᨗ</td>
        </tr>
        <tr>
            <td rowspan="2">
              <a href="unimnim/data/Buhd.toml">
                Buhid
              </a>
            </td>
            <td rowspan="2">
              <kbd>Bd</kbd>
            </td>
          <td><kbd>ka</kbd></td>
          <td dir="auto">ᝃ</td>
        </tr>
        <tr>
          <td><kbd>ki</kbd></td>
          <td dir="auto">ᝃᝒ</td>
        </tr>
        <tr>
            <td rowspan="2">
              <a href="unimnim/data/Cyrl.toml">
                Cyrillic
              </a>
            </td>
            <td rowspan="2">
              <kbd>c</kbd>
            </td>
          <td><kbd>k</kbd></td>
          <td dir="auto">к</td>
        </tr>
        <tr>
          <td><kbd>k&#39;</kbd></td>
          <td dir="auto">ќ</td>
        </tr>
        <tr>
            <td rowspan="3">
              <a href="unimnim/data/Deva.toml">
                Devanagari
              </a>
            </td>
            <td rowspan="3">
              <kbd>d</kbd>
            </td>
          <td><kbd>k</kbd></td>
          <td dir="auto">क्</td>
        </tr>
        <tr>
          <td><kbd>ka</kbd></td>
          <td dir="auto">क</td>
        </tr>
        <tr>
          <td><kbd>kim</kbd></td>
          <td dir="auto">किं</td>
        </tr>
        <tr>
            <td rowspan="1">
              <a href="unimnim/data/Goth.toml">
                Gothic
              </a>
            </td>
            <td rowspan="1">
              <kbd>GO</kbd>
            </td>
          <td><kbd>a</kbd></td>
          <td dir="auto">𐌰</td>
        </tr>
        <tr>
            <td rowspan="2">
              <a href="unimnim/data/Grek.toml">
                Greek
              </a>
            </td>
            <td rowspan="2">
              <kbd>Gr</kbd>
            </td>
          <td><kbd>a</kbd></td>
          <td dir="auto">α</td>
        </tr>
        <tr>
          <td><kbd>a&#39;</kbd></td>
          <td dir="auto">ά</td>
        </tr>
        <tr>
            <td rowspan="3">
              <a href="unimnim/data/Hano.toml">
                Hanunoo
              </a>
            </td>
            <td rowspan="3">
              <kbd>Ho</kbd>
            </td>
          <td><kbd>k</kbd></td>
          <td dir="auto">ᜣ᜴</td>
        </tr>
        <tr>
          <td><kbd>ka</kbd></td>
          <td dir="auto">ᜣ</td>
        </tr>
        <tr>
          <td><kbd>ki</kbd></td>
          <td dir="auto">ᜣᜲ</td>
        </tr>
        <tr>
            <td rowspan="4">
              <a href="unimnim/data/Hebr.toml">
                Hebrew
              </a>
            </td>
            <td rowspan="4">
              <kbd>He</kbd>
            </td>
          <td><kbd>k</kbd></td>
          <td dir="auto">כ</td>
        </tr>
        <tr>
          <td><kbd>k]</kbd></td>
          <td dir="auto">ך</td>
        </tr>
        <tr>
          <td><kbd>k.</kbd></td>
          <td dir="auto">כּ</td>
        </tr>
        <tr>
          <td><kbd>ke</kbd></td>
          <td dir="auto">כֶ</td>
        </tr>
        <tr>
            <td rowspan="2">
              <a href="unimnim/data/Hrkt.toml">
                Japanese syllabaries
              </a>
            </td>
            <td rowspan="2">
              <kbd>k</kbd>
            </td>
          <td><kbd>hka</kbd></td>
          <td dir="auto">か</td>
        </tr>
        <tr>
          <td><kbd>kka</kbd></td>
          <td dir="auto">カ</td>
        </tr>
        <tr>
            <td rowspan="4">
              <a href="unimnim/data/Latn.toml">
                Latin
              </a>
            </td>
            <td rowspan="4">
              <kbd>l</kbd>
            </td>
          <td><kbd>o</kbd></td>
          <td dir="auto">o</td>
        </tr>
        <tr>
          <td><kbd>o/</kbd></td>
          <td dir="auto">ø</td>
        </tr>
        <tr>
          <td><kbd>o/&#39;</kbd></td>
          <td dir="auto">ǿ</td>
        </tr>
        <tr>
          <td><kbd>oe</kbd></td>
          <td dir="auto">œ</td>
        </tr>
        <tr>
            <td rowspan="1">
              <a href="unimnim/data/Ogam.toml">
                Ogham
              </a>
            </td>
            <td rowspan="1">
              <kbd>OG</kbd>
            </td>
          <td><kbd>b</kbd></td>
          <td dir="auto">ᚁ</td>
        </tr>
        <tr>
            <td rowspan="1">
              <a href="unimnim/data/Runr.toml">
                Runic
              </a>
            </td>
            <td rowspan="1">
              <kbd>RU</kbd>
            </td>
          <td><kbd>b</kbd></td>
          <td dir="auto">ᛒ</td>
        </tr>
        <tr>
            <td rowspan="2">
              <a href="unimnim/data/Tagb.toml">
                Tagbanwa
              </a>
            </td>
            <td rowspan="2">
              <kbd>Tb</kbd>
            </td>
          <td><kbd>ka</kbd></td>
          <td dir="auto">ᝣ</td>
        </tr>
        <tr>
          <td><kbd>ki</kbd></td>
          <td dir="auto">ᝣᝲ</td>
        </tr>
        <tr>
            <td rowspan="2">
              <a href="unimnim/data/Yiii.toml">
                Yi
              </a>
            </td>
            <td rowspan="2">
              <kbd>Yi</kbd>
            </td>
          <td><kbd>it</kbd></td>
          <td dir="auto">ꀀ</td>
        </tr>
        <tr>
          <td><kbd>qotR</kbd></td>
          <td dir="auto">꒐</td>
        </tr>
        <tr>
            <td rowspan="6">
              <a href="unimnim/data/common/math.toml">
                math
              </a>
            </td>
            <td rowspan="6">
              <kbd>ZM</kbd>
            </td>
          <td><kbd>0s</kbd></td>
          <td dir="auto">∅</td>
        </tr>
        <tr>
          <td><kbd>+n</kbd></td>
          <td dir="auto">∑</td>
        </tr>
        <tr>
          <td><kbd>&amp;l</kbd></td>
          <td dir="auto">∧</td>
        </tr>
        <tr>
          <td><kbd>&amp;s</kbd></td>
          <td dir="auto">∩</td>
        </tr>
        <tr>
          <td><kbd>==</kbd></td>
          <td dir="auto">≡</td>
        </tr>
        <tr>
          <td><kbd>==!</kbd></td>
          <td dir="auto">≢</td>
        </tr>
        <tr>
            <td rowspan="6">
              <a href="unimnim/data/common/punctuation.toml">
                punctuation
              </a>
            </td>
            <td rowspan="6">
              <kbd>Z</kbd>
            </td>
          <td><kbd>-h</kbd></td>
          <td dir="auto">‐</td>
        </tr>
        <tr>
          <td><kbd>-m</kbd></td>
          <td dir="auto">—</td>
        </tr>
        <tr>
          <td><kbd>&#39;q</kbd></td>
          <td dir="auto">’</td>
        </tr>
        <tr>
          <td><kbd>&#39;p</kbd></td>
          <td dir="auto">′</td>
        </tr>
        <tr>
          <td><kbd>?!</kbd></td>
          <td dir="auto">‽</td>
        </tr>
        <tr>
          <td><kbd>?!I</kbd></td>
          <td dir="auto">⸘</td>
        </tr>
        <tr>
            <td rowspan="2">
              <a href="unimnim/data/common/symbol/arrow.toml">
                arrows
              </a>
            </td>
            <td rowspan="2">
              <kbd>ZA</kbd>
            </td>
          <td><kbd>-</kbd></td>
          <td dir="auto">↔</td>
        </tr>
        <tr>
          <td><kbd>|</kbd></td>
          <td dir="auto">↕</td>
        </tr>
        <tr>
            <td rowspan="1">
              <a href="unimnim/data/common/symbol/currency.toml">
                currency symbols
              </a>
            </td>
            <td rowspan="1">
              <kbd>Z$</kbd>
            </td>
          <td><kbd>Rs</kbd></td>
          <td dir="auto">₨</td>
        </tr>
        <tr>
            <td rowspan="4">
              <a href="unimnim/data/common/symbol/music.toml">
                music
              </a>
            </td>
            <td rowspan="4">
              <kbd>Zm</kbd>
            </td>
          <td><kbd>n/4</kbd></td>
          <td dir="auto">𝅘𝅥</td>
        </tr>
        <tr>
          <td><kbd>n/4.2</kbd></td>
          <td dir="auto">𝅘𝅥𝅭𝅭</td>
        </tr>
        <tr>
          <td><kbd>n/4&gt;</kbd></td>
          <td dir="auto">𝅘𝅥𝅻</td>
        </tr>
        <tr>
          <td><kbd>nx|</kbd></td>
          <td dir="auto">𝅃𝅥</td>
        </tr>
        <tr>
            <td rowspan="1">
              <a href="unimnim/data/common/symbol/other.toml">
                other symbols
              </a>
            </td>
            <td rowspan="1">
              <kbd>Z</kbd>
            </td>
          <td><kbd>co</kbd></td>
          <td dir="auto">©</td>
        </tr>
        <tr>
            <td rowspan="1">
              <a href="unimnim/data/common/symbol/regional_indicator.toml">
                regional indicators
              </a>
            </td>
            <td rowspan="1">
              <kbd>ZRI</kbd>
            </td>
          <td><kbd>UN</kbd></td>
          <td dir="auto">🇺🇳</td>
        </tr>
        <tr>
            <td rowspan="1">
              <a href="unimnim/data/common/tag_sequence.toml">
                tag sequences
              </a>
            </td>
            <td rowspan="1">
              <kbd>ZTS</kbd>
            </td>
          <td><kbd>Fgbsct</kbd></td>
          <td dir="auto">🏴󠁧󠁢󠁳󠁣󠁴󠁿</td>
        </tr>
  </tbody>
</table>
<!-- END: auto-generated examples -->

See the [data directory](unimnim/data) and its README for more details.

## Usage

The easiest way to try this out is probably by going to the [GitHub Actions
workflows](https://github.com/dseomn/unimnim/actions?query=branch%3Amain+is%3Asuccess),
clicking on the most recent build, and downloading the `python-3.13-output` zip
file at the bottom of the page.

### m17n (Linux, BSDs, possibly macOS)

Extract `unimnim.mim` from the zip file above to `~/.m17n.d/`, and install an
input method that supports the [m17n](https://www.nongnu.org/m17n/) library. I'd
recommend
[ibus-typing-booster](https://mike-fabian.github.io/ibus-typing-booster/), and
I've used [ibus-m17n](https://github.com/ibus/ibus-m17n) in the past. I've never
used [fcitx-m17n](https://github.com/fcitx/fcitx5-m17n), but it looks like it
might work too. I don't have a Mac to test on, but it looks like [there might be
a way to use it on macOS too](https://github.com/fcitx-contrib/fcitx5-macos).
Whichever you use, configure it to use the `t-unimnim` input method.

If you type normally, unimnim stays out of the way. To use it, type
<kbd>Alt</kbd> + <kbd>\\</kbd> followed by a mnemonic. To search mnemonics by
prefix, type <kbd>Alt</kbd> + <kbd>\\</kbd> twice and start typing a mnemonic.
If you want to use different key combinations, see [the documentation of
`minput_event_to_key`](https://www.nongnu.org/m17n/manual-en/group__m17nInputMethodWin.html#ga58715c630a04fd33f12394e9c93f1bad)
and add lines like these to `~/.m17n.d/config.mic`:

```
((input-method t unimnim)
 (command
   (start nil (C-`))
   (search-prefix-start nil (C-` C-`))
   )
 )
```

### Other input method engines

If you'd like support for a different engine, please file a feature request. If
you want to integrate unimnim's mnemonics into other software yourself,
`map.json` in the zip file above is a simple JSON object with all the mnemonics
and their results.

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
prefix](unimnim/data/common/symbol/currency.toml) from `Z$` to `Z` followed by a
currency symbol on your keyboard, I think it would be easy enough to add support
for prefix overrides.

For medium changes like adding `læ'` as a mnemonic for `ǽ` in addition to the
current `lae'` mnemonic, I think it would make sense to automatically generate
parts of `[maps.main]`. The input method templates might need modification too.
E.g., it looks like [m17n would need a different syntax for the
mnemonics](https://savannah.nongnu.org/bugs/?66557).

For large changes like adding mnemonics in a script other than Latin, I'm happy
to think about it more. Maybe it makes sense to have separate data directories?

## Comparison

### Switching keyboard layouts

For many use cases, switching between a few [keyboard
layouts](https://en.wikipedia.org/wiki/Keyboard_layout) is probably better than
using mnemonics. For each language with a good keyboard layout, I think it's
probably much faster for an experienced user of that layout to type directly
than to use unimnim. However, unimnim has advantages in other use cases:

*   There are a lot of mnemonics for characters that (as far as I know) aren't
    common on normal keyboard layouts, like different types of
    [dashes](https://en.wikipedia.org/wiki/Dash), mathematical symbols, music
    symbols, other symbols (©, °, ℅, etc.), and [bidirectional formatting
    characters](https://en.wikipedia.org/wiki/Bidirectional_text#Explicit_formatting).
*   For a language I only type in once every few years, I find it a lot easier
    to use mnemonics than to remember a different keyboard layout and to keep
    track of which layout I'm currently using.

### Compose sequences and dead keys

For typing a limited set of accented characters in one script, [compose
sequences](https://en.wikipedia.org/wiki/Compose_key#Compose_sequences) and/or
[dead keys](https://en.wikipedia.org/wiki/Dead_key) might be easier and/or
faster. When I've looked into it, the support for more obscure characters and
multiple scripts didn't look as good though. Also, compose sequences [don't seem
to support overlapping
mnemonics](https://github.com/mike-fabian/ibus-typing-booster/issues/691#issuecomment-2822689423),
which I think makes it harder to get visual feedback while typing a mnemonic.
For example, after typing `lae`, unimnim should show `æ`, then typing the
additional `'` changes that to `ǽ`.

### RFC 1345

[RFC 1345](https://datatracker.ietf.org/doc/html/rfc1345) defined a somewhat
similar set of mnemonics in 1992, and there's an [m17n input
method](https://www.nongnu.org/m17n/manual-en/m17nDBData.html#mim-list) using
those mnemonics. That served me very well for multiple decades, and I think it
is a pretty good set of mnemonics. unimnim is very much inspired by it.

However, it seems to have been intended for use in standards documents to define
character sets, not for use in an input method to type those characters. That
combined with its age leads to some drawbacks:

*   No support for the many many characters that have been added to Unicode
    since 1992.
*   Since it tries to encode every character in old character sets, it includes
    characters that are [no longer recommended for use in new
    text](https://charlottebuff.com/unicode/charts/deprecated/). (Which is not
    the same as characters for old writing systems. Those can still be
    recommended for new transcripts of old writings or for discussing those
    writing systems.)
*   It has some patterns that it mostly follows in the mnemonics, but there are
    many exceptions to remember.
*   Its mnemonics are limited to a smaller character set than are available on
    many modern keyboards, making some of the mnemonics a bit more awkward.

Additionally, the m17n input method based on RFC 1345 uses `&` as a starter
character to introduce a mnemonic, which makes using it while writing code in C
or C++ somewhat annoying. (That could probably be made configurable though.)

### Search

If you only rarely need to type characters that aren't on your keyboard, some
sort of character search is probably easier than remembering mnemonics. I
personally use [ibus-typing-booster's search and emoji
picker](https://mike-fabian.github.io/ibus-typing-booster/docs/user/#unicode-symbols-and-emoji-predictions)
and [GNOME Character Map](https://wiki.gnome.org/Apps/Gucharmap) in addition to
unimnim.

### CLDR transliterations

[CLDR has
transliterations](https://cldr.unicode.org/index/cldr-spec/transliteration-guidelines)
that have some similarities to the mnemonics that unimnim uses for different
scripts. However, the transliterations seem much better suited to reading text
than to writing it. E.g., they give an example of transliterating Αλφαβητικός to
Alfavi̱tikós, which does not solve the problem of how to type `i̱` and `ó`.

### Others

I don't have any experience with these, but [Input
Pad](https://github.com/fujiwarat/input-pad/wiki) looks interesting, macOS seems
to have a way to [press and hold a key to get
accents](https://support.apple.com/lv-lv/guide/mac-help/mh27474/15.0/mac/15.0),
and it might be possible to use an on-screen keyboard with a different layout
than the physical keyboard.

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
