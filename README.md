# ALTO to TEI



Ce dépôt contient les fichier permettant de transformer des sources au format ALTO 4.0 (acquises via
eScriptorium par exemple)
en fichier TEI, avec extraction des images et création d'un élément `tei:facsimile` dans lequel sont
contenus les liens vers les images et les informations de zonage. Il requiert un dossier comprenant les fichiers xml et les images.

## Installation

```
git clone https://gitlab.huma-num.fr/mgillelevenson/alto_to_tei.git
cd alto_to_tei
python3 -m venv my_env
source my_env/bin/activate
pip3 install -r requirements.txt
```

## Fonctionnement et personnalisation

La feuille de style xsl permet de produire un document XML/TEI à peu
près conforme; elle est actuellement écrite en fonction de
ma typologie des zones et des lignes et il s'agit donc de la 
personnaliser à votre projet.

Par ailleurs il faut indiquer au script le chemin vers les éléments dont
il faut extraire les images.

## Utilisation

Les fichiers alto doivent être dans un dossier, avec les images.

`python3 alto_to_tei.py dossier_entree sigle_du_temoin`

Exemple avec les fichiers de test:

`python3 alto_to_tei.py test Mad_A`
