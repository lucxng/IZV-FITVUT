# FIT VUT Brno
# IZV - Projekt část 1.
# Autor: Thanh Lam Nguyenová (xnguye18)

import requests, os, re, sys, io
import numpy as np
import zipfile, csv, pickle, gzip
from bs4 import BeautifulSoup

class DataDownloader:
    data = {}

    def __init__(self, url="https://ehw.fit.vutbr.cz/izv", folder="data", cache_filename="data_{}.pkl.gz"):
        """
        Parametry:
            url - ukazuje, z jaké adresy se data načítají
            folder - říká, kam se mají dočasná data ukládat
            cache_filename - říká, kam se soubor s rozpracovanými daty bude ukládat a odkud se budou data brát pro další zpracování
        """
        this_path = os.path.realpath(__file__)
        this_name = os.path.basename(__file__)
        
        self.url = url
        self.folder = this_path.replace(this_name, folder)
        self.cache_filename = this_path.replace(this_name, cache_filename)
        # seznam všech zip souborů
        self.list_zip = self.get_files_url()    


    def get_region_file(self, code):
        """
        Funkce vrací název souboru podle zadaného tříznakového kódu regionu
        Pokud je zadán špatný kód, vrací False
        Parametry:
            code - tříznakový kód regionu
        """
        regions = {
            "PHA": "00.csv",    "STC": "01.csv",    "JHC": "02.csv",    
            "PLK": "03.csv",    "ULK": "04.csv",    "HKK": "05.csv",    
            "JHM": "06.csv",    "MSK": "07.csv",    "OLK": "14.csv",    
            "ZLK": "15.csv",    "VYS": "16.csv",    "PAK": "17.csv",    
            "LBK": "18.csv",    "KVK": "19.csv"
        }
        if code not in regions:
            return False
        return regions.get(code)


    def download_zip(self, zip_name):
        """
        Funkce stáhne zadaný soubor z 'url'
        Parametry:
            zip_name - název souboru ke stažení
        """
        # url souboru ke stažení
        z_url = self.url + "/" + os.path.basename(self.folder) + "/" + zip_name 
        # destinace stažení
        z_path = self.folder + "/" + zip_name 
        r = requests.get(z_url)
        with open(z_path, 'wb') as x:
            x.write(r.content)


    def get_soup(self):
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15"}
        response = requests.get(self.url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        return soup


    def get_files_url(self):
        """
        Funkce vrací seznam posledních zip souborů ve všech letech
        """
        list_zip = []
        soup = self.get_soup()
        months = soup.find_all('tr')    # list měsíců
        months_count = len(months)      # celkový počet měsíců

        for x in range(11, months_count, 12):
            # last_zip ... prosincový soubor v roce
            last_zip = months[x].findChild('a', href=re.compile(r'.zip')) 
            # pokud Prosinec není posledním měsícem v roce
            if last_zip is None:
                # hledání nejaktuálnějšího zip souboru v roce
                for y in range(x-1, x-12, -1): 
                    # this_zip ... poslední měsíc v roce
                    this_zip = months[y].findChild('a', href=re.compile(r'.zip'))
                    if this_zip is not None:
                        list_zip.append(os.path.basename(this_zip.get('href')))
                        break
            else:
                list_zip.append(os.path.basename(last_zip.get('href')))
        return list_zip


    def download_data(self):
        """
        Funkce stáhne do datové složky ​folder​ všechny soubory s daty z adresy ​url
        """
        # pokud složka 'folder' neexistuje, vytvoří se nová
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)
        # stažení zip souborů
        for zipfile in self.list_zip:
            self.download_zip(zipfile)


    def check_region_files(self, file_name):
        """
        Funkce kontroluje, zda jsou všechny soubory s daty daného regionu staženy
        Parametry:
            file_name - název souboru příslušného kraje (např. 00.csv = Praha)
        """
        # pokud neexistuje složka 'data', tzn. data nejsou stažena -> stažení dat
        if not os.path.exists(self.folder):
            self.download_data()
        else:
            # pokud chybí nějaký rok -> znovustažení
            for x in self.list_zip:
                if x not in os.listdir(self.folder):
                    self.download_data()
            # kontrola, jestli soubor s daty v nějakém roce nechybí
            for f in os.listdir(self.folder):
                if f.endswith(".zip"):
                    zip_file = zipfile.ZipFile(os.path.join(self.folder, f))
                    data_list = zip_file.namelist()
                    if file_name not in data_list:
                        self.download_data()


    def parse_num(self, thislist, column, condition):
        """
        Parsování číselného záznamu a následné přidání do seznamu.
        Pokud má záznam špatnou hodnotu nebo je prázdný, do seznamu se přidá hodnota -1.
        Parametry:
            thislist - výsledný seznam záznamů daného sloupce
            column - sloupec v csv souboru
            condition - podmínka
        """
        try:
            thislist.append(column) if int(column) in condition else thislist.append(-1)
        except ValueError:
            thislist.append(-1)


    def parse_unum(self, thislist, column):
        """
        Parsování číselného záznamu a následné přidání do seznamu.
        Pokud má záznam špatnou nebo zápornou hodnotu nebo je prázdný, do seznamu se přidá hodnota -1.
        Parametry:
            thislist - výsledný seznam záznamů daného sloupce
            column - sloupec v csv souboru
        """
        try:
            thislist.append(column) if int(column) >= 0 else thislist.append(-1)
        except ValueError:
            thislist.append(-1)


    def parse_float(self, thislist, column):
        """
        Parsování float záznamu a následné přidání do seznamu.
        Pokud má záznam špatnou hodnotu nebo je prázdný, do seznamu se přidá hodnota -1.0
        Parametry:
            thislist - výsledný seznam záznamů daného sloupce
            column - sloupec v csv souboru
        """
        try:
            thislist.append(column.replace(',', '.')) if float(column.replace(',', '.')) else thislist.append(-1)
        except ValueError:
            thislist.append(-1)


    def parse_str(self, thislist, column):
        """
        Přidání string záznamu do seznamu (prázdná hodnota není považována za špatnou)
        Parametry:
            thislist - výsledný seznam záznamů daného sloupce
            column - sloupec v csv souboru
        """
        thislist.append(column)


    def parse_region_data(self, region):
        """
        Pro daný region daný tříznakovým kódem ​vyparsuje do formátu tuple: (seznam sloupců, seznam NumPy polí s daty)
        Každé NumPy pole představuje jeden sloupec.
        Parametry:
        region -- region specifikovaný tříznakovým kódem, který se má vyparsovat
        """
        # špatně zadaný tříznakový kód
        if self.get_region_file(region) is False:   
            print("Unknown region")
            return False
        else:
            # název cache souboru podle regionu (např. data_JHM.pkl.gz)
            cache_f = self.cache_filename.format(region)
            # pokud pro daný region už existuje cache soubor -> výsledek se načte z tohoto souboru
            if os.path.basename(cache_f) in os.listdir(os.path.abspath(os.path.join(os.path.realpath(__file__), os.pardir))):
                with gzip.open(cache_f, 'rb') as gz:
                    this_tuple = pickle.load(gz)
                    gz.close()
                return this_tuple
            # pokud neexistuje cache soubor, ale výsledek je v atributu 
            elif region in self.data:
                return self.data.get(region)
            # pokud neexistuje cache soubor ani atribut s daty -> parsing
            else:
                # název souboru regionu z tříznakového kódu
                file_name = self.get_region_file(region)
                # kontrola, jestli jsou všechny soubory k parsování ve 'folder'
                self.check_region_files(file_name)          

                # seznam sloupců
                columns = [
                "ID", "Druh pozemni komunikace", "Cislo pozemni komunikace", "Datum", "Den v tydnu", "Cas", "Druh nehody", "Druh srazky",
                "Druh prekazky", "Charakter nehody", "Zavineni nehody", "Alkohol pritomen", "Hlavni priciny nehody", "Usmrceno",
                "Tezce zraneno", "Lehce zraneno", "Celkova hmotna skoda", "Druh povrchu vozovky", "Stav povrchu vozovky v dobe nehody",
                "Stav komunikace", "Povetrnostni podminky v dobe nehody", "Viditelnost", "Rozhledove pomery", "Deleni komunikace",
                "Situovani nehody na komunikaci", "Rizeni provozu v dobe nehody", "Mistni uprava prednosti v jizde",
                "Specificka mista a objekty v miste nehody", "Smerove pomery", "Pocet zucastnenych vozidel", "Misto dopravni nehody",
                "Druh krizujici komunikace", "Druh vozidla", "Vyrobni znacka motoroveho vozidla", "Rok vyroby vozidla", "Charakteristika vozidla",
                "Smyk", "Vozidlo po nehode", "Unik provoznich, prepravovanych hmot", "Zpusob vyprosteni osob z vozidla",
                "Smer jizdy nebo postaveni vozidla", "Skoda na vozidle", "Kategorie ridice", "Stav ridice", "Vnejsi ovlineni ridice",
                "a", "b", "d", "e", "f", "g", "h", "i", "j", "k", "l", "n", "o", "p", "q", "r", "s", "t", "Lokalita nehody", "Kód regionu"
                ]
                # seznamy dat sloupců
                id_cislo, druh_kom, cislo_kom, datum, weekday, cas, druh_n, druh_sr, druh_prek, charakt_n, zavineni_n, alkohol, priciny_n = ([] for i in range(13))
                usmrceno, tezce_zr, lehce_zr, celkova_skoda, povrch_v, stav_povr_v, stav_kom, povetr_podm, viditelnost, rozhl_pom = ([] for i in range(10))
                deleni_kom, situovani_n, rizeni_pr, upr_predn, mista_objekty, smerove_pom, pocet_v, misto_n, kriz_kom, druh_v, znacka_v = ([] for i in range(11))
                rok_vyroby_v, charakt_v, smyk, v_po_nehode, unik_hmot, zp_vypr_osob, smer_post, skoda_na_v, kategorie_r, stav_r, vnejsi_ovl_r = ([] for i in range(11))
                a, b, d, e, f, g, h, i, j, k, l, n, o, p, q, r, s, t, lokalita_nehody, kod = ([] for i in range(20))

                for files in os.listdir(self.folder):
                    if files.endswith(".zip"):
                        with zipfile.ZipFile(os.path.join(self.folder, files), 'r') as zf:
                            with (zf.open(file_name)) as zfile:
                                reader = csv.reader(io.TextIOWrapper(zfile, encoding="windows-1250"), delimiter=';')
                                for row in reader:
                                    kod.append(region)
                                    self.parse_str(id_cislo,    row[0])
                                    self.parse_num(druh_kom,    row[1],     range(0, 9))
                                    self.parse_num(cislo_kom,   row[2],     range(0,1000000))
                                    datum.append(row[3]) if row[3] != "" and re.fullmatch(r'([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))', 
                                    row[3]) != None else datum.append(-1)
                                    self.parse_num(weekday,     row[4],     range(0, 7))
                                    cas.append(row[5]) if row[5] != "" and re.fullmatch(r'([01][0-9]|2[0-3])([0-5][0-9])', 
                                    row[5]) != None else cas.append(-1)
                                    self.parse_num(druh_n,      row[6],     range(0, 10))
                                    self.parse_num(druh_sr,     row[7],     range(0, 5))
                                    self.parse_num(druh_prek,   row[8],     range(0, 10))
                                    self.parse_num(charakt_n,   row[9],     [1, 2])
                                    self.parse_num(zavineni_n,  row[10],    range(0, 8))
                                    self.parse_num(alkohol,     row[11],    range(0, 10))
                                    self.parse_num(priciny_n,   row[12],    [100]+list(range(201, 210))+list(range(301, 312))+
                                    list(range(401, 415))+list(range(501, 517))+list(range(601, 616)))
                                    self.parse_unum(usmrceno,       row[13])
                                    self.parse_unum(tezce_zr,       row[14])
                                    self.parse_unum(lehce_zr,       row[15])
                                    self.parse_unum(celkova_skoda,  row[16])
                                    self.parse_num(povrch_v,    row[17],    range(1, 7))
                                    self.parse_num(stav_povr_v, row[18],    range(0, 10))
                                    self.parse_num(stav_kom,    row[19],    range(1, 13))
                                    self.parse_num(povetr_podm, row[20],    range(0, 8))
                                    self.parse_num(viditelnost, row[21],    range(1, 8))
                                    self.parse_num(rozhl_pom,   row[22],    range(0, 7))
                                    self.parse_num(deleni_kom,  row[23],    range(0, 7))
                                    self.parse_num(situovani_n, row[24],    range(0, 10))
                                    self.parse_num(rizeni_pr,   row[25],    [0, 1, 2, 3])
                                    self.parse_num(upr_predn,   row[26],    range(0, 6))
                                    self.parse_num(mista_objekty, row[27],  range(0, 11))
                                    self.parse_num(smerove_pom, row[28],    range(1, 8))
                                    self.parse_unum(pocet_v,    row[29])
                                    self.parse_num(misto_n,     row[30],    [0]+list(range(10, 20))+list(range(22, 30)))
                                    self.parse_num(kriz_kom,    row[31],    [1, 2, 3, 6, 7, 9])
                                    self.parse_num(druh_v,      row[32],    range(0, 19))
                                    self.parse_num(znacka_v,    row[33],    range(0, 100))
                                    rok_vyroby_v.append(row[34]) if row[34] != "" and row[34] in ['XX']+list(map(str, range(0,100))) else rok_vyroby_v.append(-1)
                                    self.parse_num(charakt_v,   row[35],    range(0, 19))
                                    self.parse_num(smyk,        row[36],    [0, 1])
                                    self.parse_num(v_po_nehode, row[37],    range(0, 5))
                                    self.parse_num(unik_hmot,   row[38],    range(0, 5))
                                    self.parse_num(zp_vypr_osob, row[39],   [1, 2, 3])
                                    self.parse_num(smer_post,   row[40],    list(range(1, 7))+list(range(10, 100)))
                                    self.parse_unum(skoda_na_v, row[41])
                                    self.parse_num(kategorie_r, row[42],    range(0, 10))
                                    self.parse_num(stav_r,      row[43],    range(0, 10))
                                    self.parse_num(vnejsi_ovl_r, row[44],   range(0, 6))
                                    self.parse_float(a, row[45])
                                    self.parse_float(b, row[46])
                                    self.parse_float(d, row[47])
                                    self.parse_float(e, row[48])
                                    self.parse_float(f, row[49])
                                    self.parse_float(g, row[50])
                                    self.parse_str(h,   row[51])
                                    self.parse_str(i,   row[52])
                                    self.parse_str(j,   row[53])
                                    self.parse_str(k,   row[54])
                                    self.parse_str(l,   row[55])
                                    self.parse_str(n,   row[56])
                                    self.parse_str(o,   row[57])
                                    self.parse_str(p,   row[58])
                                    self.parse_str(q,   row[59])
                                    self.parse_str(r,   row[60])
                                    self.parse_str(s,   row[61])
                                    self.parse_str(t,   row[62])
                                    self.parse_num(lokalita_nehody, row[63], [1, 2])
                # seznam NumPy polí
                final_data = [
                    np.asarray(id_cislo, dtype='<U12'),     np.asarray(druh_kom, dtype='int8'),     np.asarray(cislo_kom, dtype='int32'), 
                    np.asarray(datum, dtype='M'),           np.asarray(weekday, dtype='int8'),      np.asarray(cas, dtype=str), 
                    np.asarray(druh_n, dtype='int8'),       np.asarray(druh_sr, dtype='int8'),      np.asarray(druh_prek, dtype='int8'),    
                    np.asarray(charakt_n, dtype='int8'),    np.asarray(zavineni_n, dtype='int8'),   np.asarray(alkohol, dtype='int8'), 
                    np.asarray(priciny_n, dtype='int16'),   np.asarray(usmrceno, dtype=int),        np.asarray(tezce_zr, dtype=int), 
                    np.asarray(lehce_zr, dtype=int),        np.asarray(celkova_skoda, dtype=int),   np.asarray(povrch_v, dtype='int8'), 
                    np.asarray(stav_povr_v, dtype='int8'),  np.asarray(stav_kom, dtype='int8'),     np.asarray(povetr_podm, dtype='int8'), 
                    np.asarray(viditelnost, dtype='int8'),  np.asarray(rozhl_pom, dtype='int8'),     np.asarray(deleni_kom, dtype='int8'), 
                    np.asarray(situovani_n, dtype='int8'),  np.asarray(rizeni_pr, dtype='int8'),    np.asarray(upr_predn, dtype='int8'), 
                    np.asarray(mista_objekty, dtype='int8'), np.asarray(smerove_pom, dtype='int8'), np.asarray(pocet_v, dtype=int), 
                    np.asarray(misto_n, dtype='int8'),      np.asarray(kriz_kom, dtype='int8'),     np.asarray(druh_v, dtype='int8'), 
                    np.asarray(znacka_v, dtype='int8'),      np.asarray(rok_vyroby_v, dtype=str),    np.asarray(charakt_v, dtype='int8'), 
                    np.asarray(smyk, dtype='int8'),         np.asarray(v_po_nehode, dtype='int8'),  np.asarray(unik_hmot, dtype='int8'), 
                    np.asarray(zp_vypr_osob, dtype='int8'), np.asarray(smer_post, dtype='int8'),    np.asarray(skoda_na_v, dtype=int), 
                    np.asarray(kategorie_r, dtype='int8'),  np.asarray(stav_r, dtype='int8'),       np.asarray(vnejsi_ovl_r, dtype='int8'),
                    np.asarray(a, dtype=float),             np.asarray(b, dtype=float),             np.asarray(d, dtype=float), 
                    np.asarray(e, dtype=float),             np.asarray(f, dtype=float),             np.asarray(g, dtype=float), 
                    np.asarray(h, dtype=str),               np.asarray(i, dtype=str),               np.asarray(j, dtype=str), 
                    np.asarray(k, dtype=str),               np.asarray(l, dtype=str),               np.asarray(n, dtype=str), 
                    np.asarray(o, dtype=str),               np.asarray(p, dtype=str),               np.asarray(q, dtype=str), 
                    np.asarray(r, dtype=str),               np.asarray(s, dtype=str),               np.asarray(t, dtype=str), 
                    np.asarray(lokalita_nehody, dtype='int8'), np.asarray(kod, dtype=str)
                ]                  

                final_tuple = (columns, final_data)

                # výsledek do cache souboru
                with gzip.open(cache_f, 'wb') as a:
                    pickle.dump(final_tuple, a)
                    a.close()
                # výsledek do atributu
                self.data[region] = final_tuple

                return final_tuple
            

    def get_list(self, regions = None):
        """
        Vrací zpracovaná data pro vybrané kraje (regiony).
        Výstupem funkce je dvojice ve stejném formátu, jako návratová hodnota funkce 'parse_region_data'.​
        Parametry:
            regions - specifikuje seznam požadovaných krajů jejich třípísmennými kódy
        """
        # seznam dvojic daných krajů
        tuples_list = []
        # pokud není seznam krajů uveden -> zpracují se všechny kraje včetně Prahy
        if regions == None:
            regions = ["PHA","STC","JHC","PLK","ULK","HKK","JHM","MSK","OLK","ZLK","VYS","PAK","LBK","KVK"]
        for reg in regions:
            # získání tuples (parsování dat)
            tuples_list.append(self.parse_region_data(reg))
        # pokud je dán pouze 1 region
        if len(tuples_list) == 1:
            return tuples_list[0]
        else:
            final_data = (tuples_list[0])[1]
            for x in range(1, len(tuples_list)):
                for y in range(len(final_data)):
                    # konkatenace numpy polí
                    final_data[y] = np.append(final_data[y], ((tuples_list[x])[1])[y])
        # seznam názvů sloupců
        columns = tuples_list[0][0]
        
        return (columns, final_data)


if __name__ == "__main__":
    result = DataDownloader().get_list()
    print('Kraje: ' + np.array2string(np.unique(result[1][64]), separator=',')[1:-1])
    print('Počet sloupců: ' + str(len(result[0])))
    print('Názvy sloupců: ' + str(result[0])[1:-1])
    print('Počet záznamů: ' + str(len(result[1][0])))