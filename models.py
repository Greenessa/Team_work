import requests
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Candidates(Base):
    __tablename__ = "candidates"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(40), index=True)
    fam_name: so.Mapped[str] = so.mapped_column(sa.String(40), index=True)
    city: so.Mapped[str] = so.mapped_column(sa.String(40), index=True)
    user_id: so.Mapped[int]
    age: so.Mapped[int]
    gender: so.Mapped[str] = so.mapped_column(sa.String(10), index=True)
    vk_id: so.Mapped[int] = so.mapped_column(unique=True, nullable=False)
    vk_url: so.Mapped[str] = so.mapped_column(sa.String(200), index=True, unique=True, nullable=False)

    def __str__(self):
        return f"{self.id}: {self.name} {self.fam_name} {self.city} {self.age} {self.gender} {self.vk_url}"
    # homeworks = relationship("Homework", back_populates="course")


class Photos(Base):
    __tablename__ = "photos"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    candidate_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("candidates.vk_id"), nullable=False)
    photo_url: so.Mapped[str] = so.mapped_column(sa.String(1000), index=True, unique=True, nullable=False)
    cand: so.Mapped['Candidates'] = so.relationship(backref='photos')

    def __str__(self):
        return f"{self.id}: {self.candidate_id} {self.photo_url} "


# Таблица с информацией о кандидатах: True - в списке избранных, False - в черном списке, None - остальные кандидаты
class Flag(Base):
    __tablename__ = "flag"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    cand_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("candidates.id"), nullable=False, unique=True)
    flag: so.Mapped[bool]
    candidate: so.Mapped['Candidates'] = so.relationship(backref='flag')

    def __str__(self):
        return f"{self.id}: {self.cand_id} {self.flag} "


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

