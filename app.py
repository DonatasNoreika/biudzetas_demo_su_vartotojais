import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

from flask_login import LoginManager, UserMixin, current_user, logout_user, login_user, login_required
from sqlalchemy import DateTime
from datetime import datetime
import forms

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = '4654f5dfadsrfasdr54e6rae'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'biudzetas.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'prisijungti'
login_manager.login_message_category = 'info'
login_manager.login_message = "Prisijunkite, jei norite matyti puslapį."

class Vartotojas(db.Model, UserMixin):
    __tablename__ = "vartotojas"
    id = db.Column(db.Integer, primary_key=True)
    vardas = db.Column("Vardas", db.String(20), unique=True, nullable=False)
    el_pastas = db.Column("El. pašto adresas", db.String(120), unique=True, nullable=False)
    slaptazodis = db.Column("Slaptažodis", db.String(60), unique=True, nullable=False)

class Irasas(db.Model):
    __tablename__ = "irasas"
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column("Data", DateTime, default=datetime.now())
    pajamos = db.Column("Pajamos", db.Boolean)
    suma = db.Column("Vardas", db.Integer)
    vartotojas_id = db.Column(db.Integer, db.ForeignKey("vartotojas.id"))
    vartotojas = db.relationship("Vartotojas", lazy=True)

@login_manager.user_loader
def load_user(vartotojo_id):
    db.create_all()
    return Vartotojas.query.get(int(vartotojo_id))


@app.route("/registruotis", methods=['GET', 'POST'])
def registruotis():
    db.create_all()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.RegistracijosForma()
    if form.validate_on_submit():
        koduotas_slaptazodis = bcrypt.generate_password_hash(form.slaptazodis.data).decode('utf-8')
        vartotojas = Vartotojas(vardas=form.vardas.data, el_pastas=form.el_pastas.data, slaptazodis=koduotas_slaptazodis)
        db.session.add(vartotojas)
        db.session.commit()
        flash('Sėkmingai prisiregistravote! Galite prisijungti', 'success')
        return redirect(url_for('index'))
    return render_template('registruotis.html', title='Register', form=form)

@app.route("/prisijungti", methods=['GET', 'POST'])
def prisijungti():
    db.create_all()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.PrisijungimoForma()
    if form.validate_on_submit():
        user = Vartotojas.query.filter_by(el_pastas=form.el_pastas.data).first()
        if user and bcrypt.check_password_hash(user.slaptazodis, form.slaptazodis.data):
            login_user(user, remember=form.prisiminti.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Prisijungti nepavyko. Patikrinkite el. paštą ir slaptažodį', 'danger')
    return render_template('prisijungti.html', title='Prisijungti', form=form)

@app.route("/atsijungti")
def atsijungti():
    logout_user()
    return redirect(url_for('index'))


@app.route("/paskyra")
@login_required
def account():
    return render_template('paskyra.html', title='Paskyra')

@app.route("/admin")
@login_required
def admin():
    return redirect(url_for(admin))


@app.route("/irasai")
@login_required
def records():
    db.create_all()
    try:
        visi_irasai = Irasas.query.filter_by(vartotojas_id=current_user.id).all()
    except:
        visi_irasai = []
    print(visi_irasai)
    return render_template("irasai.html", visi_irasai=visi_irasai, datetime=datetime)

@app.route("/naujas_irasas", methods=["GET", "POST"])
def new_record():
    db.create_all()
    forma = forms.IrasasForm()
    if forma.validate_on_submit():
        naujas_irasas = Irasas(pajamos=forma.pajamos.data, suma=forma.suma.data, vartotojas_id=current_user.id)
        db.session.add(naujas_irasas)
        db.session.commit()
        flash(f"Įrašas sukurtas", 'success')
        return redirect(url_for('records'))
    return render_template("prideti_irasa.html", form=forma)


@app.route("/delete/<int:id>")
def delete(id):
    irasas = Irasas.query.get(id)
    db.session.delete(irasas)
    db.session.commit()
    return redirect(url_for('records'))

@app.route("/update/<int:id>", methods=['GET', 'POST'])
def update(id):
    forma = forms.IrasasForm()
    irasas = Irasas.query.get(id)
    if forma.validate_on_submit():
        irasas.pajamos = forma.pajamos.data
        irasas.suma = forma.suma.data
        db.session.commit()
        return redirect(url_for('records'))
    return render_template("update.html", form=forma, irasas=irasas)

@app.route("/balansas")
def balance():
    try:
        visi_irasai = Irasas.query.filter_by(vartotojas_id=current_user.id)
    except:
        visi_irasai = []
    balansas = 0
    for irasas in visi_irasai:
        if irasas.pajamos:
            balansas += irasas.suma
        else:
            balansas -= irasas.suma
    return render_template("balansas.html", balansas=balansas)


@app.route("/")
def index():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
    db.create_all()