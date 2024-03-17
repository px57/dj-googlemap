

from django.db.models import Q

import mailchimp_transactional as MailchimpTransactional

from kernel.interfaces.service import ServiceManager

from geo.models import Countries, Cities, CitiesRelated, CountriesRelated

import requests
import pprint
import json
import threading

class Service(ServiceManager):
    def __init__(self):
        pass

    def init(self):
        """
        The constructor method.
        """

    def __autocomplete_place__nothasresult(self):
        """
        Autocomplete place error.
        """
        pass

    def get_reference_code(self, place_id):
        """
        Get the reference code from the place id.
        """
        return 'googlemap_' + place_id
    
    def get_reference_Dbquery(self, place_id):
        """
        Get the reference query from the place id.
        """
        return Q(reference_code=self.get_reference_code(place_id))
    
    def get_code_id_reference_code(self, reference_code):
        """
        Get the code id from the reference code.
        """
        reference_code = reference_code.replace('googlemap_', '')
        return reference_code

    def __get_details(self, dbCity):
        """
        Get the details of the city.
        """
        place_details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        place_params = {
            "place_id": self.get_code_id_reference_code(dbCity.reference_code),
            "key": self.config.get('API_KEY')
        }
        place_response = requests.get(
            place_details_url, 
            params=place_params
        )
        place_data = place_response.json()
        dbCity.api_data = place_data 
        dbCity.longitude = place_data['result']['geometry']['location']['lng']
        dbCity.latitude = place_data['result']['geometry']['location']['lat']
        dbCity.save()

    def __async_get_details(self, dbCity):
        """
        Get the details of the city asynchronously.
        """
        thread = threading.Thread(target=self.__get_details, args=(dbCity,))
        thread.start()

    def __autocomplete_place(
            self, 
            input_text: str = '',
            country: list = [] 
        ):
        """
        Autocomplete a place.

        Args:
            input_text (str): The input text
            country (list): The country list to filter the cities
        """
        def country_to_str(country: list):
            """
            Convert the country to string.
            """
            if country == []:
                return ''
            components = ''
            for c in country:
                components += 'country:' + c.code + '|'
            return components[:-1]

        endpoint = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
        params = {
            "input": input_text,
            "key": self.config.get('API_KEY'),
            "components": country_to_str(country) ,
            'locationbias': 'circle:radius@lat,lng'

        }
        try:
            response = requests.get(endpoint, params=params)
            data = response.json()
            if 'predictions' in data:
                return data
            else:
                return {}
        except Exception as e:
            return {}

    def __create_or_get_city_to_db(
            self, 
            city_list: dict,
            country: list = []
        ):
        """
        Create or get the city to the database.

        Args:
            city_list['predictions'] -> The city list
        """
        query = Q()
        for city in city_list['predictions']:
            query |= self.get_reference_Dbquery(city['place_id'])
        
        if len(query) == 0:
            return []
        
        dbCities = Cities.objects.filter(query)
        dbResultCities = []
        for city in city_list['predictions']:
            dbCity = dbCities.filter(
                self.get_reference_Dbquery(city['place_id'])
            ).first()
            if dbCity is None:
                dbCity = Cities(
                        reference_code=self.get_reference_code(city['place_id']),
                        name=city['description'],
                        country=country[0]
                )
                dbCity.save()
                self.__async_get_details(dbCity)

            dbResultCities.append(dbCity)

        return dbResultCities
        
    def find_city(
            self,
            query: str = '',
            country: list = [] 
        ):
        """
        Find the country list and return the response.

        Args:
            query (str): The query
            country (list): The country list to filter the cities
        """
        city_list = self.__autocomplete_place(
            input_text=query,
            country=country
        )
        
        dbCities = self.__create_or_get_city_to_db(city_list, country)
        return dbCities