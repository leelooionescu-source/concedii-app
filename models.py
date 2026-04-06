from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Angajat(db.Model):
    __tablename__ = 'angajati'
    id = db.Column(db.Integer, primary_key=True)
    nume = db.Column(db.String(100), nullable=False)
    prenume = db.Column(db.String(100), nullable=False)
    data_angajare = db.Column(db.Date, nullable=True)
    zile_co_an = db.Column(db.Integer, default=21)
    departament = db.Column(db.String(100), default='')
    activ = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    concedii = db.relationship('Concediu', backref='angajat', lazy=True, cascade='all, delete-orphan')

    @property
    def nume_complet(self):
        return f"{self.nume} {self.prenume}"

    def __repr__(self):
        return f'<Angajat {self.nume} {self.prenume}>'


class Concediu(db.Model):
    __tablename__ = 'concedii'
    id = db.Column(db.Integer, primary_key=True)
    angajat_id = db.Column(db.Integer, db.ForeignKey('angajati.id'), nullable=False)
    data_start = db.Column(db.Date, nullable=False)
    data_sfarsit = db.Column(db.Date, nullable=False)
    tip = db.Column(db.String(20), nullable=False, default='CO')  # CO, MEDICAL, FARA_PLATA, EVENIMENT
    zile_lucratoare = db.Column(db.Integer, nullable=False)
    observatii = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Concediu {self.angajat.nume_complet} {self.data_start}-{self.data_sfarsit}>'


class SarbatoareLegala(db.Model):
    __tablename__ = 'sarbatori_legale'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    denumire = db.Column(db.String(200), nullable=False)
    an = db.Column(db.Integer, nullable=False)
