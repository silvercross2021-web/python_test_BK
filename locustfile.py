from locust import HttpUser, task, between
import random

class SecretaryUser(HttpUser):
    """
    Simule le parcours d'un secrétaire de club sur l'application.
    """
    # Chaque utilisateur virtuel attendra entre 1 et 3 secondes entre chaque action.
    wait_time = between(1, 3)

    # --- Données de test ---
    # Assurez-vous que cet email et ce nom de club existent dans votre clubs.json
    TEST_CLUB_EMAIL = "john@simplylift.co"
    TEST_CLUB_NAME = "Simply Lift"
    # Liste des compétitions pour les tests
    COMPETITIONS = ["Spring Festival", "Fall Classic"]
    # -----------------------

    @task(1)
    def login_and_view_competitions(self):
        """
        Cette tâche simule la connexion du secrétaire.
        Elle mesure la performance de "récupérer une liste de compétitions" (< 5 secondes).
        """
        self.client.post(
            "/showSummary",
            {"email": self.TEST_CLUB_EMAIL},
            name="/showSummary [récupérer compétitions]"
        )

    @task(2)
    def purchase_place(self):
        """
        Cette tâche simule l'achat d'une place.
        Elle mesure la performance de "mettre à jour le total de points" (< 2 secondes).
        Elle sera exécutée deux fois plus souvent que la connexion.
        """
        competition_name = random.choice(self.COMPETITIONS)

        self.client.post(
            "/purchasePlaces",
            {
                "club": self.TEST_CLUB_NAME,
                "competition": competition_name,
                "places": 1, # On réserve 1 place à la fois pour ne pas épuiser les points trop vite
            },
            name="/purchasePlaces [mettre à jour points]"
        )