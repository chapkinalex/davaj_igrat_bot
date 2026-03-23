"""Обработчики бота «Давай играть»."""
from datetime import datetime
from aiogram import types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.main import bot, dp
from data.database import (
    get_user_state,
    set_user_state,
    get_user_favorites,
    set_user_favorites,
    get_user_progress,
    set_user_progress,
    get_user_history,
    set_user_history,
    get_user_games_journal,
    set_user_games_journal,
    get_children,
    set_children,
    user_progress_row_exists,
    user_state_row_exists,
)
from data.games import GAMES


class FastFlowStates(StatesGroup):
    AGE = State()
    PROBLEM = State()
    GOAL = State()


FAST_AGE_MAP = {
    "fast_age_3_4": "age_2_5",
    "fast_age_5_7": "age_5_7",
    "fast_age_8_10": "age_7_10",
    "fast_age_11_14": "age_teen",
}

FAST_PROBLEM_MAP = {
    "fast_problem_contact": ["prob_silent", "prob_trust"],
    "fast_problem_conflicts": ["prob_disobedience"],
    "fast_problem_emotions": ["prob_disobedience", "prob_trust"],
    "fast_problem_anxiety": ["prob_trust"],
    "fast_problem_parent": ["prob_trust"],
}

FAST_GOAL_TO_FOCUS = {
    "fast_goal_contact": "contact",
    "fast_goal_less_conflicts": "conflicts",
    "fast_goal_help_emotions": "contact",
    "fast_goal_parent_calm": "selfcare",
}

AGE_DISPLAY_MAP = {
    "age_2_5": "2–5 лет",
    "age_5_7": "5–7 лет",
    "age_6_7": "6–7 лет",
    "age_7_10": "7–10 лет",
    "age_10_12": "10–12 лет",
    "age_teen": "подросток",
}

AGE_TEXT_MAP = {
    "age_2_5": "2–5 лет",
    "age_6_7": "6–7 лет",
    "age_7_10": "7–10 лет",
    "age_10_12": "10–12 лет",
    "age_teen": "подросток",
}

PROBLEM_TEXT_MAP_FAST = {
    "prob_disobedience": "Непослушание",
    "prob_gadgets": "Гаджеты",
    "prob_silent": "Молчит",
    "prob_trust": "Нет доверия",
}


def build_suitable_ids(problems_codes):
    suitable_ids = []
    for game in GAMES:
        game_problems = game.get("problems", [])
        if any(prob in problems_codes for prob in game_problems):
            suitable_ids.append(game["id"])
    return suitable_ids if suitable_ids else [g["id"] for g in GAMES[:5]]


def get_start_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Быстрый подбор игры", callback_data="fast_pick_start")],
            [InlineKeyboardButton(text="🔎 Разобраться глубже", callback_data="start_diagnostics")],
            [InlineKeyboardButton(text="📓 Мой журнал / позже", callback_data="show_journal_callback")],
            [InlineKeyboardButton(text="🆘 Помощь прямо сейчас", callback_data="urgent_help")],
        ]
    )


def get_fast_age_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="3–4 года", callback_data="fast_age_3_4")],
            [InlineKeyboardButton(text="5–7 лет", callback_data="fast_age_5_7")],
            [InlineKeyboardButton(text="8–10 лет", callback_data="fast_age_8_10")],
            [InlineKeyboardButton(text="11–14 лет", callback_data="fast_age_11_14")],
        ]
    )


def get_fast_problem_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Мало контакта, ребёнок отдалился", callback_data="fast_problem_contact")],
            [InlineKeyboardButton(text="Много конфликтов и крика", callback_data="fast_problem_conflicts")],
            [InlineKeyboardButton(text="Сильные эмоции, истерики, слёзы", callback_data="fast_problem_emotions")],
            [InlineKeyboardButton(text="Тревога, неуверенность у ребёнка", callback_data="fast_problem_anxiety")],
            [InlineKeyboardButton(text="Мне самой/самому очень тяжело", callback_data="fast_problem_parent")],
        ]
    )


def get_fast_goal_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Больше тёплого контакта", callback_data="fast_goal_contact")],
            [InlineKeyboardButton(text="Меньше ссор и крика", callback_data="fast_goal_less_conflicts")],
            [InlineKeyboardButton(text="Помочь ребёнку с эмоциями", callback_data="fast_goal_help_emotions")],
            [InlineKeyboardButton(text="Стать спокойнее самому/самой", callback_data="fast_goal_parent_calm")],
        ]
    )


def get_fast_first_game_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Показать первую игру", callback_data="fast_show_first_game")]]
    )


def get_fast_after_game_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить в журнал", callback_data="fast_save_to_journal")],
            [InlineKeyboardButton(text="🎮 Показать ещё одну игру", callback_data="fast_show_next_game")],
            [InlineKeyboardButton(text="🔎 Хочу разобраться глубже", callback_data="start_diagnostics")],
        ]
    )

@dp.message(CommandStart())
async def start_handler(message: Message):
    welcome_text = (
        "Привет! Я помогаю родителям через игры наладить контакт с ребёнком "
        "и сделать дома спокойнее.\n\nС чего начнём?"
    )
    await message.answer(welcome_text, reply_markup=get_start_keyboard())


@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Главное меню. С чего начнём?",
        reply_markup=get_start_keyboard(),
    )


@dp.callback_query(lambda c: c.data == "fast_pick_start")
async def fast_pick_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await state.set_state(FastFlowStates.AGE)
    await callback.message.edit_text(
        "Хорошо, подберём игру быстро. Сколько лет ребёнку?",
        reply_markup=get_fast_age_keyboard(),
    )


@dp.callback_query(lambda c: c.data.startswith("fast_age_"))
async def fast_age_selected(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    age_code = FAST_AGE_MAP.get(callback.data)
    if not age_code:
        await callback.answer("Не удалось определить возраст", show_alert=True)
        return

    await state.update_data(age=age_code)
    await state.set_state(FastFlowStates.PROBLEM)
    await callback.message.edit_text(
        "Что больше всего беспокоит сейчас в отношениях с ребёнком?",
        reply_markup=get_fast_problem_keyboard(),
    )


@dp.callback_query(lambda c: c.data.startswith("fast_problem_"))
async def fast_problem_selected(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    problems = FAST_PROBLEM_MAP.get(callback.data, ["prob_trust"])

    await state.update_data(problems=problems)
    await state.set_state(FastFlowStates.GOAL)
    await callback.message.edit_text(
        "Что сейчас важнее всего изменить?",
        reply_markup=get_fast_goal_keyboard(),
    )


@dp.callback_query(lambda c: c.data.startswith("fast_goal_"))
async def fast_goal_selected(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    focus = FAST_GOAL_TO_FOCUS.get(callback.data)
    data = await state.get_data()
    age_code = data.get("age")
    problems = data.get("problems", [])

    if not age_code or not problems or not focus:
        await callback.answer("Начните быстрый подбор заново 🙂", show_alert=True)
        return

    suitable_ids = build_suitable_ids(problems)
    total_games = len(suitable_ids)
    await state.update_data(focus=focus, suitable_ids=suitable_ids, current_index=0)

    user_id = callback.from_user.id
    user_state_data = get_user_state(user_id)
    user_state_data.update(
        {
            "age": age_code,
            "problems": problems,
            "focus": focus,
            "suitable_ids": suitable_ids,
            "current_index": -1,
        }
    )
    set_user_state(user_id, user_state_data)

    if total_games == 0:
        await callback.message.edit_text(
            "По вашим ответам я не нашла подходящих игр в своей базе.\n"
            "Можно пройти более подробную диагностику — так я подберу идеи точнее.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔎 Пройти подробную диагностику", callback_data="start_diagnostics")]
                ]
            ),
        )
        return

    await callback.message.edit_text(
        "Отлично, подобрала игры под вашу ситуацию.\n"
        "Покажу первую — попробуйте в ближайшие дни.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Показать первую игру", callback_data="fast_show_first_game")]
            ]
        ),
    )


@dp.callback_query(lambda c: c.data == "fast_show_first_game")
async def fast_show_first_game(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    suitable_ids = data.get("suitable_ids", [])
    age_code = data.get("age")
    problems = data.get("problems", [])

    if not suitable_ids or not age_code:
        await callback.answer("Сначала пройдите быстрый подбор 🙂", show_alert=True)
        return

    first_id = suitable_ids[0]
    game = next((g for g in GAMES if g["id"] == first_id), None)
    if not game:
        await callback.answer("Не удалось загрузить игру", show_alert=True)
        return

    await state.update_data(current_index=0)
    age_text = AGE_DISPLAY_MAP.get(age_code, "неизвестный возраст")
    await show_game_card(callback.message, game, age_text, problems, PROBLEM_TEXT_MAP_FAST)
    await callback.message.answer(
        "Понравилась игра? Сохраните в журнал, чтобы не потерять.",
        reply_markup=get_fast_after_game_keyboard(),
    )


@dp.callback_query(lambda c: c.data == "fast_show_next_game")
async def fast_show_next_game(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    suitable_ids = data.get("suitable_ids", [])
    age_code = data.get("age")
    problems = data.get("problems", [])
    current_index = data.get("current_index", 0)

    if not suitable_ids or not age_code:
        await callback.answer("Сначала пройдите быстрый подбор 🙂", show_alert=True)
        return

    next_index = current_index + 1
    if next_index >= len(suitable_ids):
        await callback.message.answer(
            "Игры по вашим ответам закончились, можно пройти подробную диагностику",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔎 Хочу разобраться глубже", callback_data="start_diagnostics")]
                ]
            ),
        )
        return

    game = next((g for g in GAMES if g["id"] == suitable_ids[next_index]), None)
    if not game:
        await callback.answer("Не удалось загрузить игру", show_alert=True)
        return

    await state.update_data(current_index=next_index)
    age_text = AGE_DISPLAY_MAP.get(age_code, "неизвестный возраст")
    await show_game_card(callback.message, game, age_text, problems, PROBLEM_TEXT_MAP_FAST)
    await callback.message.answer(
        "Если игра откликнулась, можно сохранить её в свой небольшой «журнал» и вернуться к ней позже.",
        reply_markup=get_fast_after_game_keyboard(),
    )


@dp.callback_query(lambda c: c.data == "fast_save_to_journal")
async def fast_save_to_journal(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    suitable_ids = data.get("suitable_ids", [])
    current_index = data.get("current_index", 0)

    if not suitable_ids:
        await callback.answer("Сначала пройдите быстрый подбор 🙂", show_alert=True)
        return

    if current_index < 0 or current_index >= len(suitable_ids):
        await callback.answer("Не удалось понять, какую игру сохранить", show_alert=True)
        return

    game_id = suitable_ids[current_index]
    user_id = callback.from_user.id
    journal = get_user_games_journal(user_id)
    journal.append(
        {
            "game_id": game_id,
            "status": "saved_fast",
            "rating": "saved",
            "reason": "Сохранено из быстрого подбора",
            "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
        }
    )
    set_user_games_journal(user_id, journal)
    await callback.message.answer("✅ Сохранила в журнал. Можно открыть его в любой момент.")


@dp.callback_query(lambda c: c.data == "urgent_help")
async def urgent_help(callback: types.CallbackQuery):
    await callback.answer()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧒 Ребёнок в истерике / очень плачет",
                    callback_data="urgent_meltdown"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⚡ Сильный конфликт / ссора только что",
                    callback_data="urgent_conflict"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="😰 Ребёнок сильно тревожится / боится",
                    callback_data="urgent_anxiety"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🧍 Мне самому/самой очень тяжело",
                    callback_data="urgent_parent"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 В главное меню",
                    callback_data="back_to_main"
                ),
            ],
        ]
    )

    await callback.message.edit_text(
        "Давай без долгих вопросов, просто поможем пережить **прямо сейчас**. "
        "Выбери, что больше всего похоже на вашу ситуацию:",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

@dp.callback_query(lambda c: c.data == "urgent_meltdown")
async def urgent_meltdown(callback: types.CallbackQuery):
    await callback.answer()
    text = (
        "🧒 Ребёнок в истерике / очень плачет\n\n"
        "Сейчас важнее **пережить волну**, а не воспитывать.\n\n"
        "1️⃣ Сначала про себя.\n"
        "Если можете — сделайте 3 медленных вдоха и выдоха. "
        "Скажите себе: «Сейчас буря, потом мы разберёмся. Мне не нужно быть идеальным родителем».\n\n"
        "2️⃣ Меньше слов — больше присутствия.\n"
        "Не убеждайте и не объясняйте, пока плач на пике. Можно тихо рядом говорить: "
        "«Я рядом», «Слышу, как тебе плохо», «Можешь поплакать, я с тобой».\n\n"
        "3️⃣ Без угроз и стыда.\n"
        "Фразы типа «Ну перестань немедленно», «Посмотри, как ты себя ведёшь» только усиливают стресс. "
        "Лучше дать понять, что чувствовать — можно, а вот про то, *что делать дальше*, вы поговорите позже.\n\n"
        "Когда станет чуть тише, можно будет подобрать спокойную игру или ритуал. "
        "Если хочешь, после этого я подберу 1–2 простые игры на успокоение."
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Дай спокойные игры",
                    callback_data="urgent_games_calm"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 В главное меню",
                    callback_data="back_to_main"
                )
            ],
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "urgent_conflict")
async def urgent_conflict(callback: types.CallbackQuery):
    await callback.answer()
    text = (
        "⚡ Сильный конфликт / ссора только что\n\n"
        "1️⃣ Поставить паузу.\n"
        "Можно сказать: «Я сейчас слишком злюсь, боюсь наговорить лишнего. "
        "Давай сделаем паузу и вернёмся к разговору чуть позже».\n\n"
        "2️⃣ Не отменять контакт.\n"
        "Важно дать понять: вы злитесь на поступок, а не на ребёнка целиком. "
        "Например: «Я злюсь из‑за того, что произошло, но ты для меня всё равно важен».\n\n"
        "3️⃣ Обсуждать, когда спадёт накал.\n"
        "Вернуться к теме позже: что произошло, что каждый чувствовал, как можно по‑другому.\n\n"
        "Могу предложить небольшие шаги и игры, которые помогут снижать количество таких ссор."
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🕊 Хочу шаги про конфликты",
                    callback_data="focus_conflicts"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎮 Дай игры, чтобы помириться",
                    callback_data="urgent_games_reconnect"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 В главное меню",
                    callback_data="back_to_main"
                )
            ],
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "urgent_anxiety")
async def urgent_anxiety(callback: types.CallbackQuery):
    await callback.answer()
    text = (
        "😰 Ребёнок сильно тревожится / боится\n\n"
        "1️⃣ Сначала признаём чувство.\n"
        "Фразы: «Я вижу, что тебе страшно», «Тревожиться — это нормально, давай попробуем помочь "
        "телу успокоиться».\n\n"
        "2️⃣ Опора на тело и дыхание.\n"
        "Можно предложить вместе сделать 3–5 медленных вдохов и выдохов, крепко обнять, сесть спиной к спине.\n\n"
        "3️⃣ Не обесценивать страх.\n"
        "Вместо «Ну чего ты выдумываешь» — «Страшно, когда так думаешь. Давай посмотрим, что мы можем "
        "сделать прямо сейчас, чтобы стало чуть спокойнее».\n\n"
        "Я могу предложить пару простых игр и ритуалов, которые помогают снижать тревогу."
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Дай игры от тревоги",
                    callback_data="urgent_games_anxiety"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 В главное меню",
                    callback_data="back_to_main"
                )
            ],
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "urgent_parent")
async def urgent_parent(callback: types.CallbackQuery):
    await callback.answer()
    text = (
        "🧍 Мне самому/самой очень тяжело\n\n"
        "1️⃣ Замечаем, что с вами происходит.\n"
        "Можно мысленно назвать: «Я сейчас выжат(а) / злой(злая) / напуган(а) / в отчаянии».\n\n"
        "2️⃣ Мини‑шаг заботы.\n"
        "Выберите что‑то очень маленькое на ближайшие минуты: выпить воды, "
        "отойти в другую комнату на пару вдохов, выйти на балкон/в коридор.\n\n"
        "3️⃣ Снимаем часть вины.\n"
        "Фраза, которую можно повторять: «Я не обязан(а) быть идеальным родителем. "
        "Сейчас мне тяжело, и это нормально искать поддержку».\n\n"
        "Хочешь, дам несколько маленьких шагов по заботе о себе и уменьшению самокритики?"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💚 Хочу шаги для себя",
                    callback_data="focus_selfcare"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 В главное меню",
                    callback_data="back_to_main"
                )
            ],
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard)






@dp.callback_query(lambda c: c.data == "start_diagnostics")
async def start_diagnostics(callback: types.CallbackQuery):
    """
    Экран выбора ребёнка перед мини‑диагностикой.
    Логика:
    - если детей ещё нет — сразу предлагаем добавить первого ребёнка;
    - если дети есть — показываем список и кнопку «➕ Добавить ребёнка».
    """
    await callback.answer()
    user_id = callback.from_user.id
    user_children = get_children(user_id)

    # Если нет ни одного ребёнка — предлагаем добавить
    if not user_children:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Добавить ребёнка",
                        callback_data="add_child"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 В главное меню",
                        callback_data="back_to_main"
                    ),
                ],
            ]
        )

        await callback.message.edit_text(
            "Сначала добавим ребёнка, для которого будем подбирать игры и шаги.\n\n"
            "Нажмите «➕ Добавить ребёнка», чтобы указать имя и возраст.",
            reply_markup=keyboard
        )
        return

    # Если дети уже есть — показываем список + кнопку добавить нового
    buttons = []
    for idx, child in enumerate(user_children):
        name = child.get("name", f"Ребёнок #{idx + 1}")
        age_code = child.get("age_code")
        age_label = AGE_LABELS.get(age_code, "возраст не указан")
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{name} ({age_label})",
                    callback_data=f"select_child_{idx}"
                ),
            ]
        )

    # Кнопка добавить нового ребёнка
    buttons.append(
        [
            InlineKeyboardButton(
                text="➕ Добавить ребёнка",
                callback_data="add_child"
            ),
        ]
    )

    # Кнопка назад
    buttons.append(
        [
            InlineKeyboardButton(
                text="🔙 В главное меню",
                callback_data="back_to_main"
            ),
        ]
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        "Выберите ребёнка, для которого сейчас будем проходить диагностику, "
        "или добавьте нового:",
        reply_markup=keyboard
    )


@dp.callback_query(lambda c: c.data == "add_child")
async def add_child(callback: types.CallbackQuery):
    """
    Шаг 1: просим ввести имя ребёнка текстом.
    """

    await callback.answer()

    user_id = callback.from_user.id
    state = get_user_state(user_id)
    state["awaiting_child_name"] = True
    set_user_state(user_id, state)

    await callback.message.edit_text(
        "Напишите, пожалуйста, имя ребёнка, для которого будем подбирать игры и шаги.\n\n"
        "Например: Маша, Лёша, Соня.",
    )


# Выбор возраста
# Выбор возраста
@dp.callback_query(lambda c: c.data.startswith("age_"))
async def age_selected(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    # Сохраняем возраст и обнуляем состояние
    set_user_state(
        user_id,
        {
            "age": callback.data,
            "child_behaviour": [],   # поведение ребёнка
            "parent_state": [],      # сюда добавим позже
            "family_dynamic": [],    # сюда добавим позже
            "current_index": 0,
            "diag_done": False,
        },
    )

    # Первый вопрос мини-диагностики
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Много ссор и крика дома", callback_data="diag_main_conflicts")],
        [InlineKeyboardButton(text="📱 Постоянно в телефоне / гаджетах", callback_data="diag_main_gadgets")],
        [InlineKeyboardButton(text="🤐 Замкнулся, мало говорит", callback_data="diag_main_silent")],
        [InlineKeyboardButton(text="💔 Стало меньше доверия и тепла", callback_data="diag_main_trust")],
        [InlineKeyboardButton(text="⏭ Пропустить вопросы и выбрать самой", callback_data="diag_skip")]
    ])

    await callback.message.edit_text(
        "Супер. Теперь чуть лучше поймём, *что больше всего про вашего ребёнка сейчас*.\n\n"
        "Выберите то, что отзывается сильнее всего:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


def get_child_behaviour_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Непослушание, игнорирование просьб", callback_data="beh_disobedience")],
        [InlineKeyboardButton(text="Грубость, хамство, огрызается", callback_data="beh_rude")],
        [InlineKeyboardButton(text="Очень эмоциональный, вспышки", callback_data="beh_emotional")],
        [InlineKeyboardButton(text="Ничего не интересует, трудно увлечь", callback_data="beh_apathy")],
        [InlineKeyboardButton(text="Много гаджетов, сложно оторвать", callback_data="beh_gadgets")],
        [InlineKeyboardButton(text="Молчит, отвечает односложно", callback_data="beh_silent")],
        [InlineKeyboardButton(text="Говорит «Ты меня не любишь»", callback_data="beh_not_loved")],
        [InlineKeyboardButton(text="Ссоры и борьба между детьми", callback_data="beh_siblings_conflict")],
        [InlineKeyboardButton(text="Жалобы от учителей/воспитателей", callback_data="beh_school_complaints")],
        [InlineKeyboardButton(text="➡️ Далее", callback_data="child_behaviour_next")]
    ])


def get_parent_state_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Быстро закипаю и срываюсь", callback_data="ps_burnout")],
        [InlineKeyboardButton(text="Много тревоги за будущее ребёнка", callback_data="ps_future_anxiety")],
        [InlineKeyboardButton(text="Чувствую, что теряю контакт", callback_data="ps_lost_contact")],
        [InlineKeyboardButton(text="Часто виню себя как родителя", callback_data="ps_guilt")],
        [InlineKeyboardButton(text="Трудно поддержать ребёнка в сложные моменты", callback_data="ps_support_hard")],
        [InlineKeyboardButton(text="Очень устаю от постоянных конфликтов", callback_data="ps_conflict_tired")],
        [InlineKeyboardButton(text="Хочется тишины и передышки", callback_data="ps_need_rest")],
        [InlineKeyboardButton(text="➡️ Далее", callback_data="parent_state_next")]
    ])

def get_family_dynamic_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Разные подходы взрослых к воспитанию", callback_data="fam_different_approaches")],
        [InlineKeyboardButton(text="Много напряжения и ссор дома", callback_data="fam_tension_conflicts")],
        [InlineKeyboardButton(text="Ревность и конкуренция между детьми", callback_data="fam_sibling_rivalry")],
        [InlineKeyboardButton(text="Мало общих тёплых ритуалов и времени вместе", callback_data="fam_few_rituals")],
        [InlineKeyboardButton(text="Основная нагрузка на одного родителя", callback_data="fam_one_parent_load")],
        [InlineKeyboardButton(text="✅ Показать результат", callback_data="family_dynamic_done")]
    ])
def get_start_improve_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Приступим к улучшению отношений", callback_data="start_improve")]
    ])


def get_focus_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤝 Больше контакта и доверия", callback_data="focus_contact")],
        [InlineKeyboardButton(text="🕊 Меньше конфликтов и крика", callback_data="focus_conflicts")],
        [InlineKeyboardButton(text="💚 Больше опоры для себя", callback_data="focus_selfcare")],
        [InlineKeyboardButton(text="🎮 Сразу перейти к играм", callback_data="focus_games_current")],
    ])


def get_focus_games_keyboard(focus_code: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Показать игры под этот фокус", callback_data=f"focus_games_{focus_code}")],
        [InlineKeyboardButton(text="⬅️ Выбрать другое направление", callback_data="start_improve")]
    ])


def get_more_steps_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Ещё один небольшой шаг", callback_data="focus_more_step")],
        [InlineKeyboardButton(text="🎮 Перейти к играм по этому направлению", callback_data="focus_games_current")],
        [InlineKeyboardButton(text="⬅️ Выбрать другое направление", callback_data="start_improve")]
    ])






AGE_LABELS = {
    "age_2_5": "2–5 лет",
    "age_5_7": "5–7 лет",
    "age_6_7": "6–7 лет",
    "age_7_10": "7–10 лет",
    "age_10_12": "10–12 лет",
    "age_teen": "подростковый возраст",
}


BEHAVIOUR_LABELS = {
    "beh_silent": "закрывается, мало говорит",
    "beh_gadgets": "много уходит в гаджеты",
    "beh_aggresive": "часто злится, дерётся или кричит",
    "beh_not_loved": "часто говорит или показывает, что чувствует себя нелюбимым",
    "beh_disobedience": "часто не слушается и игнорирует просьбы",
    "beh_rude": "отвечает грубо, может резко говорить с близкими",
    "beh_emotional": "часто реагирует очень бурно, «переполняется» эмоциями",
    "beh_apathy": "выглядит уставшим, без интереса и энергии",
    "beh_siblings_conflict": "часто конфликтует с братом или сестрой",
    "beh_school_complaints": "есть жалобы от сада/школы на поведение или вовлечённость",
}



PARENT_STATE_LABELS = {
    "ps_tired": "очень устаю и выгораю",
    "ps_guilt": "много чувствую вины",
    "ps_lost_contact": "чувствую, что теряю контакт с ребёнком",
    "ps_support_hard": "тяжело поддерживать ребёнка и быть рядом эмоционально",
    "ps_future_anxiety": "много тревоги за будущее ребёнка",
    "ps_burnout": "чувствую сильное выгорание и опустошение",
    "ps_conflict_tired": "очень устаю от ссор и конфликтов дома",
    "ps_need_rest": "очень нужен отдых и время на себя",
}




FAMILY_DYNAMIC_LABELS = {
    "fam_different_approaches": "разные подходы взрослых к воспитанию",
    "fam_tension_conflicts": "много напряжения и ссор дома",
    "fam_sibling_rivalry": "ревность и конкуренция между детьми",
    "fam_few_rituals": "мало общих тёплых ритуалов и времени вместе",
    "fam_one_parent_load": "основная нагрузка на одном родителе",
}




# Шаг 3. Обработчики ответов на первый вопрос
@dp.callback_query(lambda c: c.data.startswith("diag_main_"))
async def diag_main_selected(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    state = get_user_state(user_id)

    if not state:
        await callback.answer("Сначала выбери возраст 🙂", show_alert=True)
        return

    main_choice = callback.data  # diag_main_conflicts / diag_main_gadgets / ...

    # Привязываем первый ответ к базовым «проблемам» (для подбора игр)
    mapping = {
        "diag_main_conflicts": ["prob_disobedience", "prob_trust"],
        "diag_main_gadgets": ["prob_gadgets"],
        "diag_main_silent": ["prob_silent", "prob_trust"],
        "diag_main_trust": ["prob_trust"],
    }

    base_problems = mapping.get(main_choice, [])
    state["problems"] = base_problems
    set_user_state(user_id, state)

    # Переходим к экрану «Поведение ребёнка»
    await callback.message.edit_text(
        "Теперь посмотрим на поведение ребёнка.\n\n"
        "Отметь, что больше всего откликается сейчас. Можно выбрать несколько пунктов, потом нажать «➡️ Далее».",
        reply_markup=get_child_behaviour_keyboard()
    )


# Обработчик «Пропустить вопросы и выбрать самой»
@dp.callback_query(lambda c: c.data == "diag_skip")
async def diag_skip(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    state = get_user_state(user_id)

    if not state:
        await callback.answer("Сначала выбери возраст 🙂", show_alert=True)
        return

    await callback.message.edit_text(
        "Тогда начнём с поведения ребёнка.\n\n"
        "Отметь, что больше всего откликается сейчас. Можно выбрать несколько пунктов, потом нажать «➡️ Далее».",
        reply_markup=get_child_behaviour_keyboard()
    )


# Выбор поведения ребёнка (beh_*)
@dp.callback_query(lambda c: c.data.startswith("beh_"))
async def child_behaviour_selected(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if not user_state_row_exists(user_id):
        set_user_state(
            user_id,
            {
                "age": None,
                "child_behaviour": [],
                "parent_state": [],
                "family_dynamic": [],
                "current_index": 0,
            },
        )

    st = dict(get_user_state(user_id))
    beh_code = callback.data  # beh_disobedience, beh_rude и т.п.
    behaviours = list(st.get("child_behaviour", []))

    if beh_code not in behaviours:
        behaviours.append(beh_code)
        await callback.answer("✅ Добавлено")
    else:
        behaviours.remove(beh_code)
        await callback.answer("❌ Убрано")

    st["child_behaviour"] = behaviours
    set_user_state(user_id, st)


# Кнопка «Далее» после поведения ребёнка
@dp.callback_query(lambda c: c.data == "child_behaviour_next")
async def child_behaviour_next(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    state = get_user_state(user_id)

    if not state or not state.get("child_behaviour"):
        await callback.answer("Отметь хотя бы один пункт про поведение ребёнка 🙂", show_alert=True)
        return

    # Пока просто текст-заглушка — потом сюда добавим «Состояние родителя»
    await callback.message.edit_text(
        "Теперь немного про тебя.\n\n"
        "Выбери, какие состояния и переживания сейчас ближе всего. Можно несколько пунктов, потом нажать «➡️ Далее».",
        reply_markup=get_parent_state_keyboard()
    )
# Выбор состояний родителя (ps_*)
@dp.callback_query(lambda c: c.data.startswith("ps_"))
async def parent_state_selected(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if not user_state_row_exists(user_id):
        set_user_state(
            user_id,
            {
                "age": None,
                "child_behaviour": [],
                "parent_state": [],
                "family_dynamic": [],
                "current_index": 0,
            },
        )

    st = dict(get_user_state(user_id))
    ps_code = callback.data  # ps_burnout, ps_future_anxiety и т.п.
    states = list(st.get("parent_state", []))

    if ps_code not in states:
        states.append(ps_code)
        await callback.answer("✅ Добавлено")
    else:
        states.remove(ps_code)
        await callback.answer("❌ Убрано")

    st["parent_state"] = states
    set_user_state(user_id, st)


# Кнопка «Далее» после состояний родителя
@dp.callback_query(lambda c: c.data == "parent_state_next")
async def parent_state_next(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    state = get_user_state(user_id)

    if not state or not state.get("parent_state"):
        await callback.answer("Отметь хотя бы один пункт про себя 🙂", show_alert=True)
        return
    # Подбираем игры по результатам диагностики
    suitable_ids = []
    for game in GAMES:
        game_problems = game.get("problems", [])
        if any(prob in state.get("problems", []) for prob in game_problems):
            suitable_ids.append(game["id"])
    
    state["suitable_ids"] = suitable_ids if suitable_ids else [g["id"] for g in GAMES[:5]]  # если ничего не подошло, берём первые 5
    set_user_state(user_id, state)

    await callback.message.edit_text(
        "Теперь посмотрим на семейную ситуацию.\n\n"
        "Выбери, что больше всего откликается про вашу семью. Можно несколько пунктов, затем нажать «✅ Показать результат».",
        reply_markup=get_family_dynamic_keyboard()
    )

# Выбор семейной динамики (fam_*)
@dp.callback_query(lambda c: c.data.startswith("fam_"))
async def family_dynamic_selected(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if not user_state_row_exists(user_id):
        set_user_state(
            user_id,
            {
                "age": None,
                "child_behaviour": [],
                "parent_state": [],
                "family_dynamic": [],
                "current_index": 0,
            },
        )

    st = dict(get_user_state(user_id))
    fam_code = callback.data  # fam_different_approaches и т.п.
    dyn = list(st.get("family_dynamic", []))

    if fam_code not in dyn:
        dyn.append(fam_code)
        await callback.answer("✅ Добавлено")
    else:
        dyn.remove(fam_code)
        await callback.answer("❌ Убрано")

    st["family_dynamic"] = dyn
    set_user_state(user_id, st)


# Завершение диагностики по семейной динамике
@dp.callback_query(lambda c: c.data == "family_dynamic_done")
async def family_dynamic_done(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    state = get_user_state(user_id)

    if not state or not state.get("family_dynamic"):
        await callback.answer("Отметь хотя бы один пункт про семью 🙂", show_alert=True)
        return

    # --- СОХРАНЯЕМ ПРОГРЕСС ПОСЛЕ ДИАГНОСТИКИ ---
    # По умолчанию после диагностики пока считаем, что человек ещё не выбрал конкретный фокус.
    # Поэтому просто обнуляем прогресс (или создаём запись-заглушку).
    child_name = state.get("child_name")


    set_user_progress(
        user_id,
        child_name,
        {
            "focus": None,
            "step": 1,
            "last_game_id": None,
            "last_diagnosis_id": datetime.now().strftime("%d.%m.%Y %H:%M"),
        },
    )



    # --- ДОБАВЛЯЕМ ЗАПИСЬ В ИСТОРИЮ ДИАГНОСТИК ---
    child_name = state.get("child_name")
    age = state.get("age")
    child_behaviour = state.get("child_behaviour", [])
    parent_state = state.get("parent_state", [])
    family_dynamic = state.get("family_dynamic", [])

    record = {
        "child_name": child_name,
        "age": age,
        "child_behaviour": child_behaviour,
        "parent_state": parent_state,
        "family_dynamic": family_dynamic,
        "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }


    # Берём всю историю пользователя
    full_history = get_user_history(user_id)

    comparison_text = None

    # Фильтруем только диагностики для этого ребёнка
    same_child_records = [
        r for r in full_history
        if r.get("child_name") == child_name
    ]

    if same_child_records:
        # Берём последнюю диагностику именно для этого ребёнка
        prev_record = same_child_records[-1]

        prev_cb = len(prev_record.get("child_behaviour", []))
        prev_ps = len(prev_record.get("parent_state", []))
        prev_fam = len(prev_record.get("family_dynamic", []))

        new_cb = len(child_behaviour)
        new_ps = len(parent_state)
        new_fam = len(family_dynamic)

        comparison_lines = [
            f"📊 Изменения по сравнению с прошлой диагностикой для {child_name}:",
            f"- Поведение ребёнка: было отмечено {prev_cb} пункт(ов), стало — {new_cb}.",
            f"- Ваше состояние: было отмечено {prev_ps} пункт(ов), стало — {new_ps}.",
            f"- Семейная ситуация: было отмечено {prev_fam} пункт(ов), стало — {new_fam}.",
        ]

        comparison_text = "\n".join(comparison_lines)

    # Добавляем текущую диагностику в общую историю (для всех детей)
    full_history.append(record)
    set_user_history(user_id, full_history)

    # Если есть текст сравнения — отправляем его отдельно
    if comparison_text:
        await callback.message.answer(comparison_text)

    # Здесь вызываем финальный шаг с сценарием и играми
    await show_result(callback)






# Выбор проблем
@dp.callback_query(lambda c: c.data.startswith("prob_"))
async def problem_selected(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if not user_state_row_exists(user_id):
        set_user_state(user_id, {"age": None, "problems": [], "current_index": 0})

    st = dict(get_user_state(user_id))
    problem_code = callback.data
    problems = list(st["problems"])

    if problem_code not in problems:
        problems.append(problem_code)
        await callback.answer("✅ Добавлено")
    else:
        problems.remove(problem_code)
        await callback.answer("❌ Убрано")

    st["problems"] = problems
    set_user_state(user_id, st)


# Показать первую игру
async def show_result(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    state = get_user_state(user_id)

    # 1. Достаём ответы пользователя
    age = state.get("age")
    child_behaviour = state.get("child_behaviour", [])
    parent_state = state.get("parent_state", [])
    family_dynamic = state.get("family_dynamic", [])

    # 2. Создаём список для кусочков текста
    result_parts = []

    # 📊 Простейшее сравнение с предыдущей диагностикой (по количеству отмеченных пунктов)
    history = get_user_history(user_id)
    comparison_text = None

    # history[-1] — это текущая запись, предыдущая — [-2]
    if len(history) >= 2:
        last_record = history[-2]

        base_cb = len(last_record.get("child_behaviour", []))
        base_ps = len(last_record.get("parent_state", []))
        base_fam = len(last_record.get("family_dynamic", []))

        new_cb = len(child_behaviour)
        new_ps = len(parent_state)
        new_fam = len(family_dynamic)

        comparison_lines = [
            "📊 Изменения по сравнению с прошлой диагностикой:",
            f"- Поведение ребёнка: было отмечено {base_cb} пункт(ов), сейчас — {new_cb}.",
            f"- Ваше состояние: было отмечено {base_ps} пункт(ов), сейчас — {new_ps}.",
            f"- Семейная ситуация: было отмечено {base_fam} пункт(ов), сейчас — {new_fam}.",
        ]

        comparison_text = "\n".join(comparison_lines)

        # Добавляем этот блок в общий текст, если это не самая первая диагностика
        if len(history) >= 2 and comparison_text:
            result_parts.append(comparison_text)


    # 3. Краткий обзор ситуации
    analysis_text = "Вот что получилось по вашей ситуации:\n\n"

    if age:
        age_label = AGE_LABELS.get(age, age)
        analysis_text += f"• Возраст ребёнка: {age_label}.\n"

    if child_behaviour:
        behaviour_labels = [BEHAVIOUR_LABELS.get(code, code) for code in child_behaviour]
        analysis_text += "• Поведение / трудности, которые вы отметили: "
        analysis_text += ", ".join(behaviour_labels) + ".\n"

    if parent_state:
        parent_labels = [PARENT_STATE_LABELS.get(code, code) for code in parent_state]
        analysis_text += "• Ваше состояние сейчас: "
        analysis_text += ", ".join(parent_labels) + ".\n"

    if family_dynamic:
        family_labels = [FAMILY_DYNAMIC_LABELS.get(code, code) for code in family_dynamic]
        analysis_text += "• Семейная картина: "
        analysis_text += ", ".join(family_labels) + ".\n"

    result_parts.append(analysis_text)


    # 4. Нормализация и поддержка
    support_text = (
        "С похожими ситуациями сталкиваются многие семьи, с вами **всё** в порядке — "
        "вы уже делаете важный шаг, просто замечая это и пробуя что-то менять.\n\n"
        "Родителю не нужно быть идеальным. Достаточно быть «достаточно хорошим» — "
        "ошибаться, замечать это и постепенно пробовать способы, которые подходят именно вам и вашему ребёнку."
    )

    # 5. Усиление, если в семье напряжённо
    if "fam_tension_conflicts" in family_dynamic or "fam_different_approaches" in family_dynamic:
        support_text += (
            "\n\nЕсли сейчас в семье много напряжения или разные взгляды на воспитание, "
            "это не значит, что с вами что-то не так. Маленькие посильные шаги и "
            "доброжелательность к себе обычно дают больше результата, чем жёсткая "
            "самокритика и ожидание идеальности."
        )

    result_parts.append(support_text)

    # 6. Игры / идеи (сюда потом можно подставить свой текст с играми)
    games_text = (
        "Ниже — несколько идей, что можно попробовать в ближайшие дни.\n"
        "Выберите 1–2 шага, которые сейчас кажутся вам посильными, и дайте себе время на эксперимент."
    )
    result_parts.append(games_text)

    # 7. Собираем всё и отправляем
    full_text = "\n\n".join(result_parts)

    await callback.message.edit_text(
        full_text,
        reply_markup=get_start_improve_keyboard()
    )
@dp.callback_query(lambda c: c.data == "start_improve")
async def start_improve_clicked(callback: types.CallbackQuery):
    await callback.answer()

    await callback.message.answer(
        "Супер, что вы готовы к шагам.\n\n"
        "С чего сейчас важнее начать?",
        reply_markup=get_focus_keyboard()
    )
@dp.callback_query(lambda c: c.data == "focus_contact")
async def focus_contact(callback: types.CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    state = get_user_state(user_id)
    state["focus"] = "contact"
    state["focus_step"] = 3
    set_user_state(user_id, state)

    # Обновляем прогресс для кнопки "Продолжить"
    # Здесь мы чётко фиксируем, что выбран фокус "contact" и пользователь на самом начале пути.
    child_name = state.get("child_name")
    key = (user_id, child_name)

    set_user_progress(
        key[0],
        key[1],
        {
            "focus": "contact",
            "step": 1,
            "last_game_id": None,
            "last_diagnosis_id": (get_user_progress(key[0], key[1]) or {}).get("last_diagnosis_id"),
        },
    )





    text = (
        "🤝 Больше контакта и доверия\n\n"
        "1️⃣ Маленький ритуал «5 минут только для нас».\n"
        "Каждый день выберите короткое время (например, перед сном), когда вы без телефонов "
        "и домашних дел просто рядом: можно поговорить, поиграть в простую игру или "
        "вспомнить что-то хорошее за день.\n\n"
        "2️⃣ Три вопроса вместо допроса.\n"
        "Вместо «Ну что там опять?» попробуйте: «Как у тебя прошёл день?», «Что было приятного?», "
        "«Что было трудного?» — и больше слушать, чем советовать.\n\n"
        "Почему это важно: регулярные тёплые, пусть и короткие моменты вместе укрепляют чувство "
        "безопасности и помогают ребёнку снова почувствовать, что рядом есть взрослый, которому можно доверять."
    )

    await callback.message.answer(
        text,
        reply_markup=get_more_steps_keyboard()
    )


@dp.callback_query(lambda c: c.data == "focus_conflicts")
async def focus_conflicts(callback: types.CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    state = get_user_state(user_id)
    state["focus"] = "conflicts"
    state["focus_step"] = 3
    set_user_state(user_id, state)

    child_name = state.get("child_name")
    key = (user_id, child_name)

    set_user_progress(
        key[0],
        key[1],
        {
            "focus": "conflicts",
            "step": 1,
            "last_game_id": None,
            "last_diagnosis_id": (get_user_progress(key[0], key[1]) or {}).get("last_diagnosis_id"),
        },
    )




    text = (
        "🕊 Меньше конфликтов и крика\n\n"
        "1️⃣ Пауза перед ответом.\n"
        "Когда хочется сразу накричать, попробуйте сначала сделать вдох и мысленно досчитать до 5. "
        "Если получается, проговорите вслух: «Я сейчас очень злюсь, мне нужно пару секунд, чтобы успокоиться».\n\n"
        "2️⃣ Я‑сообщение вместо обвинений.\n"
        "Вместо «Ты опять меня выводишь!» попробуйте: «Я злюсь, когда вижу разбросанные вещи, "
        "мне важно, чтобы мы договаривались и собирали их вместе».\n\n"
        "Почему это важно: когда мы говорим о своих чувствах и правилах, а не «нападаем» на ребёнка, "
        "ему проще слышать и меньше хочется защищаться и вступать в борьбу."
    )

    await callback.message.answer(
        text,
        reply_markup=get_more_steps_keyboard()
    )


@dp.callback_query(lambda c: c.data == "focus_selfcare")
async def focus_selfcare(callback: types.CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    state = get_user_state(user_id)
    state["focus"] = "selfcare"
    state["focus_step"] = 3
    set_user_state(user_id, state)

    child_name = state.get("child_name")
    key = (user_id, child_name)
    set_user_progress(
        key[0],
        key[1],
        {
            "focus": "self_help",  # как и было, чтобы совпадало с continue_route
            "step": 1,
            "last_game_id": None,
            "last_diagnosis_id": (get_user_progress(key[0], key[1]) or {}).get("last_diagnosis_id"),
        },
    )

    text = (
        "💚 Больше опоры для себя\n\n"
        "1️⃣ Один маленький жест заботы каждый день.\n"
        "Выберите что‑то очень посильное: выпить воду, пару минут посидеть в тишине, "
        "сделать пару шагов на улице, лечь спать чуть раньше. Не надо сразу больших изменений.\n\n"
        "2️⃣ Остановка самокритики.\n"
        "Когда ловите себя на мыслях «я ужасный родитель», попробуйте заменить: "
        "«Мне сейчас очень тяжело, но я уже ищу способы помочь себе и ребёнку».\n\n"
        "Почему это важно: когда у родителя появляется чуть больше ресурса и меньше самокритики, "
        "ему легче оставаться спокойным и поддерживающим, а значит — отношения с ребёнком постепенно меняются."
    )

    await callback.message.answer(
        text,
        reply_markup=get_more_steps_keyboard()
    )


@dp.callback_query(lambda c: c.data == "focus_games_current")
async def focus_games_current(callback: types.CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    state = get_user_state(user_id)

    # Если по какой-то причине ещё нет подобранных игр
    if not state or "suitable_ids" not in state or not state["suitable_ids"]:
        await callback.message.answer(
            "Сначала давай подберём игры под твою ситуацию.\n\n"
            "Пройди мини‑диагностику и нажми «✅ Показать результат», "
            "чтобы я смог подобрать игры."
        )
        return

    # Сбрасываем индекс, чтобы начать показ игр с начала
    state["current_index"] = -1
    set_user_state(user_id, state)

    # Используем уже существующую логику показа игр
    await next_game(callback)


@dp.callback_query(lambda c: c.data == "focus_more_step")
async def focus_more_step(callback: types.CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    state = get_user_state(user_id)
    focus = state.get("focus")
    step = state.get("focus_step", 1)

    if not focus:
        await callback.message.answer("Давайте сначала выберем направление 🙂")
        await start_improve_clicked(callback)
        return

    # Если уже 10 шагов — стоп
    if step >= 10:
        await callback.message.answer(
            "Вы уже взяли достаточно шагов по этой теме.\n\n"
            "Попробуйте их в течение нескольких дней, а потом можно вернуться за новыми идеями."
        )
        return

    # Выдаём по два шага за раз: step и step+1, но не больше 10
    first_step = step
    second_step = min(step + 1, 10)

    parts = []

    # ----- ПРО КОНТАКТ -----
    if focus == "contact":
        if first_step == 3:
            parts.append(
                "3️⃣ «Маленькие заметки».\n"
                "Иногда оставляйте ребёнку короткие записки или сообщения: пару тёплых слов, "
                "поддержку перед важным днём, маленькое «я рядом».\n"
                "Это показывает, что вы помните о нём не только, когда что‑то не так."
            )
        if second_step == 4:
            parts.append(
                "4️⃣ «Правило трёх минут».\n"
                "При встрече (после школы, садика, возвращения домой) уделите ребёнку первые 3 минуты полностью: "
                "взгляд, объятие, пару вопросов — без телефонов и дел.\n"
                "Так он чувствует, что важен и замечен именно вами."
            )
        if first_step == 5:
            parts.append(
                "5️⃣ Делитесь собой.\n"
                "Иногда рассказывайте ребёнку о своём дне, чувствах и мыслях простыми словами.\n"
                "Когда взрослый делится собой, ребёнку легче открываться в ответ."
            )
        if second_step == 6:
            parts.append(
                "6️⃣ «А что было дальше?».\n"
                "Когда ребёнок что‑то рассказывает, поддерживайте разговор вопросами: "
                "«И что было потом?», «А как ты себя чувствовал(а)?», «Что тебе там понравилось?».\n"
                "Это помогает ему чувствовать ваше искреннее внимание."
            )
        if first_step == 7:
            parts.append(
                "7️⃣ Маленькие совместные дела.\n"
                "Выберите одно бытовое дело, которое будете иногда делать вместе (готовка, прогулка с собакой, "
                "поездка в магазин).\n"
                "Важно не качество дела, а возможность спокойно побыть рядом."
            )
        if second_step == 8:
            parts.append(
                "8️⃣ «Один на один».\n"
                "Если в семье несколько детей, попробуйте находить хотя бы немного времени побыть с каждым отдельно.\n"
                "Это снижает конкуренцию и даёт ребёнку опыт: «меня видят отдельно от брата/сестры»."
            )
        if first_step == 9:
            parts.append(
                "9️⃣ Называть чувства ребёнка.\n"
                "Пробуйте иногда вслух замечать: «Ты, кажется, расстроился», «Похоже, ты гордишься собой сейчас».\n"
                "Так ребёнок учится понимать себя и чувствует, что вы его эмоционально «считываете»."
            )
        if second_step == 10:
            parts.append(
                "🔟 Периодически говорить о любви напрямую.\n"
                "Даже подросткам важно слышать: «Я тебя люблю», «Ты важен для меня, даже когда мы ссоримся».\n"
                "Это создаёт внутреннюю опору, которую ребёнок берёт с собой во взрослую жизнь."
            )

    # ----- ПРО КОНФЛИКТЫ -----
    elif focus == "conflicts":
        if first_step == 3:
            parts.append(
                "3️⃣ Обсуждать конфликт позже, не в пике.\n"
                "Когда все немного отошли, вернитесь к ситуации и спокойно обсудите: что произошло, "
                "что каждый чувствовал, как можно в следующий раз сделать иначе.\n"
                "Так ребёнок учится анализировать, а не только вспыхивать."
            )
        if second_step == 4:
            parts.append(
                "4️⃣ «Стоп‑слово» для взрослого.\n"
                "Договоритесь с собой, что при внутреннем сигнале «стоп» вы делаете паузу и не продолжаете спор, "
                "а берёте время остыть.\n"
                "Лучше недосказать, чем сказать лишнего в сильной злости."
            )
        if first_step == 5:
            parts.append(
                "5️⃣ Отделять ребёнка от поступка.\n"
                "Вместо «Ты ужасный/ленивый/невоспитанный» — «Мне не подходит такой поступок», "
                "«Меня злит, когда вещи раскиданы».\n"
                "Это помогает не формировать у ребёнка ощущение «со мной всё плохо»."
            )
        if second_step == 6:
            parts.append(
                "6️⃣ Замечать хорошие моменты.\n"
                "Если ребёнок сделал что‑то по‑другому (убрал за собой, пришёл вовремя), "
                "отметьте это вслух: «Спасибо, мне это очень помогло».\n"
                "Позитивное подкрепление работает лучше, чем постоянные замечания."
            )
        if first_step == 7:
            parts.append(
                "7️⃣ Договариваться о правилах заранее.\n"
                "Выберите 1–2 важные вещи (например, гаджеты, сборы в школу) и обсудите, какие правила вы хотите "
                "сделать общими: что, когда, кто делает.\n"
                "Так меньше поводов для внезапных ссор."
            )
        if second_step == 8:
            parts.append(
                "8️⃣ Учить ребёнка говорить о себе, а не нападать.\n"
                "Можно предложить фразы: «Мне обидно, когда…», «Я злюсь, когда…».\n"
                "Это помогает решать конфликты словами, а не криками и ударами."
            )
        if first_step == 9:
            parts.append(
                "9️⃣ Разрядка через движение.\n"
                "Иногда полезно предложить безопасный способ выплеснуть напряжение: подушечные бои, "
                "побегать, потопать вместе.\n"
                "Это не отменяет разговора, но помогает сначала «снять пар»."
            )
        if second_step == 10:
            parts.append(
                "🔟 Общий «антиконфликтный» ритуал.\n"
                "Можно договориться, что после тяжёлой ссоры вы всё равно делаете что‑то маленькое вместе: "
                "чашка чая, обнимашки, короткий мультик.\n"
                "Это показывает: конфликты есть, но отношения всё равно важнее."
            )

    # ----- ПРО ЗАБОТУ О СЕБЕ -----
    elif focus == "selfcare":
        if first_step == 3:
            parts.append(
                "3️⃣ Маленький ежедневный вопрос к себе.\n"
                "В конце дня спросите: «Что я сегодня сделал(а) для себя, даже если это было совсем маленькое?».\n"
                "Это помогает замечать не только провалы, но и свои усилия."
            )
        if second_step == 4:
            parts.append(
                "4️⃣ «Одна вещь полегче».\n"
                "Посмотрите на свой день и подумайте, что можно сделать чуть менее тяжёлым: "
                "попросить помощи, сократить одно дело, отложить то, что не горит.\n"
                "Маленькое облегчение каждый день лучше, чем ждать идеального отпуска."
            )
        if first_step == 5:
            parts.append(
                "5️⃣ Планировать маленькие приятности заранее.\n"
                "Запланируйте на неделю 1–2 простых приятных вещи для себя (не для ребёнка): "
                "чай в тишине, прогулка, звонок близкому человеку.\n"
                "Когда это внесено в план, шансов, что вы себе это позволите, больше."
            )
        if second_step == 6:
            parts.append(
                "6️⃣ Ловить внутреннего критика.\n"
                "Когда в голове звучит «я всё делаю плохо», попробуйте заменить на: "
                "«Мне сейчас очень трудно, но я стараюсь настолько, насколько могу».\n"
                "Это снижает напряжение и даёт сил двигаться дальше."
            )
        if first_step == 7:
            parts.append(
                "7️⃣ Мини‑паузы в течение дня.\n"
                "Даже 30–60 секунд, чтобы сделать пару глубоких вдохов, посмотреть в окно или просто посидеть, "
                "помогают нервной системе чуть выдохнуть.\n"
                "Лучше несколько таких пауз, чем ждать, когда совсем «накроет»."
            )
        if second_step == 8:
            parts.append(
                "8️⃣ Отделять реальные обязанности от «должна быть идеальной».\n"
                "Иногда полезно спросить себя: «Кто мне это велел? Это правда обязательно или просто привычка быть идеальной?».\n"
                "Так постепенно становится легче снижать лишние требования к себе."
            )
        if first_step == 9:
            parts.append(
                "9️⃣ Замечать свои успехи как родителя.\n"
                "Раз в день попробуйте ответить на вопрос: «В чём я сегодня был(а) “достаточно хорошим” родителем?».\n"
                "Это помогает видеть не только ошибки, но и живые моменты близости и заботы."
            )
        if second_step == 10:
            parts.append(
                "🔟 Напоминание: вы не одни.\n"
                "Многие родители сталкиваются с похожими трудностями. Обращение за поддержкой — к партнёру, "
                "другу, специалисту — это не слабость, а забота о себе и о ребёнке."
            )
    else:
        parts.append("Пока нет дополнительных шагов для этого направления.")

    text = "\n\n".join(parts)

    # Обновляем номер шага: плюс 2, но не больше 10
    state["focus_step"] = min(step + 2, 10)
    set_user_state(user_id, state)

    # Обновляем step в user_progress
    child_name = state.get("child_name")
    if child_name:
        if user_progress_row_exists(user_id, child_name):
            prog = dict(get_user_progress(user_id, child_name) or {})
            prog["step"] = state["focus_step"]
            set_user_progress(user_id, child_name, prog)

    await callback.message.answer(
        text,
        reply_markup=get_more_steps_keyboard()
    )



@dp.callback_query(lambda c: c.data == "after_scenario_next")
async def after_scenario_next(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    state = get_user_state(user_id)

    if not state or "suitable_ids" not in state:
        await callback.answer("Сначала пройди мини‑диагностику 🙂", show_alert=True)
        return

    problem_map = {
        "prob_disobedience": "Непослушание",
        "prob_gadgets": "Гаджеты",
        "prob_silent": "Молчит",
        "prob_trust": "Нет доверия"
    }

    age_text = AGE_DISPLAY_MAP.get(state["age"], "неизвестный возраст")
    problems_codes = state.get("problems", [])
    suitable_ids = state.get("suitable_ids", [])

    if not suitable_ids:
        await callback.answer("Пока нет подходящих игр под этот запрос 😔", show_alert=True)
        return

    first_id = state.get("first_game_id", suitable_ids[0])
    game = next(g for g in GAMES if g["id"] == first_id)

    # Показываем карточку первой игры вместо сценария
    await show_game_card(callback.message, game, age_text, problems_codes, problem_map)




# Следующая игра
@dp.callback_query(lambda c: c.data == "next_game")
async def next_game(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    state = get_user_state(user_id)

    if not state or "suitable_ids" not in state:
        await callback.answer("Сначала подбери игры через «Показать результат» 🙂", show_alert=True)
        return

    problem_map = {
        "prob_disobedience": "Непослушание",
        "prob_gadgets": "Гаджеты",
        "prob_silent": "Молчит",
        "prob_trust": "Нет доверия"
    }

    age_text = AGE_DISPLAY_MAP.get(state["age"], "неизвестный возраст")
    problems_codes = state.get("problems", [])
    ids = state["suitable_ids"]
    idx = state.get("current_index", 0)

    idx = (idx + 1) % len(ids)
    state["current_index"] = idx
    set_user_state(user_id, state)

    game_id = ids[idx]
    game = next(g for g in GAMES if g["id"] == game_id)

    await show_game_card(callback.message, game, age_text, problems_codes, problem_map)

@dp.callback_query(lambda c: c.data.startswith("played_"))
async def mark_game_played(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data  # played_2
    try:
        game_id = int(data.split("_")[1])
    except (IndexError, ValueError):
        await callback.answer("Не получилось сохранить результат игры 😔", show_alert=True)
        return

    # Сохраняем game_id во временное хранилище, чтобы потом использовать в опросе
    st = dict(get_user_state(user_id))
    st["current_game_id"] = game_id
    st["current_game_status"] = "played"
    set_user_state(user_id, st)

    # Показываем вопрос вместо сразу сохранения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👍 Понравилось", callback_data=f"rating_liked_{game_id}"),
            InlineKeyboardButton(text="👎 Не понравилось", callback_data=f"rating_disliked_{game_id}")
        ]
    ])

    await callback.answer()
    await callback.message.edit_text(
        "Как прошла игра? Понравилась ли вам?",
        reply_markup=keyboard
    )
@dp.callback_query(lambda c: c.data.startswith("rating_liked_"))
async def rating_liked(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data  # rating_liked_2
    try:
        game_id = int(data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("Ошибка при обработке выбора", show_alert=True)
        return

    # Сохраняем рейтинг
    st = dict(get_user_state(user_id))
    st["current_game_rating"] = "liked"
    set_user_state(user_id, st)

    # Показываем вопрос о причине
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Интересная игра", callback_data=f"reason_interesting_{game_id}")],
        [InlineKeyboardButton(text="Помогла наладить контакт", callback_data=f"reason_contact_{game_id}")],
        [InlineKeyboardButton(text="Было смешно и весело", callback_data=f"reason_fun_{game_id}")],
        [InlineKeyboardButton(text="Просто зашла", callback_data=f"reason_liked_{game_id}")],
    ])

    await callback.answer()
    await callback.message.edit_text(
        "Что понравилось в игре?",
        reply_markup=keyboard
    )


@dp.callback_query(lambda c: c.data.startswith("rating_disliked_"))
async def rating_disliked(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data  # rating_disliked_2
    try:
        game_id = int(data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("Ошибка при обработке выбора", show_alert=True)
        return

    # Сохраняем рейтинг
    st = dict(get_user_state(user_id))
    st["current_game_rating"] = "disliked"
    set_user_state(user_id, st)

    # Показываем вопрос о причине
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Не интересна ребёнку", callback_data=f"reason_boring_{game_id}")],
        [InlineKeyboardButton(text="Слишком сложная", callback_data=f"reason_hard_{game_id}")],
        [InlineKeyboardButton(text="Не помогает в нашей ситуации", callback_data=f"reason_useless_{game_id}")],
        [InlineKeyboardButton(text="Просто не зашла", callback_data=f"reason_disliked_{game_id}")],
    ])

    await callback.answer()
    await callback.message.edit_text(
        "Что не понравилось в игре?",
        reply_markup=keyboard
    )
@dp.callback_query(lambda c: c.data.startswith("reason_"))
async def save_game_feedback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data  # reason_interesting_2

    try:
        reason_key = "_".join(data.split("_")[1:-1])  # interesting, contact, fun, etc.
        game_id = int(data.split("_")[-1])
    except (IndexError, ValueError):
        await callback.answer("Ошибка при сохранении отзыва", show_alert=True)
        return

    state = get_user_state(user_id)
    status = state.get("current_game_status", "played")
    rating = state.get("current_game_rating", "liked")

    # Переводим code причины в читаемый текст
    reason_map = {
        # Для "played" (понравилось)
        "interesting": "Интересная игра",
        "contact": "Помогла наладить контакт",
        "fun": "Было смешно и весело",
        "liked": "Просто зашла",
        # Для "played" (не понравилось)
        "boring": "Не интересна ребёнку",
        "hard": "Слишком сложная",
        "useless": "Не помогает в нашей ситуации",
        "disliked": "Просто не зашла",
        # Для "not_played" (попробуем в следующий раз)
        "mood": "Ребёнок был не в настроении",
        "notime": "Не было времени",
        "forgot": "Забыли про игру",
        "later": "Просто не вышло сейчас",
        # Для "not_played" (не подходит)
        "age": "Возраст ребёнка не подходит",
        "problem": "Наша проблема в другом",
        "dull": "Слишком скучная",
        "notsuit": "Не подходит нам вообще",
    }

    reason_text = reason_map.get(reason_key, "Без причины")

    # Сохраняем в журнал
    journal = get_user_games_journal(user_id)
    journal.append({
        "game_id": game_id,
        "status": status,
        "rating": rating,
        "reason": reason_text,
        "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
    })
    set_user_games_journal(user_id, journal)

    # Очищаем временные данные
    st = dict(get_user_state(user_id))
    st["current_game_id"] = None
    st["current_game_status"] = None
    st["current_game_rating"] = None
    set_user_state(user_id, st)

    await callback.answer()
    await callback.message.edit_text(
        "✅ Спасибо за отзыв! Я записал это в журнал.\n\n"
        "Вот ещё несколько игр под вашу ситуацию 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Следующая игра", callback_data="next_game")],
            [InlineKeyboardButton(text="⭐ Мои игры", callback_data="show_favorites")],
            [InlineKeyboardButton(text="🔙 К проблемам", callback_data="back_to_start")]
        ])
    )


@dp.callback_query(lambda c: c.data.startswith("not_played_"))
async def mark_game_not_played(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data  # not_played_2
    try:
        game_id = int(data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("Не получилось сохранить результат игры 😔", show_alert=True)
        return

    # Сохраняем game_id во временное хранилище
    st = dict(get_user_state(user_id))
    st["current_game_id"] = game_id
    st["current_game_status"] = "not_played"
    set_user_state(user_id, st)

    # Показываем вопрос вместо сразу сохранения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👍 В следующий раз попробуем", callback_data=f"rating_retry_{game_id}"),
            InlineKeyboardButton(text="👎 Не подходит нам", callback_data=f"rating_skip_{game_id}")
        ]
    ])

    await callback.answer()
    await callback.message.edit_text(
        "Понимаю, что не получилось сейчас.\n\n"
        "Вернёмся к этой игре потом или лучше пропустить?",
        reply_markup=keyboard
    )


# Добавить в избранное
@dp.callback_query(lambda c: c.data.startswith("fav_"))
async def add_to_favorites(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data  # "fav_2"
    try:
        game_id = int(data.split("_")[1])
    except (IndexError, ValueError):
        await callback.answer("Не удалось сохранить игру 😔", show_alert=True)
        return

    favs = set(get_user_favorites(user_id))
    favs.add(game_id)
    set_user_favorites(user_id, favs)
    await callback.answer("💾 Игра сохранена в избранное!", show_alert=False)

@dp.callback_query(lambda c: c.data.startswith("rating_retry_"))
async def rating_retry(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data  # rating_retry_2
    try:
        game_id = int(data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("Ошибка при обработке выбора", show_alert=True)
        return

    # Сохраняем выбор
    st = dict(get_user_state(user_id))
    st["current_game_rating"] = "retry"
    set_user_state(user_id, st)

    # Показываем вопрос о причине
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ребёнок был не в настроении", callback_data=f"reason_mood_{game_id}")],
        [InlineKeyboardButton(text="Не было времени", callback_data=f"reason_notime_{game_id}")],
        [InlineKeyboardButton(text="Забыли про игру", callback_data=f"reason_forgot_{game_id}")],
        [InlineKeyboardButton(text="Просто не вышло сейчас", callback_data=f"reason_later_{game_id}")],
    ])

    await callback.answer()
    await callback.message.edit_text(
        "Что помешало в этот раз?",
        reply_markup=keyboard
    )


@dp.callback_query(lambda c: c.data.startswith("rating_skip_"))
async def rating_skip(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data  # rating_skip_2
    try:
        game_id = int(data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("Ошибка при обработке выбора", show_alert=True)
        return

    # Сохраняем выбор
    st = dict(get_user_state(user_id))
    st["current_game_rating"] = "skip"
    set_user_state(user_id, st)

    # Показываем вопрос о причине
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Возраст ребёнка не подходит", callback_data=f"reason_age_{game_id}")],
        [InlineKeyboardButton(text="Наша проблема в другом", callback_data=f"reason_problem_{game_id}")],
        [InlineKeyboardButton(text="Слишком скучная", callback_data=f"reason_dull_{game_id}")],
        [InlineKeyboardButton(text="Не подходит нам вообще", callback_data=f"reason_notsuit_{game_id}")],
    ])

    await callback.answer()
    await callback.message.edit_text(
        "Почему не подходит?",
        reply_markup=keyboard
    )

@dp.message()
async def handle_child_name_or_other(message: Message):
    """
    Универсальный обработчик текстовых сообщений.
    Если ждём имя ребёнка — сохраняем его и предлагаем выбрать возраст.
    """

    user_id = message.from_user.id
    state = get_user_state(user_id)

    # Если мы НЕ ждём сейчас имя ребёнка — можно просто ничего не делать или обработать по-другому
    if not state.get("awaiting_child_name"):
        return

    child_name = message.text.strip()

    if not child_name:
        await message.answer("Имя не получилось прочитать. Напишите, пожалуйста, ещё раз.")
        return

    # Сохраняем имя во временное состояние
    state["awaiting_child_name"] = False
    state["new_child_name"] = child_name
    set_user_state(user_id, state)

    # Показываем выбор возрастной группы для этого ребёнка
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👶 2–5 лет", callback_data="new_child_age_2_5"),
                InlineKeyboardButton(text="👦 6–7 лет", callback_data="new_child_age_6_7"),
            ],
            [
                InlineKeyboardButton(text="👧 7–10 лет", callback_data="new_child_age_7_10"),
                InlineKeyboardButton(text="🧒 10–12 лет", callback_data="new_child_age_10_12"),
            ],
            [
                InlineKeyboardButton(text="🎓 Подросток", callback_data="new_child_age_teen"),
            ],
        ]
    )

    await message.answer(
        f"Отлично, запомнил ребёнка по имени {child_name}.\n\n"
        "Теперь выберите возрастную категорию:",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data.startswith("new_child_age_"))
async def set_new_child_age(callback: types.CallbackQuery):
    """
    Шаг 3: сохраняем профиль ребёнка (имя + возраст) и возвращаемся к выбору.
    """

    await callback.answer()

    user_id = callback.from_user.id
    state = get_user_state(user_id)

    child_name = state.get("new_child_name")
    if not child_name:
        await callback.message.edit_text(
            "Не получилось найти имя ребёнка. Попробуйте добавить ребёнка ещё раз через меню диагностики."
        )
        return

    # Из callback_data достаём age_code
    data = callback.data  # например, "new_child_age_7_10"
    age_code = "age_" + "_".join(data.split("_")[3:])  # превращаем в "age_7_10"

    # Сохраняем профиль ребёнка
    user_children = get_children(user_id)

    user_children.append({
        "name": child_name,
        "age_code": age_code,
    })
    set_children(user_id, user_children)

    # Очищаем временное поле
    state["new_child_name"] = None
    set_user_state(user_id, state)

    # Возвращаемся на экран выбора ребёнка
    buttons = []
    for idx, child in enumerate(user_children):
        name = child.get("name", f"Ребёнок #{idx + 1}")
        age_label = AGE_LABELS.get(child.get("age_code"), "возраст не указан")
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{name} ({age_label})",
                    callback_data=f"select_child_{idx}"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="➕ Добавить ребёнка",
                callback_data="add_child"
            )
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text="🔙 В главное меню",
                callback_data="back_to_main"
            )
        ]
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        "Ребёнок добавлен.\n\n"
        "Теперь выберите, для кого будем проходить диагностику:",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data.startswith("select_child_"))
async def select_child(callback: types.CallbackQuery):
    """
    Выбор ребёнка из списка перед диагностикой.
    Кладём имя и возраст ребёнка в user_state и запускаем первый экран диагностики.
    """

    await callback.answer()

    user_id = callback.from_user.id
    user_children = get_children(user_id)

    data = callback.data  # например, "select_child_0"
    try:
        idx = int(data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.message.answer("Не получилось понять, какого ребёнка вы выбрали 😔")
        return

    if idx < 0 or idx >= len(user_children):
        await callback.message.answer("Похоже, этого ребёнка в списке уже нет.")
        return

    child = user_children[idx]
    child_name = child.get("name", f"Ребёнок #{idx + 1}")
    age_code = child.get("age_code")

    # Обновляем состояние пользователя: выбираем ребёнка и сбрасываем предыдущие ответы диагностики
    set_user_state(
        user_id,
        {
            "child_name": child_name,
            "age": age_code,
            "child_behaviour": [],
            "parent_state": [],
            "family_dynamic": [],
            "current_index": 0,
            "diag_done": False,
        },
    )

    # Сразу запускаем первый экран мини-диагностики (как раньше после выбора возраста)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Много ссор и крика дома", callback_data="diag_main_conflicts")],
        [InlineKeyboardButton(text="📱 Постоянно в телефоне / гаджетах", callback_data="diag_main_gadgets")],
        [InlineKeyboardButton(text="🤐 Замкнулся, мало говорит", callback_data="diag_main_silent")],
        [InlineKeyboardButton(text="💔 Стало меньше доверия и тепла", callback_data="diag_main_trust")],
        [InlineKeyboardButton(text="⏭ Пропустить вопросы и выбрать самой", callback_data="diag_skip")],
    ])

    await callback.message.edit_text(
        f"Отлично, сейчас будем смотреть ситуацию с ребёнком: {child_name}.\n\n"
        "Сначала чуть лучше поймём, *что больше всего про вашего ребёнка сейчас*.\n\n"
        "Выберите то, что отзывается сильнее всего:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )



# /my_games — список избранного
@dp.message(lambda m: m.text == "/my_games")
async def show_my_games(message: Message):
    user_id = message.from_user.id
    fav_ids = get_user_favorites(user_id)

    if not fav_ids:
        await message.answer(
            "У тебя пока нет сохранённых игр.\n"
            "Сохрани любую, нажав «💾 В избранное» на карточке игры."
        )
        return

    fav_games = [g for g in GAMES if g["id"] in fav_ids]

    lines = ["💾 Твои сохранённые игры:\n"]
    for game in fav_games:
        lines.append(f"{game['id']}. {game['title']}")

    lines.append("\nЧтобы вернуться к выбору игр, нажми /start.")

    await message.answer("\n".join(lines))

@dp.message(lambda m: m.text == "/history")
async def show_history(message: Message):
    user_id = message.from_user.id
    history = get_user_history(user_id)

    if not history:
        await message.answer(
            "У тебя пока нет сохранённых диагностик.\n"
            "Пройди мини-диагностику — после неё я буду сохранять результаты."
        )
        return

    lines = ["🧾 Твои диагностики:\n"]
    for idx, record in enumerate(history, start=1):
        age = record.get("age")
        age_label = AGE_LABELS.get(age, age) if age else "возраст не указан"

        created_at = record.get("created_at", "")  # берём дату/время, если есть

        behaviours = record.get("child_behaviour", [])
        parent_states = record.get("parent_state", [])
        family_dyn = record.get("family_dynamic", [])

        if created_at:
            lines.append(f"{idx}. {created_at} — возраст: {age_label}")
        else:
            lines.append(f"{idx}. Возраст: {age_label}")
        if behaviours:
            labels = [BEHAVIOUR_LABELS.get(c, c) for c in behaviours]
            lines.append("   • Поведение: " + ", ".join(labels))
        if parent_states:
            labels = [PARENT_STATE_LABELS.get(c, c) for c in parent_states]
            lines.append("   • Состояние родителя: " + ", ".join(labels))
        if family_dyn:
            labels = [FAMILY_DYNAMIC_LABELS.get(c, c) for c in family_dyn]
            lines.append("   • Семейная картина: " + ", ".join(labels))
        lines.append("")

    await message.answer("\n".join(lines))

@dp.callback_query(lambda c: c.data.startswith("repeat_diag_"))
async def repeat_diagnostics(callback: types.CallbackQuery):
    """
    Запуск повторной диагностики на основе выбранной записи из истории.

    Логика:
    - достаём запись истории;
    - пытаемся найти ребёнка в профилях по имени и возрасту;
    - если нашли — сразу запускаем диагностику на этого ребёнка;
    - если нет — показываем старый экран выбора возраста.
    """
    await callback.answer()
    user_id = callback.from_user.id
    history = get_user_history(user_id)
    data = callback.data
    try:
        index = int(data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.message.answer("Не получилось понять, какую диагностику повторить 😔")
        return

    if index < 0 or index >= len(history):
        await callback.message.answer("Похоже, этой записи в истории уже нет.")
        return

    record = history[index]
    child_name = record.get("child_name")
    age_code = record.get("age")

    state = get_user_state(user_id)
    state["repeat_history_index"] = index
    state["repeat_child_name"] = child_name
    state["repeat_age"] = age_code
    set_user_state(user_id, state)

    # Пытаемся найти ребёнка в профилях пользователя
    user_children = get_children(user_id)
    matched_child_index = None
    if child_name and age_code and user_children:
        for idx, child in enumerate(user_children):
            if (
                child.get("name") == child_name
                and child.get("age_code") == age_code
            ):
                matched_child_index = idx
                break

    # Если совпадение нашли — запускаем диагностику сразу на этого ребёнка
    if matched_child_index is not None:
        # сохраняем выбранного ребёнка в состоянии
        state = get_user_state(user_id)
        state["child_name"] = child_name
        state["age"] = age_code
        state["diag_done"] = False
        state.setdefault("child_behaviour", [])
        state.setdefault("parent_state", [])
        state.setdefault("family_dynamic", [])
        state["current_index"] = 0
        set_user_state(user_id, state)

        # показываем первый экран мини‑диагностики (как после выбора возраста)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏠 Много ссор и крика дома",
                    callback_data="diag_main_conflicts"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📱 Постоянно в телефоне / гаджетах",
                    callback_data="diag_main_gadgets"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🤐 Замкнулся, мало говорит",
                    callback_data="diag_main_silent"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💔 Стало меньше доверия и тепла",
                    callback_data="diag_main_trust"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏭ Пропустить вопросы и выбрать самой",
                    callback_data="diag_skip"
                )
            ],
        ])

        await callback.message.edit_text(
            f"Повторная диагностика для ребёнка {child_name}.\n\n"
            "Сейчас снова посмотрим, что больше всего про него:\n\n"
            "Выберите то, что откликается сильнее всего:",
            reply_markup=keyboard
        )
        return

    # Если ребёнка по имени+возрасту не нашли — возвращаемся к старому сценарию
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👶 2–5 лет", callback_data="age_2_5"),
                InlineKeyboardButton(text="👦 6–7 лет", callback_data="age_6_7"),
            ],
            [
                InlineKeyboardButton(text="👧 7–10 лет", callback_data="age_7_10"),
                InlineKeyboardButton(text="🧒 10–12 лет", callback_data="age_10_12"),
            ],
            [
                InlineKeyboardButton(text="🎓 Подросток", callback_data="age_teen"),
            ],
        ]
    )

    await callback.message.edit_text(
        "Повторная диагностика.\n\n"
        "Не удалось автоматически найти ребёнка по имени и возрасту.\n"
        "Сначала снова выберите возраст ребёнка:",
        reply_markup=keyboard
    )



def _build_journal_text(journal: list) -> str:
    total_games = len(journal)
    played = len([e for e in journal if e.get("status") == "played"])
    liked = len([e for e in journal if e.get("status") == "played" and e.get("rating") == "liked"])
    not_played = len([e for e in journal if e.get("status") == "not_played"])
    success_rate = int((liked / total_games * 100)) if total_games > 0 else 0

    lines = [
        "📘 Журнал игр:\n",
        "📊 Статистика:",
        f"  • Всего попробовали игр: {total_games}",
        f"  • Сыграли: {played}",
        f"  • Понравилось: {liked}",
        f"  • Не получилось сейчас: {not_played}",
        f"  • Процент успеха: {success_rate}%",
        "",
        "🎮 Подробный список:",
    ]
    for idx, entry in enumerate(journal, start=1):
        game_id = entry.get("game_id")
        status = entry.get("status")
        rating = entry.get("rating")
        reason = entry.get("reason", "")
        created_at = entry.get("created_at", "")
        game = next((g for g in GAMES if g["id"] == game_id), None)
        title = game["title"] if game else f"Игра {game_id}"
        if status == "played":
            emoji = "✅" if rating == "liked" else "❌"
            status_text = "сыграли, понравилось" if rating == "liked" else "сыграли, не понравилось"
        else:
            emoji = "⏸"
            status_text = "не получилось (попробуем позже)" if rating == "retry" else "не подходит нам"
        reason_text = f" — {reason}" if reason else ""
        date_text = f" ({created_at})" if created_at else ""
        lines.append(f"{idx}. {emoji} {title}")
        lines.append(f"   {status_text}{reason_text}{date_text}")
        lines.append("")
    return "\n".join(lines)


@dp.message(lambda m: m.text == "/journal")
async def show_journal(message: Message):
    user_id = message.from_user.id
    journal = get_user_games_journal(user_id)

    if not journal:
        await message.answer(
            "Пока журнал игр пуст.\n"
            "После каждой игры нажимай «✅ Мы сыграли» или «⏸ Не получилось», "
            "и я буду это записывать."
        )
        return

    text = _build_journal_text(journal)
    await message.answer(text)





# ⭐ Избранное — кнопка под /start
@dp.callback_query(lambda c: c.data == "show_favorites")
async def show_favorites_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    fav_ids = get_user_favorites(user_id)

    if not fav_ids:
        await callback.message.edit_text(
            "У тебя пока нет сохранённых игр.\n"
            "Сохрани любую, нажав «💾 В избранное» на карточке игры."
        )
        return

    fav_games = [g for g in GAMES if g["id"] in fav_ids]

    lines = ["💾 Твои сохранённые игры:\n"]
    for game in fav_games:
        lines.append(f"{game['id']}. {game['title']}")

    lines.append("\nЧтобы вернуться к выбору игр, нажми /start.")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")]
    ])

    await callback.message.edit_text("\n".join(lines), reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "continue_route")
async def continue_route(callback: types.CallbackQuery):
    """
    Обработчик кнопки «▶️ Продолжить» на главном экране.

    Логика очень простая:
    1) Смотрим, есть ли у пользователя прогресс в БД (user_progress).
    2) Если прогресса нет — мягко отправляем его к диагностике / выбору фокуса.
    3) Если прогресс есть:
       - смотрим, какой фокус выбран: contact / conflicts / self_help;
       - смотрим, на каком шаге он сейчас (step от 1 до 10);
       - в зависимости от этого показываем:
         а) если это самый первый шаг — текст первого шага по нужному фокусу;
         б) если уже есть focus_step в состоянии пользователя — просто вызываем логику выдачи следующих шагов (focus_more_step).
    """
    user_id = callback.from_user.id
    state = get_user_state(user_id)
    child_name = state.get("child_name")

    if not child_name:
        await callback.answer()
        await callback.message.answer(
            "Сначала выберите ребёнка и пройдите мини‑диагностику — "
            "после этого я смогу продолжить маршрут именно для него."
        )
        return

    key = (user_id, child_name)

    # 1. Проверяем, есть ли прогресс для этого ребёнка
    progress = get_user_progress(key[0], key[1])

    if not progress:
        await callback.answer()
        await callback.message.answer(
            f"Пока нет маршрута, который можно продолжить для ребёнка {child_name}. 🧭\n\n"
            "Сначала пройдите мини‑диагностику и выберите направление, "
            "а потом кнопка «▶️ Продолжить» будет вести дальше по шагам."
        )
        return

    focus = progress.get("focus")          # "contact", "conflicts" или "self_help"
    step_from_progress = progress.get("step", 1)

    # Достаём текущее состояние пользователя (там мы храним focus и focus_step)
    state = get_user_state(user_id)
    focus_in_state = state.get("focus")
    focus_step_in_state = state.get("focus_step")

    # Если в state ещё ничего не проставлено, синхронизируем его с user_progress
    if not focus_in_state:
        state["focus"] = focus
        state["focus_step"] = max(1, min(step_from_progress, 10))
        set_user_state(user_id, state)
        focus_step_in_state = state["focus_step"]

    # 2. Если шаг ещё совсем начальный (<=2), показываем первый блок шагов по фокусу
    if focus_step_in_state <= 2:
        await callback.answer()
        if focus == "contact":
            await focus_contact(callback)
        elif focus == "conflicts":
            await focus_conflicts(callback)
        elif focus == "self_help":
            await focus_selfcare(callback)
        else:
            await callback.message.answer(
                "Пока не удалось определить текущее направление. "
                "Попробуй заново выбрать фокус после мини‑диагностики."
            )
        return

    # 3. Если пользователь уже проходил первые шаги, предлагаем выбрать, как продолжить
    await callback.answer()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="▶️ Дальнейшие шаги",
                    callback_data="continue_steps"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎮 Игры под ситуацию",
                    callback_data="continue_games"
                ),
            ],
        ]
    )

    await callback.message.edit_text(
        "Как продолжим?\n\n"
        "▶️ Дальнейшие шаги — ещё 2 шага по выбранному направлению.\n"
        "🎮 Игры под ситуацию — сразу перейти к подходящим играм.",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "continue_steps")
async def continue_steps(callback: types.CallbackQuery):
    """
    Пользователь выбрал продолжать именно шаги.
    Просто вызываем уже существующую логику focus_more_step.
    """
    await callback.answer()
    await focus_more_step(callback)

@dp.callback_query(lambda c: c.data == "continue_games")
async def continue_games(callback: types.CallbackQuery):
    """
    Пользователь выбрал перейти к играм.
    Используем уже существующую логику показа следующей игры.
    """
    await callback.answer()
    await next_game(callback)




@dp.callback_query(lambda c: c.data == "show_history")
async def show_history(callback: types.CallbackQuery):
    """
    История диагностик по детям.

    Для каждой записи показываем:
    - имя ребёнка;
    - возрастную группу;
    - дату/время;
    - краткое резюме по количеству отмеченных пунктов;
    - отдельную кнопку «Повторить» для этой записи.
    """
    await callback.answer()
    user_id = callback.from_user.id
    history = get_user_history(user_id)

    if not history:
        await callback.message.edit_text(
            "Пока нет ни одной сохранённой диагностики.\n\n"
            "Сначала пройдите мини‑диагностику, а я запомню результат здесь."
        )
        return

    lines = ["🧾 Ваша история диагностик:\n"]
    keyboard_rows = []

    for index, record in enumerate(history):
        created_at = record.get("created_at", "неизвестная дата")
        child_name = record.get("child_name", "Ребёнок")
        age_code = record.get("age")
        age_label = AGE_LABELS.get(age_code, "возраст не указан") if age_code else "возраст не указан"

        cb_count = len(record.get("child_behaviour", []))
        ps_count = len(record.get("parent_state", []))
        fam_count = len(record.get("family_dynamic", []))

        # Основная строка — как в макете
        lines.append(
            f"{index + 1}. {child_name} · {age_label} · {created_at}"
        )
        # Вторая строка — краткое резюме по пунктам
        lines.append(
            f"   (поведение: {cb_count}, вы: {ps_count}, семья: {fam_count})"
        )

        keyboard_rows.append(
            [
                InlineKeyboardButton(
                    text=f"🔁 Повторить #{index + 1}",
                    callback_data=f"repeat_diag_{index}"
                )
            ]
        )

    keyboard_rows.append(
        [
            InlineKeyboardButton(
                text="🔙 В главное меню",
                callback_data="back_to_main"
            )
        ]
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=keyboard
    )


@dp.callback_query(lambda c: c.data == "show_journal_callback")
async def show_journal_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    journal = get_user_games_journal(user_id)

    if not journal:
        await callback.answer()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 На главную", callback_data="back_to_start")]
        ])
        await callback.message.edit_text(
            "Пока журнал игр пуст.\n\n"
            "После каждой игры нажимай «✅ Мы сыграли» или «⏸ Не получилось», "
            "и я буду это записывать.",
            reply_markup=keyboard
        )
        return

    text = _build_journal_text(journal)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 На главную", callback_data="back_to_start")]
    ])
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=keyboard)





@dp.callback_query(lambda c: c.data == "focus_games_direct")
async def focus_games_direct(callback: types.CallbackQuery):
    """Переход к играм по текущему фокусу — используем общую логику показа игр."""
    await callback.answer()
    await focus_games_current(callback)


# Кнопка «⬅️ Назад» из избранного — вернуться на /start
@dp.callback_query(lambda c: c.data == "back_to_start")
async def back_to_start(callback: types.CallbackQuery):
    await callback.answer()
    welcome_text = (
        "Привет! Я помогаю родителям через игры наладить контакт с ребёнком "
        "и сделать дома спокойнее.\n\nС чего начнём?"
    )
    await callback.message.answer(welcome_text, reply_markup=get_start_keyboard())


# Показ карточки игры (с «⭐ Мои игры»)
async def show_game_card(message, game, age_text, problems_codes, problem_map):
    lines = [
        f"{game['title']}",
        "",
        f"👶 Возраст: *{age_text}*"
    ]
    if problems_codes:
        lines.append("❗ Запросы: *" + ", ".join(problem_map[p] for p in problems_codes) + "*")
    lines.append("")
    lines.append(f"📌 {game['short']}")
    lines.append(f"⏱️ {game['time']}")
    lines.append("")
    lines.append("🧩 Как играть:")
    for step in game["howto"]:
        lines.append(f"• {step}")

    text = "\n".join(lines)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="💾 В избранное", callback_data=f"fav_{game['id']}"),
        InlineKeyboardButton(text="➡️ Следующая", callback_data="next_game")
    ],
    [
        InlineKeyboardButton(text="✅ Мы сыграли", callback_data=f"played_{game['id']}"),
        InlineKeyboardButton(text="⏸ Не получилось", callback_data=f"not_played_{game['id']}")
    ],
    [
        InlineKeyboardButton(text="🔙 К проблемам", callback_data="back_to_start"),
        InlineKeyboardButton(text="⭐ Мои игры", callback_data="show_favorites")
    ]
])


    await message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
