import os
from telebot import TeleBot
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
/enter_scores - добавить результат ЕГЭ
/view_scores - Посмотреть свои баллы ЕГЭ'''
    )

@bot.message_handler(commands=['register'])
def register(message):
    msg = bot.send_message(message.chat.id, "Введите ваше имя и фамилию через пробел:")
    bot.register_next_step_handler(msg, process_full_name_step)

def process_full_name_step(message):
    full_name = message.text.split()
    if len(full_name) != 2:
        bot.send_message(message.chat.id, "Пожалуйста, введите имя и фамилию через пробел.")
        return register(message)

    name, surname = full_name
    telegram_id = message.from_user.id

    msg = bot.send_message(message.chat.id, "Введите пароль:")
    bot.register_next_step_handler(msg, process_password_step, name, surname, telegram_id)

def process_password_step(message, name, surname, telegram_id):
    password = message.text
    session = Session()
    try:
        student = Student(name=name, surname=surname, password=password, telegram_id=telegram_id)
        session.add(student)
        session.commit()
        bot.send_message(message.chat.id, "Регистрация прошла успешно!")
    finally:
        session.close()

@bot.message_handler(commands=['enter_scores'])
def enter_scores(message):
    session = Session()
    try:
        student = session.query(Student).filter_by(telegram_id=message.from_user.id).first()
        if not student:
            bot.send_message(message.chat.id, "Сначала зарегистрируйтесь с помощью команды /register.")
            return

        msg = bot.send_message(message.chat.id, "Введите название предмета:")
        bot.register_next_step_handler(msg, process_subject_step, student)
    finally:
        session.close()

def process_subject_step(message, student):
    subject_name = message.text
    session = Session()
    try:
        subject = session.query(Subject).filter_by(name=subject_name).first()
        if not subject:
            subject = Subject(name=subject_name)
            session.add(subject)
            session.commit()

        msg = bot.send_message(message.chat.id, "Введите ваш балл:")
        bot.register_next_step_handler(msg, process_score_step, student, subject)
    finally:
        session.close()

def process_score_step(message, student, subject):
    score_value = int(message.text)
    session = Session()
    try:
        score = Score(student_id=student.id, subject_id=subject.id, score=score_value)
        session.add(score)
        session.commit()
        bot.send_message(message.chat.id, "Балл сохранён")
    finally:
        session.close()

@bot.message_handler(commands=['view_scores'])
def view_scores(message):
    session = Session()
    try:
        student = session.query(Student).filter_by(telegram_id=message.from_user.id).first()
        if not student:
            bot.send_message(message.chat.id, "Сначала зарегистрируйтесь с помощью команды /register.")
            return

        scores = session.query(Score).filter_by(student_id=student.id).all()
        if not scores:
            bot.send_message(message.chat.id, "У вас еще нет сохраненных баллов.")
        else:
            scores_text = "\n".join([f"{score.subject.name}: {score.score}" for score in scores])
            bot.send_message(message.chat.id, f"Ваши баллы:\n{scores_text}")
    finally:
        session.close()

if __name__ == "__main__":
    bot.polling(none_stop=True)
