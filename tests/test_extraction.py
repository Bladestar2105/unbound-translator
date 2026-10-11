import importlib.util
import sys
import unittest
from pathlib import Path

from lib.pcs_text import Charmap, decode_pcs

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "001_extract_unbound_text.py"
SPEC = importlib.util.spec_from_file_location("extract_unbound_text", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
EXTRACTOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = EXTRACTOR
SPEC.loader.exec_module(EXTRACTOR)


def decode(text: str):
    encoded = Charmap().encode(text)
    return decode_pcs(encoded, 0, len(encoded))


class AlignedPointerTextTests(unittest.TestCase):
    def test_nature_names_have_both_summary_pointer_tables(self):
        nature_tables = [
            table
            for table in EXTRACTOR.POINTER_TABLES
            if table.category == "nature_names"
        ]
        self.assertEqual(
            [(table.start, table.count) for table in nature_tables],
            [(0x463E60, 25), (0x1FE65F4, 25)],
        )

    def test_easy_chat_tables_cover_only_word_info_text_fields(self):
        tables = [t for t in EXTRACTOR.POINTER_TABLES if t.category == "easy_chat_words"]
        self.assertEqual(len(tables), 18)
        self.assertEqual(sum(t.count for t in tables), 1006)
        self.assertTrue(all(t.stride == 12 for t in tables))
        self.assertEqual((tables[0].start, tables[0].count), (0x3E7FE0, 26))
        self.assertEqual((tables[-1].start, tables[-1].count), (0x3ECB50, 33))

    def test_type_selection_labels_have_explicit_record_owners(self):
        tables = [t for t in EXTRACTOR.POINTER_TABLES
                  if t.table_name == "data.menus.typeSelection.labels"]
        self.assertEqual([(t.start, t.count, t.stride) for t in tables],
                         [(0x456E74, 18, 8)])

    def test_shared_type_menu_labels_keep_their_other_owners(self):
        self.assertEqual(EXTRACTOR.MANUAL_TEXT_POINTER_SOURCES[0x961B50], [0x309C8])
        self.assertEqual(EXTRACTOR.MANUAL_TEXT_POINTER_SOURCES[0x459360], [0x456E14, 0x456E4C])

    def test_berry_prefix_slots_include_the_full_seven_byte_name_field(self):
        tables = [t for t in EXTRACTOR.FIXED_TABLES if t.category == "berry_names"]
        self.assertEqual([(t.start, t.count, t.slot_size, t.stride) for t in tables],
                         [(0x3DF7E8, 43, 7, 28)])

    def test_special_item_and_rotom_choices_have_bounded_pointer_tables(self):
        tables = [t for t in EXTRACTOR.POINTER_TABLES
                  if t.table_name.startswith("data.menus.namedChoices.")]
        self.assertEqual([(t.start, t.count) for t in tables],
                         [(0x2372C0, 8), (0x237400, 16), (0x237584, 11), (0x238D00, 7)])

    def test_link_activity_labels_keep_duplicate_wonder_owners(self):
        tables = [t for t in EXTRACTOR.POINTER_TABLES
                  if t.table_name == "data.link.activityNames"]
        self.assertEqual([(t.start, t.count) for t in tables],
                         [(0x456C78, 12), (0x456CC8, 2)])

    def test_battle_type_move_fragments_have_all_eighteen_owners(self):
        tables = [t for t in EXTRACTOR.POINTER_TABLES
                  if t.table_name == "data.battle.typeMoveFragments"]
        self.assertEqual([(t.start, t.count) for t in tables], [(0x3FEA28, 18)])

    def test_z_move_names_use_the_bounded_paired_pointer_table(self):
        tables = [t for t in EXTRACTOR.POINTER_TABLES
                  if t.table_name == "data.pokemon.zMoves.names"]
        self.assertEqual([(t.start, t.count, t.stride, t.merge_duplicates) for t in tables],
                         [(0x9A230C, 53, 4, True)])

    def test_frontier_speech_tables_only_include_the_three_text_fields(self):
        tables = [t for t in EXTRACTOR.POINTER_TABLES
                  if t.table_name.startswith("data.battleFrontier.")]
        self.assertEqual([(t.start, t.count, t.stride) for t in tables], [
            (0xA6F13C, 11, 52), (0xA6F140, 11, 52), (0xA6F144, 11, 52),
            (0xA6F378, 10, 52), (0xA6F37C, 10, 52), (0xA6F380, 10, 52),
            (0xA6F57C, 154, 20), (0xA6F580, 154, 20), (0xA6F584, 154, 20),
        ])
        self.assertTrue(all(t.skip_nulls for t in tables))

    def test_optional_pointer_table_skips_null_but_keeps_original_index(self):
        rom = bytearray(64)
        rom[4:8] = (0x08000020).to_bytes(4, "little")
        rom[32:36] = Charmap().encode("Yes")
        table = EXTRACTOR.PointerTable("trainer_dialogue", "speech", 0, 2, skip_nulls=True)
        entries, _ = EXTRACTOR.extract_pointer_table(bytes(rom), table, 0, set(), set())
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["address"], "0x20")
        self.assertEqual(entries[0]["table_index"], 1)
        self.assertEqual(entries[0]["pointer_sources"], ["0x4"])

    def test_native_move_and_encounter_labels_have_exact_literal_owners(self):
        expected = {0xA43A50: [0x9D63A0], 0xA43A87: [0x9D63B0],
                    0xA4CB06: [0x9FA42C], 0xA4CC7A: [0x9FA3BC],
                    0xA4CDA2: [0x9FA408]}
        for target, sources in expected.items():
            self.assertEqual(EXTRACTOR.MANUAL_TEXT_POINTER_SOURCES[target], sources)

    def test_additional_native_ui_labels_have_proven_literal_owners(self):
        expected = {0x41CB49: [0x13BA08], 0x419C7B: [0x137DA0],
                    0x419C62: [0x137D80], 0x415D97: [0x12FF9C],
                    0x415A97: [0xC9BC], 0x41EDBD: [0x1423B0],
                    0x416002: [0x104F08], 0x415FED: [0x106470],
                    0x793D11: [0x78A15A, 0x78A178],
                    0xA4CB9D: [0x9FA374], 0xA4CBD0: [0x9FA390],
                    0xA4CB27: [0x9F9F5C], 0xA4CB3B: [0x9F9F98]}
        for target, sources in expected.items():
            self.assertEqual(EXTRACTOR.MANUAL_TEXT_POINTER_SOURCES[target], sources)

    def test_pokedex_cry_control_has_explicit_owner(self):
        table_name, addresses = EXTRACTOR.MANUAL_TEXT_TABLES["menu_pokedex"]
        self.assertEqual(table_name, "data.menus.text.pokedex.controls")
        self.assertEqual(addresses, [0x415FAD])

    def test_opening_difficulty_selector_has_all_unaligned_labels(self):
        table_name, addresses = EXTRACTOR.MANUAL_TEXT_TABLES["menu_game_settings"]

        self.assertEqual(table_name, "data.menus.text.gameSettings")
        self.assertEqual(addresses[-2:], [0x75CE9A, 0x75CEA6])
        self.assertEqual(EXTRACTOR.MANUAL_TEXT_POINTER_SOURCES[0x75CE9A], [0x75CD61])
        self.assertEqual(EXTRACTOR.MANUAL_TEXT_POINTER_SOURCES[0x75CEA6], [0x75CDAF])

    def test_wireless_status_range_covers_unowned_count_and_cancel_slots(self):
        self.assertIn(
            EXTRACTOR.ManualTextRange(
                "menu_link_controls",
                "data.menus.text.linkControls.wirelessStatus",
                0x41E2B4,
                0x41E2F5,
            ),
            EXTRACTOR.POST_POINTER_MANUAL_TEXT_RANGES,
        )

    def test_starter_confirmation_buffers_have_unaligned_type_owners(self):
        self.assertEqual(
            EXTRACTOR.MANUAL_TEXT_POINTER_SOURCES[0x1F97855],
            [0x1E90527],
        )
        self.assertEqual(
            EXTRACTOR.MANUAL_TEXT_POINTER_SOURCES[0x1F97864],
            [0x1E90546],
        )

    def test_gendered_dialogue_fragments_have_explicit_owners(self):
        table_name, addresses = EXTRACTOR.MANUAL_TEXT_TABLES[
            "gendered_dialogue_fragments"
        ]

        self.assertEqual(table_name, "data.dialogue.text.genderedFragments")
        self.assertEqual(len(addresses), 54)
        self.assertIn(0x789224, addresses)  # him
        self.assertIn(0x78922E, addresses)  # her
        self.assertIn(0x793FCB, addresses)  # boy
        self.assertIn(0x793FCF, addresses)  # girl
        self.assertIn(0x1EF97B3, addresses)  # dudette
        self.assertEqual(
            EXTRACTOR.MANUAL_TEXT_POINTER_SOURCES[0x1F8DD33],
            [0x1E709FB, 0x1E9EE30, 0x1EA34E9, 0x1EA5258, 0x1EA57C1, 0x1EAB91D],
        )

    def test_pokedex_unknown_fallback_label_cannot_relocate(self):
        result = decode("Unknown")
        entry = EXTRACTOR.make_entry(
            "scr_1A357CC",
            "pointer_texts",
            0x1A357CC,
            result,
            result.byte_length,
            True,
            [0x88E34, 0x165BC34],
        )

        self.assertTrue(entry["no_relocation"])

    def test_accepts_sentence_and_short_label(self):
        self.assertTrue(
            EXTRACTOR.looks_like_aligned_pointer_text(
                decode("The Wireless Adapter is not connected.")
            )
        )
        self.assertTrue(EXTRACTOR.looks_like_aligned_pointer_text(decode("Bug Gem")))

    def test_rejects_control_only_and_repetitive_data(self):
        self.assertFalse(EXTRACTOR.looks_like_aligned_pointer_text(decode("\\CCF7î")))
        self.assertFalse(
            EXTRACTOR.looks_like_aligned_pointer_text(decode("zzzzizzjiiii"))
        )
        self.assertFalse(EXTRACTOR.looks_like_aligned_pointer_text(decode("AAAA")))

    def test_rejects_mid_string_fragment(self):
        self.assertFalse(
            EXTRACTOR.looks_like_aligned_pointer_text(
                decode("you gave me. It is so intriguing!")
            )
        )

    def test_rejects_trainer_struct_and_adjacent_binary_targets(self):
        self.assertTrue(EXTRACTOR.is_aligned_pointer_target_excluded(0x24019A))
        self.assertTrue(EXTRACTOR.is_aligned_pointer_target_excluded(0x246AE0))
        self.assertFalse(EXTRACTOR.is_aligned_pointer_target_excluded(0x24F1A7))

    def test_rejects_thumb_instructions_that_look_like_text_pointers(self):
        false_sources = {0x3F2B0, 0x8BBBC8, 0x8BBC70}

        self.assertTrue(false_sources <= EXTRACTOR.ALIGNED_POINTER_TEXT_EXCLUDED_SOURCES)
        for source in false_sources:
            self.assertTrue(EXTRACTOR.is_aligned_pointer_source_excluded(source))
        self.assertFalse(EXTRACTOR.is_aligned_pointer_source_excluded(0x3F2B4))

    def test_address_merge_prefers_specific_entry_and_unions_sources(self):
        script = {
            "id": "scr_123456",
            "category": "scripts",
            "address": "0x123456",
            "byte_length": 8,
            "pointer_sources": ["0x100"],
            "is_pointer_based": True,
        }
        table = {
            "id": "tbl_menu_00000_123456",
            "category": "menu",
            "address": "0x123456",
            "byte_length": 8,
            "pointer_sources": ["0x200"],
            "is_pointer_based": True,
            "table_name": "data.menu",
        }
        merged = EXTRACTOR.merge_entries_by_address([script, table])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["category"], "menu")
        self.assertEqual(merged[0]["pointer_sources"], ["0x100", "0x200"])

    def test_pointer_alias_overlapping_structured_slot_is_rejected(self):
        rom = bytearray(128)
        source = 4
        target = 40
        encoded = Charmap().encode("    Dawn Stone")
        rom[source: source + 4] = (0x08000000 + target).to_bytes(4, "little")
        rom[target: target + len(encoded)] = encoded

        entries, stats = EXTRACTOR.scan_pointer_texts(
            bytes(rom),
            known_targets={44},
            known_pointer_sources=set(),
            min_target=1,
            max_length=64,
            start_index=0,
            occupied_ranges=[(44, 57)],
        )

        self.assertEqual(entries, [])
        self.assertEqual(stats["overlap_targets"], 1)

    def test_mid_string_manual_menu_owner_is_excluded(self):
        self.assertIn(0x41736B, EXTRACTOR.MANUAL_TEXT_EXCLUDED_ADDRESSES)

    def test_bounty_descriptions_use_non_scrolling_category(self):
        self.assertEqual(len(EXTRACTOR.MISSION_DESCRIPTION_TEXT_ADDRESSES), 82)
        for address in EXTRACTOR.MISSION_DESCRIPTION_TEXT_ADDRESSES:
            self.assertEqual(
                EXTRACTOR.pointer_text_category(b"", address, []),
                "mission_descriptions",
            )

    def test_mission_registration_title_source(self):
        rom = bytearray(32)
        source = 4
        rom[source - 2: source] = b"\x0F\x00"
        rom[source: source + 4] = (0x08123456).to_bytes(4, "little")
        rom[source + 4] = 0x04
        rom[source + 5: source + 9] = (
                0x08000000 + EXTRACTOR.MISSION_HANDLER_ROM_OFFSET
        ).to_bytes(4, "little")
        self.assertTrue(
            EXTRACTOR.is_mission_registration_title_pointer_source(rom, source)
        )
        rom[source + 4] = 0x05
        self.assertFalse(
            EXTRACTOR.is_mission_registration_title_pointer_source(rom, source)
        )

    def test_mission_registration_title_addresses_are_unique(self):
        rom = bytearray(64)
        source = 4
        title = 40
        rom[source - 2: source] = b"\x0F\x00"
        rom[source: source + 4] = (0x08000000 + title).to_bytes(4, "little")
        rom[source + 4] = 0x04
        rom[source + 5: source + 9] = (
                0x08000000 + EXTRACTOR.MISSION_HANDLER_ROM_OFFSET
        ).to_bytes(4, "little")
        self.assertEqual(
            EXTRACTOR.mission_registration_title_addresses(rom), {title}
        )


    def test_trainer_classes_fixed_table_uses_pointer_name(self):
        table = next(
            t for t in EXTRACTOR.FIXED_TABLES if t.category == "trainer_classes"
        )
        self.assertTrue(table.pointer_name)
        self.assertEqual(table.count, 107)

    def test_trainer_names_fixed_table_configuration(self):
        table = next(
            t for t in EXTRACTOR.FIXED_TABLES if t.category == "trainer_names"
        )
        self.assertEqual(table.start, 0x23EACC)
        self.assertEqual(table.count, 743)
        self.assertEqual(table.slot_size, 12)
        self.assertEqual(table.stride, 40)

    def test_trainerbattle_text_pointer_sources(self):
        rom = bytearray(32)
        # Type 0 (Single battle): 5C 00 <id: 2B> <check: 2B> <intro: 4B> <defeat: 4B>
        rom[0] = 0x5C
        rom[1] = 0x00
        # intro ptr at offset 6
        self.assertTrue(EXTRACTOR.is_trainerbattle_text_pointer_source(rom, 6))
        # defeat ptr at offset 10
        self.assertTrue(EXTRACTOR.is_trainerbattle_text_pointer_source(rom, 10))
        # offset 7 or 14 is not
        self.assertFalse(EXTRACTOR.is_trainerbattle_text_pointer_source(rom, 7))
        self.assertFalse(EXTRACTOR.is_trainerbattle_text_pointer_source(rom, 14))

        # Type 14 (CFRU double battle): 5C 0E <id: 2B> <check: 2B> <intro: 4B> <defeat: 4B> <refusal: 4B>
        rom[0] = 0x5C
        rom[1] = 0x0E
        self.assertTrue(EXTRACTOR.is_trainerbattle_text_pointer_source(rom, 6))
        self.assertTrue(EXTRACTOR.is_trainerbattle_text_pointer_source(rom, 10))
        self.assertTrue(EXTRACTOR.is_trainerbattle_text_pointer_source(rom, 14))

    def test_cfru_battle_messages_manual_table(self):
        table_name, addresses = EXTRACTOR.MANUAL_TEXT_TABLES["battle_messages"]
        self.assertEqual(table_name, "data.battle.text.cfruMessages")
        self.assertEqual(len(addresses), 12)
        self.assertIn(0x905690, addresses)
        self.assertIn(0x905A30, addresses)

    def test_cfru_battle_message_source_detection(self):
        rom = bytearray(0x920000)
        source = 0x905572
        target = 0x905690
        rom[source - 1] = 0x02
        rom[source : source + 4] = (0x08000000 + target).to_bytes(4, "little")
        self.assertTrue(EXTRACTOR.is_cfru_battle_message_source(rom, source, target))
        self.assertTrue(EXTRACTOR.is_pointer_reference_source(rom, source, target))

    def test_intro_setup_and_dexnav_ranges(self):
        ranges = {
            r.table_name: (r.start, r.end, r.category)
            for r in EXTRACTOR.POST_POINTER_MANUAL_TEXT_RANGES
        }
        self.assertIn("data.menus.text.gameSettings.introSetup", ranges)
        self.assertEqual(
            ranges["data.menus.text.gameSettings.introSetup"],
            (0x1F10DC2, 0x1F11016, "menu_game_settings"),
        )
        self.assertIn("data.menus.text.dexnav", ranges)
        self.assertEqual(
            ranges["data.menus.text.dexnav"],
            (0xA43BA5, 0xA43D82, "menu_common"),
        )

    def test_cfru_trainerbattle_source_detection(self):
        source = 0x1E8637A
        rom = bytearray(source + 16)
        target = 0x1F600A3
        # 5C <type> F5 00 00 00 <ptr1>
        rom[source - 6] = 0x5C
        rom[source - 5] = 0x0D
        rom[source - 4] = 0xF5
        rom[source - 3] = 0x00
        rom[source - 2] = 0x00
        rom[source - 1] = 0x00
        rom[source : source + 4] = (0x08000000 + target).to_bytes(4, "little")
        self.assertTrue(
            EXTRACTOR.is_cfru_trainerbattle_source(rom, source, target)
        )
        # Rejects low target
        self.assertFalse(
            EXTRACTOR.is_cfru_trainerbattle_source(rom, source, 0x123)
        )

    def test_gendered_dialogue_fragment_78da8e_pointer_source(self):
        self.assertEqual(
            EXTRACTOR.MANUAL_TEXT_POINTER_SOURCES[0x78DA8E],
            [0x78A3E6],
        )



if __name__ == "__main__":
    unittest.main()


def test_aligned_interior_flash_alias_is_not_an_independent_owner():
    assert EXTRACTOR.is_aligned_pointer_source_excluded(0x52FF70)


def test_post_pointer_manual_range_does_not_duplicate_script_body():
    rom = bytearray(128)
    rom[4:8] = (0x08000000 + 40).to_bytes(4, "little")
    text = Charmap().encode("WARNING! Do not lower the difficulty.")
    rom[40:40 + len(text)] = text
    targets, sources = set(), set()
    scripts, _ = EXTRACTOR.scan_pointer_texts(
        bytes(rom), targets, sources, 1, 64, 0, include_aligned_pointer_text=True,
    )
    assert any(int(e["address"], 16) == 40 for e in scripts)
    entries, _ = EXTRACTOR.extract_manual_tables(
        bytes(rom), 0, targets, sources,
        [EXTRACTOR.ManualTextRange("menu_game_settings", "test", 45, 40 + len(text))],
        include_tables=False, additional_occupied_ranges=[(40, 40 + len(text))],
    )
    assert entries == []


def test_manual_range_cannot_overwrite_a_pointer_owned_suffix():
    rom = bytearray(64)
    text = Charmap().encode(" was too spicy!")
    rom[20:20 + len(text)] = text
    entries, _ = EXTRACTOR.extract_manual_tables(
        bytes(rom), 0, {21}, set(),
        [EXTRACTOR.ManualTextRange("battle_messages", "test", 20, 20 + len(text))],
        include_tables=False,
    )
    assert entries == []
