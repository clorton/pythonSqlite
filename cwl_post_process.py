#!/usr/bin/python

"""
Purpose:

Assumptions/Inputs:

Outputs:

How-To Use:
This script can be invoked directly from the DTK if it is renamed to 
dtk_post_process.py, or can be imported from a script with that name and 
invoked by calling this application method.
"""

import sys
import os
import json
import csv
import warnings
import re
import time

# ----------
# Constants
# ----------
ByAgeAndGender_filename     = "output/ReportHIVByAgeAndGender.csv"
output_fn                   = "output/Calibration.json"

class ReportHIVByAgeAndGender:

    def __init__(self, filename):
        self.colMap = {}
        self.file_contents = []
        self.output = {}

        self.file_chunks = {}

        self.unique_report_years = []
        self.year_to_report_year = {}

        self.clorton = {}
        self.load_csv_file(filename)

        self.NodeIds = list(set( [int(x['NodeId']) for x in self.file_contents] ))

    def load_csv_file(self, filename):

        def convert(value):
            try:
                return float(value)
            except:
                return value

        print( time.strftime('%H:%M:%S') + ' Reading: ' + filename )
        with open( filename, 'rb') as f:
            reader = csv.DictReader(f,skipinitialspace=True)

            rows = 0
            for row in reader:
                # Convert data to float
                entry = {k:(convert(v)) for (k,v) in row.iteritems() }
                self.file_contents.append( entry )

                year = entry['Year']
                if not year in self.clorton:
                    self.clorton[year] = {}
                gender = entry['Gender']
                if not gender in self.clorton[year]:
                    self.clorton[year][gender] = {}
                age = entry['Age']
                if not age in self.clorton[year][gender]:
                    self.clorton[year][gender][age] = []
                self.clorton[year][gender][age].append( entry )

                rows += 1
        print( time.strftime('%H:%M:%S') + ' Read {0} rows.'.format( rows ) )

    def update_unique_report_years(self):
       if not self.unique_report_years:
            self.unique_report_years = list(sorted(set( [x['Year'] for x in  self.file_contents] )))

    def find_year_range(self, begin_year, end_year):
        self.update_unique_report_years()

        return [y for y in self.unique_report_years if
                    y > begin_year
                    and y <= end_year ]
 

    def find_closest_year(self, year):
        self.update_unique_report_years()

        if year in self.year_to_report_year:
            return self.year_to_report_year[year]

        closest_sim_year = min( self.unique_report_years, key=lambda x:abs(x-year))

        # Add to map
        self.year_to_report_year[year] = [closest_sim_year] # list for compatibility with find_year_range

        if abs(year-closest_sim_year) > 0.1:
            warnings.warn( 'Mapping data year ' + str(year) + " to simulation output year " + str(closest_sim_year) )

        return self.year_to_report_year[year]

    def GetOutput(self):
        return self.output

    def Process(self):
        entries = []

        self.update_unique_report_years()
        last_prevalence_year = int(self.unique_report_years[-1])
        print self.unique_report_years
        last_incidence_year = int(self.unique_report_years[-1]-1)

        # Prevalence_15_49
        entry = {}
        entry['Name'] = 'Prevalence_by_AgeBin_and_Gender'
        entry['Type'] = 'Prevalence'
        entry['Year'] = [x for x in xrange(1980, last_prevalence_year+1)]
        entry['AgeBins'] = [(15,50)]
        entry['Gender'] = [0, 1]
        entry['ByNode'] = True
        entry['Lambda_Map'] = lambda x: (
            x['Infected CD4 Under 200 (Not On ART)'],
            x['Infected CD4 200 To 349 (Not On ART)'],
            x['Infected CD4 350 To 499 (Not On ART)'],
            x['Infected CD4 500 Plus (Not On ART)'],
            x['On_ART'], 
            x['Population'])
        entry['Lambda_Reduce'] = lambda x: (x[0]+x[1]+x[2]+x[3]+x[4]) / x[5] if x[5] > 0 else 0
        #entry['Lambda_Map'] = lambda x: (x['Infected'], x['Population'])
        #entry['Lambda_Reduce'] = lambda x: x[0] / x[1] if x[1] > 0 else 0
        entries.append(entry)

        # Population
        entry = {}
        entry['Name'] = 'Population_by_5Yr_AgeBin_and_Gender'
        entry['Type'] = 'Prevalence'
        entry['Year'] = [x for x in xrange(2002, 2013+1)]
        entry['AgeBins'] = [(0,1), (1,5), (5,10), (10,15), (15,20), (20,25), (25,30), (30,35), (35,40), (40,45), (45,50), (50,55), (55,60), (60,65), (65,70), (70,75), (75,100)]
        entry['Gender'] = [0, 1]
        entry['ByNode'] = True
        entry['Lambda_Map'] = lambda x: x['Population']
        entry['Lambda_Reduce'] = lambda x: x
        entries.append(entry)

        # Infections
        entry = {}
        entry['Name'] = 'Infected_by_5Yr_AgeBin_and_Gender'
        entry['Type'] = 'Prevalence'
        entry['Year'] = [x for x in xrange(2002, 2013+1)]
        entry['AgeBins'] = [(15,20), (20,25), (25,30), (30,35), (35,40), (40,45), (45,50), (50,55)]
        entry['Gender'] = [0, 1]
        entry['ByNode'] = True
        entry['Lambda_Map'] = lambda x: (
            x['Infected CD4 Under 200 (Not On ART)'],
            x['Infected CD4 200 To 349 (Not On ART)'],
            x['Infected CD4 350 To 499 (Not On ART)'],
            x['Infected CD4 500 Plus (Not On ART)'],
            x['On_ART'])
        entry['Lambda_Reduce'] = lambda x: (x[0]+x[1]+x[2]+x[3]+x[4])
        #entry['Lambda_Map'] = lambda x: x['Infected']
        #entry['Lambda_Reduce'] = lambda x: x
        entries.append(entry)

### NATIONAL

        # ANC_Infected
        entry = {}
        entry['Name'] = 'ANC_Infected'
        entry['Type'] = 'Prevalence'
        entry['Year'] = range(1965, 2012+1)
        entry['AgeBins'] = [(0,15), (15,20), (20,25), (25,30), (30,35), (35,40), (40,45), (45,50), (50,100)]
        entry['Gender'] = [1]
        entry['ByNode'] = False
        # Percent from Table 4 of 2012 Zimbabwe ANC report
        entry['Bin_Weights'] = [0.01, 0.193, 0.303, 0.239, 0.156, 0.077, 0.015, 0.001, 0.0]
        #entry['Lambda_Map'] = lambda x: (x['Infected'])
        #entry['Lambda_Reduce'] = lambda x: x
        #entry['Lambda_PostWeighting'] = lambda x: x[0]
        entry['Lambda_Map'] = lambda x: (
            x['Infected CD4 Under 200 (Not On ART)'],
            x['Infected CD4 200 To 349 (Not On ART)'],
            x['Infected CD4 350 To 499 (Not On ART)'],
            x['Infected CD4 500 Plus (Not On ART)'],
            x['On_ART'])
        entry['Lambda_Reduce'] = lambda x: (x[0]+x[1]+x[2]+x[3]+x[4])
        entry['Lambda_PostWeighting'] = lambda x: x[0]

        entries.append(entry)

        # ANC_Population
        entry = {}
        entry['Name'] = 'ANC_Population'
        entry['Type'] = 'Prevalence'
        entry['Year'] = range(1965, 2012+1)
        entry['AgeBins'] = [(0,15), (15,20), (20,25), (25,30), (30,35), (35,40), (40,45), (45,50), (50,100)]
        entry['Gender'] = [1]
        entry['ByNode'] = False
# Percent from Table 4 of 2012 Zimbabwe ANC report
        entry['Bin_Weights'] = [0.01, 0.193, 0.303, 0.239, 0.156, 0.077, 0.015, 0.001, 0.0]
        entry['Lambda_Map'] = lambda x: (x['Population'])
        entry['Lambda_Reduce'] = lambda x: x
        entry['Lambda_PostWeighting'] = lambda x: x[0]
        entries.append(entry)

        # Mean Age of Infected 15+
        # Prevalence_MeanAge_15plus_HSRC
        #entry = {}
        #entry['Name'] = 'Mean_Age_of_Infected_15plus'
        #entry['Type'] = 'Prevalence'
        #entry['Year'] = [2002.5, 2005.5, 2008.5, 2012.5]
        #entry['AgeBins'] = [(15,100)]
        #entry['Gender'] = [0, 1]
        #entry['Lambda_Map'] = lambda x: (x['Age'] * x['Infected'], x['Infected'])
        #entry['Lambda_Reduce'] = lambda x: x[0] / x[1] if x[1] > 0 else 0
        #entries.append(entry)

        # AllCause_Deaths_under15_SSA, AllCause_Deaths_15_24_SSA, AllCause_Deaths_25_49_SSA, AllCause_Deaths_50plus_SSA, AllCause_Deaths_15plus_SSA
        #entry = {}
        #entry['Name'] = 'Deaths_by_AgeBin_and_Gender'
        #entry['Type'] = 'Incidence'
        #entry['Year'] = [x+0.5 for x in xrange(1980, last_incidence_year+1)]
        #entry['AgeBins'] = [ (0,15), (15,25), (25,50), (50,100), (15,100)]
        #entry['Gender'] = [0, 1]
        #entry['Lambda_Map'] = lambda x: x['Died']
        #entry['Lambda_Reduce'] = lambda x: x
        #entries.append(entry)

        # SSA_deaths
        #entry = {}
        #entry['Name'] = 'Deaths_by_5Yr_AgeBin_and_Gender'
        #entry['Type'] = 'Incidence'
        #entry['Year'] = [x+0.5 for x in xrange(1997, 2013+1)]
        #entry['AgeBins'] = [(15,20), (20,25), (25,30), (30,35), (35,40), (40,45), (45,50)]
        #entry['Gender'] = [0, 1]
        #entry['Lambda_Map'] = lambda x: x['Died']
        #entry['Lambda_Reduce'] = lambda x: x
        #entries.append(entry)

        # ART_number
        entry = {}
        entry['Name'] = 'Number_On_ART'
        entry['Type'] = 'Prevalence'
        entry['Year'] = [x+0.5 for x in xrange(2000, last_prevalence_year+1)]
        entry['AgeBins'] = [(0,15), (15,100)]
        entry['Gender'] = [0, 1]
        entry['ByNode'] = True
        entry['Lambda_Map'] = lambda x: x['On_ART']
        entry['Lambda_Reduce'] = lambda x: x
        entries.append(entry)

        # ART_coverage
        #entry = {}
        #entry['Name'] = 'ART_Coverage'
        #entry['Type'] = 'Prevalence'
        #entry['Year'] = [2012.5]
        #entry['AgeBins'] = [(15,25), (25,50), (50,100)]
        #entry['Gender'] = [0, 1]
        #entry['Lambda_Map'] = lambda x: (x['On_ART'], x['Infected'])
        #entry['Lambda_Reduce'] = lambda x: x[0] / x[1] if x[1] > 0 else 0
        #entries.append(entry)

        # Testing_ever
        entry = {}
        entry['Name'] = 'Testing_Ever'
        entry['Type'] = 'Prevalence'
        entry['Year'] = [x for x in xrange(1980, last_prevalence_year+1)]
        entry['AgeBins'] = [(15,20), (20,25), (25,30), (30,40), (40,50)]
        entry['Gender'] = [0, 1]
        entry['ByNode'] = False
        entry['Lambda_Map'] = lambda x: (x['Tested Ever HIVPos'], x['Tested Ever HIVNeg'], x['Population'])
        entry['Lambda_Reduce'] = lambda x: (x[0]+x[1]) / x[2] if x[2] > 0 else 0
        entries.append(entry)

        # Number Tested HIV Positive
        #entry = {}
        #entry['Name'] = 'HIVTestedPositive_by_AgeBin_and_Gender'
        #entry['Type'] = 'Incidence'
        #entry['Year'] = [x+0.5 for x in xrange(1990, last_incidence_year+1)]
        #entry['AgeBins'] = [(15,25), (25,35), (35,45), (45,60), (60,100)]
        #entry['Gender'] = [0, 1]
        #entry['Lambda_Map'] = lambda x: x['Tested Positive']
        #entry['Lambda_Reduce'] = lambda x: x
        #entries.append(entry)

        # Number Tested HIV Negative
        #entry = {}
        #entry['Name'] = 'HIVTestedNegative_by_AgeBin_and_Gender'
        #entry['Type'] = 'Incidence'
        #entry['Year'] = [x+0.5 for x in xrange(1990, last_incidence_year+1)]
        #entry['AgeBins'] = [(15,25), (25,35), (35,45), (45,60), (60,100)]
        #entry['Gender'] = [0, 1]
        #entry['Lambda_Map'] = lambda x: x['Tested Negative']
        #entry['Lambda_Reduce'] = lambda x: x
        #entries.append(entry)

        # Testing_PastYear_15plus: Percent of ever tested that tested in the past year
        #entry = {}
        #entry['Name'] = 'Testing_PastYear'
        #entry['Type'] = 'Prevalence'
        #entry['Year'] = [x+0.5 for x in xrange(1980, last_prevalence_year+1)]
        #entry['AgeBins'] = [(15,100)]
        #entry['Gender'] = [0, 1]
        #entry['Lambda_Map'] = lambda x: (x['Tested Past Year or On_ART'], x['Tested Ever HIVPos'], x['Tested Ever HIVNeg'])
        #entry['Lambda_Reduce'] = lambda x: x[0] / (x[1]+x[2]) if (x[1]+x[2]) > 0 else 0
        #entries.append(entry)

        # Testing_disaggregated_HIVpos
        #entry = {}
        #entry['Name'] = 'Testing_Ever_Disaggregated_HIVPos'
        #entry['Type'] = 'Prevalence'
        #entry['Year'] = [x+0.5 for x in xrange(1980, last_prevalence_year+1)]
        #entry['AgeBins'] = [(15,25), (25,35), (35,45), (45,60), (60,100)]
        #entry['Gender'] = [0, 1]
        #entry['Lambda_Map'] = lambda x: (x['Tested Ever HIVPos'], x['Infected'])
        #entry['Lambda_Reduce'] = lambda x: x[0] / x[1] if x[1] > 0 else 0
        #entries.append(entry)

        # Testing_disaggregated_HIVneg
        #entry = {}
        #entry['Name'] = 'Testing_Ever_Disaggregated_HIVNeg'
        #entry['Type'] = 'Prevalence'
        #entry['Year'] = [x+0.5 for x in xrange(1980, last_prevalence_year+1)]
        #entry['AgeBins'] = [(15,25), (25,35), (35,45), (45,60), (60,100)]
        #entry['Gender'] = [0, 1]
        #entry['Lambda_Map'] = lambda x: (x['Tested Ever HIVNeg'], x['Population'], x['Infected'])
        #entry['Lambda_Reduce'] = lambda x: x[0] / (x[1]-x[2]) if x[1]-x[2] > 0 else 0
        #entries.append(entry)



        for e in entries:
            if e['Name'] not in self.output:
                self.output[ e['Name'] ] = self.parse_entry(e)

        #############################################################################
        # Incidence requires special handling                                       #
        #############################################################################

        # Incidence_15_24, Incidence_15_49, Incidence_25plus
        #num = {}
        #num['Name'] = 'Newly Infected'
        #num['Type'] = 'Incidence'
        #num['Year'] = [x+0.5 for x in xrange(1980, last_incidence_year+1)]
        #num['AgeBins'] = [(15,25), (15,50), (25,100)]
        #num['Gender'] = [0, 1]
        #num['Lambda_Map'] = lambda x: x['Newly Infected']
        #num['Lambda_Reduce'] = lambda x: x

        #den = {}
        #den['Name'] = 'Susceptible'
        #den['Type'] = 'Prevalence'
        #den['Year'] = [x+0.5 for x in xrange(1980, last_incidence_year+1)]
        #den['AgeBins'] = [(15,25), (15,50), (25,100)]
        #den['Gender'] = [0, 1]
        #den['Lambda_Map'] = lambda x: x['Population'] - x['Infected']
        #den['Lambda_Reduce'] = lambda x: x

        # Parse num and den
        #num_parse = self.parse_entry(num)
        #den_parse = self.parse_entry(den)

        #incidence = {}
        #incidence['Name'] = 'Incidence'
        #incidence['Type'] = 'Incidence'
        #incidence['Year'] = num['Year']
        #incidence['AgeBins'] = num['AgeBins']
        #incidence['Gender'] = den['Gender']

        #for gender in {'Male', 'Female'}:
            #incidence[gender] = [ [n/d if d > 0 else 0 for n,d in zip(nv,dv)] for nv,dv in zip(num_parse[gender], den_parse[gender]) ]

        #self.output[ incidence['Name'] ] = incidence


    def parse_entry(self, entry):
        print( time.strftime('%H:%M:%S') + ' Parsing entry: ' + entry['Name'] )
        output = {}
        output['Name'] = entry['Name']
        output['Year'] = entry['Year']
        output['Gender'] = entry['Gender']
        output['ByNode'] = entry['ByNode']
        output['AgeBins'] = entry['AgeBins']
        output['NodeData'] = []

        if 'Bin_Weights' in entry:
            output['Bin_Weights'] = entry['Bin_Weights']

        if entry['ByNode']:
            nodes = 0
            for nodeId in self.NodeIds:
                node_data = self.parse_subentry(entry, [nodeId] )
                output['NodeData'].append(node_data)
                nodes += 1
            print( time.strftime('%H:%M:%S') + ' Processed {0} nodes.'.format( nodes ) )
        else:
            node_data = self.parse_subentry(entry, self.NodeIds)
            output['NodeData'].append(node_data)
            print( time.strftime('%H:%M:%S') + ' Processed nodes.' )

        return output


    def parse_subentry(self, entry, nodeIds):

        def chunk_func(age_bin_0, age_bin_1, gender, sim_years):
            return [ x for x in self.file_contents if
                     x['Year'] in sim_years
                     and x['Age'] >= age_bin_0
                     and x['Age'] < age_bin_1
                     and x['Gender'] == gender
                     ]

        def out_func(lambda_map, chunk):
            return [ lambda_map(x) for x in chunk if x['NodeId'] in nodeIds ]

        output = {}
        output['NodeIds'] = nodeIds

        if 0 in entry['Gender']:
            output['Male'] = []
        if 1 in entry['Gender']:
            output['Female'] = []

        for year in entry['Year']:
            if entry['Type'] is 'Prevalence':
                sim_years = self.find_closest_year(year)
            else:
                sim_years = self.find_year_range(year-0.5, year+0.5)

            for gender in entry['Gender']:
                simdat = []

                for agebin in entry['AgeBins']:
                    key = ( agebin[0], agebin[1], gender, tuple(sim_years) )
                    if key in self.file_chunks.keys():
                        #print('Cached Chunk')
                        chunk = self.file_chunks[key]
                    else:
                        #print('New Chunk')

#                        chunk = chunk_func( agebin[0], agebin[1], gender, sim_years )
                        chunk = []
                        if sim_years[0] in self.clorton:
                            year_data = self.clorton[sim_years[0]]
                            if gender in year_data:
                                gender_data = year_data[gender]
                                minimum = agebin[0]
                                maximum = agebin[1]
                                for (age, entries) in gender_data.iteritems():
                                    if (age >= minimum) and (age < maximum):
                                        chunk.extend( entries )
                                    pass

                        self.file_chunks[key] = chunk

#                    out = [ entry['Lambda_Map'](x) for x in chunk if x['NodeId'] in nodeIds ]
                    lambda_map = entry['Lambda_Map']
#                    out = [ lambda_map(x) for x in chunk if x['NodeId'] in nodeIds ]
                    out = out_func( lambda_map, chunk )

                    # Sum by channel across bins
                    if type( out[0] ) is tuple:
                        out_sum = [sum(x) for x in zip(*out)]
                    else:
                        out_sum = sum(out)

                    simdat.append( entry['Lambda_Reduce'](out_sum) )

                if 'Bin_Weights' in entry:
                    # Weighted sum across bins
                    try:    # Tuple, e.g. (x['Infected'], x['Population']
                        weighted_bin_sum = [sum(p*q for p,q in zip(entry['Bin_Weights'],x)) for x in zip(*simdat)]
                    except TypeError, te: # Scalar
                        weighted_bin_sum = [sum(p*q for p,q in zip(entry['Bin_Weights'],simdat))]

                    simfinal = entry['Lambda_PostWeighting'](weighted_bin_sum)
                else:
                    simfinal = simdat

                if gender == 0:
                    output['Male'].append( simfinal )
                else:
                    output['Female'].append( simfinal )

        return output

# -----------------------------------------------------------------------------
# The main application ...
# -----------------------------------------------------------------------------
def application():

    print( time.asctime() + " Started Python processing." )
    print( "Hello from Python!" );
    print( "Current working directory is: " + os.getcwd() )

    if os.path.isfile( ByAgeAndGender_filename ) == False :
        print( "!!!! Can't open " + ByAgeAndGender_filename +"!!!!" )
        return

    # ------------------------------------------------------
    # Read the parameter information used in the simulation
    # ------------------------------------------------------
    hiv = ReportHIVByAgeAndGender( ByAgeAndGender_filename )
    hiv.Process()
    hiv_output = hiv.GetOutput()

    # -------------------------------
    # Write the PFA results to a file
    # -------------------------------
    with open( output_fn, "w" ) as fout:
        json.dump(hiv_output, fout)

    print ("Pyhton post processing complete!")
    print( time.asctime() + " Finished Python processing." )

if __name__ == "__main__":
    application()
