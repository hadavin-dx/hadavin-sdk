"""PR H batch 8, Issue 7: how much shown text does an unterminated C1 string opener (U+0090, U+0098, U+009D, U+009E, U+009F) cost?
Made-up text only: short Russian and Greek words (a made-up word list written here), turned into mojibake by encoding them as UTF-8
and reading the bytes as Latin-1 (what a wrong decoder does). Each text is a log line `INFO <mojibake words> done`. The
measure is how many characters of the line `hidden.strip` removes beyond the opener itself. Run from the repository root:
    PYTHONPATH=src python handover/evidence/PRH/b8/mojibake_loss.py
"""

from hadavin_sdk.guard import hidden

WORDS_RU = ["Привет", "Заказ", "Оплата", "Клиент", "Ошибка", "Сервер", "Запрос", "Отчет", "Пароль", "Адрес", "привет", "заказ", "оплата", "клиент", "ошибка", "сервер", "запрос", "отчет", "пароль", "адрес"]
WORDS_EL = ["Καλημερα", "Παραγγελια", "Πελατης", "Σφαλμα", "Αιτημα", "Διακομιστης", "καλημερα", "παραγγελια", "πελατης", "σφαλμα", "αιτημα", "διακομιστης"]
OPEN = "\x90\x98\x9d\x9e\x9f"


def main() -> None:
    texts = []
    for i in range(len(WORDS_RU)):
        words = [WORDS_RU[(i + k) % len(WORDS_RU)] for k in range(4)]
        texts.append("INFO " + " ".join(words).encode("utf-8").decode("latin-1") + " done")
    for i in range(len(WORDS_EL)):
        words = [WORDS_EL[(i + k) % len(WORDS_EL)] for k in range(3)]
        texts.append("INFO " + " ".join(words).encode("utf-8").decode("latin-1") + " done")
    with_open = [t for t in texts if any(c in t for c in OPEN)]
    lost = [len(t) - len(hidden.strip(t)[0]) - sum(t.count(c) for c in OPEN) for t in with_open]
    print(f"made-up mojibake lines: {len(texts)}; lines holding a C1 string opener: {len(with_open)}")
    print(f"characters removed beyond the opener itself: total {sum(lost)}, lines that lose more than 5: {sum(1 for x in lost if x > 5)}")
    for t in with_open[:2]:
        print("  example:", ascii(t), "->", ascii(hidden.strip(t)[0]))


main()
