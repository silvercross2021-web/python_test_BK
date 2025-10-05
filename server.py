import json
from flask import Flask,render_template,request,redirect,flash,url_for, session
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

@app.route('/showSummary', methods=['POST'])
def showSummary():
    clubs = loadClubs()
    email = request.form.get('email', '').strip()
    club = next((c for c in clubs if c.get('email') == email), None)
    
    if not club:
        flash('Adresse e-mail inconnue. Veuillez réessayer.')
        return redirect(url_for('index'))
    
    # On enregistre l'email de l'utilisateur dans sa "carte de membre" (session)
    session['email'] = club['email']
    # On le redirige vers la nouvelle page du tableau de bord
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('index'))

    clubs = loadClubs()
    competitions = loadCompetitions()
    club = next((c for c in clubs if c.get('email') == session['email']), None)
    
    # Prépare les données pour l'affichage
    future_competitions = []
    total_places_booked = 0
    for comp in competitions:
        comp_date = datetime.strptime(comp['date'], '%Y-%m-%d %H:%M:%S')
        comp['is_past'] = comp_date < datetime.now()
        
        # Ne garder que les compétitions futures pour l'affichage principal
        if not comp['is_past']:
            future_competitions.append(comp)

        # Calculer le total des places réservées par le club
        if comp.get('placesBookedByClub') and club['name'] in comp['placesBookedByClub']:
            total_places_booked += int(comp['placesBookedByClub'][club['name']])
    
    return render_template(
        'welcome.html', 
        club=club, 
        competitions=future_competitions,  # On envoie la liste filtrée
        total_places_booked=total_places_booked
    )

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

@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    if 'email' not in session:
        return redirect(url_for('index'))

    competitions = loadCompetitions()
    clubs = loadClubs()
    club = next((c for c in clubs if c.get('email') == session['email']), None)
    competition = next((c for c in competitions if c.get('name') == request.form.get('competition')), None)
    
    if not competition or not club:
        flash('Erreur : Club ou compétition introuvable.')
        return redirect(url_for('dashboard')) # Erreur grave, on retourne au tableau de bord

    try:
        placesRequired = int(request.form.get('places', 0))
    except ValueError:
        flash('Erreur : Veuillez entrer un nombre valide.')
        # On reste sur la page de réservation
        return redirect(url_for('book', competition=competition['name'], club=club['name']))

    # --- SÉRIE DE VÉRIFICATIONS SÉCURISÉES ---
    
    if placesRequired <= 0:
        flash('Erreur : Vous devez réserver au moins 1 place.')
        # On reste sur la page de réservation
        return redirect(url_for('book', competition=competition['name'], club=club['name']))

    comp_date = datetime.strptime(competition['date'], '%Y-%m-%d %H:%M:%S')
    if comp_date < datetime.now():
        flash("Action non autorisée : Cette compétition est déjà terminée.")
        # Erreur non corrigeable par l'utilisateur, on retourne au tableau de bord
        return redirect(url_for('dashboard'))
    
    competition.setdefault('placesBookedByClub', {})
    places_already_booked = competition['placesBookedByClub'].get(club['name'], 0)
    if places_already_booked + placesRequired > 12:
        places_remaining_for_club = 12 - places_already_booked
        flash(f"Action non autorisée : Vous avez déjà {places_already_booked} places. Il ne vous en reste que {places_remaining_for_club} à réserver.")
        # On reste sur la page de réservation pour qu'il puisse corriger
        return redirect(url_for('book', competition=competition['name'], club=club['name']))
    
    if placesRequired > int(club.get('points', 0)):
        flash(f"Achat impossible. Vous n'avez que {club.get('points')} points.")
        # On reste sur la page de réservation
        return redirect(url_for('book', competition=competition['name'], club=club['name']))

    if placesRequired > int(competition.get('numberOfPlaces', 0)):
        flash(f"Action impossible : il ne reste que {competition.get('numberOfPlaces')} places disponibles.")
        # On reste sur la page de réservation
        return redirect(url_for('book', competition=competition['name'], club=club['name']))

    # --- Si tout est OK, on procède à la transaction ---
    club['points'] = int(club['points']) - placesRequired
    competition['numberOfPlaces'] = int(competition['numberOfPlaces']) - placesRequired
    competition['placesBookedByClub'][club['name']] = places_already_booked + placesRequired
    saveData(clubs, competitions)
    
    flash('Réservation réussie ! Vos points ont été déduits.')
    # En cas de SUCCÈS, on redirige vers le tableau de bord pour voir le résultat global
    return redirect(url_for('dashboard'))

@app.route('/points-board')
def points_board():
    """
    Affiche un tableau de bord public et trié, avec le menu adapté.
    """
    clubs = loadClubs()
    sorted_clubs = sorted(clubs, key=lambda item: int(item['points']), reverse=True)
    
    try:
        total_points = sum(int(club['points']) for club in clubs)
    except (ValueError, TypeError):
        total_points = 0
    
    # On vérifie si un utilisateur est connecté via la session
    logged_in_club = None
    if 'email' in session:
        logged_in_club = next((c for c in clubs if c.get('email') == session['email']), None)
    
    # On passe le club connecté (ou None) au template
    return render_template(
        'points_board.html', 
        clubs=sorted_clubs, 
        total_points=total_points, 
        club=logged_in_club  # C'est cette variable qui contrôle le menu
    )
@app.route('/competitions')
def competitions_list():
    """Affiche la liste complète et filtrable de toutes les compétitions."""
    
    # --- CORRECTION : VÉRIFIER LA CONNEXION D'ABORD ---
    if 'email' not in session:
        return redirect(url_for('index'))

    all_competitions = loadCompetitions()
    clubs = loadClubs()
    
    # --- CORRECTION : TROUVER LE VRAI CLUB CONNECTÉ ---
    # Au lieu de prendre un club au hasard, on cherche celui de la session
    club = next((c for c in clubs if c.get('email') == session['email']), None)
    if not club:
        # Si le club n'existe plus pour une raison quelconque, on déconnecte
        session.pop('email', None)
        return redirect(url_for('index'))

    # --- Le reste de la logique de filtre ne change pas ---
    status_filter = request.args.get('status', 'all')
    date_filter_str = request.args.get('date', '')

    filtered_competitions = []
    for comp in all_competitions:
        comp_date = datetime.strptime(comp['date'], '%Y-%m-%d %H:%M:%S')
        is_past = comp_date < datetime.now()
        comp['is_past'] = is_past

        passes_status_filter = (
            (status_filter == 'all') or
            (status_filter == 'future' and not is_past) or
            (status_filter == 'past' and is_past)
        )

        passes_date_filter = True
        if date_filter_str:
            try:
                filter_date = datetime.strptime(date_filter_str, '%Y-%m-%d').date()
                if comp_date.date() < filter_date:
                    passes_date_filter = False
            except ValueError:
                passes_date_filter = True

        if passes_status_filter and passes_date_filter:
            filtered_competitions.append(comp)
        
    return render_template(
        'competitions.html',
        competitions=filtered_competitions,
        club=club,  # On passe le VRAI club à la page
        current_filters={'status': status_filter, 'date': date_filter_str}
    )

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    """Affiche et gère la mise à jour du profil du club."""
    if 'email' not in session:
        return redirect(url_for('index'))

    clubs = loadClubs()
    all_competitions = loadCompetitions()
    club = next((c for c in clubs if c.get('email') == session['email']), None)

    if not club:
        session.pop('email', None)
        return redirect(url_for('index'))

    # --- LOGIQUE DE MISE À JOUR (QUAND ON CLIQUE SUR "SAUVEGARDER") ---
    if request.method == 'POST':
        old_name = club['name']
        new_name = request.form.get('club_name').strip()

        # On ne fait la mise à jour que si le nom a réellement changé et n'est pas vide
        if new_name and new_name != old_name:
            
            # --- CORRECTION DU BUG : MIGRATION DE L'HISTORIQUE ---
            # On parcourt toutes les compétitions pour mettre à jour l'ancien nom
            for comp in all_competitions:
                if comp.get('placesBookedByClub') and old_name in comp['placesBookedByClub']:
                    # On récupère le nombre de places réservées avec l'ancien nom
                    places = comp['placesBookedByClub'].pop(old_name)
                    # On ré-enregistre ces places avec le nouveau nom
                    comp['placesBookedByClub'][new_name] = places
            
            # On met à jour le nom du club lui-même
            club['name'] = new_name
            
            # On sauvegarde TOUT (les clubs et les compétitions modifiées)
            saveData(clubs, all_competitions)
            flash('Le nom du club a été mis à jour avec succès !')
        
        return redirect(url_for('profile'))
        
    # --- LOGIQUE D'AFFICHAGE (QUAND LA PAGE SE CHARGE) ---
    
    booking_history = []
    for comp in all_competitions:
        if comp.get('placesBookedByClub') and club['name'] in comp.get('placesBookedByClub'):
            booking_info = {
                'name': comp['name'],
                'date': comp['date'],
                'places': comp['placesBookedByClub'][club['name']]
            }
            booking_history.append(booking_info)

    sorted_clubs = sorted(clubs, key=lambda item: int(item['points']), reverse=True)
    current_rank = -1
    for i, c in enumerate(sorted_clubs):
        if c['email'] == club['email']:
            current_rank = i + 1
            break

    return render_template(
        'profile.html', 
        club=club, 
        history=booking_history, 
        rank=current_rank
    )


@app.route('/logout')
def logout():
    # On supprime la "carte de membre" de l'utilisateur
    session.pop('email', None)
    return redirect(url_for('index'))




if __name__ == '__main__':
    app.run(debug=True)