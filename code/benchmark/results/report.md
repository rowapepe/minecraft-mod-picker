# Benchmark поиска — 2026-11-17T16:05:12+00:00

Корпус: 30 документов (`corpus.jsonl`); вопросы: 10 обычных и 5 ловушек; k = 5.

## Метрики по настройкам (одна настройка за раз)

| Настройка | Recall@5 | MRR@5 |
| --------- | -------- | ----- |
| базовая: лемматизация, k1 = 1.2, b = 0.75 | 0.567 | 0.775 |
| k1 = 1.5 | 0.533 | 0.775 |
| k1 = 2.0 | 0.533 | 0.820 |
| b = 0.5 | 0.567 | 0.800 |
| b = 1.0 | 0.533 | 0.753 |
| без лемматизации | 0.533 | 0.708 |
| удаление стоп-слов | 0.600 | 0.687 |
| полный снимок, 1000 модов (базовая; Recall — оценка снизу) | 0.192 | 0.233 |

## Ответы

| Accuracy (из 10) | Correct Rejection Rate (из 5) |
| -------- | ---------------------- |
| — | — |

_нет answers.jsonl: ответы LLM ещё не получены._

## Выдача базовой настройки по вопросам

| Вопрос | Релевантные | Первые 5 (★ — релевантный) | Recall@5 | RR | Полный снимок: первые 5 |
| ------ | ----------- | ---------------------------- | -------- | -- | ------------------------- |
| Q01 | D01 D02 D03 | D01★ D02★ D06 D16 D26 | 0.667 | 1.000 | niftycarts D02★ D01★ dynamictrees dynamictreesplus |
| Q02 | D03 D04 D05 D06 | D06★ D04★ D03★ D26 D18 | 0.750 | 1.000 | D06★ lets-do-brewery-farmcharm-compat lets-do-candlelight-farmcharm-compat cobblecuisine my-nethers-delight |
| Q03 | D07 D08 D09 | D26 D24 D28 D08★ D23 | 0.333 | 0.250 | notenoughcrashes tree-harvester faster-random lumyrei simpletms-tms-and-trs-for-cobblemon |
| Q04 | D10 D11 D12 | D10★ D29 D23 D28 D04 | 0.333 | 1.000 | dynamic-fps lazydfu distanthorizons the-broken-script faster-random |
| Q05 | D13 D14 D15 | D28 D14★ D19 D04 D29 | 0.333 | 0.500 | sodium-extras better-stats better-animations-collection yungs-cave-biomes dynamicsurroundingsfabric |
| Q06 | D16 D17 D18 | D17★ D16★ D18★ D27 D25 | 1.000 | 1.000 | illager-invasion ribbits D17★ spell-engine paladins-and-priests |
| Q07 | D19 D20 D21 | D21★ D19★ D26 D11 D18 | 0.667 | 1.000 | gensokyo-delight-youkais-feasts D21★ lets-do-bloomingnature D19★ nullscape |
| Q08 | D22 D23 D24 D25 | D23★ D19 D26 D21 D10 | 0.250 | 1.000 | philips-ruins galosphere structory quark aquamirae |
| Q09 | D25 D26 D27 | D16 D25★ D26★ D17 D18 | 0.667 | 0.500 | meet-your-fight true-ending mariums-soulslike-weaponry incendium adventurez |
| Q10 | D28 D29 D30 | D24 D29★ D19 D26 D28★ | 0.667 | 0.500 | miners-delight endrem mischief-illagers minecells illager-invasion |
| T01 (ловушка) | — | D23 D14 D29 D24 D19 | — | — | dawn trek sodium-extras kubejs icarus |
| T02 (ловушка) | — | D12 D29 D19 D14 D18 | — | — | automobility create-aeronautics dungeons-and-taverns-ancient-city-overhaul patchouli bellsandwhistles |
| T03 (ловушка) | — | D25 D26 D02 D21 D24 | — | — | cobblemon-fight-or-flight-reborn cobblemon-capture-xp cobblesafari cobblemon-playerxp cobblemonraiddens |
| T04 (ловушка) | — | D30 D27 D29 D11 D28 | — | — | simple-voice-chat plasmo-voice talkbubbles immersive-melodies patpat |
| T05 (ловушка) | — | D19 D03 D10 D16 D15 | — | — | tacz-tes-compat taczaddon rpl gd656killicon thermoo |

В столбце полного снимка документы вне D01…D30 показаны slug Modrinth.
