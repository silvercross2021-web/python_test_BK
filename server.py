import json
from flask import Flask,render_template,request,redirect,flash,url_for


def loadClubs():
    with open('clubs.json') as c:
         listOfClubs = json.load(c)['clubs']
         return listOfClubs


def loadCompetitions():
    with open('competitions.json') as comps:
         listOfCompetitions = json.load(comps)['competitions']
         return listOfCompetitions


app = Flask(__name__)
app.secret_key = 'something_special'

competitions = loadCompetitions()
clubs = loadClubs()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/showSummary',methods=['POST'])
def showSummary():
    club = [club for club in clubs if club['email'] == request.form['email']][0]
    return render_template('welcome.html',club=club,competitions=competitions)


@app.route('/book/<competition>/<club>')
def book(competition,club):
    foundClub = [c for c in clubs if c['name'] == club][0]
    foundCompetition = [c for c in competitions if c['name'] == competition][0]
    if foundClub and foundCompetition:
        return render_template('booking.html',club=foundClub,competition=foundCompetition)
    else:
        flash("Something went wrong-please try again")
        return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/purchasePlaces',methods=['POST'])
def purchasePlaces():
    # ... (les premières lignes de la fonction restent les mêmes)
    competition = next((c for c in competitions if c.get('name') == request.form.get('competition')), None)
    club = next((c for c in clubs if c.get('name') == request.form.get('club')), None)
    
    # ... (la gestion des erreurs et la validation des places restent les mêmes)
    try:
        placesRequired = int(request.form.get('places', 0))
    except ValueError:
        flash('Nombre de places invalide.')
        return redirect(url_for('index'))

    if placesRequired <= 0:
        flash('Veuillez sélectionner au moins 1 place.')
        return redirect(url_for('index'))
        
    # --- DÉBUT DE LA CORRECTION ---
    
    # 1. On récupère le nombre de places actuel de la compétition.
    # On utilise int() pour le transformer en nombre afin de pouvoir le comparer.
    competition_places = int(competition.get('numberOfPlaces', 0))
    
    # 2. C'est la vérification clé : on compare les places demandées aux places disponibles.
    if placesRequired > competition_places:
        # 3. Si la demande est trop élevée, on bloque et on envoie un message d'erreur.
        flash(f"Action impossible : il ne reste que {competition_places} places disponibles.")
        # On retourne l'utilisateur sur la page de bienvenue pour qu'il voie les soldes actuels.
        return render_template('welcome.html', club=club, competitions=competitions)
        
    # --- FIN DE LA CORRECTION ---
    
    # Cette ligne n'est exécutée QUE SI la vérification ci-dessus a réussi.
    competition['numberOfPlaces'] = competition_places - placesRequired
    
    flash('Réservation réussie !')
    return render_template('welcome.html', club=club, competitions=competitions)

# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)