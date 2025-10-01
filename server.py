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
    competition = next((c for c in competitions if c.get('name') == request.form.get('competition')), None)
    club = next((c for c in clubs if c.get('name') == request.form.get('club')), None)
    
    if not competition or not club:
        flash('Erreur : Club ou compétition introuvable. Transaction annulée.')
        return redirect(url_for('index'))

    try:
        placesRequired = int(request.form.get('places', 0))
    except ValueError:
        flash('Nombre de places invalide.')
        return redirect(url_for('index'))

    if placesRequired <= 0:
        flash('Veuillez sélectionner au moins 1 place.')
        return redirect(url_for('index'))
    
        # --- NOUVELLE VÉRIFICATION AJOUTÉE ---
    if placesRequired > 12:
        flash("Action non autorisée : vous ne pouvez pas réserver plus de 12 places à la fois.")
        return render_template('welcome.html', club=club, competitions=competitions)
    # --- FIN DE L'AJOUT ---
        
    club_points = int(club.get('points', 0))
    competition_places = int(competition.get('numberOfPlaces', 0))

    # VÉRIFICATION 1 : Le club a-t-il assez de points ?
    if placesRequired > club_points:
        flash(f"Achat impossible. Vous n'avez que {club_points} points.")
        return render_template('welcome.html', club=club, competitions=competitions)

    # VÉRIFICATION 2 : Y a-t-il assez de places ?
    if placesRequired > competition_places:
        flash(f"Action impossible : il ne reste que {competition_places} places disponibles.")
        return render_template('welcome.html', club=club, competitions=competitions)
        
    # --- DÉBUT DE LA CORRECTION ---
    # Si toutes les vérifications ci-dessus ont réussi, ALORS on fait la transaction.
    # Cette section est maintenant au bon endroit.
    
    club['points'] = str(club_points - placesRequired)
    competition['numberOfPlaces'] = str(competition_places - placesRequired)
    
    # --- FIN DE LA CORRECTION ---
    
    flash('Réservation réussie ! Vos points ont été déduits.')
    return render_template('welcome.html', club=club, competitions=competitions)

# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)