from __future__ import division, absolute_import
from __future__ import print_function, unicode_literals

import numpy as np
from autologging import logged

import pkp.polimi
import pkp.detailed_model
from pkp.polimi import TriangleCoal
from pkp.detailed_model import M_elements
import cantera
import os


def set_reference_coal(name, c, h, o):
    return pkp.polimi.set_reference_coal(name,
                                         {'C': c,
                                          'H': h,
                                          'O': o})


def set_reference_coal_mass(name, c, h, o):
    ua = {}
    ua['C'] = c
    ua['H'] = h
    ua['O'] = o
    ua['N'] = 0
    ua['S'] = 0
    return pkp.detailed_model.DetailedModel(
        name=name,
        ultimate_analysis=ua,
        proximate_analysis={'FC': 50,
                            'VM': 50,
                            'Ash': 0,
                            'Moist': 0})


def set_reference_biomass(name, comp):
    biomass.TPY = 300, 101325, comp
    return pkp.polimi.set_reference_coal(
        name,
        atoms={el: biomass.elemental_mass_fraction(el)
               for el in ('C', 'H', 'O')})


biomass_xml = os.path.join(os.path.dirname(pkp.bins.__file__),
                           'Biomass.xml')
biomass = cantera.Solution(biomass_xml)

bio1 = set_reference_coal('CELL', c=6, h=10, o=5)
bio2 = set_reference_coal('HCE', c=5, h=8, o=4)
bio3 = set_reference_coal(name='LIGC', c=15, h=14, o=4)
bio4 = set_reference_coal(name='LIGO', c=20, h=22, o=10)
bio5 = set_reference_coal(name='LIGH', c=22, h=28, o=9)

# TODO check correct definition of bioSi in terms of reference species
bioS1_comp = {'CELL': 0.6, 'HCE': 0.4}
# bioS1 = set_reference_biomass(name='S1', comp=bioS1_comp)
bioS1 = set_reference_coal_mass(name='S1', c=0.448, h=0.0616, o=0.4906)

bioS2_comp = {'LIGO': 0.8, 'LIGC': 0.2}
# bioS2 = set_reference_biomass(name='S2', comp=bioS2_comp)
bioS2 = set_reference_coal_mass(name='S2', c=0.59, h=0.0544, o=0.3556)

bioS3_comp = {'LIGH': 0.8, 'LIGC': 0.2}
# bioS3 = set_reference_biomass(name='S3', comp=bioS3_comp)
bioS3 = set_reference_coal_mass(name='S3', c=0.619, h=0.064, o=0.3172)

bio_comp_species = list(set(bioS1_comp.keys() +
                            bioS2_comp.keys() +
                            bioS3_comp.keys()))

triangle_123 = TriangleCoal(bioS1, bioS2, bioS3)


@logged
class BioPolimi(pkp.polimi.Polimi):
    '''
    Biomass Polimi Multiple Step Kinetic Model
    '''
    light_gas = ['HAA',
                 'HMFU',
                 'LVG',
                 'XYLOSE',
                 'Glyoxal',
                 'Phenol',
                 'pCoumaryl',
                 'C11H12O4',
                 'C3H6O2',
                 'C3H4O2',
                 'ALD3',
                 'MECHO',
                 'C2H6OH',
                 'C2H4',
                 'CH3OH',
                 'CH4',
                 'CO2',
                 'CO',
                 'H2O',
                 'H2',
                 'GCO2',
                 'GCO',
                 'GCOH2',
                 'GH2',
                 'EtOH',
                 'HCOOH']
    raw = bio_comp_species
    char = ['Char']
    metaplast = ['CELLA',
                 'HCE',
                 'HCE1',
                 'HCE2',
                 'ACQUA',
                 'LIGOH',
                 'LIGCC',
                 'LIG',
                 'GCO2',
                 'GCO',
                 'GCOH2',
                 'GH2',
                 'GCH4',
                 'GCH3OH',
                 'GC2H4']
    tar = []

    def _define_triangle(self):
        if triangle_123.is_inside(self):
            self.triangle = triangle_123
            w = self.triangle.weights(self)
            self.composition = {
                sp: (
                    np.dot(w,
                           [b.get(sp, 0)
                            for b in [bioS1_comp, bioS2_comp,
                                      bioS3_comp]]))
                for sp in bio_comp_species}
            self.weights = w
            self.plot_vankravelen(show=False).figure.savefig(
                'biomass_vankravelen.png')
            self.plot_CH(show=False).figure.savefig(
                'biomass_CH.png')
        else:
            self.__log.error(
                'Biomass composition %s '
                'outside definition triangle\n %s',
                self.van_kravelen,
                triangle_123)
            self.plot_vankravelen(show=True)
            self.plot_CH(show=True)
            raise pkp.polimi.CompositionError(
                'Biomass composition outside definition triangle'
                '{}'.format(triangle_123))

    def plot_vankravelen(self, ax=None, show=False):
        '''Plot Van Kravelen diagram for the given biomass and
        reference'''
        import matplotlib.pyplot as plt
        import itertools
        if ax is None:
            _, ax = plt.subplots()
        for v1, v2 in itertools.combinations(triangle_123, 2):
            points = np.array([v1, v2])
            ax.plot(points[:, 0], points[:, 1], color='black',
                    marker='o', markersize=6)
        tr = self.van_kravelen
        self.__log.debug('tr[0] %s tr[1] %s', tr[0], tr[1])
        ax.plot(tr[0], tr[1], marker='o', markersize=10, color='red')
        ax.set_xlabel('O/C')
        ax.set_ylabel('H/C')
        if show:
            plt.show()
        return ax

    def plot_CH(self, ax=None, show=False):
        '''Plot CH diagram'''
        import matplotlib.pyplot as plt
        import itertools
        if ax is None:
            _, ax = plt.subplots()
        for coals in itertools.combinations(
                triangle_123.itercoals(), 2):
            c = [c.ultimate_analysis['C'] for c in coals]
            h = [h.ultimate_analysis['H'] for h in coals]
            self.__log.debug('c %s h %s', c, h)
            ax.plot(c, h, color='black',
                    marker='o', markersize=6)
        ax.plot(self.ultimate_analysis['C'],
                self.ultimate_analysis['H'],
                marker='o', markersize=10, color='red')
        ax.set_xlabel('C')
        ax.set_ylabel('H')
        if show:
            plt.show()
        return ax

    def _get_mechanism(self):
        return super(BioPolimi, self)._get_mechanism()

    def _set_mechanism(self, value=None):
        if value is None:
            value = biomass_xml
        super(BioPolimi, self)._set_mechanism(value)

    mechanism = property(_get_mechanism, _set_mechanism)
