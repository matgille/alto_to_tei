import argparse
import glob
import json
import string
import numpy as np
from PIL import Image, ImageDraw
from lxml import etree
import os
import tqdm
import random
import subprocess
import multiprocessing as mp

import istarmap


def extract(dossier, sigle, workers):
    fichier_xml = DocumentXML(dossier, sigle, workers)
    fichier_xml.to_tei()
    # fichier_xml.get_images(["//tei:lb", "//tei:graphic[@type='lettrine']", "//tei:add"])
    # fichier_xml.get_images(["//tei:lb", "//tei:graphic[@type='lettrine']"])
    fichier_xml.get_images(["//tei:lb"])
    fichier_xml.produce_xml_file()


class DocumentXML:
    def __init__(self, dossier_entree, sigle, workers):
        self.input_folder = dossier_entree
        self.sigle = sigle
        self.sortie = None
        self.root = None
        self.coordonnees = None  # On la définit plus bas.
        self.pre_extraction_file = f"output/{sigle}/{sigle}.xml"
        self.directory = sigle
        self.workers = workers
        try:
            os.mkdir(f"output/{self.directory}")
        except:
            pass
        try:
            os.mkdir("lignes")
        except:
            pass
        try:
            os.mkdir(f"lignes/{self.directory}")
        except:
            [os.remove(image) for image in glob.glob(f"lignes/{self.directory}/*.png")]
        self.input_format = None

    def to_tei(self):
        """
        Cette fonction produit la transformation xsl.
        :return:
        """
        # On utilise le fichier xsl comme fichier xml d'entrée: on a toujours besoin d'un fichier
        # d'entrée...
        list_command = [
            "java",
            "-jar",
            saxon,
            "-xi:on",
            f"input_files={self.input_folder}",
            f"output_file={self.pre_extraction_file}",
            f"sigle={self.sigle}",
            f"MainZoneTag={MainZone}",
            f"MarginTextZoneTag={MarginTextZone}",
            f"NumberingZoneTag={NumberingZone}",
            f"QuireMarksZoneTag={QuireMarksZone}",
            f"RunningTitleZoneTag={RunningTitleZone}",
            f"TitleZoneTag={TitleZone}",
            f"DropCapitalZoneTag={DropCapitalZone}",
            f"HeadingLine_rubricTag={HeadingLine_rubric}",
            "to_tei.xsl",
            "to_tei.xsl"
        ]

        subprocess.run(list_command)
        f = etree.parse(self.pre_extraction_file)
        self.root = f.getroot()

    def get_coordinates(self, element):
        """
        Extrait les coordonnées à partir du XML.
        :return: Un dictionnaire e la forme {position : (id, chemin_vers_le_folio, coordonnees)}
        """
        print(f"Getting coordinates for {element}")
        liste_element = self.root.xpath(element, namespaces=tei)
        liste_images = [element.xpath("preceding::tei:pb[1]/@facs", namespaces=tei)[0] for element in liste_element]
        global dict_of_arrays
        dict_of_arrays = {}
        for image in list(set(liste_images)):
            as_array = np.asarray(Image.open(image).convert("RGBA"))
            maskIm = Image.new('L', (as_array.shape[1], as_array.shape[0]), 0)
            dict_of_arrays[image] = (as_array, maskIm)
        self.input_format = liste_images[0].split(".")[-1]
        liste_coordonnees = [element.xpath("@facs", namespaces=tei)[0] for element in liste_element]

        liste_coordonnees_et_positions = list(
            zip(
                range(len(liste_coordonnees)), liste_images, liste_coordonnees
            )
        )
        dict_coordonnees_et_positions = {}
        for position, image, coordonnees in liste_coordonnees_et_positions:
            dict_coordonnees_et_positions[position] = generateur_id(), image, self.formattage_coordonnes(coordonnees)

        self.coordonnees = dict_coordonnees_et_positions

    def formattage_coordonnes(self, coordonnees):
        x_coords = coordonnees.split(' ')[0::2]
        y_coords = coordonnees.split(' ')[1::2]
        result = [(int(x), int(y)) for x, y in
                  list(
                      zip(x_coords, y_coords)
                  )
                  ]

        return result

    def extraction_parallele(self):
        # https://stackoverflow.com/a/57364423
        with mp.Pool(processes=int(self.workers)) as pool:
            data = [(self.directory, identifiant, image_path, coordonnees, self.input_format) for
                    _, (identifiant, image_path, coordonnees) in self.coordonnees.items()]
            for _ in tqdm.tqdm(pool.istarmap(extract_images, data),
                               total=len(data)):
                pass

    def update_xml_tree(self, element):
        """
        Met à jour l'arbre XML de sortie: crée un élément tei:surface, ajoute les liens vers l'image découpée
        et met à jour l'élément correspondant en lui ajoutant un @facs qui pointe vers cette zone
        :param element:
        :return:
        """
        print(f"Updating xml tree for {element}")
        all_element = self.root.xpath(element, namespaces=tei)  # https://stackoverflow.com/a/17269384 pour l'efficacité
        # plutôt que de chercher à chaque fois le bon élément tei avec un count(preceding::tei:*) qui est très
        # long à calculer

        for position, (identifiant, path_to_folio, coordonnees) in self.coordonnees.items():
            folio_basename = path_to_folio.split("/")[-1]
            path_to_line = f"../../lignes/{self.directory}/{folio_basename.replace(f'.{self.input_format}', '')}_{identifiant}.png"
            coordonnees_out = []
            for tuple_coordonnees in coordonnees:
                x, y = tuple_coordonnees
                coordonnees_out.append(f"{x},{y}")
            chaine_coordonnees = " ".join(coordonnees_out)

            xml_id = f"elem_{identifiant}"
            current_lb = all_element[position]
            current_lb.set("facs", f"#facs_{identifiant}")
            current_lb.set('{http://www.w3.org/XML/1998/namespace}id', xml_id)

            facsimile = self.root.xpath("//tei:facsimile", namespaces=tei)[0]
            surface = etree.SubElement(facsimile, f"{tei_namespace}surface")
            surface.set('{http://www.w3.org/XML/1998/namespace}id', f"facs_{identifiant}")
            surface.set("points", chaine_coordonnees)
            surface.set("corresp", f"#{xml_id}")
            graphic = etree.SubElement(surface, f"{tei_namespace}graphic")
            graphic.set("url", path_to_line)

    def get_images(self, xpath_expressions):
        """
        Cette fonction permet d'extraire les coordonnées, les images, et de créer le xml de sortie.
        :param xpath_expression: une expression xpath vers l'élément donc les images sont à extraire.
        :return: None
        """
        for expression in xpath_expressions:
            self.get_coordinates(expression)
            self.extraction_parallele()
            self.update_xml_tree(expression)

    def produce_xml_file(self):
        print("Saving xml file.")
        sortie = f'output/{self.directory}/{self.sigle}_out.xml'

        for page_break in self.root.xpath("//tei:pb", namespaces=tei):
            path = page_break.xpath("@facs")[0]
            page_break.set("facs", f"../../{path}")

        with open(sortie, 'w+') as sortie_xml:
            output = etree.tostring(self.root, pretty_print=True, encoding='utf-8', xml_declaration=True).decode('utf8')
            sortie_xml.write(str(output))


def generateur_lettre_initiale(size=1, chars=string.ascii_lowercase):  # éviter les nombres en premier caractère de
    # l'@xml:id (interdit)
    return ''.join(random.choice(chars) for _ in range(size))


def generateur_id(size=5, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    return generateur_lettre_initiale() + ''.join(random.choice(chars) for _ in range(size))


def extract_images(directory, identifiant, image_path, coordonnees, input_format):
    """
    Extrait les images des lignes à partir des coordonnées extraites auparavant.
    :return: None
    """
    # https://stackoverflow.com/a/22650239
    image_basename = image_path.split("/")[-1]

    # convert to numpy (for convenience)
    # image_array = np.asarray(image)
    global dict_of_arrays
    image_array = dict_of_arrays[image_path][0]
    maskIm = dict_of_arrays[image_path][1]
    polygone = coordonnees
    # maskIm = Image.new('L', (image_array.shape[1], image_array.shape[0]), 0)  # c'est ici qu'on initialise
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
    cropped_img.save(f"lignes/{directory}/{image_basename.replace(f'.{input_format}', '')}_{identifiant}.png")


tei = {'tei': 'http://www.tei-c.org/ns/1.0'}
tei_namespace_url = 'http://www.tei-c.org/ns/1.0'
tei_namespace = '{%s}' % tei_namespace_url
NSMAP0 = {None: tei}
saxon = "saxon9he.jar"

arguments = argparse.ArgumentParser()
arguments.add_argument("-i", "--inputs", help="Input folder")
arguments.add_argument("-s", "--sigla", help="Sigla and output folder")
arguments.add_argument("-w", "--workers", help="Number of workers", default=1)
arguments.add_argument("-c", "--conf", help="Path to conf file with correct tagrefs", default=1)

arguments = arguments.parse_args()
inputs = arguments.inputs
sigla = arguments.sigla
workers = arguments.workers
conf_file = arguments.conf

with open(conf_file, "r") as input_conf_file:
    conf_dict = json.load(input_conf_file)

MainZone = conf_dict["MainZone"]
MarginTextZone = conf_dict["MarginTextZone"]
NumberingZone = conf_dict["NumberingZone"]
QuireMarksZone = conf_dict["QuireMarksZone"]
RunningTitleZone = conf_dict["RunningTitleZone"]
TitleZone = conf_dict["TitleZone"]
DropCapitalZone = conf_dict["DropCapitalZone"]
HeadingLine_rubric = conf_dict["HeadingLine_rubric"]

global dict_of_arrays
extract(inputs, sigla, workers)
