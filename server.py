import json
from flask import Flask,render_template,request,redirect,flash,url_for
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent
def loadClubs():
    with open(BASE_DIR / 'clubs.json', encoding='utf-8') as c:
         listOfClubs = json.load(c)['clubs']
         return listOfClubs


def loadCompetitions():
    with open(BASE_DIR / 'competitions.json', encoding='utf-8') as comps:
         listOfCompetitions = json.load(comps)['competitions']
         return listOfCompetitions

def saveData(clubs, competitions):
    """Sauvegarde les listes de clubs et de compétitions dans leurs fichiers JSON respectifs."""
    with open(BASE_DIR / 'clubs.json', 'w', encoding='utf-8') as c:
        json.dump({'clubs': clubs}, c, indent=4)
    with open(BASE_DIR / 'competitions.json', 'w', encoding='utf-8') as comps:
        json.dump({'competitions': competitions}, comps, indent=4)


app = Flask(__name__)
app.secret_key = 'something_special'



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/showSummary',methods=['POST'])
def showSummary():
    competitions = loadCompetitions()
    clubs = loadClubs()
    email = request.form.get('email', '').strip()
    club = next((c for c in clubs if c.get('email') == email), None)
    if club is None:
        flash('Adresse e-mail inconnue. Veuillez réessayer.')
        return redirect(url_for('index'))
    
    # --- NOUVELLE LOGIQUE : ÉTIQUETER LES COMPÉTITIONS ---
    # On ne filtre plus, on ajoute une information à chaque compétition
    for comp in competitions:
        comp_date = datetime.strptime(comp['date'], '%Y-%m-%d %H:%M:%S')
        if comp_date < datetime.now():
            comp['is_past'] = True
        else:
            comp['is_past'] = False
    # --- FIN DE LA NOUVELLE LOGIQUE ---
 
    return render_template('welcome.html',club=club,competitions=competitions)

@app.route('/book/<competition>/<club>')
def book(competition,club):
    competitions = loadCompetitions()
    clubs = loadClubs()
    foundClub = next((c for c in clubs if c.get('name') == club), None)
    foundCompetition = next((c for c in competitions if c.get('name') == competition), None)
    
    if not foundClub or not foundCompetition:
        flash("Club ou compétition introuvable.")
        return redirect(url_for('index'))

    # --- C'EST CE BLOC QUI MANQUE ---
    # Vérifie si la date de la compétition est passée
    competition_date = datetime.strptime(foundCompetition['date'], '%Y-%m-%d %H:%M:%S')
    if competition_date < datetime.now():
        flash("Cette compétition est déjà terminée et ne peut pas être réservée.")
        return redirect(url_for('index'))
    # --- FIN DE LA CORRECTION ---
    
    # Si la date est bonne, on affiche la page de réservation
    return render_template('booking.html', club=foundClub, competition=foundCompetition)

@app.route('/purchasePlaces',methods=['POST'])
def purchasePlaces():
    competitions = loadCompetitions()
    clubs = loadClubs()
    competition = next((c for c in competitions if c.get('name') == request.form.get('competition')), None)
    club = next((c for c in clubs if c.get('name') == request.form.get('club')), None)
    
    if not competition or not club:
        flash('Erreur : Club ou compétition introuvable. Transaction annulée.')
        return redirect(url_for('index'))
    
    # --- Début des vérifications ---
    try:
        placesRequired = int(request.form.get('places', 0))
    except ValueError:
        flash('Erreur : Veuillez entrer un nombre valide.')
        return redirect(url_for('book', competition=competition['name'], club=club['name']))

    if placesRequired <= 0:
        flash('Erreur : Vous devez réserver au moins 1 place.')
        return redirect(url_for('book', competition=competition['name'], club=club['name']))

    # --- Vérifications qui affichent un message sur la page d'accueil ---
    error = None # On prépare une variable pour les erreurs
    
    comp_date = datetime.strptime(competition['date'], '%Y-%m-%d %H:%M:%S')
    if comp_date < datetime.now():
        error = "Action non autorisée : Cette compétition est déjà terminée."

    competition.setdefault('placesBookedByClub', {})
    places_already_booked = competition['placesBookedByClub'].get(club['name'], 0)
    if not error and places_already_booked + placesRequired > 12:
        places_remaining_for_club = 12 - places_already_booked
        error = f"Action non autorisée : Vous avez déjà {places_already_booked} places. Vous ne pouvez en réserver que {places_remaining_for_club} de plus."
    
    if not error and placesRequired > int(club.get('points', 0)):
        error = f"Achat impossible. Vous n'avez que {club.get('points')} points."

    if not error and placesRequired > int(competition.get('numberOfPlaces', 0)):
        error = f"Action impossible : il ne reste que {competition.get('numberOfPlaces')} places disponibles."

    # Si une erreur a été trouvée, on recharge la page d'accueil en affichant l'erreur
    if error:
        return render_template('welcome.html', club=club, competitions=competitions, error=error)
    
    # --- Si tout est OK, on procède à la transaction ---
    club['points'] = int(club['points']) - placesRequired
    competition['numberOfPlaces'] = int(competition['numberOfPlaces']) - placesRequired
    competition['placesBookedByClub'][club['name']] = places_already_booked + placesRequired
    saveData(clubs, competitions)
    
    flash('Réservation réussie ! Vos points ont été déduits.')
    return render_template('welcome.html', club=club, competitions=competitions)
# TODO: Add route for points display


@app.route('/points-board')
def points_board():
    """
    Affiche un tableau public et en lecture seule des points de chaque club.
    Accessible sans connexion pour la transparence.
    """
    clubs = loadClubs()

    sorted_clubs = sorted(clubs, key=lambda item: int(item['points']), reverse=True)

    print("Contenu de la variable 'clubs' envoyée au template :", clubs)

    return render_template('points_board.html', clubs=sorted_clubs)




@app.route('/logout')
def logout():
    return redirect(url_for('index'))




if __name__ == '__main__':
    app.run(debug=True)