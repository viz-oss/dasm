# Decyzje, które już tu zapadły
- Stała musi być zdefiniowana przed użyciem. Jeden przebieg z góry na dół. Użycie przed .set zostawia zwykłą nazwę, czyli Ptr. Jeśli stałe mają być dostępne w całym pliku, potrzebny jest przebieg wstępny zbierający wszystkie .set, potem drugi z podmianą.
- Stałe nie mogą nazywać się rN, spójnie z regułą o rejestrach.
- .set usuwa linię, ale zostawia pustą, żeby numery linii w błędach parsera się zgadzały.
- Wartość to liczba, w tym ujemna i hex. Stała zapisana jako 0xFF wraca do tekstu jako 255.
# Do przemyślenia
- Kolumny po podmianie stałych są korygowane przez `ColumnMap` z `preprocess_with_map()`. Błąd wskazuje oryginalną kolumnę, a kontekst oryginalną linię. Wnętrze podstawionej wartości mapuje się na początek nazwy stałej. Podmiana nadal jest tekstowa, ale mapa kolumn odtwarza pozycje.
- art() i art:. Etykieta to osobny token label, więc jest bezpieczna. Wywołanie art() to token name, więc zostałoby zamienione na 1() i dało mylący błąd składni. Warto dodać wyjątek: jeśli następnym znaczącym tokenem jest (, rzucić błąd “constant used as a call”.
- Stała po lewej stronie. art = r0 po podmianie to 1 = r0, czyli cicho zapis pod adres 1 (Ptr(Int(1))). Może to być zamierzone, ale łatwo o pomyłkę.
- Duplikacja reguł leksykalnych. Regexy _TOKEN_RE powtarzają to, co jest w gramatyce (komentarze, napisy, NAME, LABEL). Gdy zmienisz składnię komentarzy w jednym miejscu, a w drugim nie, preprocesor zacznie się mylić. Najprostsze zabezpieczenie to wspólne stałe z regexami albo test, który sprawdza oba na tych samych przykładach.
- Nazwa stałej a nazwa etykiety. Jeśli istnieje .set art = 1 i etykieta art:, art: zostaje (osobny token), ale r0 = art stanie się r0 = 1, a nie odwołaniem do etykiety. Rozważ błąd przy takiej kolizji, ale to wymaga znajomości etykiet z całego pliku, czyli przebiegu wstępnego.
