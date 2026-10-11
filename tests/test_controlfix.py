from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.helpers import load_script_module

controlfix = load_script_module("004_controlfix_translations.py", "controlfix_under_test")


def _args(**overrides):
    values = {
        "no_wrap": False,
        "wrap_width": 12,
        "description_wrap_width": 12,
        "move_description_max_pixels": 122,
        "ability_description_max_pixels": 191,
        "ability_description_max_lines": 1,
        "ability_description_max_chars": 34,
        "pokedex_description_wrap_width": 43,
        "pokedex_description_max_lines": 3,
        "pokedex_description_max_total": 124,
        "mission_objective_wrap_width": 35,
        "mission_objective_max_lines": 2,
        "mission_objective_max_total": 65,
        "mission_description_max_pixels": 172,
        "mission_description_max_lines": 3,
        "item_description_wrap_width": 14,
        "item_description_max_lines": 3,
        "battle_message_max_pixels": 208,
        "setting_name_max_width": 93,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_repair_control_sequences_restores_required_prefix_tokens():
    original = "[black]Hello [player]!"
    translated = "Ciao [player]!"

    fixed, changed = controlfix.repair_control_sequences(translated, original)

    assert changed
    assert fixed == "[black]Ciao [player]!"
    assert controlfix.controls_match(fixed, original)


def test_normalize_and_repair_common_control_damage():
    assert controlfix.normalize_braced_controls("{[black]}Ciao {\\btn01}") == "[black]Ciao \\btn01"
    assert controlfix.repair_split_controls("\\nqoCiao\\pqc") == "\\qoCiao\\qc"
    assert controlfix.fix_apostrophes("l'amico d{B4}oro") == "l{B4}amico d{B4}oro"


def test_paragraph_before_indonesian_k_is_not_pokemon_glyph():
    fixed = controlfix.normalize_actual_layout_breaks("Pertama.\n\nkamu lanjut.")

    assert fixed == "Pertama.\\pkamu lanjut."
    assert controlfix.Charmap(target_lang="id").encode(fixed) == controlfix.Charmap(
        target_lang="id"
    ).encode("Pertama.\n\nkamu lanjut.")


def test_paragraph_before_italian_n_preserves_first_letter():
    fixed = controlfix.normalize_actual_layout_breaks(
        "ottenere il pacco\n\nnecessario per la missione"
    )

    assert fixed == "ottenere il pacco\\pnecessario per la missione"
    assert controlfix.Charmap(target_lang="it").encode(fixed) == controlfix.Charmap(
        target_lang="it"
    ).encode("ottenere il pacco\n\nnecessario per la missione")


@pytest.mark.parametrize(
    "text,expected_clean",
    [
        ("\\pnon possiamo farlo", "non possiamo farlo"),
        ("\\pnord della citta", "nord della citta"),
        ("\\pnecessario per vincere", "necessario per vincere"),
        ("\\pNon possiamo farlo", "Non possiamo farlo"),
        ("\\pnebbia fitta", "nebbia fitta"),
        ("\\pnuovo gioco", "nuovo gioco"),
        ("\\pnome del giocatore", "nome del giocatore"),
        ("\\pnotte fonda", "notte fonda"),
        ("\\pniente da fare", "niente da fare"),
        ("\\pnessuno puo passare", "nessuno puo passare"),
        ("\\pkamu lanjut", "kamu lanjut"),
    ],
)
def test_remove_layout_tokens_preserves_words_starting_with_n_and_k(text, expected_clean):
    clean, layout = controlfix.remove_layout_tokens(text)
    assert clean == expected_clean
    assert layout == ["\\p"]


def test_remove_excess_dynamic_name_keeps_possessive_position():
    fixed, changed = controlfix.remove_excess_name_tokens(
        "[player]PC di [player]", "[player]’s PC"
    )
    rival_fixed, rival_changed = controlfix.remove_excess_name_tokens(
        "[rival]Casa di [rival]", "[rival]’s house"
    )

    assert changed and rival_changed
    assert fixed == "PC di [player]"
    assert rival_fixed == "Casa di [rival]"


def test_ready_trainer_change_prompt_uses_official_italian_wording():
    fixture_path = Path(__file__).parent / "fixtures" / "trainer_change_prompt.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    ready_path = Path(__file__).resolve().parents[1] / "ready-translations" / "it.json"
    ready_entries = json.loads(ready_path.read_text(encoding="utf-8"))["entries"]
    ready_entry = next(entry for entry in ready_entries if entry["id"] == fixture["id"])

    assert ready_entry["translated"] == fixture["translated"]
    assert "\\p" in ready_entry["translated"]
    assert controlfix.controls_match(fixture["translated"], fixture["original"])


def test_ready_save_overwrite_prompts_use_official_italian_layout():
    fixture_path = Path(__file__).parent / "fixtures" / "save_overwrite_prompt.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    ready_path = Path(__file__).resolve().parents[1] / "ready-translations" / "it.json"
    ready_entries = json.loads(ready_path.read_text(encoding="utf-8"))["entries"]
    ready_by_id = {entry["id"]: entry for entry in ready_entries}

    for entry_id in fixture["ids"]:
        assert ready_by_id[entry_id]["translated"] == fixture["translated"]


def test_ready_battle_send_out_messages_fit_fragile_original_slots():
    fixture_path = Path(__file__).parent / "fixtures" / "battle_send_out_messages.json"
    fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))
    ready_path = Path(__file__).resolve().parents[1] / "ready-translations" / "it.json"
    ready_entries = json.loads(ready_path.read_text(encoding="utf-8"))["entries"]
    ready_by_id = {entry["id"]: entry for entry in ready_entries}
    charmap = controlfix.Charmap()

    for fixture in fixtures:
        entry = ready_by_id[fixture["id"]]
        assert entry["translated"] == fixture["translated"]
        assert len(charmap.encode(entry["translated"])) <= entry["byte_length"]
        assert controlfix.controls_match(entry["translated"], entry["original"])


def test_ready_choice_scarf_uses_official_name_and_fits_slots():
    fixture_path = Path(__file__).parent / "fixtures" / "choice_scarf_item.json"
    fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))
    ready_path = Path(__file__).resolve().parents[1] / "ready-translations" / "it.json"
    ready_entries = json.loads(ready_path.read_text(encoding="utf-8"))["entries"]
    ready_by_id = {entry["id"]: entry for entry in ready_entries}
    charmap = controlfix.Charmap()

    for fixture in fixtures:
        entry = ready_by_id[fixture["id"]]
        assert entry["translated"] == fixture["translated"]
        assert len(charmap.encode(entry["translated"])) <= entry["byte_length"]
        assert controlfix.controls_match(entry["translated"], entry["original"])


def test_pokedex_category_keeps_only_category_text():
    assert controlfix.normalize_pokedex_category("Pokémon Ratto") == ("Ratto", True)
    assert controlfix.normalize_pokedex_category("Ratto Pokémon") == ("Ratto", True)
    assert controlfix.normalize_pokedex_category("Ratto") == ("Ratto", False)


def test_short_battle_fragments_preserve_assembly_spaces():
    sharp, sharp_changed = controlfix.restore_short_battle_fragment_spacing(
        "di molto", "sharply ", {"category": "battle_messages"}
    )
    little, little_changed = controlfix.restore_short_battle_fragment_spacing(
        "poco!", " little!", {"category": "battle_messages"}
    )

    assert sharp_changed and little_changed
    assert sharp + "aumenta!" == "di molto aumenta!"
    assert little == " poco!"

    modifier, modifier_changed = controlfix.restore_short_battle_fragment_spacing(
        "di molto ",
        "sharply ",
        {"id": "tbl_battle_messages_00224_3FCB41", "category": "battle_messages"},
    )
    assert modifier_changed
    assert "aumenta" + modifier + "!" == "aumenta di molto!"


def test_wrap_translation_uses_dialogue_layout_for_scripts():
    wrapped, changed, long_words, skipped = controlfix.wrap_translation(
        "uno due tre quattro cinque sei",
        {"category": "scripts"},
        "Hello",
        _args(wrap_width=12),
        {"scripts"},
    )

    assert changed
    assert not skipped
    assert long_words == 0
    assert wrapped == "uno due tre\nquattro\\lcinque sei"


def test_battle_messages_wrap_dynamic_controls_by_pixel_width():
    text = r"\\1C Das Team von \\1D \\2E Das Team von \\2F"
    wrapped, changed, _long_words, skipped = controlfix.wrap_translation(
        text,
        {"category": "battle_messages"},
        "Battle message",
        _args(wrap_width=35, battle_message_max_pixels=208),
        {"battle_messages"},
    )

    assert changed
    assert not skipped
    assert max(map(controlfix.text_pixel_width, wrapped.splitlines())) <= 208
    for token in (r"\\1C", r"\\1D", r"\\2E", r"\\2F"):
        assert wrapped.count(token) == 1


def test_wrap_translation_uses_plain_line_breaks_for_plain_scripts_and_descriptions():
    plain_wrapped, changed, _long_words, skipped = controlfix.wrap_translation(
        "uno due tre quattro cinque sei sette",
        {"category": "plain_scripts"},
        "Line one\nLine two",
        _args(wrap_width=12),
        {"plain_scripts"},
    )

    assert changed
    assert not skipped
    assert "\\l" not in plain_wrapped
    assert plain_wrapped.splitlines() == ["uno due tre", "quattro", "", "cinque sei", "sette"]

    item_wrapped, changed, _long_words, skipped = controlfix.wrap_translation(
        "cura ogni problema di stato del pokemon",
        {"category": "item_descriptions"},
        "Item description",
        _args(item_description_wrap_width=14, item_description_max_lines=0),
        {"item_descriptions"},
    )

    assert changed
    assert not skipped
    assert "\\l" not in item_wrapped
    assert item_wrapped == "cura ogni\nproblema di\nstato del\npokemon"


def test_ready_german_lab_dialogue_is_stored_with_dialogue_line_break():
    ready_path = Path(__file__).resolve().parents[1] / "ready-translations" / "de.json"
    entries = json.loads(ready_path.read_text(encoding="utf-8"))["entries"]
    entry = next(item for item in entries if item["id"] == "scr_1F2CBB6")

    assert entry["translated"] == "Was zum\\.? Wie bist du hier\nreingekommen?"


def test_wrap_only_preserves_runtime_tokens_in_mission_objectives():
    wrapped, _changed, _long_words, skipped = controlfix.wrap_translation(
        "Verbünde dich ein letztes Mal mit [rival], um Marlon zu besiegen!",
        {"category": "mission_objectives"},
        "Team up with [rival] one last time to defeat Marlon!",
        _args(mission_objective_wrap_width=35, mission_objective_max_lines=2),
        {"mission_objectives"},
    )

    assert not skipped
    assert "[rival]" in wrapped


def test_move_descriptions_use_french_observed_pixel_width():
    narrow_text = "iiii iiiii iiiii iiiii iiiii"
    wrapped, changed, _long_words, skipped = controlfix.wrap_translation(
        narrow_text,
        {"category": "move_descriptions"},
        "Move description",
        _args(move_description_max_pixels=122),
        {"move_descriptions"},
    )

    assert not changed
    assert not skipped
    assert wrapped == narrow_text
    assert controlfix.visible_width(wrapped) > 24

    wrapped, changed, _long_words, skipped = controlfix.wrap_translation(
        "MMMMM MMMMM MMMMM MMMMM",
        {"category": "move_descriptions"},
        "Move description",
        _args(move_description_max_pixels=60),
        {"move_descriptions"},
    )
    assert changed
    assert not skipped
    assert max(map(controlfix.text_pixel_width, wrapped.splitlines())) <= 60


def test_ability_descriptions_use_original_rom_one_line_pixel_budget():
    wrapped, changed, _long_words, skipped = controlfix.wrap_translation(
        "Potenzia le mosse Folletto.",
        {"category": "ability_descriptions"},
        "Ability description",
        _args(),
        {"ability_descriptions"},
    )

    assert not changed
    assert not skipped
    assert len(wrapped.splitlines()) == 1
    assert max(map(controlfix.text_pixel_width, wrapped.splitlines())) <= 191

    with pytest.raises(ValueError, match="needs 2 rows"):
        controlfix.wrap_translation(
            "Le mosse Normali diventano di tipo Ghiaccio.",
            {"id": "ability-test", "category": "ability_descriptions"},
            "Ability description",
            _args(),
            {"ability_descriptions"},
        )

    full, changed, _long_words, skipped = controlfix.wrap_translation(
        "Le mosse Normali diventano di tipo Ghiaccio.",
        {
            "id": "ability-test",
            "category": "ability_descriptions",
            "translated_fixed": "Mosse Normali diventano Ghiaccio.",
        },
        "Ability description",
        _args(),
        {"ability_descriptions"},
    )
    assert not changed
    assert not skipped
    assert full == "Le mosse Normali diventano di tipo Ghiaccio."


def test_pokedex_description_uses_french_observed_three_line_budget():
    text = (
        "La composizione delle sue cellule è simile a quella delle molecole "
        "d{B4}acqua. Di conseguenza, quando si scioglie nell{B4}acqua, non può essere visto."
    )
    wrapped, changed, _long_words, skipped = controlfix.wrap_translation(
        text,
        {"category": "pokedex_descriptions", "table_index": 133},
        "Source description",
        _args(),
        {"pokedex_descriptions"},
    )

    lines = wrapped.splitlines()
    assert changed
    assert not skipped
    assert len(lines) <= 3
    assert max(map(controlfix.visible_width, lines)) <= 43
    assert controlfix.visible_width(wrapped.replace("\n", " ")) <= 124
    assert "..." in wrapped


def test_ready_constrained_text_is_meaningfully_condensed_without_added_ellipsis():
    fixture_path = Path(__file__).parent / "fixtures" / "condensed_layout_cases.json"
    fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))
    ready_path = Path(__file__).resolve().parents[1] / "ready-translations" / "it.json"
    entries = json.loads(ready_path.read_text(encoding="utf-8"))["entries"]
    by_id = {entry["id"]: entry for entry in entries}

    for fixture in fixtures:
        assert by_id[fixture["id"]]["translated"] == fixture["translated"]
        assert "..." not in fixture["translated"]
        assert "\u2026" not in fixture["translated"]

    budgets = {
        "pokedex_descriptions": (43, 3, 124),
        "mission_objectives": (35, 2, 65),
    }
    checked = {category: 0 for category in budgets}
    for entry in entries:
        category = entry.get("category")
        if category not in budgets:
            continue

        width, max_lines, max_total = budgets[category]
        translated = entry.get("translated", "")
        lines = translated.splitlines()
        checked[category] += 1

        if "..." not in entry.get("original", ""):
            assert "..." not in translated, entry["id"]
        if "\u2026" not in entry.get("original", ""):
            assert "\u2026" not in translated, entry["id"]
        assert len(lines) <= max_lines, entry["id"]
        assert max(map(controlfix.visible_width, lines), default=0) <= width, entry["id"]
        assert controlfix.visible_width(" ".join(lines)) <= max_total, entry["id"]

    assert checked == {
        "pokedex_descriptions": 993,
        "mission_objectives": 57,
    }


def test_mission_objective_uses_french_observed_shared_budget():
    wrapped, changed, _long_words, skipped = controlfix.wrap_translation(
        "Guardati intorno nel Magazzino Vivill e trova un modo per entrare nel Centro di Comando!",
        {"category": "mission_objectives", "table_index": 37},
        "Look around Vivill Warehouse and find a way into the Command Centre!",
        _args(),
        {"mission_objectives"},
    )

    lines = wrapped.splitlines()
    assert changed
    assert not skipped
    assert len(lines) <= 2
    assert max(map(controlfix.visible_width, lines)) <= 35
    assert controlfix.visible_width(" ".join(lines)) <= 65


def test_mission_log_description_uses_up_to_three_pixel_bounded_lines():
    wrapped, changed, _long_words, skipped = controlfix.wrap_translation(
        "Scopri i segreti dietro le misteriose tavolette di pietra!",
        {"category": "mission_descriptions", "table_index": 1},
        "Uncover the secrets behind the mysterious stone tablets!",
        _args(),
        {"mission_descriptions"},
    )

    lines = wrapped.splitlines()
    assert changed
    assert not skipped
    assert len(lines) <= 3
    assert max(map(controlfix.text_pixel_width, lines)) <= 172
    assert "..." not in wrapped


def test_mission_log_description_never_emits_scroll_or_page_controls():
    wrapped, _changed, _long_words, skipped = controlfix.wrap_translation(
        "Aiuta uno scienziato a conoscere i Pokémon che vivono nella Palude Cootes! Usa il DexNav per aiutarlo a catturarli tutti.",
        {"category": "mission_descriptions", "table_index": 4},
        "Help a scientist learn about the Pokémon living in Cootes Bog!",
        _args(),
        {"mission_descriptions"},
    )

    assert not skipped
    assert len(wrapped.splitlines()) <= 3
    assert "\\l" not in wrapped
    assert "\\p" not in wrapped
    assert max(map(controlfix.text_pixel_width, wrapped.splitlines())) <= 172


def test_menu_and_battle_layout_repairs():
    menu_text, menu_changed = controlfix.restore_compact_menu_line_breaks(
        "Sì No",
        "Yes\nNo",
        {"category": "menu_common"},
    )
    assert menu_changed
    assert menu_text == "Sì\nNo"

    battle_text, battle_changed = controlfix.restore_battle_prompt_layout(
        "Cosa farà \\\\12?",
        "What will \\\\12 do?",
        {"id": "tbl_battle_messages_00412_3FE6D5"},
    )
    assert battle_changed
    assert battle_text == "Cosa farà\n\\\\12?"

    battle_text, battle_changed = controlfix.restore_battle_prompt_layout(
        "Was soll \\\\12 tun?",
        "What will \\\\12 do?",
        {"id": "tbl_battle_messages_00412_3FE6D5"},
    )
    assert battle_changed
    assert battle_text == "Was soll\n\\\\12 tun?"

    repaired, changed = controlfix.restore_battle_prompt_layout(
        "Cosa deve fare\\n\n\\\\12?",
        "What will\n\\\\12 do?",
        {"id": "tbl_battle_messages_00412_3FE6D5"},
    )
    assert changed
    assert repaired == "Cosa deve fare\n\\\\12?"


def test_mission_and_start_menu_labels_are_trimmed_to_width():
    mission_text, mission_changed = controlfix.trim_mission_name("Missione lunghissima", 8)
    start_text, start_changed = controlfix.compact_start_menu_label(
        "Impostazioni lunghissime",
        {"category": "start_menu_labels"},
        "Settings",
        13,
    )

    assert mission_changed
    assert mission_text == "Missione"
    assert start_changed
    assert start_text == "Impostazioni"


def test_setting_names_use_screen_pixel_width_not_character_count():
    text, changed = controlfix.trim_to_pixel_width("Opzioni generali", 93)
    assert not changed
    assert text == "Opzioni generali"

    text, changed = controlfix.trim_to_pixel_width("Opzioni generali estese", 93)
    assert changed
    assert text == "Opzioni generali"


def test_battle_wrapper_reserves_the_actual_move_name_width():
    widths = {0x14: controlfix.text_pixel_width("Apokalyptische Steinpresse")}
    text = r"Die Attacke \\14 trifft!"
    wrapped, changed, long_words = controlfix.wrap_battle_message(text, 208, widths)
    assert changed
    assert long_words == 0
    expanded = wrapped.replace(r"\\14", "Apokalyptische Steinpresse")
    assert max(map(controlfix.text_pixel_width, expanded.splitlines())) <= 208
    assert controlfix.controls_match(wrapped, text)


def test_battle_runtime_widths_use_effective_names_and_both_move_tokens():
    widths = controlfix.battle_runtime_widths([
        {"category": "move_names", "translated": "Langer Name", "translated_fixed": "Kurz"},
        {"category": "move_names", "translated": "Apokalyptische Steinpresse"},
        {"category": "trainer_classes", "translated": "Kampfkoryphäe"},
    ])
    assert widths[0x14] == widths[0x15] == controlfix.text_pixel_width("Apokalyptische Steinpresse")
    assert widths[0x1C] == controlfix.text_pixel_width("Kampfkoryphäe")


def test_battle_buffers_are_context_specific_not_player_names():
    entries = [{"category": "move_names", "translated": "Apokalyptische Steinpresse"}]
    profiles = controlfix.battle_buffer_widths(entries)
    assert profiles[0x3FB2A4][1] == controlfix.text_pixel_width(entries[0]["translated"])
    assert profiles[0x3FB2A4][0] == 90
    assert profiles[0x3FB545][0] == 12
    assert profiles[0x3FB28E][1] == 18
    text = r"\\00 hat [player] erlernt!"
    wrapped, changed, long_words = controlfix.wrap_battle_message(text, 208, profiles[0x3FB2A4])
    assert changed and not long_words
    expanded = wrapped.replace(r"\\00", "MMMMMMMMMM").replace("[player]", entries[0]["translated"])
    import re
    assert max(controlfix.text_pixel_width(line) for line in re.split(r"\\[nlp]|\n", expanded)) <= 208


def test_battle_max_move_width_includes_runtime_prefix():
    entries = [{"category": "move_names", "table_index": 0x359, "translated": "Brennender Zorn"}]
    widths = controlfix.battle_runtime_widths(entries)
    assert widths[0x14] == widths[0x15] == controlfix.text_pixel_width("G-Max Brennender Zorn")


def test_proven_pointer_battle_buffers_use_same_wrapper():
    text = r"wurde von \\00 geheilt!"
    entry = {"category": "pointer_texts", "address": "0xA37A75"}
    args = _args(battle_buffer_widths={0xA37A75: {0: 135}}, battle_runtime_widths={})
    wrapped, changed, long_words, skipped = controlfix.wrap_translation(
        text, entry, text, args, {"battle_messages"}
    )
    assert changed and not long_words and not skipped
    assert wrapped == r"wurde von \\00" + "\n" + "geheilt!"
    assert controlfix.wrap_translation(text, entry, text, args, {"scripts"}) == (text, False, 0, False)
    entry["category"] = "battle_messages"
    assert controlfix.wrap_translation(text, entry, text, args, {"scripts"}) == (text, False, 0, False)


def test_battle_wrapper_scrolls_after_second_visible_line_and_preserves_pages():
    wrapped, changed, long_words = controlfix.wrap_battle_message(
        "Erster Zweiter Dritter Vierter", 45
    )
    assert changed and long_words == 0
    assert wrapped == "Erster\nZweiter\\lDritter\\lVierter"
    wrapped, _, _ = controlfix.wrap_battle_message(
        r"Erster\nZweiter\lDritter\pVierter", 208
    )
    assert wrapped == r"Erster\nZweiter\lDritter\pVierter"


def test_frontier_trainer_dialogue_uses_scrolling_pixel_layout():
    wrapped, changed, long_words, skipped = controlfix.wrap_translation(
        "Erster Zweiter Dritter Vierter",
        {"category": "trainer_dialogue"}, "English speech",
        _args(battle_message_max_pixels=45), {"trainer_dialogue"},
    )
    assert changed and not skipped and long_words == 0
    assert wrapped == "Erster\nZweiter\\lDritter\\lVierter"


def test_battle_runtime_widths_cover_second_trainer_partner_and_new_mon_names():
    widths = controlfix.battle_runtime_widths([
        {"category": "trainer_classes", "translated": "Kampfkoryphäe"},
        {"category": "trainer_names", "translated": "Alexandra"},
    ])
    assert widths[0x1C] == widths[0x2E] == widths[0x32]
    assert widths[0x1D] == widths[0x2F] == widths[0x33]
    assert widths[0x3A] == widths[0x3B] == widths[0x3C] == 90


def test_battle_pokemon_ligature_does_not_reset_scroll_row():
    wrapped, _, _ = controlfix.wrap_battle_message(
        "Erste\nZweite " + r"\pk\mn" + "\nDritte", 208
    )
    assert wrapped == "Erste\nZweite " + r"\pk\mn\lDritte"


def test_battle_widths_include_untranslated_names_in_partial_batches():
    widths = controlfix.battle_runtime_widths([
        {"category": "move_names", "original": '"A long untranslated move"'},
    ])
    assert widths[0x14] == controlfix.text_pixel_width("A long untranslated move")
