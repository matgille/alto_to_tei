#!/usr/bin/env python3

import argparse
import copy
import glob
import json
import string
import sys
import shutil 

import numpy as np
from PIL import Image, ImageDraw
from lxml import etree
import os
import tqdm
import random
import subprocess
import multiprocessing as mp

import istarmap
from operator import itemgetter
from itertools import groupby
from scipy.ndimage.interpolation import zoom


def move_input_files(dossier, output):
    try:
        os.mkdir(f"{output}/input_files/")
    except:
        pass
    for file in glob.glob(f"{dossier}/*"):
        shutil.copy(file, f"{output}/input_files/")

def extract(dossier, sigle, workers, output, double_page):
    fichier_xml = DocumentXML(dossier, sigle, workers, output, 1, double_page)
    print("Please make sure each xml file can be converted to a numerical value "
          "and that the input dir name matches the sigla. "
          "Error in ordering of pages could occur if not.")
    fichier_xml.to_tei()
    # fichier_xml.produce_headings()
    # fichier_xml.get_images(["//tei:lb", "//tei:graphic[@type='lettrine']", "//tei:add"])
    # fichier_xml.get_images(["//tei:lb", "//tei:add"])
    fichier_xml.get_images(["//tei:lb"])
    fichier_xml.test_lines_order()
    fichier_xml.produce_xml_file()
    move_input_files(dossier, output)


class DocumentXML:
    def __init__(self, dossier_entree, sigle, workers, output, resize_factor, double_page):
        self.input_folder = dossier_entree
        self.output = output
        self.sigle = sigle
        self.sortie = None
        self.root = None
        self.coordonnees = None  # On la définit plus bas.
        self.pre_extraction_file = f"{self.output}/sortie_HTR/{sigle}.xml"
        self.directory = "sortie_HTR"
        self.workers = workers
        self.original_lines_order = []
        # Le facteur de mise à l'échelle des images (réduit la consommation de RAM et la taille des lignes extraites)
        self.resize_factor = resize_factor
        self.double_page = str(double_page)
        try:
            os.mkdir(f"{self.output}")
        except:
            pass
        try:
            os.mkdir(f"{self.output}/{self.directory}")
        except:
            pass
        try:
            os.mkdir(f"{self.output}/lignes")
        except:
            pass
        try:
            os.mkdir(f"{self.output}/{self.directory}")
        except:
            [os.remove(image) for image in glob.glob(f"{self.output}/lignes/*.png")]
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
            f"double_page={self.double_page}",
            "to_tei.xsl",
            "to_tei.xsl"
        ]

        subprocess.run(list_command)
        f = etree.parse(self.pre_extraction_file)
        self.root = f.getroot()
        self.original_lines_order = self.root.xpath("//tei:lb/@n", namespaces=tei)

    def test_lines_order(self):
        lines_order = self.root.xpath("//tei:lb/@n", namespaces=tei)
        try:
            assert lines_order == self.original_lines_order
        except AssertionError:
            print(len(lines_order) == len(self.original_lines_order))
            print(set(lines_order) - set(self.original_lines_order))

    def identify_lines(self):
        lines = self.root.xpath("//tei:lb", namespaces=tei)
        [add_id(line) for line in lines]

    def get_coordinates(self, element):
        """
        Extrait les coordonnées à partir du XML.
        :return: Un dictionnaire e la forme {position : (id, chemin_vers_le_folio, coordonnees)}
        """
        print(f"Getting coordinates for {element}")
        liste_element = self.root.xpath(element, namespaces=tei)
        liste_images = [element.xpath("preceding::tei:pb[1]/@facs", namespaces=tei)[0] for element in liste_element]


        try:
            self.input_format = liste_images[0].split(".")[-1]
        except:
            self.input_format = None
        liste_coordonnees = [element.xpath("@facs", namespaces=tei)[0] for element in liste_element]
        liste_id = [element.xpath("@xml:id", namespaces=tei)[0] for element in liste_element]

        liste_id_coordonnees_et_positions = list(
            zip(
                range(len(liste_coordonnees)), liste_id, liste_images, liste_coordonnees
            )
        )
        dict_coordonnees_et_positions = {}
        for position, identifier, image, coordonnees in liste_id_coordonnees_et_positions:
            dict_coordonnees_et_positions[position] = identifier, image, self.formattage_coordonnes(
                coordonnees, self.resize_factor), self.output

        self.coordonnees = dict_coordonnees_et_positions

    def formattage_coordonnes(self, coordonnees, resize_factor):
        x_coords = coordonnees.split(' ')[0::2]
        y_coords = coordonnees.split(' ')[1::2]
        result = [(round(int(x) * resize_factor), (round(int(y) * resize_factor))) for x, y in
                  list(
                      zip(x_coords, y_coords)
                  )
                  ]

        return result

    def chargement_parallele_images(self, list_of_images, resize_factor) -> dict:
        print("Charging images.")
        dictionnary = {}
        with mp.Pool(processes=int(self.workers)) as pool:
            data = [(image, resize_factor) for image in list_of_images]
            for result in tqdm.tqdm(pool.istarmap(save_image_to_dict, data)):
                dictionnary.update(result)
        return dictionnary

    def extraction_parallele(self):
        print("Extraction de l'image de chaque ligne")
        # https://stackoverflow.com/a/57364423
        with mp.Pool(processes=int(self.workers)) as pool:
            data = [(identifiant, image_path, coordonnees, self.input_format, output) for
                    _, (identifiant, image_path, coordonnees, output) in self.coordonnees.items()]
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

        for position, (identifiant, path_to_folio, coordonnees, output) in tqdm.tqdm(self.coordonnees.items()):
            folio_basename = path_to_folio.split("/")[-1]
            path_to_line = f"../lignes/{folio_basename.replace(f'.{self.input_format}', '')}_{identifiant}.png"
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
            # surface.set("points", chaine_coordonnees)
            surface.set("corresp", f"#{xml_id}")
            graphic = etree.SubElement(surface, f"{tei_namespace}graphic")
            graphic.set("url", f"{path_to_line}")

    def produce_headings(self):
        all_lines = self.root.xpath("//tei:lb", namespaces=tei)
        all_nodes = self.root.xpath("//tei:text/descendant::tei:div/node()", namespaces=tei)
        all_nodes_and_id = [(node, node.xpath("@n") if type(node) != etree._ElementUnicodeResult else []) for node in
                            all_nodes]
        all_rubricated_lines = list()
        for index, line in enumerate(all_lines):
            try:
                line.xpath('@rend')[0] == 'rubric'
                all_rubricated_lines.append(index)
            except IndexError:
                pass

        # https://stackoverflow.com/a/2154437
        print(all_rubricated_lines)
        ranges = []
        for k, g in groupby(enumerate(all_rubricated_lines), lambda x: x[0] - x[1]):
            group = (map(itemgetter(1), g))
            group = list(map(int, group))
            ranges.append([group[0], group[-1] + 1])

        for num_div, rang in enumerate(ranges):
            element_to_insert = etree.Element("{" + tei_namespace_url + "}" + "head")
            for index, position in enumerate(range(rang[0], rang[1])):
                line = all_lines[position]
                print(index)
                if index == 0:
                    print("Yeas")
                    line.addprevious(element_to_insert)
                element_to_insert.append(line)
            rang_max = rang[-1]
            paragraph = etree.Element("{" + tei_namespace_url + "}" + "p")
            anchor = all_lines[rang_max]
            anchor_n = anchor.xpath("@n")
            anchor.addprevious(paragraph)
            try:
                rang_min_suivant = ranges[num_div + 1][0]
                anchor_suivant = all_lines[rang_min_suivant]
                anchor_suivant_n = anchor_suivant.xpath("@n")
                for index, element in enumerate(all_nodes_and_id):
                    if len(element[1]) == 1:
                        if element[1][0] == anchor_n[0]:
                            min_position_in_full_list = index
                        elif element[1][0] == anchor_suivant_n[0]:
                            max_position_in_full_list = index
                for index, position in enumerate(range(min_position_in_full_list, max_position_in_full_list)):
                    element = all_nodes[position]
                    try:
                        continue
                        paragraph.append(element)
                    except TypeError:
                        all_nodes[position - 1].tail = element
            except IndexError:
                pass

    def get_images(self, xpath_expressions):
        """
        Cette fonction permet d'extraire les coordonnées, les images, et de créer le xml de sortie.
        :param xpath_expression: une expression xpath vers l'élément donc les images sont à extraire.
        :return: None
        """
        self.charge_images()
        for expression in xpath_expressions:
            self.get_coordinates(expression)
            self.extraction_parallele()
            self.update_xml_tree(expression)
    
    def charge_images(self):
        liste_images = self.root.xpath("descendant::tei:pb/@facs", namespaces=tei)
        charged_images = self.chargement_parallele_images(list(set(liste_images)), resize_factor=self.resize_factor)
        global dict_of_arrays
        dict_of_arrays = charged_images
    
    def produce_xml_file(self):
        print("Saving xml file.")
        sortie = f'{self.output}/{self.directory}/{self.sigle}_out.xml'

        for page_break in self.root.xpath("//tei:pb", namespaces=tei):
            if "../input_files/" in page_break.xpath("@facs")[0]:
                pass
            else:
                path = page_break.xpath("@facs")[0].replace(inputs, "../input_files/")
                page_break.set("facs", f"{path}")

        with open(sortie, 'w+') as sortie_xml:
            output = etree.tostring(self.root, pretty_print=True, encoding='utf-8', xml_declaration=True).decode('utf8')
            sortie_xml.write(str(output))


def add_id(line):
    return line.set("n", generateur_id(5))


def generateur_lettre_initiale(size=1, chars=string.ascii_lowercase):  # éviter les nombres en premier caractère de
    # l'@xml:id (interdit)
    return ''.join(random.choice(chars) for _ in range(size))


def generateur_id(size=5, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    return generateur_lettre_initiale() + ''.join(random.choice(chars) for _ in range(size))


def save_image_to_dict(image, resize_factor):
    dico = {}
    print(image)
    as_array = np.asarray(Image.open(image).convert("RGBA"))
    maskIm = Image.new('L',
                       (round(as_array.shape[1] * resize_factor), round(as_array.shape[0] * resize_factor)), 0)
    new_shape = (round(as_array.shape[1] * resize_factor), round(as_array.shape[0] * resize_factor))
    im = Image.fromarray(np.uint8(as_array))
    downsampled = im.resize(new_shape, Image.Resampling.LANCZOS)
    as_array = np.array(downsampled)
    dico[image] = (as_array, maskIm)
    return dico


def extract_images(identifiant, image_path, coordonnees, input_format, output):
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
    try:
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
        cropped_img.save(f"{output}/lignes/{image_basename.replace(f'.{input_format}', '')}_{identifiant}.png")
    except TypeError:
        blank_image = np.zeros((200,200,3), np.uint8)
        # colors (three first columns, RGB)
        img = Image.fromarray(blank_image, 'RGB')
        img.save(f"{output}/lignes/{image_basename.replace(f'.{input_format}', '')}_{identifiant}.png")
        


tei = {'tei': 'http://www.tei-c.org/ns/1.0'}
tei_namespace_url = 'http://www.tei-c.org/ns/1.0'
tei_namespace = '{%s}' % tei_namespace_url
NSMAP0 = {None: tei}
saxon = "saxon9he.jar"
arguments = argparse.ArgumentParser()
arguments.add_argument("-i", "--inputs", help="Input folder")
arguments.add_argument("-s", "--sigla", help="Sigla and output folder")
arguments.add_argument("-w", "--workers", help="Number of workers", default=1)
arguments.add_argument("-o", "--output", help="Output dir", default=1)
arguments.add_argument("-dp", "--double_page", help="Page mode (single page or double page)", default=False)


arguments = arguments.parse_args()
double_page = arguments.double_page
output_dir = arguments.output
inputs = arguments.inputs
sigla = arguments.sigla
workers = arguments.workers


extract(inputs, sigla, workers, output_dir, double_page)
