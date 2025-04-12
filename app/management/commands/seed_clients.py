import random
from django.core.management.base import BaseCommand
from app.models import Client, User
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Génère 1000 clients réalistes avec relations familiales'

    def add_arguments(self, parser):
        parser.add_argument('--delete', action='store_true', help='Supprimer tous les clients existants')

    def handle(self, *args, **options):
        if options['delete']:
            Client.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Tous les clients ont été supprimés'))

        # 1. Création des clients de base AVEC QR CODE
        sexes = ['M', 'F']
        regions = ['Antananarivo', 'Toamasina', 'Fianarantsoa', 'Mahajanga', 'Toliara', 'Antsiranana']
        
        # Création individuelle pour générer le QR code
        for i in range(1, 1001):
            sexe = random.choice(sexes)
            Client.objects.create(
                sexe=sexe,
                nom=f"Rakoto{'' if sexe == 'M' else 'v'}",
                prenom=f"Jean{i}" if sexe == 'M' else f"Jeanne{i}",
                date_naissance=date(1990, 1, 1) + timedelta(days=random.randint(1, 365*30)),
                adresse=f"Adresse {i}",
                cin=f"CNI{str(i).zfill(6)}"
            )

        self.stdout.write(self.style.SUCCESS('1000 clients de base créés avec QR codes'))

        # 2. Création des relations
        all_clients = list(Client.objects.all())
        male_clients = [c for c in all_clients if c.sexe == 'M']
        female_clients = [c for c in all_clients if c.sexe == 'F']

        # Création des couples
        for i in range(min(len(male_clients), len(female_clients)) // 2):
            mari = male_clients[i]
            femme = female_clients[i]
            
            # Vérification de la validité du couple
            if mari.sexe == femme.sexe:
                continue  # Skip les couples invalides

            # Création des enfants (1-3 enfants par couple)
            enfants = []
            for _ in range(random.randint(1, 3)):
                sexe_enfant = random.choice(sexes)
                enfant = Client.objects.create(
                    sexe=sexe_enfant,
                    nom=mari.nom,
                    prenom=f"Enfant{_+1}",
                    date_naissance=date(2010, 1, 1) + timedelta(days=random.randint(1, 365*10)),
                    adresse=mari.adresse,
                    cin=f"ENF{str(i).zfill(6)}{_}",
                    enfants=[]  # Initialiser explicitement la relation
                )
                # Ajout des parents APRÈS la création
                enfant.parents.add(mari, femme)
                enfant.save()  # Force la génération du QR code avec les parents
                enfants.append(enfant)

            # Mise à jour des relations
            mari.conjoint = femme
            mari.save()
            femme.conjoint = mari
            femme.enfants.set(enfants)
            femme.save()

        self.stdout.write(self.style.SUCCESS('Relations familiales créées avec succès'))

        # 3. Les utilisateurs sont créés automatiquement via le signal post_save
        self.stdout.write(self.style.SUCCESS(f'{User.objects.filter(is_client=True).count()} utilisateurs clients créés automatiquement'))