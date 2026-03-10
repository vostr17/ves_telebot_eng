"""Модели для базы данных телебота"""

import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()



""" Класс 'Пользователь' """
class User(Base):
    __tablename__ = 'user'
    id = sq.Column(sq.Integer, primary_key=True)
    """Имя пользователя"""
    name = sq.Column(sq.String(100), nullable=True)
    """Идентификатор пользователя в Телеграмм"""
    user_id = sq.Column(sq.BIGINT, nullable=False)

    def __str__(self):
        return f'User {self.id} ({self.name}: {self.user_id})'



""" Класс 'База данных со словами' """
class DataBaseWords(Base):
    __tablename__ = 'db_words'
    id = sq.Column(sq.Integer, primary_key=True)
    """Перевод слова"""
    rus_word = sq.Column(sq.String(length=50), nullable=False)
    """Английское слово"""
    eng_word = sq.Column(sq.String(length=50), nullable=False)
    """Идентификатор пользователя, кто добавил это слово"""
    user_id = sq.Column(sq.Integer, sq.ForeignKey('user.id'), nullable=False)

    user = relationship(User, backref="dbw")

    def __str__(self):
        return f'Word {self.id}: "{self.rus_word}" - "{self.eng_word}" (user = {self.user_id})'



""" Класс 'Логирование бота'"""
class BotLogger(Base):
    __tablename__ = 'bot_logger'
    id = sq.Column(sq.Integer, primary_key=True)
    date_time = sq.Column(sq.DateTime, nullable=False)
    user_id = sq.Column(sq.BIGINT, nullable=False)
    rus_word = sq.Column(sq.String(length=50), nullable=False)
    operation = sq.Column(sq.String(length=5), nullable=False)
    status = sq.Column(sq.BOOLEAN, nullable=False)
    def __str__(self):
        return f'Log date {self.date} - {self.user_id} - {self.rus_word} - {self.operation} - {self.status}'



def create_tables(engine):
    #Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)