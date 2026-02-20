import random

def get_ai_settings(level: int):
    """
    AI controls display speed based on level
    """
    if level <= 3:
        return {"display_time": 1500}
    elif level <= 6:
        return {"display_time": 1200}
    else:
        return {"display_time": 900}

def generate_sequence(level: int):
    settings = get_ai_settings(level)

    # ALWAYS generate numbers from 0 to 100
    sequence = [random.randint(0, 100) for _ in range(level)]

    return sequence, settings

def ai_feedback(user_seq, correct_seq):
    if not user_seq:
        return "You didn’t enter anything. Try grouping numbers."

    if len(user_seq) < len(correct_seq):
        return "You missed some numbers. Try remembering in pairs."

    correct = sum(
        1 for i in range(min(len(user_seq), len(correct_seq)))
        if user_seq[i] == correct_seq[i]
    )

    if correct >= len(correct_seq) // 2:
        return "Good attempt! You remembered most of it."

    return "Try focusing on the middle numbers."

def ai_praise(level: int):
    messages = [
        "Excellent!",
        "You're doing great!",
        "Awesome memory!",
        "Nice work!",
        "Perfect!",
        "Keep it up!"
    ]

    if level >= 6:
        messages += [
            "Impressive focus!",
            "Your memory is sharp!"
        ]

    return random.choice(messages)
