# Writing the book in Hebrew

Everything the players or the DM read in the app is Hebrew. Only `id` fields, image paths, `ref`, `op`
and other keys stay in English.

## Game terms (as in the Hebrew Swords & Wizardry books)

| English | Hebrew in the book | notes |
|---|---|---|
| Hit Dice (HD) | קוביות פגיעה, קב״פ | `hd` field: "2", "4+1", "1ק6" |
| hit points (hp) | נקודות פגיעה, נק״פ | |
| Armor Class (AC) | דירוג שריון, דרג״ש | **ascending**. Descending AC X → 19 − X (AC 7 [12] → 12). If the source gives both ("7 [12]"), take the bracket. |
| to-hit bonus | תוסף התקפה | |
| saving throw | גלגול הצלה | monsters have one number (`save`) |
| save vs. traps / breath / death & poison / spells | הצלה נגד מלכודות וסכנות / נשיפת דרקון / מוות ורעל / לחשים | the player handbook's four columns |
| experience points (XP) | נקודות ניסיון, נק״ן | |
| gold / silver / copper pieces | מטבעות זהב / כסף / נחושת – מ״ז / מ״כ / מ״נ | 1 מ״ז = 10 מ״כ = 100 מ״נ |
| 1d6, 2d8+1, d% | 1ק6, 2ק8+1, ק% | always ק, always digits before it ("1ק6", not "ק6") |
| round / turn (10 min) | סיבוב / תור | |
| movement 12 | תנועה 12 | keep the number; it means metres per round in the Hebrew books |
| 10 feet / 5 ft square | 3 מ' / משבצת של 1.5 מ' | convert feet to metres: 10 ft = 3 m, 1 ft ≈ 0.3 m; round sensibly |
| level (character) | דרגה | spell level = עוצמה |
| NPC | דמות בלי שחקן, דב״ש | |
| fighter, cleric, magic-user, thief | לוחם, כוהן, קוסם, גנב | dwarf → גמד (שומר מעוז), elf → אלף (קשת), halfling → בן־מחצית (גשש / נועז) |
| Lawful / Neutral / Chaotic | סדר / ניטרלי / תוהו | |
| wandering monsters | מפלצות משוטטות | |
| secret door | דלת סתרים / דלת סודית | |
| read-aloud / boxed text | קטע הקראה | |
| Referee / DM | מנחה | the Hebrew books address the DM in the feminine |

Monster names: use references/monsters.md. Spell names: use the Hebrew handbook's names if you know
them ("קליע קסם", "הרדמה", "ריפוי פצעים קלים", "גילוי קסם", "אור", "הגנה מרוע", "הקסמת איש"…); if not sure,
translate plainly and add the English in parentheses once.

## Style

- Short, clear sentences. Present tense. Instructions to the DM in the impersonal plural ("מגלגלים", "אם הדמויות…").
- `read` (read-aloud): second person plural or plain description, what the characters perceive. No secrets, no numbers.
  If the source has no boxed text, write a short summary from the room description and say so in `readNote`.
- `dm`: a list of separate notes, each one idea, each ending with its page in parentheses: "(עמ' 9)".
  Put what matters at the table first: what happens when they enter, then details, then lore.
- Keep every number from the source: damage, distances, DCs, durations, chances, XP, treasure values.
- Names of people and places: transliterate, keep consistent across the whole book (make a name list first).
- Page references are the source's own page numbers: `"page": "עמ' 9"`, ranges `"עמ' 9–10"` (en dash).
- Hebrew punctuation: gershayim ״ in abbreviations (נק״ן, מ״ז), maqaf ־ in compounds (איש־נחש, בן־אדם),
  en dash – in ranges. Numbers and dice stay as digits.
- Translation, not adaptation: do not add, cut or "improve" content. Where you must interpret (unclear
  text, a stat the source omits), write it in a separate `dm` note marked as yours, e.g. "(פרשנות שלי: …)".
- A book written by the user themselves (Word etc.): keep their wording; only fix structure, split rooms,
  pull out monsters/traps/treasure into fields. Ask before rewording.
