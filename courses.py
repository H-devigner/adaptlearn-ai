"""Catalogue des leçons Python et de leurs quiz éditoriaux."""
from textwrap import dedent

LEVELS = ('Débutant', 'Intermédiaire', 'Avancé')

COURSES = [
    {
        'id': 'python-debut',
        'title': 'Premiers pas avec Python',
        'level': 'Débutant',
        'duration': 20,
        'description': 'Découvrir Python et écrire son premier programme.',
        'topics': ['print()', 'Exécution', 'Commentaires'],
        'prerequisites': [],
        'content': dedent("""\
            Un programme Python est une suite d’instructions. Créez un fichier bonjour.py
            avec un éditeur de texte et écrivez ces trois lignes :

                # Un premier programme
                print("Bonjour !")
                print("Bienvenue dans le cours Python.")

            Dans un terminal ouvert dans le dossier du fichier, lancez python bonjour.py.
            Si Python est disponible sous le nom python3, lancez python3 bonjour.py.
            L’interpréteur lit le fichier et exécute les instructions dans l’ordre.
            print() affiche son argument, puis termine la ligne. Les guillemets
            délimitent le texte et ne font pas partie du message affiché.

            En dehors d’une chaîne, le caractère # introduit un commentaire qui s’arrête
            à la fin de la ligne. Python l’ignore pendant l’exécution. Dans
            print("# Départ"), le # est entre guillemets et s’affiche avec le texte.

            À vous de jouer : ajoutez une instruction qui affiche votre prénom, puis
            relancez le fichier. Retirez ensuite un guillemet fermant et observez l’erreur
            de syntaxe signalée. Rétablissez le guillemet et relancez le programme.
            """).strip(),
        'questions': [
            {'question': 'Quelle instruction affiche Bonjour ?',
             'options': ['echo("Bonjour")', 'print("Bonjour")', '# Bonjour', '"Bonjour"'],
             'answer': 1, 'explanation': 'Dans un fichier Python, print() affiche son argument.'},
            {'question': 'Que fait Python de la ligne # Un premier programme ?',
             'options': ['Il affiche cette ligne.', 'Il arrête le programme.',
                         'Il demande une entrée.', 'Il ignore cette ligne.'],
             'answer': 3, 'explanation': 'Hors d’une chaîne, # introduit un commentaire.'},
            {'question': 'Que produit un fichier contenant print("A") puis print("B") ?',
             'options': ['A puis B sur deux lignes', 'B puis A sur deux lignes', 'AB sur une ligne',
                         'B seulement'],
             'answer': 0, 'explanation': 'Les instructions s’exécutent dans l’ordre et chaque print() termine sa ligne.'},
            {'question': 'Quelle commande lance bonjour.py si Python est accessible avec python3 ?',
             'options': ['bonjour.py python3', 'print bonjour.py', 'python3 bonjour.py',
                         'python3("bonjour.py")'],
             'answer': 2, 'explanation': 'Le nom du fichier est passé en argument à l’interpréteur dans le terminal.'},
        ],
    },
    {
        'id': 'variables',
        'title': 'Les variables',
        'level': 'Débutant',
        'duration': 25,
        'description': 'Stocker et manipuler des nombres et du texte.',
        'topics': ['Variables', 'Types', 'Calculs'],
        'prerequisites': ['python-debut'],
        'content': dedent("""\
            Une variable est un nom qui désigne une valeur. Pour affecter une valeur,
            placez le nom à gauche de = et l’expression à droite. Un nom comme
            prix_unitaire indique le rôle de la valeur.

                produit = "carnet"
                quantite = 3
                prix_unitaire = 2.50
                total = quantite * prix_unitaire
                print(produit, total)  # carnet 7.5

            produit désigne du texte (str), quantite un entier (int) et prix_unitaire
            un nombre à virgule flottante (float). En Python, les nombres décimaux
            s’écrivent avec un point. On peut additionner avec +, soustraire avec -,
            multiplier avec * et diviser avec /. Les parenthèses modifient l’ordre
            du calcul.

            Le type des valeurs change le sens de +. L’expression 2 + 3 vaut 5,
            tandis que "2" + "3" donne "23". Utilisez int("3") pour obtenir l’entier
            3 à partir du texte, ou str(3) pour faire l’inverse. Une nouvelle
            affectation remplace la valeur associée au nom :

                quantite = quantite + 1
                print(quantite)  # 4

            À vous de jouer : recalculez total après cette affectation et affichez
            le nouveau montant.
            """).strip(),
        'questions': [
            {'question': 'Quel est le type de prix_unitaire = 2.50 ?',
             'options': ['str', 'int', 'float', 'list'],
             'answer': 2, 'explanation': 'Un nombre écrit avec un point décimal est un float.'},
            {'question': 'Quelle est la valeur de "2" + "3" ?',
             'options': ['"23"', '5', '"5"', '23'],
             'answer': 0, 'explanation': 'Avec deux chaînes, + assemble le texte et renvoie une chaîne.'},
            {'question': 'Que vaut total après total = 3 * (2 + 1) ?',
             'options': ['7', '6', '8', '9'],
             'answer': 3, 'explanation': 'Les parenthèses imposent de calculer 2 + 1 avant la multiplication.'},
            {'question': 'Que produit int("3") + 1 ?',
             'options': ['"31"', '4', '"4"', '31'],
             'answer': 1, 'explanation': 'int() convertit le texte en entier avant l’addition.'},
        ],
    },
    {
        'id': 'conditions-boucles',
        'title': 'Conditions et boucles',
        'level': 'Intermédiaire',
        'duration': 35,
        'description': 'Prendre des décisions et répéter des instructions.',
        'topics': ['if / else', 'for', 'while'],
        'prerequisites': ['python-debut', 'variables'],
        'content': dedent("""\
            Une condition choisit quelles instructions exécuter. La comparaison ==
            teste l’égalité, et >= teste si la valeur de gauche atteint ou dépasse
            celle de droite. Après if ou else, placez un deux-points et indentez
            les instructions du bloc de quatre espaces.

                score = 70
                if score >= 70:
                    print("Objectif atteint")
                else:
                    print("Encore un effort")

            Une boucle for parcourt les valeurs d’un objet itérable. Dans
            range(1, 4), la borne de début est incluse et la borne de fin est exclue :

                for numero in range(1, 4):
                    print(numero)  # Affiche 1, puis 2, puis 3

            Une boucle while vérifie la condition avant chaque tour. Assurez-vous
            que la variable utilisée dans la condition évolue vers un cas qui arrête
            la boucle :

                restant = 3
                while restant > 0:
                    print(restant)
                    restant = restant - 1

            À vous de jouer : remplacez 70 par 69 dans le premier exemple et observez
            quelle branche s’exécute. Vérifiez ensuite que le compte à rebours
            s’arrête sans afficher 0.
            """).strip(),
        'questions': [
            {'question': 'Quelle comparaison teste l’égalité entre score et 70 ?',
             'options': ['score = 70', 'score != 70', 'score > 70', 'score == 70'],
             'answer': 3, 'explanation': '== compare des valeurs. Le signe = sert à affecter une valeur.'},
            {'question': 'Quelles valeurs produit range(1, 4) ?',
             'options': ['0, 1, 2, 3', '1, 2, 3, 4', '1, 2, 3', '2, 3, 4'],
             'answer': 2, 'explanation': 'Le début est inclus et la borne de fin est exclue.'},
            {'question': 'À quel moment le bloc else de l’exemple du score s’exécute-t-il ?',
             'options': ['Quand score est inférieur à 70.', 'Quand score vaut 70.',
                         'Quand score est supérieur à 70.', 'À chaque exécution.'],
             'answer': 0, 'explanation': 'Le bloc else s’exécute quand score >= 70 est faux.'},
            {'question': 'Pourquoi le compte à rebours avec while s’arrête-t-il ?',
             'options': ['print() arrête la boucle.', 'restant atteint zéro.',
                         'while n’exécute le bloc qu’une fois.', 'La valeur de restant augmente.'],
             'answer': 1, 'explanation': 'Après trois diminutions, restant > 0 est faux et la boucle se termine.'},
        ],
    },
    {
        'id': 'fonctions-collections',
        'title': 'Fonctions et collections',
        'level': 'Intermédiaire',
        'duration': 40,
        'description': 'Organiser ses traitements et manipuler des ensembles de données.',
        'topics': ['def', 'Listes', 'Dictionnaires'],
        'prerequisites': ['python-debut', 'variables', 'conditions-boucles'],
        'content': dedent("""\
            Une fonction regroupe un traitement réutilisable. def introduit son nom
            et ses paramètres. Lorsque la fonction est appelée, return renvoie une
            valeur que l’appelant peut utiliser dans une autre expression.

                def double(nombre):
                    return 2 * nombre

                valeurs = [4, 7, 10]
                valeurs.append(double(3))
                print(valeurs)     # [4, 7, 10, 6]
                print(valeurs[0])  # 4

            Une liste conserve ses éléments dans l’ordre. Les indices commencent à
            zéro. append() ajoute un élément à la fin de la liste existante.

            Un dictionnaire associe des clés à des valeurs. Ici, les clés sont des
            chaînes qui nomment des articles. Les crochets permettent d’accéder à
            la valeur associée à une clé. Si la clé peut être absente, get() accepte
            une valeur par défaut :

                stock = {"carnet": 4, "crayon": 8}
                print(stock["carnet"])     # 4
                print(stock.get("gomme", 0))  # 0

            À vous de jouer : écrivez une fonction quantite(stock, article) qui
            renvoie le nombre d’unités ou 0 quand l’article manque. Appelez-la
            avec "crayon", puis avec "gomme".
            """).strip(),
        'questions': [
            {'question': 'Que renvoie double(3) dans la leçon ?',
             'options': ['3', '6', '"6"', 'Aucune valeur'],
             'answer': 1, 'explanation': 'La fonction évalue 2 * nombre et return renvoie le résultat.'},
            {'question': 'Que vaut [4, 7, 10][0] ?',
             'options': ['7', '10', '0', '4'],
             'answer': 3, 'explanation': 'Le premier élément d’une liste se trouve à l’indice 0.'},
            {'question': 'Que fait valeurs.append(6) ?',
             'options': ['Ajoute 6 à la fin de valeurs.', 'Remplace le premier élément par 6.',
                         'Retire l’élément situé à l’indice 6.', 'Trie les six premiers éléments.'],
             'answer': 0, 'explanation': 'append() modifie la liste en y ajoutant un dernier élément.'},
            {'question': 'Que produit stock.get("gomme", 0) si la clé gomme est absente ?',
             'options': ['Une erreur', '"gomme"', '0', 'La première valeur du dictionnaire'],
             'answer': 2, 'explanation': 'get() renvoie son deuxième argument quand la clé est absente.'},
        ],
    },
    {
        'id': 'generateurs',
        'title': 'Compréhensions et générateurs',
        'level': 'Avancé',
        'duration': 45,
        'description': 'Transformer des collections et produire des valeurs à la demande.',
        'topics': ['Compréhensions', 'yield', 'Itérateurs'],
        'prerequisites': ['python-debut', 'variables', 'conditions-boucles', 'fonctions-collections'],
        'content': dedent("""\
            Une compréhension de liste construit une nouvelle liste à partir d’un
            itérable. L’expression placée au début indique quoi produire. Une
            condition à la fin peut filtrer les valeurs :

                carres_pairs = [n * n for n in range(6) if n % 2 == 0]
                print(carres_pairs)  # [0, 4, 16]

            Avec les parenthèses, une expression similaire crée un générateur.
            Il calcule chaque valeur à la demande. next() demande la valeur
            suivante et peut renvoyer une valeur par défaut à l’épuisement :

                carres = (n * n for n in range(3))
                print(next(carres))            # 0
                print(list(carres))            # [1, 4]
                print(next(carres, "fini"))    # fini

            Une fonction contenant yield crée aussi un générateur. À chaque yield,
            son exécution se suspend et la valeur est fournie à l’itérateur. Elle
            repart du même endroit quand on demande une autre valeur :

                def compte_a_rebours(depart):
                    while depart > 0:
                        yield depart
                        depart = depart - 1

                for nombre in compte_a_rebours(3):
                    print(nombre)  # Affiche 3, puis 2, puis 1

            À vous de jouer : appelez deux fois cette fonction et consommez chaque
            générateur avec list(). Vérifiez qu’un générateur épuisé donne une liste
            vide si vous le passez une deuxième fois à list().
            """).strip(),
        'questions': [
            {'question': 'Que produit [n * n for n in range(6) if n % 2 == 0] ?',
             'options': ['[0, 2, 4]', '[1, 9, 25]', '[0, 4, 16]', '[4, 16, 36]'],
             'answer': 2, 'explanation': 'Le filtre garde 0, 2 et 4, dont les carrés sont 0, 4 et 16.'},
            {'question': 'Quand une expression génératrice calcule-t-elle sa prochaine valeur ?',
             'options': ['Quand on la demande, par exemple avec next().', 'À la fin du programme.',
                         'Quand on déclare l’expression, avec toutes les valeurs.', 'Après son épuisement.'],
             'answer': 0, 'explanation': 'Un générateur avance à la demande, par exemple dans une boucle for.'},
            {'question': 'Que fait yield dans compte_a_rebours ?',
             'options': ['Il redémarre la fonction.', 'Il renvoie toutes les valeurs à la fois.',
                         'Il modifie le paramètre depart.', 'Il fournit une valeur et suspend l’exécution.'],
             'answer': 3, 'explanation': 'La fonction reprend après le yield lorsqu’une autre valeur est demandée.'},
            {'question': 'Que donne list() sur un générateur déjà épuisé ?',
             'options': ['Une copie de toutes les valeurs', 'Une liste vide',
                         'La dernière valeur produite', 'Un générateur neuf'],
             'answer': 1, 'explanation': 'Un générateur épuisé ne produit plus de valeurs. Il faut en créer un autre pour recommencer.'},
        ],
    },
]


def get_course(course_id):
    """Retrouve une leçon d’après son identifiant stable."""
    return next((course for course in COURSES if course['id'] == course_id), None)
