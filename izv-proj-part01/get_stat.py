# FIT VUT Brno
# IZV - Projekt část 1.
# Autor: Thanh Lam Nguyenová (xnguye18)

import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
from download import DataDownloader


def plot_stat(data_source, fig_location=None, show_figure=False):
    """
    Načítá data a vizualizuje počty nehod
    Parametry:
        data_source - data získaná z funkce get_list()
        fig_location - pokud je daná, uloží se statistika ve formátu png
        show_figure - pokud je 'True', zobrazí se statistika v okně plt.show()
    """
    # seznam let (např. ['2016', '2017', '2018'])
    roky_list = np.asarray(np.unique(data_source[1][3].astype('datetime64[Y]')), dtype=str).tolist()  
    # seznam krajů (např. ['PHA', 'JHM', 'STC'])
    kraje_list = np.unique(data_source[1][64]).tolist()
    # seznam všech let v datasetu
    roky_data = np.asarray(data_source[1][3].astype('datetime64[Y]'), dtype=str).tolist()
    # numpy pole záznamů s kraji v datasetu
    kraje_data = data_source[1][64]

    # dictionary počtu nehod v jednotlivých letech (např. { '2017': [20, 10, 30], '2018': [5, 6, 50] })
    result = {}
    for x in roky_list: 
        pocty_v_roce = []
        for i in kraje_list: 
            pocet_nehod = 0
            for y in range(len(roky_data)): 
                if roky_data[y] == x and kraje_data[y] == i:
                    pocet_nehod += 1
            pocty_v_roce.append(pocet_nehod)
        result[x] = pocty_v_roce

    # vizualizace              
    fig = plt.figure(figsize=(8.27,11.7))
    fig.suptitle('Počet nehod v ČR', fontsize='16', weight='bold')

    for a, rok in enumerate(roky_list, 1):
        plt.title(rok, pad=15)
        ax = plt.subplot(len(roky_list),1,a)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.set_axisbelow(True)
        ax.grid(axis='y', color='lightgray')
        bars = plt.bar(kraje_list, result[rok], color='indianred')

        order = []
        pocty_sorted = sorted(result[rok], reverse=True)
        for b in result[rok]:
            order.append(pocty_sorted.index(b)+1)

        for rect, o in zip(bars, order):
            height = rect.get_height()
            plt.text(rect.get_x() + rect.get_width()/2.0, height, o, ha='center', va='bottom')
            plt.text(rect.get_x() + rect.get_width()/2.0, 500, height, ha='center', va='bottom', color='white', fontsize='8')

    plt.tight_layout()

    if show_figure:
        plt.show()

    if fig_location is not None:
        plt.savefig(fig_location)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fig_location')
    parser.add_argument('--show_figure')

    args = parser.parse_args()
    fig_loc = args.fig_location
    show_fig = args.show_figure

    return fig_loc, show_fig


if __name__ == "__main__":
    source = DataDownloader().get_list()
    arg1, arg2 = parse_args()
    plot_stat(source, arg1, arg2)