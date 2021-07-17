#!/usr/bin/env python
# coding: utf-8

# In[25]:


import csv
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
chromedriver = r"C:\Users\nihal\Documents\chromedriver\chromedriver.exe"
options = webdriver.ChromeOptions().add_argument('--headless')


# In[2]:


from IPython.core.display import display, HTML
display(HTML("<style>.container { width:100% !important; }</style>"))


# # Old

# In[7]:



#features = input("input different marketing terms seperated by commas, with car manufacturer as the first entry, model as the second, year as the third, vehicle type as the fourth, price as the fifth").lower().split(', ')
#features = "Ford, Pre-Collision Assist with Automatic Emergency BrakingS, Lane-Keeping SystemS, BLIS with Cross-Traffic AlertS, Ford Co-Pilot360S, Ford Co-Pilot360 Assist+O, Adaptive Cruise Control with Stop-and-Go and Lane CenteringO, Speed Sign RecognitionO, Reverse Sensing SystemS, Post-Collision BrakingS".lower().split(', ')


# In[ ]:


#from urllib.request import urlopen
#
#page = urlopen('https://www.ford.com/suvs-crossovers/escape/models/escape-s/').read().lower()


# In[ ]:


#previous iteration of program, does not scrape page
#with open('translations.csv', 'r') as translations:
#    reader = csv.reader(translations, delimiter=',', quotechar='"')
#    for row in reader:
#        if row[0].lower() == 'manufacturer':
#            adas = row
#            numbers = [x for x in range(len(row))]
#        if row[0].lower() == features[0]:
#            market = [s.lower() for s in row]
#    listval = [[x, y] for x, y in zip(market, numbers)]
#    newlist = []
#    keylist = []
#    for pair in listval:
#        if ", " in pair[0]:
#            newkeys = pair[0].split(", ")
#            for newkey in newkeys:
#                newlist.append([newkey, pair[1]])
#            keylist.append(pair)
#    listval += newlist
#    for key in keylist:
#        listval.remove(key)
#    
#    datarow = [None]*(len(row)+11)
#    with open('codedrows.csv', 'a', newline='') as data:
#        for item in features:
#            bool = False
#            for pair in listval:
#                if item[:-1] == pair[0]:
#                    print(item[:-1] + " in translations")
#                    if(item[-1] == "s"):
#                        datarow[pair[1]+11] = 'X'
#                    elif(item[-1] == 'o'):
#                        if(datarow[pair[1]+11] != 'X'):
#                            datarow[pair[1]+11] = 'O'
#                    bool = True
#            if not bool:
#                print(item[:-1] + " is not in the translations dataset")
#        datarow[0] = features[0].capitalize()
#        writer = csv.writer(data, delimiter=',')
#        writer.writerow(["Manufacturer", "Model Name","Trim Level","Year","Vehicle Type","MSRP","Link", "Gas", "Diesel", "Hybrid", "PHEV", "BEV"] + adas[1:])
#        writer.writerow(datarow)


# # Functions

# In[79]:


def websiteoutput(url, manufacturer, model_name='', trim='', year='', vehicle_type='', msrp='', text=None, printfeatures=True, printpage=False, start=None, stop=None):
    
    #gets plain text from webpage
    pagetext = getpagecontent(url, manufacturer, text, printpage, start, stop)
    
    #getting translations array and adas features list from csv download of Market Translations datasheet
    adas, translations = gettranslations('translations.csv', manufacturer)

    #compare page text and translations array, creates array of Xs, writes it to a csv
    writedata('codedrows.csv', url, manufacturer, model_name, trim, year, vehicle_type, msrp, adas, translations, pagetext, printfeatures)


# In[53]:


def getpagecontent(url, manufacturer, text, printpage, start, stop):
    
    #if text is given manually, just return that
    if text:
        return text.lower()
    
    #toyota has content in html not in plain text
    
    #may need selenium later for pages that require button presses to get to the text. If I redo Ford, would require this. Scrath that, need this for Chevrolet.

    browser = webdriver.Chrome(executable_path=chromedriver, options=options)

    #some code that I don't understand and just copied from online. It gets the plain text from the webpage
    #s = requests_html.HTMLSession()
    #pagetext = s.get(url)
    browser.get(url)

    print("From website " + url)
    
    
    #loading actions for certain manufacturers
    if manufacturer == "Ford":
        pagetext = browser.page_source
        soup=bs(pagetext,'lxml')
        pagetext = soup.get_text().lower()
        pagetext = pagetext[pagetext.index("search submit"):pagetext.index("exercise your rights under the california consumer privacy act")]
        
    elif manufacturer == "BMW":
        pagetext = browser.page_source[:browser.page_source.index('<div class="disclaimers">')]
        soup=bs(pagetext,'lxml')
        pagetext = soup.get_text().lower()

    elif manufacturer == "Chevrolet":
        WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".features-compare")))
        pagetext = browser.page_source
        soup=bs(pagetext,'lxml')
        pagetext = soup.get_text().lower()
        if 'return to build' in pagetext:
            pagetext = pagetext[pagetext.index("return to build"):]
            
    elif manufacturer == 'Toyota':
        pagetext = browser.page_source
        pagetext = pagetext[pagetext.index('JSON.stringify('):]
        pagetext = pagetext[pagetext.index('fsoData:')+11:pagetext.index(',{"categoryData"')].lower()
        if start and stop:
            start = '"' + start + '":'
            stop = '"' + stop + '":'
            icounter = 0
            newtext=''
            while start in pagetext[icounter:]:
                if stop in pagetext[icounter:]:
                    sindex = pagetext.index(stop, icounter)
                else:
                    sindex = len(pagetext)-10
                newtext += pagetext[pagetext.index(start, icounter): sindex]
                icounter = sindex+1
            pagetext = newtext
        
    elif manufacturer == 'Honda':
        pagetext = browser.page_source
        pagetext = pagetext[pagetext.index('<div class="responsive-table-filter">'):].lower()
        
    elif manufacturer == 'Nissan':
        pagetext = browser.page_source
        pagetext = pagetext[pagetext.index('class="headline">'):].lower()

    browser.quit()
    if printpage: print(pagetext)
    return pagetext


# In[5]:


def gettranslations(inputpath, manufacturer):
    #pulls and returns array of Manufacturer terms and links them with the column number in the SAE datasheet
    
    #opens csv download of 'Copy of Market Translations' Google Sheet
    with open(inputpath, 'r') as translations_csv:
        reader = csv.reader(translations_csv, delimiter=',', quotechar='"')
        
        #iterates through table looking for the first row and the specific manufacturer row
        for row in reader:
            if row[0].lower() == 'manufacturer':
                adas = row
                numbers = [x for x in range(len(row))]
            if row[0].lower() == manufacturer.lower():
                market = [s.lower() for s in row]
        
        #zips together ADAS column number and the content of the cell 
        translations = [[x, y] for x, y in zip(market, numbers)]
        
        #this next bit is for splitting up the cells with multiple terms into multiple entries
        newlist = []
        keylist = []
        for pair in translations:
            #it splits them by the ', ' identifier, any cells with a comma and space will be split
            if ", " in pair[0]:
                newkeys = pair[0].split(", ")
                for newkey in newkeys:
                    #appending new entries to temp list to later add to main list
                    newlist.append([newkey, pair[1]])
                #appending old entries to another temp list to later be removed from main list
                keylist.append(pair)
            elif pair[0] == '':
                keylist.append(pair)
        translations += newlist
        for key in keylist:
            translations.remove(key)
            
        return (adas, translations)


# In[6]:


def writedata(outputpath, url, manufacturer, model_name, trim, year, vehicle_type, msrp, adas, translations, pagetext, printfeatures):
    #compares translations array with page text, creates an array of 'X's, then writes it to a csv
    
    #creates blank array to later fill
    datarow = [None]*(len(adas)+12)
    
    #sets bool to true if the output csv already exists, false otherwise. This is for whether to write the header of the csv or not.
    bool = os.path.isfile(outputpath)
    
    #special thing, we can automatically pull price
    if not msrp:
        if manufacturer == 'Chevrolet':
            if '$' in pagetext:
                msrp = pagetext[pagetext.index('$')+1:pagetext.index(' ', pagetext.index('$'))]
        elif manufacturer == 'Toyota':
            if '$' in pagetext:
                msrp = pagetext[pagetext.index('$')+1:pagetext.index('"', pagetext.index('$'))]
        elif manufacturer == 'Honda':
            # determine trim number
            tindex = pagetext.rindex('trims-', 0, pagetext.index('<h5>' + trim.lower() + '</h5>'))
            print(pagetext[tindex-50:tindex+50])
            trimnum = pagetext[tindex+6:pagetext.index('"', tindex)]
            print("Trim num = " + trimnum)
            mindex = pagetext.index('$', pagetext.index('"' + trim.lower() +'" data-starting-price'))
            msrp = pagetext[mindex+1:pagetext.index('<', mindex)]
        elif manufacturer == 'Nissan':
            mindex = pagetext.index('class="price">$')
            msrp = pagetext[mindex+len('class="price">$'):pagetext.index('<', mindex)]
            pagetext = pagetext[pagetext.index('<li class="accordion-group ', pagetext.index('data-section-type="key-features"')):pagetext.index('<div class="grade-images-placeholder">')]

    #loops through translation array
    counter = 0
    for pair in translations:
        #if a term is in the text of the page...
        if pair[0] in pagetext:
            if pair[0] == manufacturer.lower():
                continue
            
            if manufacturer == 'Ford':
                icounter=0
                while pair[0] in pagetext[icounter:]:
                    index = pagetext.index(pair[0], icounter)
                    if 'standard' in pagetext[:index]:
                        sindex = pagetext.rindex('standard', 0, index)
                    else:
                        sindex = 0
                    if 'optional' in pagetext[:index]:
                        oindex = pagetext.rindex('optional', 0, index)
                    else:
                        oindex = 0
                    if sindex > oindex:
                        if printfeatures: print(pair[0] + " in page and is " + adas[pair[1]])
                        if not datarow[pair[1]+12]: counter += 1
                        datarow[pair[1]+12] = 'X'
                        break
                    else:
                        if printfeatures: print(pair[0] + " is optional and is " + adas[pair[1]])
                    icounter = index + 1

            elif manufacturer == 'Chevrolet':
                #special thing for Chevrolet, they list all terms, then mark "standard" after the actual ones
                #find index of feature
                icounter=0
                while pair[0] in pagetext[icounter:]:
                    if pagetext[pagetext.index(pair[0], icounter) - 1] == ' ' or pagetext[pagetext.index(pair[0], icounter) + len(pair[0])] == ',':
                        icounter = pagetext.index(pair[0], icounter)+1
                    else:
                        index = pagetext.index(pair[0], icounter)
                        break
                
                if pagetext[index+len(pair[0]):index+len(pair[0])+8] == 'standard':
                    if printfeatures: print(pair[0] + " is standard and is " + adas[pair[1]])
                    if not datarow[pair[1]+12]: counter += 1
                    datarow[pair[1]+12] = 'X'
                elif pagetext[index+len(pair[0]):index+len(pair[0])+9] == 'available':
                    if printfeatures: print(pair[0] + " is optional and is " + adas[pair[1]])
                    #if not datarow[pair[1]+12]: 
                        #counter += 1
                        #datarow[pair[1]+12] = 'O'
                #else:
                    #if printfeatures: print(pair[0] + " is not available")
            
            elif manufacturer == "Toyota":
                #special for Toyota, same as above
                icounter = 0
                while pair[0] in pagetext[icounter:]:
                    index = pagetext.index(pair[0], icounter)
                    if 'standard' in pagetext[index:]:
                        sindex = pagetext.index('standard', index)
                    else:
                        sindex = len(pagetext)
                    if 'available' in pagetext[index:]:
                        aindex = pagetext.index('available', index)
                    else:
                        aindex = len(pagetext)
                    if 'not-available' in pagetext[index:]:
                        nindex = pagetext.index('not-available', index)
                    else:
                        nindex = len(pagetext)
                    
                    is_present = min(min(sindex, aindex), nindex)
                
                    if pagetext[is_present] == 's':
                        if printfeatures: print(pair[0] + " is standard and is " + adas[pair[1]])
                        if not datarow[pair[1]+12]: counter += 1
                        datarow[pair[1]+12] = 'X'
                        break
                    elif pagetext[is_present] == 'a':
                        if printfeatures: print(pair[0] + " is optional and is " + adas[pair[1]])
                        #if not datarow[pair[1]+12]: 
                            #counter += 1
                            #datarow[pair[1]+12] = 'O'
                    #elif pagetext[is_present] == 'n':
                        #if printfeatures: print(pair[0] + " is not available")
                    icounter = index + 1
            elif manufacturer == "Honda":
                #special for Toyota, same as above
                icounter = 0
                while pair[0] in pagetext[icounter:]:
                    
                    index=pagetext.index(pair[0], icounter)
                    if pagetext.rindex('col-', 0, index) > pagetext.rindex('responsive-table-fixed-column', 0, index):
                        if pagetext[pagetext.rindex('col-', 0, index)+len('col-'):pagetext.index(' ', pagetext.rindex('col-', 0, index))] == str(trimnum):
                            if printfeatures: print(pair[0] + " is standard and is " + adas[pair[1]])
                            if not datarow[pair[1]+12]: counter += 1
                            datarow[pair[1]+12] = 'X'
                            break
                        else:
                            icounter = index + 1
                            continue
                    
                    index = pagetext.index('col-'+trimnum, index)
                    brindex = pagetext.index('</td>', index)
                    is_present = min([pagetext.index(option, index, brindex) if option in pagetext[index:brindex] else len(pagetext)-1 for option in ['mi-circle-check', '<p>', 'available', 'mi-dash']])
                    
                    print(pair[0])
                    print(pagetext[index:])
                    
                    if pagetext[is_present:is_present+15] == 'mi-circle-check' or pagetext[is_present:is_present+3] == '<p>':
                        if printfeatures: print(pair[0] + " is standard and is " + adas[pair[1]])
                        if not datarow[pair[1]+12]: counter += 1
                        datarow[pair[1]+12] = 'X'
                        break
                    elif pagetext[is_present] == 'a':
                        if printfeatures: print(pair[0] + " is optional and is " + adas[pair[1]])
                        #if not datarow[pair[1]+12]: 
                            #counter += 1
                            #datarow[pair[1]+12] = 'O'
                    #elif pagetext[is_present] == 'n':
                        #if printfeatures: print(pair[0] + " is not available")
                    icounter = index + 1
            elif manufacturer == "Nissan":
                #special for Toyota, same as above
                icounter = 0
                while pair[0] in pagetext[icounter:]:
                    index = pagetext.index(pair[0], icounter)
                    brindex = pagetext.index('</tr>', index)
                    is_present = min([pagetext.index(option, index, brindex) if option in pagetext[index:brindex] else len(pagetext)-1 for option in ['icon-included', 'icon-optional', 'icon-not-included']])
                    
                    
                    if pagetext[is_present:is_present+len('icon-included')] == 'icon-included':
                        if printfeatures: print(pair[0] + " is standard and is " + adas[pair[1]])
                        if not datarow[pair[1]+12]: counter += 1
                        datarow[pair[1]+12] = 'X'
                        break
                    elif pagetext[is_present:is_present+len('icon-optional')] == 'icon-optional':
                        if printfeatures: print(pair[0] + " is optional and is " + adas[pair[1]])
                        #if not datarow[pair[1]+12]: 
                            #counter += 1
                            #datarow[pair[1]+12] = 'O'
                    #elif pagetext[is_present] == 'n':
                        #if printfeatures: print(pair[0] + " is not available")
                    icounter = index + 1
            else: 
                #print and add X to that blank array
                if printfeatures: print(pair[0] + " in page and is " + adas[pair[1]])
                if not datarow[pair[1]+12]: counter += 1
                datarow[pair[1]+12] = 'X'
    
    print(str(counter) + " ADAS features found")
    
    if manufacturer == 'Chevrolet':
        if 'diesel' in pagetext:
            index = pagetext.index('engine', pagetext.index('diesel'))
            if pagetext[index+6:index+14] == 'standard' or pagetext[index+6:index+15] == 'available':
                print("Has diesel")
                datarow[8] = 'X'
    
    #add the beginning info to the row of data
    datarow[0] = manufacturer
    datarow[1] = model_name
    datarow[2] = trim
    datarow[3] = year
    datarow[4] = vehicle_type
    datarow[5] = msrp
    datarow[6] = '=HYPERLINK("'+url+'", "L")'
    datarow[12] = ''
    
    
    #opens csv to write into
    with open(outputpath, 'a', newline='') as data:
        writer = csv.writer(data, delimiter=',')
        
        #writes an ADAS header if the file is new
        if not bool: 
            writer.writerow(["Manufacturer", "Model Name","Trim Level","Year","Vehicle Type","MSRP","Link", "Gas", "Diesel", "Hybrid", "PHEV", "FEV", "BEV"] + adas[1:])
            
        #writes data
        writer.writerow(datarow)


# In[7]:


def toyotadata(url, model, trims, trimdatas, year='', vehicle_type='', printfeatures=False, printpage=False):
    for i, trim in enumerate(trims):
        print("/n")
        print("trim is " + trim)
        websiteoutput(url, 'Toyota', model, trim, year, vehicle_type, printfeatures=printfeatures, printpage=printpage, start=trimdatas[i], stop=trimdatas[(i+1) % len(trimdatas)])


# In[8]:


def modeloutput(url, manufacturer, model='', trims=[], year='', vehicle_type='', msrp='', text=None, printfeatures=False, printpage=False, start=None, stop=None):
    for trim in trims:
        print("trim is " + trim)
        websiteoutput(url, manufacturer, model, trim, year, vehicle_type, None, text, printfeatures, printpage, start, stop)


# # Ford

# Ford's Models

# In[66]:


websiteoutput('https://www.ford.com/suvs-crossovers/escape/models/escape-s/', 'Ford')
websiteoutput('https://www.ford.com/suvs-crossovers/escape/models/escape-se/', 'Ford')
websiteoutput('https://www.ford.com/suvs-crossovers/escape/models/escape-sel/', 'Ford')
websiteoutput('https://www.ford.com/suvs-crossovers/escape/models/escape-titanium/', 'Ford')


# In[67]:


websiteoutput('https://www.ford.com/suvs-crossovers/ecosport/models/ecosport-s/', 'Ford')
websiteoutput('https://www.ford.com/suvs-crossovers/ecosport/models/ecosport-se/', 'Ford')
websiteoutput('https://www.ford.com/suvs-crossovers/ecosport/models/ecosport-titanium/', 'Ford')
websiteoutput('https://www.ford.com/suvs-crossovers/ecosport/models/ecosport-ses/', 'Ford')


# In[68]:


websiteoutput('https://www.ford.com/suvs/bronco-sport/models/bronco-sport-base/', 'Ford')
websiteoutput('https://www.ford.com/suvs/bronco-sport/models/bronco-sport-big-bend/', 'Ford')
websiteoutput('https://www.ford.com/suvs/bronco-sport/models/bronco-sport-outer-banks/', 'Ford')
websiteoutput('https://www.ford.com/suvs/bronco-sport/models/bronco-sport-badlands/', 'Ford')
websiteoutput('https://www.ford.com/suvs/bronco-sport/models/bronco-sport-first-edition/', 'Ford')


# In[69]:


websiteoutput('https://www.ford.com/suvs/bronco/models/bronco-base/', 'Ford')
websiteoutput('https://www.ford.com/suvs/bronco/models/bronco-big-bend/', 'Ford')
websiteoutput('https://www.ford.com/suvs/bronco/models/bronco-black-diamond/', 'Ford')
websiteoutput('https://www.ford.com/suvs/bronco/models/bronco-outer-banks/', 'Ford')
websiteoutput('https://www.ford.com/suvs/bronco/models/bronco-badlands/', 'Ford')
websiteoutput('https://www.ford.com/suvs/bronco/models/bronco-wildtrak/', 'Ford')
websiteoutput('https://www.ford.com/suvs/bronco/models/bronco-first-edition/', 'Ford')


# In[70]:


websiteoutput('https://www.ford.com/suvs-crossovers/edge/models/edge-se/', 'Ford')
websiteoutput('https://www.ford.com/suvs-crossovers/edge/models/edge-sel/', 'Ford')
websiteoutput('https://www.ford.com/suvs-crossovers/edge/models/edge-st-line/', 'Ford')
websiteoutput('https://www.ford.com/suvs-crossovers/edge/models/edge-titanium/', 'Ford')
websiteoutput('https://www.ford.com/suvs-crossovers/edge/models/edge-st/', 'Ford')


# In[71]:


websiteoutput('https://www.ford.com/suvs/explorer/models/explorer/', 'Ford')
websiteoutput('https://www.ford.com/suvs/explorer/models/explorer-xlt/', 'Ford')
websiteoutput('https://www.ford.com/suvs/explorer/models/explorer-limited/', 'Ford')
websiteoutput('https://www.ford.com/suvs/explorer/models/explorer-st/', 'Ford')
websiteoutput('https://www.ford.com/suvs/explorer/models/explorer-king-ranch/', 'Ford')
websiteoutput('https://www.ford.com/suvs/explorer/models/explorer-platinum/', 'Ford')


# In[72]:


websiteoutput('https://www.ford.com/suvs/mach-e/models/mach-e-select/', 'Ford')
websiteoutput('https://www.ford.com/suvs/mach-e/models/mach-e-california-route-1/', 'Ford')
websiteoutput('https://www.ford.com/suvs/mach-e/models/mach-e-premium/', 'Ford')
websiteoutput('https://www.ford.com/suvs/mach-e/models/mach-e-gt/', 'Ford')


# In[73]:


websiteoutput('https://www.ford.com/suvs/expedition/models/expedition-xl-stx/', 'Ford')
websiteoutput('https://www.ford.com/suvs/expedition/models/expedition-xlt/', 'Ford')
websiteoutput('https://www.ford.com/suvs/expedition/models/expedition-limited/', 'Ford')
websiteoutput('https://www.ford.com/suvs/expedition/models/expedition-king-ranch/', 'Ford')
websiteoutput('https://www.ford.com/suvs/expedition/models/expedition-platinum/', 'Ford')


# In[74]:


websiteoutput('https://www.ford.com/trucks/ranger/models/ranger-xl/', 'Ford')
websiteoutput('https://www.ford.com/trucks/ranger/models/ranger-xlt/', 'Ford')
websiteoutput('https://www.ford.com/trucks/ranger/models/ranger-lariat/', 'Ford')


# In[75]:


websiteoutput('https://www.ford.com/trucks/f150/models/f150-xl/', 'Ford')
websiteoutput('https://www.ford.com/trucks/f150/models/f150-xlt/', 'Ford')
websiteoutput('https://www.ford.com/trucks/f150/models/f150-lariat/', 'Ford')
websiteoutput('https://www.ford.com/trucks/f150/models/f150-king-ranch/', 'Ford')
websiteoutput('https://www.ford.com/trucks/f150/models/f150-platinum/', 'Ford')
websiteoutput('https://www.ford.com/trucks/f150/models/f150-limited/', 'Ford')


# In[76]:


websiteoutput('https://www.ford.com/trucks/super-duty/models/f250-xl/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f250-xlt/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f250-lariat/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f250-king-ranch/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f250-platinum/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f250-limited/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f350-xl/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f350-xlt/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f350-lariat/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f350-king-ranch/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f350-platinum/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f350-limited/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f450-xl/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f450-xlt/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f450-lariat/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f450-king-ranch/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f450-platinum/', 'Ford')
websiteoutput('https://www.ford.com/trucks/super-duty/models/f450-limited/', 'Ford')


# In[77]:


websiteoutput('https://www.ford.com/trucks/transit-connect-passenger-van-wagon/models/transit-connect-xl-passenger-wagon/', 'Ford')
websiteoutput('https://www.ford.com/trucks/transit-connect-passenger-van-wagon/models/transit-connect-xlt-passenger-wagon/', 'Ford')
websiteoutput('https://www.ford.com/trucks/transit-connect-passenger-van-wagon/models/transit-connect-titanium-passenger-wagon/', 'Ford')


# In[78]:


websiteoutput('https://www.ford.com/trucks/transit-passenger-van-wagon/models/transit-xl/', 'Ford')
websiteoutput('https://www.ford.com/trucks/transit-passenger-van-wagon/models/transit-xlt/', 'Ford')


# In[79]:


websiteoutput('https://www.ford.com/cars/fusion/models/fusion-s/', 'Ford')
websiteoutput('https://www.ford.com/cars/fusion/models/fusion-se/', 'Ford')
websiteoutput('https://www.ford.com/cars/fusion/models/fusion-sel/', 'Ford')
websiteoutput('https://www.ford.com/cars/fusion/models/fusion-titanium/', 'Ford')
websiteoutput('https://www.ford.com/cars/fusion/models/fusion-hybrid-se/', 'Ford')
websiteoutput('https://www.ford.com/cars/fusion/models/fusion-hybrid-sel/', 'Ford')
websiteoutput('https://www.ford.com/cars/fusion/models/fusion-hybrid-titanium/', 'Ford')
websiteoutput('https://www.ford.com/cars/fusion/models/fusion-plug-in-hybrid-titanium/', 'Ford')


# In[80]:


websiteoutput('https://www.ford.com/cars/mustang/models/ecoboost-fastback/', 'Ford')
websiteoutput('https://www.ford.com/cars/mustang/models/ecoboost-premium-fastback/', 'Ford')
websiteoutput('https://www.ford.com/cars/mustang/models/ecoboost-convertible/', 'Ford')
websiteoutput('https://www.ford.com/cars/mustang/models/ecoboost-premium-fastback/', 'Ford')
websiteoutput('https://www.ford.com/cars/mustang/models/gt-fastback/', 'Ford')
websiteoutput('https://www.ford.com/cars/mustang/models/gt-premium-fastback/', 'Ford')
websiteoutput('https://www.ford.com/cars/mustang/models/gt-premium-convertible/', 'Ford')
websiteoutput('https://www.ford.com/cars/mustang/models/mach-1/', 'Ford')
websiteoutput('https://www.ford.com/cars/mustang/models/mach-1-premium/', 'Ford')
websiteoutput('https://www.ford.com/cars/mustang/models/shelby-gt500/', 'Ford')


# # BMW

# BMW's Models

# In[142]:


websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21XA.html', 'BMW', 'X1', 'sDrive28i', '2021', 'SUV', '35,400')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21XB.html', 'BMW', 'X1', 'xDrive28i', '2021', 'SUV', '37,400')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.22XX.html', 'BMW', 'X2', 'sDrive28i', '2022', 'SUV', '36,600')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.22XY.html', 'BMW', 'X2', 'xDrive28i', '2022', 'SUV', '38,600')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.22XZ.html', 'BMW', 'X2', 'M35i', '2022', 'SUV', '46,450')


# In[143]:


websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21XQ.html', 'BMW', 'X3', 'sDrive30i', '2021', 'SUV', '43,000')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21XD.html', 'BMW', 'X3', 'xDrive30i', '2021', 'SUV', '45,000')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21SC.html', 'BMW', 'X3', 'xDrive30e', '2021', 'SUV', '49,600')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21XE.html', 'BMW', 'X3', 'M40i', '2021', 'SUV', '56,600')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21SO.html', 'BMW', 'X3', 'M', '2021', 'SUV', '69,900')


# In[144]:


websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21XR.html', 'BMW', 'X4', 'xDrive30i', '2021', 'SUV', '51,600')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21XV.html', 'BMW', 'X4', 'M40i', '2021', 'SUV', '61,700')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21SP.html', 'BMW', 'X4', 'M', '2021', 'SUV', '73,400')


# In[145]:


websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21XO.html', 'BMW', 'X5', 'sDrive40i', '2021', 'SUV', '59,400')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21XG.html', 'BMW', 'X5', 'xDrive40i', '2021', 'SUV', '61,700')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21XT.html', 'BMW', 'X5', 'xDrive45e', '2021', 'SUV', '65,400')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21SJ.html', 'BMW', 'X5', 'M50i', '2021', 'SUV', '82,800')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21XK.html', 'BMW', 'X5', 'M', '2021', 'SUV', '105,100')


# In[146]:


websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21XU.html', 'BMW', 'X6', 'sDrive40i', '2021', 'SUV', '65,050')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21XL.html', 'BMW', 'X6', 'xDrive40i', '2021', 'SUV', '67,350')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21XM.html', 'BMW', 'X6', 'M50i', '2021', 'SUV', '86,250')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21XN.html', 'BMW', 'X6', 'M', '2021', 'SUV', '108,600')


# In[147]:


websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21SA.html', 'BMW', 'X7', 'xDrive40i', '2021', 'SUV', '74,900')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21SL.html', 'BMW', 'X7', 'M50i', '2021', 'SUV', '99,800')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21SQ.html', 'BMW', 'X7 Alpina', 'Alpina XB7', '2021', 'SUV', '141,300')


# In[148]:


websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.212V.html', 'BMW', '2', '228i Gran Coupe', '2021', 'Sedan', '35,700')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.212T.html', 'BMW', '2', '228i xDrive Gran Coupe', '2021', 'Sedan', '37,700')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.212U.html', 'BMW', '2', 'M235i xDrive Gran Coupe', '2021', 'Sedan', '45,500')


# In[149]:


websiteoutput('https://www.bmwusa.com/vehicles/2-series/coupe/pricing-features.html', 'BMW', '2', '230i Coupe', '2021', 'Coupe', '35,900', """01 Drive


01.1

Performance and Efficiency
Engine, transmission, and aerodynamic features.

2.0-liter BMW TwinPower Turbo inline 4-cylinder, 16-valve 248-hp engine. Combines a twin-scroll turbocharger with variable valve control (Double-VANOS and Valvetronic) and high-precision direct injection
Auto Start-Stop function
8-speed Sport Automatic transmission with Sport and Manual shift modes, steering wheel-mounted paddle shifters and Launch Control
Electronic throttle control
Electronically controlled engine cooling (map cooling)
Brake Energy Regeneration
Driving Dynamics Control with ECO PRO, COMFORT, SPORT and SPORT+ modes
Launch Control (automatic transmission only)

01.2

Handling, Ride and Braking
Ensuring a smooth, safe, comfortable drive.

Servotronic power-steering assist
Dynamic Stability Control (DSC), including Brake Fade Compensation, Start-off Assistant, Brake Drying, and Brake Stand-by features; with Dynamic Traction Control (DTC)
Double-pivot spring and strut-type front suspension
Five-link fully independent rear suspension
Twin-tube gas-pressure shock absorbers
4-wheel ventilated disc brakes with Anti-lock Braking System (ABS), Dynamic Brake Control (DBC) and Cornering Brake Control (CBC)
02 Appearance


02.1

Exterior
Paint, accents, and lights.

17" Double-spoke bi-color wheels, style 725 with all-season run-flat tires
Non-metallic paint
Chrome-line exterior trim
Highgloss Black Kidney Frame

02.2

Interior Trim
Upholstery and trim.

SensaTec upholstery
High-gloss Black interior trim with Pearl Gloss Chrome highlight
Floormats
Anthracite headliner
03 Technology


03.1

Connectivity
Wireless features, remote services, and intuitive technology.

BMW TeleServices
BMW ConnectedDrive® Services
Apple CarPlay™ Compatibility
Advanced Real Time Traffic Information and On-Street Parking Availability information (select markets)

03.2

Audio System
Systems, speakers and more.

Anti-theft AM/FM stereo with Radio Data System (RDS)
HiFi Sound System with 205-watt digital amplifier and 7 speakers
HD Radio™ with "multicast" FM station reception
SiriusXM® Satellite Radio with 1-year All Access subscription

03.3

Instrumentation and Controls
Advanced features for a smarter drive.

3-spoke leather-wrapped sport steering wheel with paddle shifters
USB audio connection and hands-free Bluetooth® including Audio Streaming
Key fob with Sport Line motif
Dynamic Cruise Control
Rear-window defroster
Tire Pressure Monitor
Instrument Cluster with Extended Contents
BMW Navigation Business system with iDrive Controller, 6.5" high-resolution screen and programmable memory buttons

03.4

Comfort and Convenience
Comfort and Convenience Luxury features for a pleasant ride.

Engine Start/Stop button
Storage package (storage compartment under light switch, nets on driver and front passenger seatbacks and additional storage configurability in trunk)
Front-seat center armrest
Automatic climate control includes micro-filter, automatic air recirculation, digital driver/passenger temperature controls, temperature- and volume-adjustable rear outlet, windshield misting sensor, MAX A/C function, and recall of individual user settings
Rain-sensing windshield wipers with adjustable speed and automatic headlight control
Advanced Vehicle & Key Memory includes most recently used climate-control temperature and air-distribution settings; exterior mirror and power seat settings; audio tone settings and radio presets; central-locking preferences; and lighting preferences
Tilt/telescopic steering wheel column
Power front windows with "one-touch" up/down operation
Locking glovebox
Electric interior trunk release
Three 12V power sockets
10-way power front sport seats; including 2-way power side bolsters, 1-way manual headrests and thigh support; driver memory for exterior mirror and seat positions
Folding rear-seat headrests
04 Protection


04.1

Safety and Security
Protecting you and your vehicle, on the road and off.

Anti-lock Braking System (ABS)
Front and rear Head Protection System (HPS)
Driver's and passenger's front airbag supplemental restraint system (SRS) with advanced technology: dual-threshold, dual-stage deployment
Seat-mounted front side-impact airbags
Knee airbags for driver and front passenger
Front safety belts with automatic pretensioners
Front-passenger-seat-occupation recognition with Passenger's Airbag Off indicator
Coded Driveaway Protection
Automatic-locking retractors (ALR) on all passenger safety belts for installation of child-restraint seat
LATCH attachments for child-restraint safety installation
Impact sensors that activate Battery Safety Terminal disconnect of alternator and starter from battery; disable fuel pump; automatically unlock doors; and turn on hazard and interior lights
Active Driving Assistant, includes Frontal Collision Warning, Lane Departure Warning
Programmable LED Daytime Running Lights
Anti-theft alarm system
BMW Assist eCall™ includes Emergency Request (SOS button) and Enhanced Automatic Collision Notification
Rear-view Camera
Park Distance Control, front and rear
BMW Remote Services includes Stolen Vehicle Recovery, Remote Door Unlock and BMW Connected App
LED Headlights
LED fog lights

04.2

Warranty
Complete coverage and peace of mind.

BMW Ultimate Care (for complete details, visit click here)
4-year/50,000-mile New Vehicle Limited Warranty for Passenger Cars and Light Trucks 2021 Models (valid only in the USA including Puerto Rico)
12-year Unlimited Mileage Rust Perforation Limited Warranty
4-year Unlimited Mileage Roadside Assistance Program""")
websiteoutput('https://www.bmwusa.com/vehicles/2-series/coupe/pricing-features.html', 'BMW', '2', '230i xDrive Coupe', '2021', 'Coupe', '37,900', """01 Drive


01.1

Performance and Efficiency
Engine, transmission, and aerodynamic features.

2.0-liter BMW TwinPower Turbo inline 4-cylinder, 16-valve 248-hp engine. Combines a twin-scroll turbocharger with variable valve control (Double-VANOS and Valvetronic) and high-precision direct injection
Auto Start-Stop function
8-speed Sport Automatic transmission with Sport and Manual shift modes, steering wheel-mounted paddle shifters and Launch Control
Electronic throttle control
Electronically controlled engine cooling (map cooling)
Brake Energy Regeneration
Driving Dynamics Control with ECO PRO, COMFORT, SPORT and SPORT+ modes
Launch Control (automatic transmission only)

01.2

Handling, Ride and Braking
Ensuring a smooth, safe, comfortable drive.

Servotronic power-steering assist
Dynamic Stability Control (DSC), including Brake Fade Compensation, Start-off Assistant, Brake Drying, and Brake Stand-by features; with Dynamic Traction Control (DTC)
Double-pivot spring and strut-type front suspension
Five-link fully independent rear suspension
Twin-tube gas-pressure shock absorbers
4-wheel ventilated disc brakes with Anti-lock Braking System (ABS), Dynamic Brake Control (DBC) and Cornering Brake Control (CBC)
xDrive all-wheel-drive system
02 Appearance


02.1

Exterior
Paint, accents, and lights.

17" Double-spoke bi-color wheels, style 725 with all-season run-flat tires
Non-metallic paint
Chrome-line exterior trim
Highgloss Black Kidney Frame

02.2

Interior Trim
Upholstery and trim.

SensaTec upholstery
High-gloss Black interior trim with Pearl Gloss Chrome highlight
Floormats
Anthracite headliner
03 Technology


03.1

Connectivity
Wireless features, remote services, and intuitive technology.

BMW TeleServices
BMW ConnectedDrive® Services
Apple CarPlay™ Compatibility
Advanced Real Time Traffic Information and On-Street Parking Availability information (select markets)

03.2

Audio System
Systems, speakers and more.

Anti-theft AM/FM stereo with Radio Data System (RDS)
HiFi Sound System with 205-watt digital amplifier and 7 speakers
HD Radio™ with "multicast" FM station reception
SiriusXM® Satellite Radio with 1-year All Access subscription

03.3

Instrumentation and Controls
Advanced features for a smarter drive.

3-spoke leather-wrapped sport steering wheel with paddle shifters
USB audio connection and hands-free Bluetooth® including Audio Streaming
Key fob with Sport Line motif
Dynamic Cruise Control
Rear-window defroster
Tire Pressure Monitor
Instrument Cluster with Extended Contents
BMW Navigation Business system with iDrive Controller, 6.5" high-resolution screen and programmable memory buttons

03.4

Comfort and Convenience
Comfort and Convenience Luxury features for a pleasant ride.

Engine Start/Stop button
Storage package (storage compartment under light switch, nets on driver and front passenger seatbacks and additional storage configurability in trunk)
Front-seat center armrest
Automatic climate control includes micro-filter, automatic air recirculation, digital driver/passenger temperature controls, temperature- and volume-adjustable rear outlet, windshield misting sensor, MAX A/C function, and recall of individual user settings
Rain-sensing windshield wipers with adjustable speed and automatic headlight control
Advanced Vehicle & Key Memory includes most recently used climate-control temperature and air-distribution settings; exterior mirror and power seat settings; audio tone settings and radio presets; central-locking preferences; and lighting preferences
Tilt/telescopic steering wheel column
Power front windows with "one-touch" up/down operation
Locking glovebox
Electric interior trunk release
Three 12V power sockets
10-way power front sport seats; including 2-way power side bolsters, 1-way manual headrests and thigh support; driver memory for exterior mirror and seat positions
Folding rear-seat headrests
04 Protection


04.1

Safety and Security
Protecting you and your vehicle, on the road and off.

Anti-lock Braking System (ABS)
Front and rear Head Protection System (HPS)
Driver's and passenger's front airbag supplemental restraint system (SRS) with advanced technology: dual-threshold, dual-stage deployment
Seat-mounted front side-impact airbags
Knee airbags for driver and front passenger
Front safety belts with automatic pretensioners
Front-passenger-seat-occupation recognition with Passenger's Airbag Off indicator
Coded Driveaway Protection
Automatic-locking retractors (ALR) on all passenger safety belts for installation of child-restraint seat
LATCH attachments for child-restraint safety installation
Impact sensors that activate Battery Safety Terminal disconnect of alternator and starter from battery; disable fuel pump; automatically unlock doors; and turn on hazard and interior lights
Active Driving Assistant, includes Frontal Collision Warning, Lane Departure Warning
Programmable LED Daytime Running Lights
Anti-theft alarm system
BMW Assist eCall™ includes Emergency Request (SOS button) and Enhanced Automatic Collision Notification
Rear-view Camera
Park Distance Control, front and rear
BMW Remote Services includes Stolen Vehicle Recovery, Remote Door Unlock and BMW Connected App
LED Headlights
LED fog lights

04.2

Warranty
Complete coverage and peace of mind.

BMW Ultimate Care (for complete details, visit click here)
4-year/50,000-mile New Vehicle Limited Warranty for Passenger Cars and Light Trucks 2021 Models (valid only in the USA including Puerto Rico)
12-year Unlimited Mileage Rust Perforation Limited Warranty
4-year Unlimited Mileage Roadside Assistance Program""")
websiteoutput('https://www.bmwusa.com/vehicles/2-series/coupe/pricing-features.html', 'BMW', '2', 'M240i Coupe', '2021', 'Coupe', '46,350', """01 Drive


01.1

Performance and Efficiency
Engine, transmission, and aerodynamic features.

3.0-liter BMW M TwinPower Turbo inline 6-cylinder, 24-valve 335-hp engine. Combines a twin-scroll turbocharger with variable valve control (Double-VANOS and Valvetronic) and high-precision direct injection
8-speed Sport Automatic transmission with Sport and Manual shift modes, steering wheel-mounted paddle shifters and Launch Control
Electronic throttle control
Electronically controlled engine cooling (map cooling)
Brake Energy Regeneration
Driving Dynamics Control with ECO PRO, COMFORT, SPORT and SPORT+ modes
Launch Control (automatic transmission only)
Sport exhaust system
Auto Start-Stop function

01.2

Handling, Ride and Braking
Ensuring a smooth, safe, comfortable drive.

Variable Sport Steering
Adaptive M Suspension
M Sport brakes
Dynamic Stability Control (DSC), including Brake Fade Compensation, Start-off Assistant, Brake Drying, and Brake Stand-by features; with Dynamic Traction Control (DTC)
Double-pivot spring and strut-type front suspension
Five-link fully independent rear suspension
Twin-tube gas-pressure shock absorbers
4-wheel ventilated disc brakes with Anti-lock Braking System (ABS), Dynamic Brake Control (DBC) and Cornering Brake Control (CBC)
02 Appearance


02.1

Exterior
Paint, accents, and lights.

18" M Double-spoke jet black wheels, style 719M with performance non run-flat tires
Non-metallic paint
Aerodynamic kit
Shadowline exterior trim
Highgloss Black Mirror Caps
Cerium Grey Kidney Frame

02.2

Interior Trim
Upholstery and trim.

SensaTec upholstery
Aluminum Hexagon interior trim with Estoril Blue highlight
Floormats
Anthracite headliner
03 Technology


03.1

Connectivity
Wireless features, remote services, and intuitive technology.

BMW TeleServices
BMW ConnectedDrive® Services
Apple CarPlay™ Compatibility
Advanced Real Time Traffic Information and On-Street Parking Availability information (select markets)

03.2

Audio System
Systems, speakers and more.

Anti-theft AM/FM stereo with Radio Data System (RDS)
HiFi Sound System with 205-watt digital amplifier and 7 speakers
HD Radio™ with "multicast" FM station reception
SiriusXM® Satellite Radio with 1-year All Access subscription

03.3

Instrumentation and Controls
Advanced features for a smarter drive.

3-spoke power telescopic, leather-wrapped, multi-function M sport steering wheel
USB audio connection and hands-free Bluetooth® including Audio Streaming
Dynamic Cruise Control
Rear-window defroster
Tire Pressure Monitor
Instrument Cluster with Extended Contents
BMW Navigation Business system with iDrive Controller, 6.5" high-resolution screen and programmable memory buttons

03.4

Comfort and Convenience
Comfort and Convenience Luxury features for a pleasant ride.

Engine Start/Stop button
Storage package (storage compartment under light switch, nets on driver and front passenger seatbacks and additional storage configurability in trunk)
Front-seat center armrest
Automatic climate control includes micro-filter, automatic air recirculation, digital driver/passenger temperature controls, temperature- and volume-adjustable rear outlet, windshield misting sensor, MAX A/C function, and recall of individual user settings
Automatic-dimming interior rear-view mirror and driver's-side exterior mirror
BMW Ambient Lighting front and rear; ground-illuminating lights in door handles; and courtesy lights (include fade in/fade out, actuation from remote, automatic switch-on when engine is turned off, separately controlled left/right reading lights, front footwell lighting, and illuminated vanity mirrors)
Comfort Access keyless entry with hands-free trunk/lid opening
2-way power glass moonroof with "one-touch" operation and sliding interior sunshade
Rain-sensing windshield wipers with adjustable speed and automatic headlight control
Advanced Vehicle & Key Memory includes most recently used climate-control temperature and air-distribution settings; exterior mirror and power seat settings; audio tone settings and radio presets; central-locking preferences; and lighting preferences
Tilt/telescopic steering wheel column
Power front windows with "one-touch" up/down operation
Locking glovebox
Electric interior trunk release
Three 12V power sockets
10-way power front sport seats; including 2-way power side bolsters, 1-way manual headrests and thigh support; driver memory for exterior mirror and seat positions
4-way power lumbar support for front seats
Folding rear-seat headrests
04 Protection


04.1

Safety and Security
Protecting you and your vehicle, on the road and off.

Anti-lock Braking System (ABS)
Front and rear Head Protection System (HPS)
Driver's and passenger's front airbag supplemental restraint system (SRS) with advanced technology: dual-threshold, dual-stage deployment
Seat-mounted front side-impact airbags
Knee airbags for driver and front passenger
Front safety belts with automatic pretensioners
Front-passenger-seat-occupation recognition with Passenger's Airbag Off indicator
Coded Driveaway Protection
Automatic-locking retractors (ALR) on all passenger safety belts for installation of child-restraint seat
LATCH attachments for child-restraint safety installation
Impact sensors that activate Battery Safety Terminal disconnect of alternator and starter from battery; disable fuel pump; automatically unlock doors; and turn on hazard and interior lights
Active Driving Assistant, includes Frontal Collision Warning, Lane Departure Warning
Programmable LED Daytime Running Lights
Anti-theft alarm system
BMW Assist eCall™ includes Emergency Request (SOS button) and Enhanced Automatic Collision Notification
Rear-view Camera
Park Distance Control, front and rear
BMW Remote Services includes Stolen Vehicle Recovery, Remote Door Unlock and BMW Connected App
LED Headlights

04.2

Warranty
Complete coverage and peace of mind.

BMW Ultimate Care (for complete details, visit click here)
4-year/50,000-mile New Vehicle Limited Warranty for Passenger Cars and Light Trucks 2021 Models (valid only in the USA including Puerto Rico)
""")
websiteoutput('https://www.bmwusa.com/vehicles/2-series/coupe/pricing-features.html', 'BMW', '2', 'M240i xDrive Coupe', '2021', 'Coupe', '48,350',"""01 Drive


01.1

Performance and Efficiency
Engine, transmission, and aerodynamic features.

3.0-liter BMW M TwinPower Turbo inline 6-cylinder, 24-valve 335-hp engine. Combines a twin-scroll turbocharger with variable valve control (Double-VANOS and Valvetronic) and high-precision direct injection
Sport exhaust system
Auto Start-Stop function
8-speed Sport Automatic transmission with Sport and Manual shift modes, steering wheel-mounted paddle shifters and Launch Control
Electronic throttle control
Electronically controlled engine cooling (map cooling)
Brake Energy Regeneration
Driving Dynamics Control with ECO PRO, COMFORT, SPORT and SPORT+ modes
Launch Control (automatic transmission only)

01.2

Handling, Ride and Braking
Ensuring a smooth, safe, comfortable drive.

Variable Sport Steering
Adaptive M Suspension
M Sport brakes
Dynamic Stability Control (DSC), including Brake Fade Compensation, Start-off Assistant, Brake Drying, and Brake Stand-by features; with Dynamic Traction Control (DTC)
Double-pivot spring and strut-type front suspension
Five-link fully independent rear suspension
Twin-tube gas-pressure shock absorbers
4-wheel ventilated disc brakes with Anti-lock Braking System (ABS), Dynamic Brake Control (DBC) and Cornering Brake Control (CBC)
xDrive all-wheel-drive system
02 Appearance


02.1

Exterior
Paint, accents, and lights.

18" M Double-spoke wheels, style 719M Jet Black with all-season run-flat tires
Non-metallic paint
Aerodynamic kit
Shadowline exterior trim
Highgloss Black Mirror Caps
Cerium Grey Kidney Frame

02.2

Interior Trim
Upholstery and trim.

SensaTec upholstery
Aluminum Hexagon interior trim with Estoril Blue highlight
Floormats
Anthracite headliner
03 Technology


03.1

Connectivity
Wireless features, remote services, and intuitive technology.

BMW TeleServices
BMW ConnectedDrive® Services
Apple CarPlay™ Compatibility
Advanced Real Time Traffic Information and On-Street Parking Availability information (select markets)

03.2

Audio System
Systems, speakers and more.

Anti-theft AM/FM stereo with Radio Data System (RDS)
HiFi Sound System with 205-watt digital amplifier and 7 speakers
HD Radio™ with "multicast" FM station reception
SiriusXM® Satellite Radio with 1-year All Access subscription

03.3

Instrumentation and Controls
Advanced features for a smarter drive.

3-spoke power telescopic, leather-wrapped, multi-function M sport steering wheel
USB audio connection and hands-free Bluetooth® including Audio Streaming
Dynamic Cruise Control
Rear-window defroster
Tire Pressure Monitor
Instrument Cluster with Extended Contents
BMW Navigation Business system with iDrive Controller, 6.5" high-resolution screen and programmable memory buttons

03.4

Comfort and Convenience
Comfort and Convenience Luxury features for a pleasant ride.

Engine Start/Stop button
Storage package (storage compartment under light switch, nets on driver and front passenger seatbacks and additional storage configurability in trunk)
Front-seat center armrest
Automatic climate control includes micro-filter, automatic air recirculation, digital driver/passenger temperature controls, temperature- and volume-adjustable rear outlet, windshield misting sensor, MAX A/C function, and recall of individual user settings
Automatic-dimming interior rear-view mirror and driver's-side exterior mirror
BMW Ambient Lighting front and rear; ground-illuminating lights in door handles; and courtesy lights (include fade in/fade out, actuation from remote, automatic switch-on when engine is turned off, separately controlled left/right reading lights, front footwell lighting, and illuminated vanity mirrors)
Comfort Access keyless entry with hands-free trunk/lid opening
2-way power glass moonroof with "one-touch" operation and sliding interior sunshade
Rain-sensing windshield wipers with adjustable speed and automatic headlight control
Advanced Vehicle & Key Memory includes most recently used climate-control temperature and air-distribution settings; exterior mirror and power seat settings; audio tone settings and radio presets; central-locking preferences; and lighting preferences
Tilt/telescopic steering wheel column
Power front windows with "one-touch" up/down operation
Locking glovebox
Electric interior trunk release
Three 12V power sockets
10-way power front sport seats; including 2-way power side bolsters, 1-way manual headrests and thigh support; driver memory for exterior mirror and seat positions
4-way power lumbar support for front seats
Folding rear-seat headrests
04 Protection


04.1

Safety and Security
Protecting you and your vehicle, on the road and off.

Anti-lock Braking System (ABS)
Front and rear Head Protection System (HPS)
Driver's and passenger's front airbag supplemental restraint system (SRS) with advanced technology: dual-threshold, dual-stage deployment
Seat-mounted front side-impact airbags
Knee airbags for driver and front passenger
Front safety belts with automatic pretensioners
Front-passenger-seat-occupation recognition with Passenger's Airbag Off indicator
Coded Driveaway Protection
Automatic-locking retractors (ALR) on all passenger safety belts for installation of child-restraint seat
LATCH attachments for child-restraint safety installation
Impact sensors that activate Battery Safety Terminal disconnect of alternator and starter from battery; disable fuel pump; automatically unlock doors; and turn on hazard and interior lights
Active Driving Assistant, includes Frontal Collision Warning, Lane Departure Warning
Programmable LED Daytime Running Lights
Anti-theft alarm system
BMW Assist eCall™ includes Emergency Request (SOS button) and Enhanced Automatic Collision Notification
Rear-view Camera
Park Distance Control, front and rear
BMW Remote Services includes Stolen Vehicle Recovery, Remote Door Unlock and BMW Connected App
LED Headlights

04.2

Warranty
Complete coverage and peace of mind.

BMW Ultimate Care (for complete details, visit click here)
4-year/50,000-mile New Vehicle Limited Warranty for Passenger Cars and Light Trucks 2021 Models (valid only in the USA including Puerto Rico)
12-year Unlimited Mileage Rust Perforation Limited Warranty
4-year Unlimited Mileage Roadside Assistance Program""")
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.212S.html', 'BMW', '2', 'M2 Competition Coupe', '2021', 'Coupe', '58,900')


# In[150]:


websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.213O.html', 'BMW', '3', '330i Sedan', '2021', 'Sedan', '41,250')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.213W.html', 'BMW', '3', '330i xDrive Sedan', '2021', 'Sedan', '43,250')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.213B.html', 'BMW', '3', '330e Sedan', '2021', 'Sedan', '44,550')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.213C.html', 'BMW', '3', '330e xDrive Sedan', '2021', 'Sedan', '46,550')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.213Q.html', 'BMW', '3', 'M340i Sedan', '2021', 'Sedan', '54,700')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.213Z.html', 'BMW', '3', 'M340i xDrive Sedan', '2021', 'Sedan', '56,700')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21TN.html', 'BMW', '3', 'M3 Sedan', '2021', 'Sedan', '69,900')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21TP.html', 'BMW', '3', 'M3 Competition Sedan', '2021', 'Sedan', '72,800')


# In[151]:


websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.214B.html', 'BMW', '4', '430i Coupe', '2021', 'Coupe', '45,600')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.214D.html', 'BMW', '4', '430i xDrive Coupe', '2021', 'Coupe', '47,600')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.214G.html', 'BMW', '4', 'M440i xDrive Coupe', '2021', 'Coupe', '58,500')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.214H.html', 'BMW', '4', 'M4 Coupe', '2021', 'Coupe', '71,800')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.214X.html', 'BMW', '4', 'M4 Competition Coupe', '2021', 'Coupe', '77,700')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.214J.html', 'BMW', '4', '430i Convertible', '2021', 'Convertible', '53,100')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.214K.html', 'BMW', '4', 'M440i Convertible', '2021', 'Convertible', '64,000')


# In[152]:


websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.215A.html', 'BMW', '5', '530i Sedan', '2021', 'Sedan', '54,200')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.215B.html', 'BMW', '5', '530i xDrive Sedan', '2021', 'Sedan', '56,500')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.215C.html', 'BMW', '5', '540i Sedan', '2021', 'Sedan', '59,450')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.215D.html', 'BMW', '5', '540i xDrive Sedan', '2021', 'Sedan', '61,750')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.215O.html', 'BMW', '5', '530e Sedan', '2021', 'Sedan', '57,200')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.215P.html', 'BMW', '5', '530e xDrive Sedan', '2021', 'Sedan', '59,500')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.215Q.html', 'BMW', '5', 'M550i xDrive Sedan', '2021', 'Sedan', '76,800')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.215G.html', 'BMW', '5', 'M5 Sedan', '2021', 'Sedan', '103,500')


# In[153]:


websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.227F.html', 'BMW', '7', '740i Sedan', '2022', 'Sedan', '86,800')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.227N.html', 'BMW', '7', '740i xDrive Sedan', '2022', 'Sedan', '89,800')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.227I.html', 'BMW', '7', '750i xDrive Sedan', '2022', 'Sedan', '103,000')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.217P.html', 'BMW', '7', '745e xDrive Sedan', '2021', 'Sedan', '95,900')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.227M.html', 'BMW', '7', 'M550i xDrive Sedan', '2022', 'Sedan', '157,800')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.227J.html', 'BMW', '7 Alpina', 'ALPINA B7 xDrive Sedan', '2022', 'Sedan', '143,200')


# In[154]:


websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.228A.html', 'BMW', '8', '840i Coupe', '2022', 'Coupe', '85,000')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.228B.html', 'BMW', '8', '840i xDrive Coupe', '2022', 'Coupe', '87,900')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.228C.html', 'BMW', '8', 'M850i xDrive Coupe', '2022', 'Coupe', '99,900')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.228F.html', 'BMW', '8', 'M8 Competition Coupe', '2022', 'Coupe', '130,000')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.228D.html', 'BMW', '8', '840i Convertible', '2022', 'Convertible', '94,400')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.228E.html', 'BMW', '8', '840i xDrive Convertible', '2022', 'Convertible', '97,300')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.228G.html', 'BMW', '8', 'M850i Convertible', '2022', 'Convertible', '109,400')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.228K.html', 'BMW', '8', 'M8 Competition Convertible', '2022', 'Convertible', '139,500')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.228H.html', 'BMW', '8', '840i Gran Coupe', '2022', 'Sedan', '85,000')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.228I.html', 'BMW', '8', '840i xDrive Gran Coupe', '2022', 'Sedan', '87,900')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.228J.html', 'BMW', '8', 'M850i xDrive Gran Coupe', '2022', 'Sedan', '99,900')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.228L.html', 'BMW', '8', 'M8 Competition Gran Coupe', '2022', 'Sedan', '130,000')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.228Q.html', 'BMW', '8 Alpina', 'ALPINA B8 xDrive Gran Coupe', '2022', 'Sedan', '139,900')


# In[155]:


websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21ZA.html', 'BMW', 'Z4', 'sDrive30i', '2021', 'Sports Car', '49,700')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21ZB.html', 'BMW', 'Z4', 'M40i', '2021', 'Sports Car', '63,700')


# In[156]:


websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21IA.html', 'BMW', 'i', 'i3', '2021', 'Sedan', '44,450')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21IF.html', 'BMW', 'i', 'i3s', '2021', 'Sedan', '47,650')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21IB.html', 'BMW', 'i', 'i3 with Range Extender', '2021', 'Sedan', '48,300')
websiteoutput('https://www.bmwusa.com/standard-features.iframe.standard-features.21IG.html', 'BMW', 'i', 'i3s with Range Extender', '2021', 'Sedan', '51,500')


# # Chevrolet

# Chevrolet's Models

# In[96]:


websiteoutput('https://www.chevrolet.com/suvs/previous-year/trailblazer/build-and-price/features/trims/table?section=Highlights&section=Mechanical&section=Exterior&section=Interior&section=Safety&section=Dimensions&section=Warranty&styleOne=411610', 'Chevrolet', 'Trailblazer', 'L', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/previous-year/trailblazer/build-and-price/features/trims/table?section=Highlights&section=Mechanical&section=Exterior&section=Interior&section=Safety&section=Dimensions&section=Warranty&styleOne=411611', 'Chevrolet', 'Trailblazer', 'LS', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/previous-year/trailblazer/build-and-price/features/trims/table?section=Highlights&section=Mechanical&section=Exterior&section=Interior&section=Safety&section=Dimensions&section=Warranty&styleOne=411612', 'Chevrolet', 'Trailblazer', 'LT', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/previous-year/trailblazer/build-and-price/features/trims/table?section=Highlights&section=Mechanical&section=Exterior&section=Interior&section=Safety&section=Dimensions&section=Warranty&styleOne=411613', 'Chevrolet', 'Trailblazer', 'ACTIV', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/previous-year/trailblazer/build-and-price/features/trims/table?section=Highlights&section=Mechanical&section=Exterior&section=Interior&section=Safety&section=Dimensions&section=Warranty&styleOne=411614', 'Chevrolet', 'Trailblazer', 'RS', '2021', 'SUV')


# In[97]:


websiteoutput('https://www.chevrolet.com/suvs/previous-year/trax/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Exterior&section=Interior&section=Safety&section=Fuel+Efficiency&section=Dimensions&section=Warranty&styleOne=412540', 'Chevrolet', 'Trax', 'LS', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/previous-year/trax/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Exterior&section=Interior&section=Safety&section=Fuel+Efficiency&section=Dimensions&section=Warranty&styleOne=412541', 'Chevrolet', 'Trax', 'LT', '2021', 'SUV')


# In[98]:


websiteoutput('https://www.chevrolet.com/suvs/equinox/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Exterior&section=Interior&section=Safety&section=Fuel+Efficiency&section=Dimensions&section=Warranty&styleOne=416245', 'Chevrolet', 'Equinox', 'L', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/equinox/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Exterior&section=Interior&section=Safety&section=Fuel+Efficiency&section=Dimensions&section=Warranty&styleOne=416247', 'Chevrolet', 'Equinox', 'LS', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/equinox/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Exterior&section=Interior&section=Safety&section=Fuel+Efficiency&section=Dimensions&section=Warranty&styleOne=416249', 'Chevrolet', 'Equinox', 'LT', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/equinox/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Exterior&section=Interior&section=Safety&section=Fuel+Efficiency&section=Dimensions&section=Warranty&styleOne=416250', 'Chevrolet', 'Equinox', 'Premier', '2021', 'SUV')


# In[99]:


websiteoutput('https://www.chevrolet.com/suvs/blazer/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413882', 'Chevrolet', 'Blazer', 'L', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/blazer/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413883', 'Chevrolet', 'Blazer', '1LT', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/blazer/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413884', 'Chevrolet', 'Blazer', '2LT', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/blazer/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413885', 'Chevrolet', 'Blazer', '3LT', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/blazer/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413886', 'Chevrolet', 'Blazer', 'RS', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/blazer/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413887', 'Chevrolet', 'Blazer', 'Premier', '2021', 'SUV')


# In[100]:


websiteoutput('https://www.chevrolet.com/suvs/traverse/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=415903', 'Chevrolet', 'Traverse', 'L', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/traverse/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=415905', 'Chevrolet', 'Traverse', 'LS', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/traverse/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=415907', 'Chevrolet', 'Traverse', 'LT Cloth', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/traverse/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=415908', 'Chevrolet', 'Traverse', 'LT Leather', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/traverse/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=415909', 'Chevrolet', 'Traverse', 'RS', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/traverse/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=415910', 'Chevrolet', 'Traverse', 'Premier', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/traverse/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=415911', 'Chevrolet', 'Traverse', 'High Country', '2021', 'SUV')


# In[101]:


websiteoutput('https://www.chevrolet.com/suvs/tahoe/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412518', 'Chevrolet', 'Tahoe', 'LS', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/tahoe/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412519', 'Chevrolet', 'Tahoe', 'LT', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/tahoe/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412520', 'Chevrolet', 'Tahoe', 'RST', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/tahoe/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412526', 'Chevrolet', 'Tahoe', 'Z71', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/tahoe/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412521', 'Chevrolet', 'Tahoe', 'Premier', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/tahoe/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412522', 'Chevrolet', 'Tahoe', 'High Country', '2021', 'SUV')


# In[102]:


websiteoutput('https://www.chevrolet.com/suvs/suburban/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412286', 'Chevrolet', 'Suburban', 'LS', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/suburban/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412287', 'Chevrolet', 'Suburban', 'LT', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/suburban/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412295', 'Chevrolet', 'Suburban', 'Z71', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/suburban/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412288', 'Chevrolet', 'Suburban', 'RST', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/suburban/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412290', 'Chevrolet', 'Suburban', 'Premier', '2021', 'SUV')
websiteoutput('https://www.chevrolet.com/suvs/suburban/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412291', 'Chevrolet', 'Suburban', 'High Country', '2021', 'SUV')


# In[103]:


websiteoutput('https://www.chevrolet.com/trucks/colorado/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412254', 'Chevrolet', 'Colarado', 'WT', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/colorado/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412237', 'Chevrolet', 'Colarado', 'LT', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/colorado/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412240', 'Chevrolet', 'Colarado', 'Z71', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/colorado/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412246', 'Chevrolet', 'Colarado', 'ZR2', '2021', 'Pickup Truck')


# In[104]:


websiteoutput('https://www.chevrolet.com/trucks/silverado/1500/build-and-price/trim/compare/trims/table?section=Mechanical&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&styleOne=413014', 'Chevrolet', 'Silverado', 'WT', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/silverado/1500/build-and-price/trim/compare/trims/table?section=Mechanical&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&styleOne=413016', 'Chevrolet', 'Silverado', 'Custom', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/silverado/1500/build-and-price/trim/compare/trims/table?section=Mechanical&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&styleOne=413035', 'Chevrolet', 'Silverado', 'Custom Trail Boss', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/silverado/1500/build-and-price/trim/compare/trims/table?section=Mechanical&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&styleOne=413017', 'Chevrolet', 'Silverado', 'LT', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/silverado/1500/build-and-price/trim/compare/trims/table?section=Mechanical&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&styleOne=413044', 'Chevrolet', 'Silverado', 'LT Trail Boss', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/silverado/1500/build-and-price/trim/compare/trims/table?section=Mechanical&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&styleOne=413023', 'Chevrolet', 'Silverado', 'RST', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/silverado/1500/build-and-price/trim/compare/trims/table?section=Mechanical&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&styleOne=413024', 'Chevrolet', 'Silverado', 'LTZ', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/silverado/1500/build-and-price/trim/compare/trims/table?section=Mechanical&section=Warranty&section=Dimensions&section=Safety&section=Interior&section=Exterior&styleOne=413025', 'Chevrolet', 'Silverado', 'High Country', '2021', 'Pickup Truck')


# In[105]:


websiteoutput('https://www.chevrolet.com/trucks/silverado/2500hd/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412906', 'Chevrolet', 'Silverado 2500 HD', 'WT', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/silverado/2500hd/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412907', 'Chevrolet', 'Silverado 2500 HD', 'LT', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/silverado/2500hd/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412909', 'Chevrolet', 'Silverado 2500 HD', 'Custom', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/silverado/2500hd/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412919', 'Chevrolet', 'Silverado 2500 HD', 'LTZ', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/silverado/2500hd/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=412938', 'Chevrolet', 'Silverado 2500 HD', 'High Country', '2021', 'Pickup Truck')


# In[106]:


websiteoutput('https://www.chevrolet.com/trucks/silverado/3500hd/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413291', 'Chevrolet', 'Silverado 3500 HD', 'WT', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/silverado/3500hd/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413294', 'Chevrolet', 'Silverado 3500 HD', 'LT', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/silverado/3500hd/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413307', 'Chevrolet', 'Silverado 3500 HD', 'LTZ', '2021', 'Pickup Truck')
websiteoutput('https://www.chevrolet.com/trucks/silverado/3500hd/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413336', 'Chevrolet', 'Silverado 3500 HD', 'High Country', '2021', 'Pickup Truck')


# In[107]:


websiteoutput('https://www.chevrolet.com/cars/spark/build-and-price/trim/compare/trims/table?section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&section=Highlights&styleOne=412643', 'Chevrolet', 'Spark', 'LS Manual', '2021', 'Hatchback')
websiteoutput('https://www.chevrolet.com/cars/spark/build-and-price/trim/compare/trims/table?section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&section=Highlights&styleOne=412644', 'Chevrolet', 'Spark', 'LS Automatic', '2021', 'Hatchback')
websiteoutput('https://www.chevrolet.com/cars/spark/build-and-price/trim/compare/trims/table?section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&section=Highlights&styleOne=412645', 'Chevrolet', 'Spark', '1LT Manual', '2021', 'Hatchback')
websiteoutput('https://www.chevrolet.com/cars/spark/build-and-price/trim/compare/trims/table?section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&section=Highlights&styleOne=412646', 'Chevrolet', 'Spark', '1LT Automatic', '2021', 'Hatchback')
websiteoutput('https://www.chevrolet.com/cars/spark/build-and-price/trim/compare/trims/table?section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&section=Highlights&styleOne=412647', 'Chevrolet', 'Spark', '2LT Manual', '2021', 'Hatchback')
websiteoutput('https://www.chevrolet.com/cars/spark/build-and-price/trim/compare/trims/table?section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&section=Highlights&styleOne=412648', 'Chevrolet', 'Spark', '2LT Automatic', '2021', 'Hatchback')
websiteoutput('https://www.chevrolet.com/cars/spark/build-and-price/trim/compare/trims/table?section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&section=Highlights&styleOne=412649', 'Chevrolet', 'Spark', 'ACTIV Manual', '2021', 'Hatchback')
websiteoutput('https://www.chevrolet.com/cars/spark/build-and-price/trim/compare/trims/table?section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&section=Highlights&styleOne=412650', 'Chevrolet', 'Spark', 'ACTIV Automatic', '2021', 'Hatchback')


# In[108]:


websiteoutput('https://www.chevrolet.com/cars/malibu/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413660', 'Chevrolet', 'Malibu', 'L', '2021', 'Sedan')
websiteoutput('https://www.chevrolet.com/cars/malibu/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413662', 'Chevrolet', 'Malibu', 'LS', '2021', 'Sedan')
websiteoutput('https://www.chevrolet.com/cars/malibu/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413663', 'Chevrolet', 'Malibu', 'RS', '2021', 'Sedan')
websiteoutput('https://www.chevrolet.com/cars/malibu/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413664', 'Chevrolet', 'Malibu', 'LT', '2021', 'Sedan')
websiteoutput('https://www.chevrolet.com/cars/malibu/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413665', 'Chevrolet', 'Malibu', 'Premier', '2021', 'Sedan')


# In[109]:


websiteoutput('https://www.chevrolet.com/2021-bolt-ev/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=418204', 'Chevrolet', 'Bolt EV', 'LT', '2021', 'Hatchback')
websiteoutput('https://www.chevrolet.com/2021-bolt-ev/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=418205', 'Chevrolet', 'Bolt EV', 'Premier', '2021', 'Hatchback')

websiteoutput('https://www.chevrolet.com/electric/bolt-ev/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=419660', 'Chevrolet', 'Bolt EV', '1LT', '2022', 'Hatchback')
websiteoutput('https://www.chevrolet.com/electric/bolt-ev/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=419661', 'Chevrolet', 'Bolt EV', '2LT', '2022', 'Hatchback')

websiteoutput('https://www.chevrolet.com/electric/bolt-euv/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=419707', 'Chevrolet', 'Bolt EUV', 'LT', '2022', 'Hatchback')
websiteoutput('https://www.chevrolet.com/electric/bolt-euv/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=419708', 'Chevrolet', 'Bolt EUV', 'Premier', '2022', 'Hatchback')


# In[110]:


websiteoutput('https://www.chevrolet.com/performance/camaro/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412679', 'Chevrolet', 'Camaro', '1LS', '2021', 'Coupe')
websiteoutput('https://www.chevrolet.com/performance/camaro/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412680', 'Chevrolet', 'Camaro', '1LT', '2021', 'Coupe')
websiteoutput('https://www.chevrolet.com/performance/camaro/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412681', 'Chevrolet', 'Camaro', '2LT', '2021', 'Coupe')
websiteoutput('https://www.chevrolet.com/performance/camaro/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412682', 'Chevrolet', 'Camaro', '3LT', '2021', 'Coupe')
websiteoutput('https://www.chevrolet.com/performance/camaro/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412683', 'Chevrolet', 'Camaro', 'LT1', '2021', 'Coupe')
websiteoutput('https://www.chevrolet.com/performance/camaro/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412684', 'Chevrolet', 'Camaro', '1SS', '2021', 'Coupe')
websiteoutput('https://www.chevrolet.com/performance/camaro/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412685', 'Chevrolet', 'Camaro', '2SS', '2021', 'Coupe')
websiteoutput('https://www.chevrolet.com/performance/camaro/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412686', 'Chevrolet', 'Camaro', 'ZL1', '2021', 'Coupe')


# In[111]:


websiteoutput('https://www.chevrolet.com/performance/camaro/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412687', 'Chevrolet', 'Camaro', '1LT', '2021', 'Convertible')
websiteoutput('https://www.chevrolet.com/performance/camaro/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412688', 'Chevrolet', 'Camaro', '2LT', '2021', 'Convertible')
websiteoutput('https://www.chevrolet.com/performance/camaro/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412690', 'Chevrolet', 'Camaro', '3LT', '2021', 'Convertible')
websiteoutput('https://www.chevrolet.com/performance/camaro/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412691', 'Chevrolet', 'Camaro', 'LT1', '2021', 'Convertible')
websiteoutput('https://www.chevrolet.com/performance/camaro/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412692', 'Chevrolet', 'Camaro', '1SS', '2021', 'Convertible')
websiteoutput('https://www.chevrolet.com/performance/camaro/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412693', 'Chevrolet', 'Camaro', '2SS', '2021', 'Convertible')
websiteoutput('https://www.chevrolet.com/performance/camaro/build-and-price/trim/compare/trims/table?section=Highlights&section=Mechanical&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&styleOne=412689', 'Chevrolet', 'Camaro', 'ZL1', '2021', 'Convertible')


# In[112]:


websiteoutput('https://www.chevrolet.com/performance/corvette/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413677', 'Chevrolet', 'Corvette Stingray', '1LT', '2021', 'Coupe')
websiteoutput('https://www.chevrolet.com/performance/corvette/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413678', 'Chevrolet', 'Corvette Stingray', '2LT', '2021', 'Coupe')
websiteoutput('https://www.chevrolet.com/performance/corvette/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413680', 'Chevrolet', 'Corvette Stingray', '3LT', '2021', 'Coupe')
websiteoutput('https://www.chevrolet.com/performance/corvette/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413682', 'Chevrolet', 'Corvette Stingray', '1LT', '2021', 'Convertible')
websiteoutput('https://www.chevrolet.com/performance/corvette/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413683', 'Chevrolet', 'Corvette Stingray', '2LT', '2021', 'Convertible')
websiteoutput('https://www.chevrolet.com/performance/corvette/build-and-price/trim/compare/trims/table?section=Highlights&section=Warranty&section=Dimensions&section=Fuel+Efficiency&section=Safety&section=Interior&section=Exterior&section=Mechanical&styleOne=413685', 'Chevrolet', 'Corvette Stingray', '3LT', '2021', 'Convertible')


# # Toyota

# In[113]:


websiteoutput("https://www.toyota.com/priusprime/features/mileage_estimates/1235", 'Toyota', 'Prius Prime', 'LE', '2021', 'Sedan')
websiteoutput("https://www.toyota.com/priusprime/features/mileage_estimates/1237", 'Toyota', 'Prius Prime', 'XLE', '2021', 'Sedan')
websiteoutput("https://www.toyota.com/priusprime/features/mileage_estimates/1239", 'Toyota', 'Prius Prime', 'Limited', '2021', 'Sedan')


# In[114]:


websiteoutput("https://www.toyota.com/prius/2021/features/mpg/1221", 'Toyota', 'Prius', 'L Eco', '2021', 'Sedan', start='l-eco', stop='le')
websiteoutput("https://www.toyota.com/prius/2021/features/mpg/1223", 'Toyota', 'Prius', 'LE', '2021', 'Sedan', start='le', stop='le-awd')
websiteoutput("https://www.toyota.com/prius/2021/features/mpg/1263", 'Toyota', 'Prius', 'LE AWD', '2021', 'Sedan', start='le-awd', stop='xle')
websiteoutput("https://www.toyota.com/prius/2021/features/mpg/1225", 'Toyota', 'Prius', 'XLE', '2021', 'Sedan', start='xle', stop='xle-awd')
websiteoutput("https://www.toyota.com/prius/2021/features/mpg/1265", 'Toyota', 'Prius', 'XLE AWD', '2021', 'Sedan',start='xle-awd', stop='2020-edition')
websiteoutput("https://www.toyota.com/prius/2021/features/mpg/1219", 'Toyota', 'Prius', '2020 Edition', '2021', 'Sedan', start='2020-edition', stop='limited')
websiteoutput("https://www.toyota.com/prius/2021/features/mpg/1227", 'Toyota', 'Prius', 'Limited', '2021', 'Sedan', start='limited', stop='l-eco')


# In[43]:


toyotadata('https://www.toyota.com/priusprime/features/mileage_estimates', 'Prius Prime', ['LE', 'XLE', 'Limited'], ['le', 'xle', 'limited'], '2021', 'Sedan')


# In[44]:


toyotadata('https://www.toyota.com/prius/2021/features/mpg', 'Prius', ['L Eco', 'LE', 'LE AWD-E', 'XLE', 'XLE AWD-E', '2020 Edition', 'Limited'], ['l-eco', 'le', 'le-awd', 'xle', 'xle-awd', '2020-edition', 'limited'], '2021', 'Sedan')


# In[45]:



toyotadata('https://www.toyota.com/corollahatchback/features/mileage_estimates/6276', 'Corolla Hatchback', ['SE', 'SE Nightshade Edition', 'XSE'], ['se', 'nightshade', 'xse'], '2021', 'Hatchback')


# In[46]:



toyotadata('https://www.toyota.com/camry/features/mpg/2532/2515/2559/', 'Camry', ['LE', 'LE Hybrid', 'SE', 'SE Hybrid', 'SE Nightshade Edition', 'XLE', 'XLE Hybrid', 'XSE', 'XSE Hybrid', 'TRD', 'XLE V6', 'XSE V6'], ['camry_le', 'camry_hybrid_le',  'camry_se', 'camry_hybrid_se', 'camry_se_nightshade', 'camry_xle', 'camry_hybrid_xle',  'camry_xse','camry_hybrid_xse', 'trd', 'camry_xle_v6', 'camry_xse_v6'], '2021', 'Sedan')


# In[47]:


toyotadata('https://www.toyota.com/avalon/features/mpg/3544/3555/3504', 'Avalon', ['XLE', 'XLE Hybrid', 'XSE Nightshade', 'XSE Hybrid', 'TRD', 'Touring',  'Limited', 'Limited Hybrid'], ['xle', 'hybrid-xle','xse-nightshade', 'hybrid-xse', 'trd',  'touring', 'limited', 'hybrid-limited'], '2021', 'Sedan')


# In[48]:


toyotadata('https://www.toyota.com/mirai/features/mileage_estimates/3002/3003', 'Mirai', ['XLE', 'Limited'], ['xle', 'limited'], '2021', 'Sedan')


# In[49]:



toyotadata('https://www.toyota.com/86/features/mpg/6253/6254/6255', '86', ['86', '86 GT'], ['86', '86gt'], '2020', 'Coupe')


# In[50]:



toyotadata('https://www.toyota.com/gr-supra/features/mileage_estimates/2370/2372/2374', 'GR Supra', ['2.0', '3.0', '3.0 Premium', 'A91 Edition'], ['2', '3', '3premium', 'a91edition'], '2021', 'Coupe')


# In[51]:


toyotadata('https://www.toyota.com/sienna/features/mileage_estimates/5402/5411/5419', 'Sienna', ['LE', 'XLE’', 'XSE',  'Limited', 'Platinum'], ['le', 'xle','xse', 'limited', 'platinum'], '2021', 'Van')


# In[52]:


toyotadata('https://www.toyota.com/tacoma/features/mpg/7594/7544/7582', 'Tacoma', ['SR', 'SR5', 'TRD Sport',  'TRD Off-Road', 'Limited', 'TRD Pro'], ['sr', 'sr5','trd_sport', 'trd_off_road', 'limited', 'trd_pro'], '2021', 'Pickup Truck')


# In[53]:


toyotadata('https://www.toyota.com/tundra/features/mpg/8261/8252/8275', 'Tundra', ['SR', 'SR5', 'Limited', 'Platinum', '1794 Edition', 'TRD Pro'], ['sr', 'sr5','limited', 'platinum', '1794', 'trdpro'], '2021', 'Pickup Truck')


# In[54]:


toyotadata('https://www.toyota.com/venza/features/mpg/2810/2820/2830', 'Venza', ['LE', 'XLE', 'Limited'], ['le', 'xle', 'limited'], '2021', 'SUV')


# In[55]:


toyotadata('https://www.toyota.com/c-hr/features/mpg/2402/2404/2405', 'C-HR', ['LE', 'XLE', 'Nightshade Edition', 'Limited'], ['le', 'xle', 'nightshade', 'limited'], '2021', 'SUV')


# In[56]:


toyotadata('https://www.toyota.com/rav4prime/features/mpg/4544/4550', 'Rav4 Prime', ['Prime SE', 'Prime XSE'], ['prime_se', 'prime_xse'], '2021', 'SUV', printfeatures=True)


# In[57]:


toyotadata('https://www.toyota.com/rav4/features/mpg/4450', 'Rav4', ['LE', 'LE Hybrid', 'XLE', 'XLE Hybrid','XLE Premium', 'XLE Premium Hybrid', 'Adventure', 'TRD Off-Road',  'XSE Hybrid', 'Limited', 'Limited Hybrid'], ['le', 'le-hybrid', 'xle', 'xle-hybrid', 'xle_premium', 'xle-premium-hybrid',  'adventure', 'trd_off_road',  'xse-hybrid','limited', 'limited-hybrid'], '2021', 'SUV')


# In[58]:


toyotadata('https://www.toyota.com/highlander/features/mileage_estimates/6964/6953/6961', 'Highlander', ['L', 'LE', 'Hybrid LE', 'XLE', 'XLE Hybrid', 'XSE', 'Limited', 'Hybrid Limited', 'Platinum', 'Hybrid Platinum'], ['l', 'le', 'hybrid-le',  'xle', 'hybrid-xle', 'xse', 'limited', 'hybrid-limited', 'platinum', 'hybrid-platinum'], '2021', 'SUV')


# In[59]:


toyotadata('https://www.toyota.com/4runner/features/mileage_estimates/8664/8666/8667/', '4Runner', ['SR5', 'Trial Special Edition', 'SR5 Premium', 'TRD Off-Road', 'TRD Off-Road Premium', 'Venture Special Edition', 'Limited', 'Nightshade Special Edition', 'TRD Pro'], ['sr5', 'trail_special_edition', 'sr5_premium', 'trd_off_road', 'trd_off_road_premium', 'venture_edition', 'limited', 'limited_nightshade', 'trd_pro'], '2021', 'SUV')


# In[60]:


toyotadata('https://www.toyota.com/sequoia/features/mpg/7917/7921/7927', 'Sequoia', ['SR5', 'TRD Sport', 'Limited', 'Nightshade Special Edition', 'Platinum', 'TRD Pro'], ['sr5', 'trd_sport', 'limited', 'nightshade_special_edition', 'platinum', 'trd_pro'], '2021', 'SUV')


# In[61]:


toyotadata('https://www.toyota.com/landcruiser/features/mpg/6156/6157', 'Land Cruiser', ['Land Cruiser', 'Heritage Edition'], ['landcruiser', 'heritage_edition'], '2021', 'SUV')


# # Honda

# In[99]:


modeloutput("https://automobiles.honda.com/hr-v/specs-features-trim-comparison#", 'Honda', 'HR-V', ['LX', 'Sport', 'EX', 'EX-L'] , '2021', 'SUV')


# In[100]:


modeloutput("https://automobiles.honda.com/cr-v/specs-features-trim-comparison", 'Honda', 'CR-V', ['LX', 'Special Edition', 'EX', 'EX-L', 'Touring'] , '2021', 'SUV')


# In[101]:


modeloutput("https://automobiles.honda.com/pilot/specs-features-trim-comparison", 'Honda', 'Pilot', ['LX', 'EX', 'EX-L',  'Special Edition', 'Touring', 'Elite', 'Black Edition'] , '2021', 'SUV')


# In[102]:


modeloutput("https://automobiles.honda.com/passport/specs-features-trim-comparison", 'Honda', 'Passport', ['Sport','EX-L', 'Touring','Elite'] , '2021', 'SUV')


# In[103]:


modeloutput("https://automobiles.honda.com/civic-sedan/specs-features-trim-comparison", 'Honda', 'Civic', ['LX', 'Sport','EX', 'Touring'] , '2021', 'Sedan')


# In[104]:


modeloutput("https://automobiles.honda.com/accord-sedan/specs-features-trim-comparison", 'Honda', 'Accord', ['LX', 'Hybrid', 'Sport','Sport Special Edition', 'Hybrid EX','EX-L', 'Touring'] , '2021', 'Sedan')


# In[105]:


modeloutput("https://automobiles.honda.com/insight/specs-features-trim-comparison", 'Honda', 'Insight', ['EX', 'Touring'] , '2021', 'Sedan')


# In[106]:


modeloutput("https://automobiles.honda.com/clarity-fuel-cell/specs-features-trim-comparison", 'Honda', 'Clarity', ['Fuel Cell'] , '2021', 'Sedan')


# In[107]:


modeloutput("https://automobiles.honda.com/clarity-plug-in-hybrid/specs-features-trim-comparison", 'Honda', 'Clarity', ['Plug-In Hybrid', 'Touring'] , '2021', 'Sedan')


# In[108]:


modeloutput("https://automobiles.honda.com/civic-hatchback/specs-features-trim-comparison", 'Honda', 'Civic Hatchback', ['LX', 'Sport','EX', 'Sport Touring'] , '2021', 'Hatchback')


# In[111]:


modeloutput("https://automobiles.honda.com/civic-type-r/specs-features-trim-comparison", 'Honda', 'Civic Type R', ['Civic Type R', 'Limited Edition'] , '2021', 'Hatchback')


# In[109]:


modeloutput("https://automobiles.honda.com/odyssey/specs-features-trim-comparison", 'Honda', 'Odyssey', ['LX', 'EX', 'EX-L',  'Touring', 'Elite'] , '2021', 'Minivan')


# In[110]:


modeloutput("https://automobiles.honda.com/ridgeline/specs-features-trim-comparison", 'Honda', 'Ridgeline', ['Sport', 'RTL', 'RTL-E', 'Black Edition'] , '2021', 'Pickup Truck')


# # Nissan

# In[ ]:


SUVS, have Navilink


# In[90]:


websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/kicks/specs/compare-specs.html#modelName=S|Xtronic%20CVT%C2%AE", 'Nissan', 'Kicks', 'S', '2021', 'SUV')
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/kicks/specs/compare-specs.html#modelName=SV|Xtronic%20CVT%C2%AE", 'Nissan', 'Kicks', 'SV', '2021', 'SUV')
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/kicks/specs/compare-specs.html#modelName=SR|Xtronic%20CVT%C2%AE", 'Nissan', 'Kicks', 'SR', '2021','SUV')


# In[91]:


websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/rogue-sport/specs/compare-specs.html#modelName=S|FWD%20Xtronic%20CVT%C2%AE", 'Nissan', 'Rogue Sport', 'S', '2021', 'SUV')
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/rogue-sport/specs/compare-specs.html#modelName=SV|FWD%20Xtronic%20CVT%C2%AE", 'Nissan', 'Rogue Sport', 'SV', '2021', 'SUV')
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/rogue-sport/specs/compare-specs.html#modelName=SL|FWD%20Xtronic%20CVT%C2%AE", 'Nissan', 'Rogue Sport', 'SL', '2021','SUV')


# In[92]:


websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/rogue/specs/compare-specs.html#modelName=S|FWD", 'Nissan', 'Rogue', 'S', '2021', 'SUV')
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/rogue/specs/compare-specs.html#modelName=SV|FWD", 'Nissan', 'Rogue', 'SV', '2021', 'SUV')
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/rogue/specs/compare-specs.html#modelName=SL|FWD", 'Nissan', 'Rogue', 'SL', '2021','SUV') 
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/rogue/specs/compare-specs.html#modelName=Platinum|FWD", 'Nissan', 'Rogue', 'Platinum', '2021','SUV')


# In[93]:


websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/murano/specs/compare-specs.html#modelName=S|FWD", 'Nissan', 'Murano', 'S', '2021', 'SUV')
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/murano/specs/compare-specs.html#modelName=SV|2WD", 'Nissan', 'Murano', 'SV', '2021', 'SUV')
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/murano/specs/compare-specs.html#modelName=SL|FWD", 'Nissan', 'Murano', 'SL', '2021','SUV') 
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/murano/specs/compare-specs.html#modelName=Platinum|FWD", 'Nissan', 'Murano', 'Platinum', '2021','SUV')


# In[94]:


websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/pathfinder/specs/compare-specs.html#modelName=S|2WD", 'Nissan', 'Pathfinder', 'S', '2021', 'SUV')
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/pathfinder/specs/compare-specs.html#modelName=SV|2WD", 'Nissan', 'Pathfinder', 'SV', '2021', 'SUV')
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/pathfinder/specs/compare-specs.html#modelName=SL|2WD", 'Nissan', 'Pathfinder', 'SL', '2021','SUV') 
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/pathfinder/specs/compare-specs.html#modelName=SV%20Rock%20Creek%E2%84%A2%20Edition|2WD", 'Nissan', 'Pathfinder', 'SV Rock Creek Edition', '2021', 'SUV')
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/pathfinder/specs/compare-specs.html#modelName=SL%20Rock%20Creek%E2%84%A2%20Edition|2WD", 'Nissan', 'Pathfinder', 'SL Rock Creek Edition', '2021','SUV') 
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/pathfinder/specs/compare-specs.html#modelName=Platinum|2WD", 'Nissan', 'Pathfinder', 'Platinum', '2021','SUV')


# In[95]:


websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/armada/specs/compare-specs.html#modelName=S|2WD", 'Nissan', 'Armada', 'S', '2021', 'SUV')
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/armada/specs/compare-specs.html#modelName=SV|2WD", 'Nissan', 'Armada', 'SV', '2021', 'SUV')
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/armada/specs/compare-specs.html#modelName=SL|2WD", 'Nissan', 'Armada', 'SL', '2021','SUV')
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/armada/specs/compare-specs.html#modelName=Midnight%20Edition|2WD", 'Nissan', 'Armada', 'Midnight Edition', '2021','SUV') 
websiteoutput("https://www.nissanusa.com/vehicles/crossovers-suvs/armada/specs/compare-specs.html#modelName=Platinum|2WD", 'Nissan', 'Armada', 'Platinum', '2021','SUV')


# In[96]:


websiteoutput("https://www.nissanusa.com/vehicles/cars/versa-sedan/specs/compare-specs.html#modelName=S|5-speed%20manual%20transmission", 'Nissan', 'Versa', 'S', '2021', 'Sedan')
websiteoutput("https://www.nissanusa.com/vehicles/cars/versa-sedan/specs/compare-specs.html#modelName=SV|Xtronic%20CVT%C2%AE", 'Nissan', 'Versa', 'SV', '2021', 'Sedan')
websiteoutput("https://www.nissanusa.com/vehicles/cars/versa-sedan/specs/compare-specs.html#modelName=SR|Xtronic%20CVT%C2%AE", 'Nissan', 'Versa', 'SR', '2021','Sedan')


# In[97]:


websiteoutput("https://www.nissanusa.com/vehicles/cars/sentra/specs/compare-specs.html#modelName=S|Xtronic%20CVT%C2%AE", 'Nissan', 'Senta', 'S', '2021', 'Sedan')
websiteoutput("https://www.nissanusa.com/vehicles/cars/sentra/specs/compare-specs.html#modelName=SV|Xtronic%20CVT%C2%AE", 'Nissan', 'Senta', 'SV', '2021', 'Sedan')
websiteoutput("https://www.nissanusa.com/vehicles/cars/sentra/specs/compare-specs.html#modelName=SR|Xtronic%20CVT%C2%AE", 'Nissan', 'Senta', 'SR', '2021','Sedan')


# In[44]:


websiteoutput("https://www.nissanusa.com/vehicles/cars/altima/specs/compare-specs.html#modelName=S|FWD", 'Nissan', 'Altima', 'S', '2021', 'Sedan')
websiteoutput("https://www.nissanusa.com/vehicles/cars/altima/specs/compare-specs.html#modelName=SV|FWD", 'Nissan', 'Altima', 'SV', '2021', 'Sedan')
websiteoutput("https://www.nissanusa.com/vehicles/cars/altima/specs/compare-specs.html#modelName=SR|FWD", 'Nissan', 'Altima', 'SR', '2021','Sedan')
websiteoutput("https://www.nissanusa.com/vehicles/cars/altima/specs/compare-specs.html#modelName=SL|FWD", 'Nissan', 'Altima', 'SL', '2021','Sedan')
websiteoutput("https://www.nissanusa.com/vehicles/cars/altima/specs/compare-specs.html#modelName=SR%20VC-Turbo%E2%84%A2|FWD", 'Nissan', 'Altima', 'SR VC-Turbo', '2021','Sedan')
websiteoutput("https://www.nissanusa.com/vehicles/cars/altima/specs/compare-specs.html#modelName=Platinum|Intelligent%20AWD%20[[2021_ALTIMA_1323]]", 'Nissan', 'Altima', 'Platinum', '2021','Sedan')


# In[45]:


websiteoutput("https://www.nissanusa.com/vehicles/cars/maxima/specs/compare-specs.html#modelName=SV|Xtronic%20CVT%C2%AE", 'Nissan', 'Maxima', 'SV', '2021', 'Sedan')
websiteoutput("https://www.nissanusa.com/vehicles/cars/maxima/specs/compare-specs.html#modelName=SR|Xtronic%20CVT%C2%AE", 'Nissan', 'Maxima', 'SR', '2021','Sedan')
websiteoutput("https://www.nissanusa.com/vehicles/cars/maxima/specs/compare-specs.html#modelName=Platinum|Xtronic%20CVT%C2%AE", 'Nissan', 'Maxima', 'Platinum', '2021','Sedan')
websiteoutput("https://www.nissanusa.com/vehicles/cars/maxima/specs/compare-specs.html#modelName=40th%20Anniversary%20Edition|Xtronic%20CVT%C2%AE", 'Nissan', 'Maxima', '40th Anniversary Edition', '2021','Sedan')


# In[54]:


websiteoutput("https://www.nissanusa.com/vehicles/electric-cars/leaf/specs/compare-specs.html#modelName=S|40%20kWh", 'Nissan', 'Leaf', 'S', '2021', 'Hatchback')
websiteoutput("https://www.nissanusa.com/vehicles/electric-cars/leaf/specs/compare-specs.html#modelName=SV|40%20kWh", 'Nissan',  'Leaf', 'SV', '2021', 'Hatchback')
websiteoutput("https://www.nissanusa.com/vehicles/electric-cars/leaf/specs/compare-specs.html#modelName=S%20PLUS|62%20kWh", 'Nissan',  'Leaf', 'S Plus', '2021','Hatchback')
websiteoutput("https://www.nissanusa.com/vehicles/electric-cars/leaf/specs/compare-specs.html#modelName=SV%20PLUS|62%20kWh", 'Nissan',  'Leaf', 'SV Plus', '2021','Hatchback')
websiteoutput("https://www.nissanusa.com/vehicles/electric-cars/leaf/specs/compare-specs.html#modelName=SL%20PLUS|62%20kWh", 'Nissan',  'Leaf', 'SL Plus', '2021','Hatchback')


# In[184]:


websiteoutput("https://www.nissanusa.com/vehicles/trucks/frontier/specs/compare-specs.html#modelName=King%20Cab%C2%AE%20S|4x2", 'Nissan', 'Frontier', 'King Cab S', '2021', 'Pickup Truck')
websiteoutput("https://www.nissanusa.com/vehicles/trucks/frontier/specs/compare-specs.html#modelName=King%20Cab%C2%AE%20SV|4x2", 'Nissan', 'Frontier', 'King Cab SV', '2021', 'Pickup Truck')
websiteoutput("https://www.nissanusa.com/vehicles/trucks/frontier/specs/compare-specs.html#modelName=Crew%20Cab%20S|4x2", 'Nissan', 'Frontier', 'Crew Cab S', '2021', 'Pickup Truck')
websiteoutput("https://www.nissanusa.com/vehicles/trucks/frontier/specs/compare-specs.html#modelName=Crew%20Cab%20SV|4x2", 'Nissan', 'Frontier', 'Crew Cab SV', '2021', 'Pickup Truck')
websiteoutput("https://www.nissanusa.com/vehicles/trucks/frontier/specs/compare-specs.html#modelName=Crew%20Cab%20Midnight%20Edition%C2%AE|4x4", 'Nissan', 'Frontier', 'Crew Cab Midnight Edition', '2021', 'Pickup Truck')
websiteoutput("https://www.nissanusa.com/vehicles/trucks/frontier/specs/compare-specs.html#modelName=Crew%20Cab%20Long%20Bed%20SV|4x4", 'Nissan', 'Frontier', 'Crew Cab Long Bed SV', '2021', 'Pickup Truck')
websiteoutput("https://www.nissanusa.com/vehicles/trucks/frontier/specs/compare-specs.html#modelName=Crew%20Cab%20PRO-4X%C2%AE|4x4", 'Nissan', 'Frontier', 'Crew Cab PRO-4X', '2021', 'Pickup Truck')


# In[185]:


websiteoutput("https://www.nissanusa.com/vehicles/trucks/titan/specs/compare-specs.html#modelName=King%20Cab%C2%AE%20S|4x2", 'Nissan', 'Titan', 'King Cab S', '2021', 'Pickup Truck')
websiteoutput("https://www.nissanusa.com/vehicles/trucks/titan/specs/compare-specs.html#modelName=Crew%20Cab%20S|4x2", 'Nissan', 'Titan', 'Crew Cab S', '2021', 'Pickup Truck')
websiteoutput("https://www.nissanusa.com/vehicles/trucks/titan/specs/compare-specs.html#modelName=King%20Cab%C2%AE%20SV|4x2", 'Nissan', 'Titan', 'King Cab SV', '2021', 'Pickup Truck')
websiteoutput("https://www.nissanusa.com/vehicles/trucks/titan/specs/compare-specs.html#modelName=Crew%20Cab%20SV|4x2", 'Nissan', 'Titan', 'Crew Cab SV', '2021', 'Pickup Truck')
websiteoutput("https://www.nissanusa.com/vehicles/trucks/titan/specs/compare-specs.html#modelName=Crew%20Cab%20PRO-4X%C2%AE|4x4", 'Nissan', 'Titan', 'Crew Cab PRO-4X', '2021', 'Pickup Truck')
websiteoutput("https://www.nissanusa.com/vehicles/trucks/titan/specs/compare-specs.html#modelName=Crew%20Cab%20Platinum%20Reserve|4x4", 'Nissan', 'Titan', 'Crew Cab Platinum Reserve', '2021', 'Pickup Truck')


# In[190]:


websiteoutput("https://www.nissanusa.com/vehicles/trucks/titan-xd/specs/compare-specs.html#modelName=Crew%20Cab%20S|4x4", 'Nissan', 'Titan XD', 'Crew Cab S', '2021', 'Pickup Truck')
websiteoutput("https://www.nissanusa.com/vehicles/trucks/titan-xd/specs/compare-specs.html#modelName=Crew%20Cab%20SV|4x4", 'Nissan', 'Titan XD', 'Crew Cab SV', '2021', 'Pickup Truck')
websiteoutput("https://www.nissanusa.com/vehicles/trucks/titan-xd/specs/compare-specs.html#modelName=Crew%20Cab%20PRO-4X%C2%AE|4x4", 'Nissan', 'Titan XD', 'Crew Cab PRO-4X', '2021', 'Pickup Truck')
websiteoutput("https://www.nissanusa.com/vehicles/trucks/titan-xd/specs/compare-specs.html#modelName=Crew%20Cab%20Platinum%20Reserve|4x4", 'Nissan', 'Titan XD', 'Crew Cab Platinum Reserve', '2021', 'Pickup Truck')


# In[191]:


websiteoutput("https://www.nissanusa.com/vehicles/sports-cars/gt-r/specs/compare-specs.html#modelName=Premium|Dual-clutch%206-Speed%20Transmission", 'Nissan', 'GT-R', 'Premium', '2021', 'Coupe')
websiteoutput("https://www.nissanusa.com/vehicles/sports-cars/gt-r/specs/compare-specs.html#modelName=NISMO%C2%AE|Dual-clutch%206-Speed%20Transmission", 'Nissan', 'GT-R', 'NISMO', '2021', 'Coupe')


# In[192]:


websiteoutput("https://www.nissanusa.com/vehicles/commercial/nv-cargo/specs/compare-specs.html#modelName=NV1500%C2%AE%20S|Cargo%20Standard%20Roof%20V6", 'Nissan', 'NV Cargo', 'NV1500 S', '2021', 'Van')
websiteoutput("https://www.nissanusa.com/vehicles/commercial/nv-cargo/specs/compare-specs.html#modelName=NV2500%C2%AE%20HD%20S|Cargo%20High%20Roof%20V6", 'Nissan', 'NV Cargo', 'NV2500 HD S', '2021', 'Van')
websiteoutput("https://www.nissanusa.com/vehicles/commercial/nv-cargo/specs/compare-specs.html#modelName=NV1500%C2%AE%20SV|Cargo%20Standard%20Roof%20V6", 'Nissan', 'NV Cargo', 'NV1500 SV', '2021', 'Van')
websiteoutput("https://www.nissanusa.com/vehicles/commercial/nv-cargo/specs/compare-specs.html#modelName=NV2500%C2%AE%20HD%20SV|Cargo%20Standard%20Roof%20V8", 'Nissan', 'NV Cargo', 'NV2500 HD SV', '2021', 'Van')
websiteoutput("https://www.nissanusa.com/vehicles/commercial/nv-cargo/specs/compare-specs.html#modelName=NV3500%C2%AE%20HD%20SV|Cargo%20High%20Roof%20V8", 'Nissan', 'NV Cargo', 'NV3500 HD SV', '2021', 'Van')
websiteoutput("https://www.nissanusa.com/vehicles/commercial/nv-cargo/specs/compare-specs.html#modelName=NV3500%C2%AE%20HD%20SL|Cargo%20High%20Roof%20V8", 'Nissan', 'NV Cargo', 'NV3500 HD SL', '2021', 'Van')


# In[193]:


websiteoutput("https://www.nissanusa.com/vehicles/commercial/nv200-compact-cargo/specs/compare-specs.html#modelName=S|Xtronic%20CVT%C2%AE", 'Nissan', 'NV200 Compact Cargo', 'S', '2021', 'Van')
websiteoutput("https://www.nissanusa.com/vehicles/commercial/nv200-compact-cargo/specs/compare-specs.html#modelName=SV|Xtronic%20CVT%C2%AE", 'Nissan', 'NV200 Compact Cargo', 'SV', '2021', 'Van')


# In[194]:


websiteoutput("https://www.nissanusa.com/vehicles/commercial/nv-passenger/specs/compare-specs.html#modelName=S|Passenger%20S", 'Nissan', 'NV Passenger', 'S', '2021', 'Van')
websiteoutput("https://www.nissanusa.com/vehicles/commercial/nv-passenger/specs/compare-specs.html#modelName=SV|Passenger%20SV", 'Nissan', 'NV Passenger', 'SV', '2021', 'Van')
websiteoutput("https://www.nissanusa.com/vehicles/commercial/nv-passenger/specs/compare-specs.html#modelName=SL|Passenger%20SL", 'Nissan', 'NV Passenger', 'SL', '2021', 'Van')


# # Jeep

# In[ ]:





# In[103]:


def getjeep(url, manufacturer, model_name='', trims=[], year='', vehicle_type='', printfeatures=True, printpage=False):
    chromedriver = r"C:\Users\nihal\Documents\chromedriver\chromedriver.exe"
    options = webdriver.ChromeOptions().add_argument('--headless')
    browser = webdriver.Chrome(executable_path=chromedriver, options=options)
    
    
    #some code that I don't understand and just copied from online. It gets the plain text from the webpage
    #s = requests_html.HTMLSession()
    #pagetext = s.get(url)
    browser.get(url)
    print("From website " + url)
    
    browser.execute_script("arguments[0].click();", browser.find_element_by_xpath("//span[contains (text(), 'Display Model Comparison') and @class='gcss-colors-text-body-primary']"))
    
    time.sleep(0.5)
        
    for trim in trims:
        
        print ("Trim is " + trim)
        
        if trim == '80th Anniversary':
            while not browser.find_element_by_xpath("//span[@class='gcss-no-text-transform']/span[contains(text(), '80')]").is_displayed():
                browser.execute_script("arguments[0].click();", browser.find_element_by_xpath("//a[.//span[text()='Next Model']]"))
                time.sleep(0.5)
        else: 
            while not browser.find_element_by_xpath("(//span[contains(text(), "+ "'" + trim + "'" + ") and @class='gcss-no-text-transform'])[1] | (//span[@class='gcss-no-text-transform']/span[contains(text(), "+ "'" + trim + "'" + ")])[1]").is_displayed():
                browser.execute_script("arguments[0].click();", browser.find_element_by_xpath("//a[.//span[text()='Next Model']]"))
                time.sleep(0.5)

        
        pagetext = browser.page_source
        mindex = pagetext.index('>$', pagetext.index(trim, pagetext.index(trim)+1))
        msrp = pagetext[mindex+len('>$'):pagetext.index('</div></div></div>', mindex)]
        
        browser.execute_script("arguments[0].click();", browser.find_element_by_xpath("(//a[contains (@data-context,'" +  trim.replace(' ', '_')+ "') and @data-lid='View Standard Features'])[1]"))
        
        time.sleep(0.5)
        
        pagetext = browser.find_element_by_xpath("//div[@class='standard-feat-modal-content']").get_attribute('innerHTML')
        pagetext = pagetext.lower()
        
        browser.execute_script("arguments[0].click();", browser.find_element_by_xpath("(//button[@aria-label='CLOSE'])[2]"))

        time.sleep(0.5)
        
        if printpage: print(pagetext)
            
        adas, translations = gettranslations('translations.csv', manufacturer)

        writedata('codedrows.csv', url, manufacturer, model_name, trim, year, vehicle_type, msrp, adas, translations, pagetext, printfeatures)

    browser.quit()


# In[71]:


getjeep('https://www.jeep.com/bmo.renegade.2021.html#/models/2021/renegade?app=bmo&pageType=vehiclepage&vehicle=renegade&year=2021', 'Jeep', 'Renegade', ['Sport', 'Jeepster', 'Latitude', 'Upland', 'Freedom', '80th Anniversary', 'Island', 'Limited', 'Trailhawk'], '2021', 'SUV')


# In[72]:


getjeep('https://www.jeep.com/bmo.compass.2021.html#/models/2021/compass?app=bmo&pageType=vehiclepage&vehicle=compass&year=2021', 'Jeep', 'Compass', ['Sport', 'Freedom', 'Latitude', 'Altitude', '80th Anniversary', 'Limited', 'Trailhawk'], '2021', 'SUV')


# In[73]:


getjeep('https://www.jeep.com/bmo.wrangler.2021.html#/models/2021/wrangler?app=bmo&pageType=vehiclepage&vehicle=wrangler&year=2021', 'Jeep', 'Wrangler', ['Sport', 'Willys Sport', 'Sport S', 'Islander', 'Willys', '80th Anniversary', 'Freedom', 'Sport Altitude', 'RHD', 'Sahara', 'Rubicon', 'Sahara Altitude', 'High Altitude', 'Rubicon 392' ], '2021', 'SUV')


# In[100]:


getjeep('https://www.jeep.com/bmo.wrangler_4xe.2021.html#/models/2021/wrangler_4xe?app=bmo&pageType=vehiclepage&vehicle=wrangler_4xe&year=2021', 'Jeep', 'Wrangler 4xe', ['Sahara', 'Rubicon', 'High Altitude'], '2021', 'SUV')


# In[74]:


getjeep('https://www.jeep.com/bmo.gladiator.2021.html#/models/2021/gladiator?app=bmo&pageType=vehiclepage&vehicle=gladiator&year=2021', 'Jeep', 'Gladiator', ['Sport', 'Willys Sport', 'Sport S', 'California Edition', 'Willys', '80th Anniversary', 'Freedom', 'Overland', 'Rubicon', 'Mojave', 'High Altitude'], '2021', 'SUV')


# In[75]:


getjeep('https://www.jeep.com/bmo.cherokee.2021.html#/models/2021/cherokee?app=bmo&pageType=vehiclepage&vehicle=cherokee&year=2021', 'Jeep', 'Cherokee', ['Latitude', 'Freedom', 'Latitude Plus', 'Altitude', 'Latitude Lux', '80th Anniversary', 'Limited', 'Trailhawk', 'High Altitude'], '2021', 'SUV')


# In[76]:


getjeep('https://www.jeep.com/bmo.grand_cherokee.2021.html#/models/2021/grand_cherokee?app=bmo&pageType=vehiclepage&vehicle=grand_cherokee&year=2021', 'Jeep', 'Grand Cherokee', ['Laredo E', 'Freedom', 'Laredo X', 'Limited', 'Limited X', '80th Anniversary', 'Trailhawk', 'Overland', 'High Altitude', 'Summit', 'SRT', 'Trackhawk'], '2021', 'SUV')


# In[77]:


getjeep('https://www.jeep.com/bmo.grand_cherokee_l.2021.html#/models/2021/grand_cherokee_l', 'Jeep', 'Grand Cherokee L', ['Laredo', 'Altitude', 'Limited', 'Overland', 'Summit', 'Summit Reserve'], '2021', 'SUV')


# In[109]:


getjeep('https://www.jeep.com/bmo.wagoneer.2022.html#/model/CUJ202215', 'Jeep', 'Wagoneer', ['Series II', 'Series III'], '2022', 'SUV')


# In[110]:


getjeep('https://www.jeep.com/bmo.grand_wagoneer.2022.html#/models/2022/grand_wagoneer', 'Jeep', 'Grand Wagoneer', ['Series I', 'Series II', 'Obsidian', 'Series III'], '2022', 'SUV')


# # New heading

# In[115]:





# In[ ]:




