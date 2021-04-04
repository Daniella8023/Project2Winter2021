#################################
##### Name: Dan Qiao
##### Uniqname: jordannn
#################################

from bs4 import BeautifulSoup
import requests
import time
import json
import secrets # file that contains your API key

CACHE_FILE_NAME = 'cacheSI_Scrape.json'
CACHE_DICT = {}


def load_cache():
    '''
    load cache
    Parameters
    ----------
    None

    Return
    ----------
    cache: dict
    '''
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache


def save_cache(cache):
    '''
    Save cache

    Parameters
    ----------
    None

    Return
    ---------
    None
    '''
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()


def make_url_request_using_cache(url, cache):
    '''
    check whether url have been scrapped or not,
    if url is new, fetch and save cache
    if not, use the caching data 

    Parameters
    ----------
    url, cache

    Returns
    ----------
    cache[url]: text 
    '''
    if (url in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]


def make_api_request_using_cache(url, cache):
    '''
    check whether url is new or not,
    if url is new, use API Search and save cache
    if not, use the caching data 
    
    Parameters
    ----------
    url, cache

    Returns
    ----------
    cache[url]: dict
    '''
    if (url in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        resp = requests.get(url)
        cache[url] = resp.json()
        save_cache(cache)
        return cache[url]


class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone 
    
    def info(self):
        return self.name + ' (' + self.category + '): ' + self.address + ' '+ self.zipcode


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''

    BASE_URL = "https://www.nps.gov/index.htm"
    #response = requests.get(BASE_URL)
    response = make_url_request_using_cache(BASE_URL, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')
    
    URL_DICT = {}
    
    Button = soup.find('div', class_='SearchBar-keywordSearch input-group input-group-lg')
    State_list = Button.find_all('a')
    for State in State_list:
        URL_DICT[State.string.lower()] = 'https://www.nps.gov' + State['href'] # 'michigan':'https://...'
    
    return URL_DICT


def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    #SCRAP PARK PAGES -> category, name, address, zipcode, phone
    #response = requests.get(site_url)
    response = make_url_request_using_cache(site_url, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')

    #category
    category = (soup.find('div', class_='Hero-designationContainer').find('span').string).strip()
    #name
    name = (soup.find('div', class_='Hero-titleContainer clearfix').find('a').string).strip()
    #address
    adr = soup.find('div',class_='mailing-address')
    if (adr is not None):
        addressLocality = adr.find('span',itemprop = 'addressLocality').string
        addressRegion = adr.find('span',itemprop = 'addressRegion').string
        address = addressLocality + ', ' + addressRegion
    #zipcode
    zipcode = (soup.find('p',class_='adr').find('span',itemprop = 'postalCode').string).strip()
    #phone
    phone = (soup.find('span',itemprop='telephone').string).strip()

    # Create a NationSite INSTANCE
    site_instance = NationalSite(category, name, address, zipcode, phone)
    return site_instance


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    #response = requests.get(state_url)
    response = make_url_request_using_cache(state_url, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')
    PARK_parent_URLs = soup.find('div', class_='col-md-9 col-sm-12 col-xs-12 stateCol').find_all('h3')
    #state -> sites

    site_list = [] #store the list of sties

    for PARK_parent_URL in PARK_parent_URLs: #for each site
        PARK_URL = 'https://www.nps.gov' + PARK_parent_URL.find('a')['href'] + 'index.htm' # site pages e.g. https://www.nps.gov/isro/index.htm
        site_list.append(get_site_instance(PARK_URL)) #scrap the information, append to list

    return site_list


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    # url
    BASE_URL = 'http://www.mapquestapi.com/search/v2/radius?'
    key = secrets.API_KEY
    #origin = site_object.zipcode
    origin = site_object.zipcode
    radius = '10'
    maxMatches = '10'
    ambiguities = 'ignore'
    outFormat = 'json'

    url = BASE_URL+'&key='+key+'&origin='+origin+'&radius='+radius+'&maxMatches='+maxMatches+'&ambiguities='+ambiguities+'&outFormat='+outFormat
    
    # API result
    results = make_api_request_using_cache(url, CACHE_DICT)
    
    num = len(results['searchResults'])
    for i in range(num):
        #find name, category, city from API results
        name = results['searchResults'][i]['name']

        category = results['searchResults'][i]['fields']['group_sic_code_name']
        if (category == ''):
            category = 'no category'

        address = results['searchResults'][i]['fields']['address']
        if (address == ''):
            address = 'no address'

        city = results['searchResults'][i]['fields']['city']
        if (city == ''):
            city = 'no city'
        
        output = '- ' + name +'('+category + '): '+ address + ', '+city
        print(output)
    
    return results

CACHE_DICT = load_cache()  # init cache
URL_DICT = build_state_url_dict() # create dictionary {'michigan':'https://...'}

#PART 5: Interface
while(1):
    state_name = input('Enter a state name (e.g. Michigan, michigan) or "exit" : ')

    #[Step1]
    if (state_name == 'exit'):
        exit()  

    elif (state_name.lower() in URL_DICT):
    
        state_url = URL_DICT[state_name.lower()] # Micigan: https://www.nps.gov/state/mi/index.htm
        site_list = get_sites_for_state(state_url) # https://www.nps.gov/state/mi/index.htm --> [Isle Royale, Keweenaw, North Country...]
    
        #[step2]
        print("-----------------------------------")
        print('List of national sites in',state_name)
        print("-----------------------------------")
        i=1
        for park in site_list:
            print('[{}]'.format(i), park.info() ) #print site info
            i=i+1

        #[step3]
        while(1):
            print("-----------------------------------")
            a = input('Choose the number for detail search or "exit" or "back" : ')
            if (a.isnumeric() is True):
                if (int(a) <= len(site_list)):

                    #[step4]
                    print("-----------------------------------")
                    print('Places near',site_list[int(a)-1].name)
                    print("-----------------------------------")
                    get_nearby_places(site_list[int(a)-1])
                    continue
                else:
                    print('[Error] Invalid input')
                    print('')

            #[step5]
            elif (a == 'exit'):
                exit()
            elif ( a == 'back'):
                break
            else:
                print('[Error] Invalid input')
                print('')

    else:
        print('[Error] Enter proper state name')
        print(' ')

    
if __name__ == "__main__":
    pass