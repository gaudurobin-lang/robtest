# Script de la vidéo : chaque ligne = (début s, fin s, texte prononcé, sous-titre affiché)
# Dans les sous-titres, *mot* = mot-clé surligné.
LINES = [
    # HOOK 0-3
    (0.15, 3.0, "Dans cinq jours, plus personne ne va aller au travail.",
     "Dans *5 JOURS* plus personne ne va aller au *TRAVAIL* 😳"),
    # CONTEXTE 3-10
    (3.1, 6.4, "Treize ans. Treize ans qu'on attend depuis GTA cinq.",
     "*13 ANS* 13 ans qu'on attend depuis *GTA 5*"),
    (6.5, 10.0, "Deux reports plus tard... cette fois, c'est la bonne.",
     "*2 REPORTS* plus tard... cette fois c'est la *BONNE* 🔥"),
    # INFOS 10-40
    (10.1, 16.0, "Un : la date. Jeudi dix-neuf novembre, dans la nuit de mercredi à jeudi.",
     "*1* la *DATE* jeudi *19 NOVEMBRE* dans la nuit de mercredi à jeudi"),
    (16.1, 22.0, "Deux : PS cinq et Xbox Série seulement. Le prix : soixante-dix-neuf euros quatre-vingt-dix-neuf.",
     "*2* *PS5* et *XBOX SERIES* seulement le prix *79,99 €* 💰"),
    (22.1, 28.0, "Trois : retour à Vaïsse Siti, dans l'État de Léonida. Le Miami de Rockstar.",
     "*3* retour à *VICE CITY* dans l'État de *LEONIDA* le Miami de Rockstar 🌴"),
    (28.1, 34.0, "Quatre : deux héros, Lucia et Djèïsonne. Un duo façon Bonnie and Claïde.",
     "*4* deux héros *LUCIA* et *JASON* un duo façon *BONNIE & CLYDE*"),
    (34.1, 40.0, "Cinq : le préchargement est déjà ouvert. Lance-le maintenant, ça va être lourd.",
     "*5* le *PRÉCHARGEMENT* est déjà ouvert lance-le *MAINTENANT* ça va être lourd 🎮"),
    # DEBAT 40-52
    (40.2, 46.0, "Alors, vraie question : tu poses ta journée le dix-neuf... ou tu te fais porter pâle ?",
     "Alors vraie question tu *POSES TA JOURNÉE* le 19... ou tu te fais *PORTER PÂLE?*"),
    (46.2, 52.0, "Et toi, tu joues Lucia ou Djèïsonne ? Dis-le en commentaire.",
     "Et toi tu joues *LUCIA* ou *JASON?* Dis-le en *COMMENTAIRE* 👇"),
    # CTA + BOUCLE 52-60
    (52.2, 56.6, "Abonne-toi pour tout savoir le jour J.",
     "*ABONNE-TOI* pour tout savoir le *JOUR J*"),
    (56.8, 60.0, "Parce que dans cinq jours...",
     "Parce que dans *5 JOURS...*"),
]
