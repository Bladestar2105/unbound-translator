# Dynamic battle-text widths

The battle renderer does not use the normal overworld placeholder meanings:
`FD01`, displayed as `[player]` by the shared PCS codec, is battle buffer 2.
It can contain a move, nickname, ability, level, or a composed stat modifier.
Counting it as a fixed 54-pixel player name missed overflows.

`lib/battle_buffer_profiles.json` describes the buffer producers for the
original Unbound v2.1.1.1 message addresses. The pinned
[CFRU battle renderer](https://github.com/Skeli789/Complete-Fire-Red-Upgrade/blob/b637a27898b14e25dd24d0f69a3e302f0069deb8/src/battle_strings.c)
and [FireRed buffer expander](https://github.com/pret/pokefirered/blob/master/src/battle_message.c)
explain the context-dependent expansion. These addresses are ROM-specific,
not universal placeholder definitions.

- Move, item, ability, species, type, trainer, and stat widths use the effective
  injected name, including `translated_fixed` when present.
- Nicknames reserve 90 pixels for ten glyphs. Money/experience reserve ten
  digits, levels three digits, and hit/stockpile/perish counts two digits.
- Status/stat-modifier fragments conservatively reserve 135 pixels rather than
  the former 54-pixel estimate; this is not a general bound for arbitrary
  strings or arbitrary compositions of battle-buffer expansion commands.
- Current/last move widths also account for the runtime `Max ` and `G-Max `
  prefixes on move-table indices 820–856 and 857–922 respectively.
- Proven pointer-discovered battle messages use the same pixel wrapper.
  Generic pointer strings are not automatically treated as battle messages.
- The canonical battle-message audit rejects missing profiles for generic
  buffers, including symbolic `[player]` and `[buffer1/2/3]` aliases.

The stricter audit found and reflowed 16 German messages without changing
their semantic placeholders or source text. Scroll/page controls and fixed
slot byte limits remain enforced. Unknown overworld buffer producers and
all possible runtime menu/window combinations are **not** covered by this
battle-specific model; static checks are not an exhaustive playthrough.
