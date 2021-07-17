# ADASVehicleScraper3000
This is a Jupyter Notebook program that can automatically scrape about nine car manufacturer's websites, gather information on all cars, specifically what
ADAS (advanced driving assist systems) features come standard, and output an Excel sheet in the form of a csv with this information. 

This repo mainly contains the one `rowgenerator.ipynb` file and its backups. 
This file contains the main program, split into two main sections.
The first defines the webscraper functions and logic, the other (much longer) section contains all the calls of the function on manufacturer's websites.

It also contains a `translations.csv` file that contains translations of the ADAS features (manufacturer jargon to NHTSA terminology) for the program to use.

Currently, logic, calls, and translations are present for nine manufacturers. Ford, BMW, Chevrolet, Toyota, Honda, Nissan, Jeep, Subara, and Mercedes-Benz. More can be added.


# Quick Overview of Design:
The data-pulling function, websiteoutput(), contains three main parts. 

The first pulls website content. It takes the URL of a specific car model on a manufacturer's website, then, depending on the manufacturer, 
pulls some section of either the text on the page or the raw HTML of the page.

The seconds pulls the translation databank. It reads in from 'translations.csv', an exported Excel sheet that marks which manufacturer terms correspond to which ADAS features.
As an example, Ford Copilot360 corresponds to the Lane Keep Assist and Advanced Driving Assist NHTSA featurus. This is then stored in a matrix.

The third uses both the website content and translation matrix and checks which terms are present. For some manufacturers, it's as simple as doing a text search for a term.
For others, there has to be complicated logic looking at the HTML to determine whether a term is marked as standard or optional or not available at all.
Afterwards, it writes this data as one row of 'X' marks corresponding to which ADAS features this car model has.

This websiteoutput() function, in the second section, is run on all car models and trims on those nine manufacturers available, to compile the full spreadsheet. 


FYI: This program worked as of July 2021, and even then barely. As a webscraper dependent on specific websites, it is not robust in the slightest.
It is most likely (completely certain, actually) that the program will not remain functional without being maintained. Check the last commit before using.
Otherwise, any number of things could go wrong. 
 - The same year versions of cars will not be sold, breaking the list of URLs. 
 - Manufacturer websites could change, rendering some of the program logic wrong. 
 - New features could be released, or change names, causing them to be missed by the translations.csv and the program.