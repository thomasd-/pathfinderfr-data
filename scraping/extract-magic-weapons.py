#!/usr/bin/python3
# -*- coding: utf-8 -*-

import urllib.request
import yaml
import sys
import html
import re
from bs4 import BeautifulSoup
from lxml import html

from libhtml import table2text, extractBD_Type1, extractBD_Type2, html2text, cleanName

## Configurations pour le lancement
MOCK_MAGIC = None
#MOCK_MAGIC = "mocks/magic-weapons.html"                  # décommenter pour tester avec les armes pré-téléchargées
MOCK_MAGIC_ITEM = None
#MOCK_MAGIC_ITEM = "mocks/magic-carreau.html"      # décommenter pour tester avec détails pré-téléchargé

TEXTE = 'Si l’arme bénéficie seulement d’un bonus d’altération, son niveau de lanceur de sorts est égal à trois fois son bonus. Si l’objet possède un bonus d’altération ainsi que des propriétés magiques, le plus haut niveau de lanceur de sorts entre les deux est celui qui doit être considéré. Armes à distance et projectiles. \n\nLe bonus d’altération d’une arme à projectiles ne se cumule pas avec le bonus d’altération de ses munitions. Seule la plus haute valeur est prise en compte.'

liste = []


# first = column with name
# second = column with cost
PATHFINDER = "http://www.pathfinder-fr.org/Wiki/"
REFERENCE = PATHFINDER + "Pathfinder-RPG.Armes%20magiques.ashx"
TYPE = "Arme"
IGNORE = ["Arme spécifique"]
TABLEDEF = {
    1: [4,5,"Arme ", {'descr': TEXTE}],
    2: [4,5,"Arme càc: "],
    3: [4,5,"Arme càc: "],
    4: [4,5,"Arme dist: "],
    5: [4,5,"Arme dist"],
    6: [4,5,""],
    7: [4,5,""],
}


if MOCK_MAGIC:
    content = BeautifulSoup(open(MOCK_MAGIC),features="lxml").body
else:
    content = BeautifulSoup(urllib.request.urlopen(REFERENCE).read(),features="lxml").body


propList = []

tables = content.find_all('table',{'class':['tablo col1centre']})

liste = []

tableIdx = 0
for t in tables:
    tableIdx += 1
    caption = t.find('caption').text
    for tr in t.find_all('tr'):
        
        if tr.has_attr('class') and (tr['class'][0] == 'titre' or tr['class'][0] == 'soustitre'):
            continue
        
        columnIdx = 0
        for td in tr.find_all('td'):
            columnIdx += 1
            if columnIdx == TABLEDEF[tableIdx][0]:
                nom = html2text(td)
                href = td.find('a')
                if href:
                    href = href['href']
            elif columnIdx == TABLEDEF[tableIdx][1]:
                prix = html2text(td)
        
        # sauter les entrées du type "relancer le dé"
        if u"le dé" in nom:
            continue
        
        # ignorer certaines entrées (référence à un autre tableau dans la page)
        if nom in IGNORE:
            continue
        else:
            nom = TABLEDEF[tableIdx][2] + nom
        
        # référence de base
        reference = REFERENCE
        
        data = {"nom": cleanName(nom), "prix": prix.strip(), "descr": ""}
        
        if len(TABLEDEF[tableIdx]) == 4:
            data = { **data, **TABLEDEF[tableIdx][3] }
        
        # débogage
        #print("Traitement de %s..." % nom.strip())
        
        # get description from same page
        if href and "#" in href and not "NOTE" in href:
            ref = "#" + href.split('#')[1]
            jumpTo = content.find('a',{'href':ref})
            if jumpTo is None:
                print("Lien invalide: %s" % href)
                exit(1)
            data = {**data, **extractBD_Type1(jumpTo.find_next('div',{'class':['BD']}))}
            
            reference = PATHFINDER + href
            if len(data['descr']) == 0:
                print("Description invalide pour: %s" % href)
                exit(1)
        
        elif href and not "#" in href:
            # récupérer le détail d'un objet
            if MOCK_MAGIC_ITEM:
                page = BeautifulSoup(open(MOCK_MAGIC_ITEM),features="lxml").body
            else:
                page = BeautifulSoup(urllib.request.urlopen(PATHFINDER + href).read(),features="lxml").body
                
            reference = PATHFINDER + href
            data = {**data, **extractBD_Type2(page.find('div',{'class':['BD']}))}
            descr = data['descr']
            
            if len(data['descr']) == 0:
                print("Description invalide pour: %s" % href)
                exit(1)
        
        element = {}
        element["01Nom"] = data["nom"]
        element["02Type"] = TYPE
        element["03Prix"] = data["prix"]
        element["04Source"] = "MJ"
        element["20Description"] = data["descr"]
        element["21Référence"] = reference
        
        # infos additionnelles
        if "emplacement" in data:
            element["05Emplacement"] = data["emplacement"]
        if "poids" in data:
            element["06Poids"] = data["poids"]
        if "aura" in data:
            element["07Aura"] = data["aura"]
        if "nls" in data:
            # NLS parfois variable
            if isinstance(data["nls"], int):
                element["08NLS"] = data["nls"]
            else:
                element["20Description"] = "NLS: " + data["nls"] + "\n\n" + element["20Description"]
        if "conditions" in data:
            element["09Conditions"] = data["conditions"]
        if "coût" in data:
            element["10Coût"] = data["coût"]
        
        element["EMPTY"] = ""
        liste.append(element)
    
#exit(1)

yml = yaml.safe_dump(liste,default_flow_style=False, allow_unicode=True)
yml = yml.replace('01Nom','Nom')
yml = yml.replace('02Type','Type')
yml = yml.replace('03Prix','Prix')
yml = yml.replace('04Source','Source')
yml = yml.replace('05Emplacement','Emplacement')
yml = yml.replace('06Poids','Poids')
yml = yml.replace('07Aura','Aura')
yml = yml.replace('08NLS','NLS')
yml = yml.replace('09Conditions','Conditions')
yml = yml.replace('10Coût','Coût')
yml = yml.replace('20Description','Description')
yml = yml.replace('21Référence','Référence')
yml = yml.replace("EMPTY: ''",'')
print(yml)
