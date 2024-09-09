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

La feuille de style xsl permet de produire un document XML/TEI pseudo-conforme; elle est actuellement écrite en fonction de
ma propre typologie des zones et des lignes et il s'agit donc de la 
personnaliser à votre projet dans le fichier xsl.



## Utilisation

Les fichiers alto doivent être dans un dossier, avec les images. Ils doivent pouvoir être ordonnés numériquement 
(i.e. correspondre à l'expression régulière `\d+.xml`).

`python3 alto_to_tei.py  -i alignement_multilingue/borghia_ch2/ -o output/borghia_ch2 -dp False -w 8 -s borghia_ch2`

