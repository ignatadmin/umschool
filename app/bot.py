import os
from telebot import TeleBot, types
from sqlalchemy.orm import sessionmaker
from models import Base, Student, Subject, Score, engine

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = TeleBot(TOKEN)

Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        '''Cписок команд:
/register - Регистрация
/add - Добавить результат ЕГЭ
/view - Посмотреть свои баллы ЕГЭ'''
    )


@bot.message_handler(commands=['register'])
def register(message):
    msg = bot.send_message(message.chat.id, "Введите имя и фамилию через пробел:")
    bot.register_next_step_handler(msg, process_full_name_step)


def process_full_name_step(message):
    full_name = message.text.split()
    if len(full_name) != 2:
        bot.send_message(message.chat.id, "Ввод не корректен")
        return register(message)

    name, surname = full_name
    telegram_id = message.from_user.id

    session = Session()
    try:
        student = Student(name=name, surname=surname, telegram_id=telegram_id)
        session.add(student)
        session.commit()
        bot.send_message(message.chat.id, "Регистрация прошла успешно")
    finally:
        session.close()


@bot.message_handler(commands=['add'])
def enter_scores(message):
    session = Session()
    try:
        student = session.query(Student).filter_by(telegram_id=message.from_user.id).first()
        if not student:
            bot.send_message(message.chat.id, "Сначала зарегистрируйтесь с помощью команды /register")
            return

        subjects = session.query(Subject).all()
        keyboard = types.InlineKeyboardMarkup()

        for subject in subjects:
            keyboard.add(types.InlineKeyboardButton(subject.name, callback_data=f"subject_{subject.id}"))

        keyboard.add(types.InlineKeyboardButton("Добавить предмет", callback_data="add_new_subject"))

        bot.send_message(message.chat.id, "Выберите предмет:", reply_markup=keyboard)
    finally:
        session.close()


@bot.callback_query_handler(func=lambda call: call.data.startswith("subject_"))
def select_subject(call):
    subject_id = int(call.data.split("_")[1])
    msg = bot.send_message(call.message.chat.id, "Введите ваш балл:")
    bot.register_next_step_handler(msg, process_score_step, subject_id, call.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data == "add_new_subject")
def add_subject_inline(call):
    if call.from_user.id != int(os.getenv("SUPERUSER_ID")):
        bot.send_message(call.message.chat.id, "У вас недостаточно прав")
        return

    msg = bot.send_message(call.message.chat.id, "Введите название нового предмета:")
    bot.register_next_step_handler(msg, process_new_subject)


def process_new_subject(message):
    subject_name = message.text
    session = Session()
    try:
        existing_subject = session.query(Subject).filter_by(name=subject_name).first()
        if existing_subject:
            bot.send_message(message.chat.id, "Этот предмет уже существует")
            return

        subject = Subject(name=subject_name)
        session.add(subject)
        session.commit()
        bot.send_message(message.chat.id, "Предмет добавлен")
        enter_scores(message)
    finally:
        session.close()


def process_score_step(message, subject_id, telegram_id):
    try:
        score_value = int(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "Введите целое число")
        return

    session = Session()
    try:
        student = session.query(Student).filter_by(telegram_id=telegram_id).first()
        subject = session.query(Subject).get(subject_id)

        if not student or not subject:
            bot.send_message(message.chat.id, "Не удалось найти данные")
            return

        existing_score = session.query(Score).filter_by(student_id=student.id, subject_id=subject.id).first()
        if existing_score:
            bot.send_message(message.chat.id, "Вы уже добавили балл по этому предмету")
            return

        score = Score(student_id=student.id, subject_id=subject.id, score=score_value)
        session.add(score)
        session.commit()
        bot.send_message(message.chat.id, "Балл сохранён")
    finally:
        session.close()


@bot.message_handler(commands=['view'])
def view_scores(message):
    session = Session()
    try:
        student = session.query(Student).filter_by(telegram_id=message.from_user.id).first()
        if not student:
            bot.send_message(message.chat.id, "Сначала зарегистрируйтесь с помощью команды /register")
            return

        scores = session.query(Score).filter_by(student_id=student.id).all()
        if not scores:
            bot.send_message(message.chat.id, "У вас еще нет сохраненных баллов")
        else:
            scores_text = "\n".join([f"{score.subject.name}: {score.score}" for score in scores])
            bot.send_message(
                message.chat.id,
                f"Баллы ученика {student.name} {student.surname}:\n{scores_text}"
            )
    finally:
        session.close()


if __name__ == "__main__":
    bot.polling(none_stop=True)
