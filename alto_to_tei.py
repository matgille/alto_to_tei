import string
import sys
import numpy as np
from PIL import Image, ImageDraw
from lxml import etree
import os
import tqdm
import random
import subprocess


class DocumentXML:
    def __init__(self, fichier_entree, sigle):
        self.entree = fichier_entree
        self.sortie = self.entree.replace('.xml', '_out.xml')
        f = etree.parse(self.entree)
        self.root = f.getroot()
        self.sigle = sigle
        self.coordonnees = None  # On la définit plus bas.

    def get_coordinates(self, element):
        """
        Extrait les coordonnées à partir du XML
        :return: Un dictionnaire e la forme {position : (id, chemin_vers_le_folio, coordonnees)}
        """
        liste_element = self.root.xpath(element, namespaces=tei)
        liste_images = [element.xpath("preceding::tei:pb[1]/@facs", namespaces=tei)[0] for element in liste_element]
        liste_coordonnees = [element.xpath("@facs", namespaces=tei)[0] for element in liste_element]

        tuple_coordonnees_et_positions = tuple(
            zip(
                [liste_coordonnees.index(item) for item in liste_coordonnees], liste_images, liste_coordonnees
            )
        )

        dict_coordonnees_et_positions = {}
        for position, image, coordonnees in tuple_coordonnees_et_positions:
            dict_coordonnees_et_positions[position] = generateur_id(), image, [(int(x), int(y)) for x, y in
                                                                               list(
                                                                                   zip(
                                                                                       coordonnees.split(' ')[0::2],
                                                                                       coordonnees.split(' ')[1::2]
                                                                                   )
                                                                               )]

        self.coordonnees = dict_coordonnees_et_positions

    def extract_images(self):
        """
        Extrait les images des lignes à partir des coordonnées extraites auparavant.
        :return: None
        """
        # https://stackoverflow.com/a/22650239
        for position, (identifiant, image_path, coordonnees) in tqdm.tqdm(self.coordonnees.items()):
            image_basename = image_path.split("/")[-1]
            image = Image.open(image_path).convert("RGBA")

            # convert to numpy (for convenience)
            image_array = np.asarray(image)
            polygone = coordonnees
            maskIm = Image.new('L', (image_array.shape[1], image_array.shape[0]), 0)  # c'est ici qu'on initialise
            # une plus petite image.
            ImageDraw.Draw(maskIm).polygon(polygone, outline=1, fill=1)
            mask = np.array(maskIm)

            # assemble new image (uint8: 0-255)
            newImArray = np.empty(image_array.shape, dtype='uint8')

            # colors (three first columns, RGB)
            newImArray[:, :, :3] = image_array[:, :, :3]

            # transparency (4th column)
            newImArray[:, :, 3] = mask * 255

            # https://stackoverflow.com/a/43591567
            # On selectionne le rectangle qui contient la ligne (= les valeurs d'abcisse et d'ordonnée
            # maximales et minimales)
            x_max = max([i[0] for i in coordonnees])
            x_min = min([i[0] for i in coordonnees])
            y_max = max([i[1] for i in coordonnees])
            y_min = min([i[1] for i in coordonnees])
            rectangle_coordinates = (x_min, y_min, x_max, y_max)

            # On enregistre
            newIm = Image.fromarray(newImArray, "RGBA")
            cropped_img = newIm.crop(rectangle_coordinates)
            os.makedirs("lignes", exist_ok=True) # l'exception ne marche pas, je ne sais pas pourquoi
            cropped_img.save(f"lignes/{image_basename.replace('.jpg', '')}_{identifiant}.png")
            print(f"lignes/{image_basename.replace('.jpg', '')}_{identifiant}.png")


    def produce_xml_file(self, element):
        all_element = self.root.xpath(element, namespaces=tei)  # https://stackoverflow.com/a/17269384 pour l'efficacité
        # plutôt que de chercher à chaque fois le bon élément tei avec un count(preceding::tei:*) qui est très
        # long à calculer
        for position, (identifiant, path_to_folio, coordonnees) in tqdm.tqdm(self.coordonnees.items()):
            print(path_to_folio)
            folio_basename = path_to_folio.split("/")[-1]
            path_to_line = f"lignes/{folio_basename.replace('.jpg', '')}_{identifiant}.png"
            coordonnees_out = []
            for tuple_coordonnees in coordonnees:
                x, y = tuple_coordonnees
                coordonnees_out.append(f"{x},{y}")
            chaine_coordonnees = " ".join(coordonnees_out)

            facsimile = self.root.xpath("//tei:facsimile", namespaces=tei)[0]
            surface = etree.SubElement(facsimile, f"{tei_namespace}surface")
            xml_id = f"elem_{identifiant}"
            surface.set('{http://www.w3.org/XML/1998/namespace}id', f"facs_{identifiant}")
            surface.set("points", chaine_coordonnees)
            surface.set("corresp", f"#{xml_id}")

            graphic = etree.SubElement(surface, f"{tei_namespace}graphic")
            graphic.set("url", path_to_line)
            current_lb = all_element[position]
            current_lb.set("facs", f"#facs_{identifiant}")
            current_lb.set('{http://www.w3.org/XML/1998/namespace}id', xml_id)
        sortie = f'output/{self.sigle}_out.xml'
        with open(sortie, 'w+') as sortie_xml:
            output = etree.tostring(self.root, pretty_print=True, encoding='utf-8', xml_declaration=True).decode('utf8')
            sortie_xml.write(str(output))

    def get_images(self, xpath_expression):
        """
        Cette fonction permet d'extraire les coordonnées, les images, et de créer le xml de sortie.
        :param xpath_expression: une expression xpath vers l'élément donc les images sont à extraire.
        :return: None
        """
        self.get_coordinates(xpath_expression)
        self.extract_images()
        self.produce_xml_file(xpath_expression)

def generateur_lettre_initiale(size=1, chars=string.ascii_lowercase):  # éviter les nombres en premier caractère de
    # l'@xml:id (interdit)
    return ''.join(random.choice(chars) for _ in range(size))


def generateur_id(size=5, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    return generateur_lettre_initiale() + ''.join(random.choice(chars) for _ in range(size))


def to_tei(input_folder, output_file):
    # On utilise le fichier xsl comme fichier xml d'entrée: on a toujours besoin d'un fichier
    # d'entrée...
    subprocess.run(["java", "-jar", saxon, "-xi:on", f"input_files={input_folder}", f"output_file={output_file}",
                    "to_tei.xsl", "to_tei.xsl"])


def main(fichier, sigle):
    output_file = f"output/{sigle}.xml"
    to_tei(fichier, output_file)
    fichier_xml = DocumentXML(output_file, sigle)

    fichier_xml.get_images("//tei:lb")
    fichier_xml.get_images("//tei:graphic[@type='lettrine']")
    fichier_xml.get_images("//tei:add")


tei = {'tei': 'http://www.tei-c.org/ns/1.0'}
tei_namespace_url = 'http://www.tei-c.org/ns/1.0'
tei_namespace = '{%s}' % tei_namespace_url
NSMAP0 = {None: tei}
saxon = "saxon9he.jar"

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
