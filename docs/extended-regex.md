# Extended Regex Guide {: .doctitle}
An introduction to backrefs.

## Overview
BH uses Python's re regex engine, but it also adds some additional back references to aid in the creation of bracket patterns.  This is done with a custom wrapper called backrefs that was originally written for [RegReplace](https://github.com/facelessuser/RegReplace).

Backrefs was written to add various additional backrefs that are known to some regex engines, but not to Python's re.  Backrefs adds: `\p`, `\P`, `\u`, `\U`, `\l`, `\L`, `\Q` or `\E` (though `\u` and `\U` are replaced with `\c` and `\C`).

### Search Back References

| Back&nbsp;References | Description |
| ---------------------|-------------|
| `\c`                 | Uppercase character class.  ASCII or Unicode when re Unicode flag is used.  Can be used in character classes `[]`. |
| `\l`                 | Lowercase character class.  ASCII or Unicode when re Unicode flag is used.  Can be used in character classes `[]`. |
| `\C`                 | Inverse uppercase character class.  ASCII or Unicode when re Unicode flag is used.  Can be used in character classes `[]`. |
| `\L`                 | Inverse lowercase character class.  ASCII or Unicode when re Unicode flag is used.  Can be used in character classes `[]`. |
| `\Q...\E`            | Quotes (escapes) text for regex.  `\E` signifies the end of the quoting. Will be ignored in character classes `[]`. |
| `\p{UnicodeProperty}`| Unicode property character class. Search string must be a Unicode string. Can be used in character classes `[]`. See [Unicode Properties](#unicode-properties) for more info. |
| `\P{UnicodeProperty}`| Inverse Unicode property character class. Search string must be a Unicode string. Can be used in character classes `[]`. See [Unicode Properties](#unicode-properties) for more info. |

### Replace Back References
None of the replace back references can be used in character classes `[]`.  Since bracket rules are only for search, replace back references will only apply if using the backrefs module in a bh_plugin.

| Back&nbsp;References | Description |
| ---------------------|-------------|
| `\c`                 | Uppercase the next character. |
| `\l`                 | Lowercase the next character. |
| `\C...\E`            | Apply uppercase to all characters until either the end of the string or the end marker `\E` is found. |
| `\L...\E`            | Apply lowercase to all characters until either the end of the string or the end marker `\E` is found. |

!!! tip "Tip"
    Complex configurations of casing should work fine.

    - `\L\cTEST\E` --> `Test`
    - `\c\LTEST\E` --> `Test`
    - `\L\cTEST \cTEST\E` --> `Test Test`

### Unicode Properties
Unicode properties can be used with the format: `\p{UnicodeProperty}`.  The inverse can also be used to specify everything not in a Unicode property: `\P{UnicodeProperty}`.  They are only used in the search patterns. You can use either the verbose format or the terse format, but only one property may specified between the curly braces.  If you want to use multiple properties, you can place them in a character class: `[\p{UnicodeProperty}\p{OtherUnicodeProperty}]`.  See the table below to see all the Unicode properties that can be used.

| Verbose&nbsp;Property&nbsp;Form | Terse&nbsp;Property&nbsp;Form |
|---------------------------------|-------------------------------|
| Other | C |
| Control | Cc |
| Format | Cf |
| Surrogate | Cs |
| Private_Use | Co |
| Unassigned | Cn |
| Letter | L |
| Uppercase_Letter | Lu |
| Lowercase_Letter | Ll |
| Titlecase_Letter | Lt |
| Modifier_Letter | Lm |
| Other_Letter | Lo |
| Mark | M |
| Nonspacing_Mark | Mc |
| Spacing_Mark | Me |
| Enclosing_Mark | Md |
| Number | N |
| Decimal_Number | Nd |
| Letter_Number | Nl |
| Other_Number | No |
| Punctuation | P |
| Connector_Punctuation | Pc |
| Dash_Punctuation | Pd |
| Open_Punctuation | Ps |
| Close_Punctuation | Pe |
| Initial_Punctuation | Pi |
| Final_Punctuation | Pf |
| Other_Punctuation | Po |
| Symbol | S |
| Math_Symbol | Sm |
| Currency_Symbol | Sc |
| Modifier_Symbol | Sk |
| Other_Symbol | So |
| Separator | Z |
| Space_Separator | Zs |
| Line_Separator | Zl |
| Paragraph_Separator | Z |

### Using Backrefs in BracketHighlighter Plugins
You can import backrefs into a `bh_plugin`:

```python
import BracketHighlighter.backrefs as bre
```

Backrefs does provide a wrapper for all of re's normal functions such as `match`, `sub`, etc., but is recommended to pre-compile your search patterns **and** your replace patterns for the best performance; especially if you plan on reusing the same pattern multiple times.  As re does cache a certain amount of the non-compiled calls you will be spared from some of the performance hit, but backrefs does not cache the pre-processing of search and replace patterns.

To use pre-compiled functions, you compile the search pattern with `compile_search`.  If you want to take advantage of replace backrefs, you need to compile the replace pattern as well.  Notice the compiled pattern is fed into the replace pattern; you can feed the replace compiler the string representation of the search pattern as well, but the compiled pattern will be faster and is the recommended way.

```python
pattern = bre.compile_search(r'somepattern', flags)
replace = bre.compile_replace(pattern, r'\1 some replace pattern')
```

Then you can use the complied search pattern and replace

```python
text = pattern.sub(replace, r'sometext')
```

or

```python
m = pattern.match(r'sometext')
if m:
    text = replace(m)  # similar to m.expand(template)
```

To use the non-compiled search/replace functions, you call them just them as you would in re; the names are the same.  Methods like `sub` and `subn` will compile the replace pattern on the fly if given a string.

```python
for m in bre.finditer(r'somepattern', 'some text', bre.UNICODE | bre.DOTALL):
    # do something
```

If you want to replace without compiling, you can use the `expand` method.

```python
m = bre.match(r'sometext')
if m:
    text = bre.expand(m, r'replace pattern')
```
