from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False)

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            # do not serialize the password, its a security breach
        }


class People(db.Model):
    __tablename__ = 'people'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    gender: Mapped[str] = mapped_column(String(40), nullable=True)
    birth_year: Mapped[str] = mapped_column(String(40), nullable=True)
    height: Mapped[str] = mapped_column(String(40), nullable=True)

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "birth_year": self.birth_year,
            "height": self.height,
        }


class Planet(db.Model):
    __tablename__ = 'planets'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    climate: Mapped[str] = mapped_column(String(120), nullable=True)
    population: Mapped[str] = mapped_column(String(120), nullable=True)

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "climate": self.climate,
            "population": self.population,
        }


class Favorite(db.Model):
    __tablename__ = 'favorite'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey('user.id'), nullable=False)
    planet_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey('planets.id'), nullable=True)
    people_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey('people.id'), nullable=True)

    user = db.relationship('User', backref=db.backref('favorites', lazy=True))
    planet = db.relationship(
        'Planet', backref=db.backref('favorited_by', lazy=True))
    people = db.relationship(
        'People', backref=db.backref('favorited_by', lazy=True))

    def serialize(self):
        data = {
            "id": self.id,
            "user_id": self.user_id,
        }
        if self.planet_id is not None:
            data.update({"planet": self.planet.serialize()
                        if self.planet else None})
        if self.people_id is not None:
            data.update({"people": self.people.serialize()
                        if self.people else None})
        return data
