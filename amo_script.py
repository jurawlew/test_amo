import json

import requests
import logging


logger = logging.getLogger(__name__)

AMOCRM_SUBDOMAIN = ''
AMOCRM_CLIENT_ID = ''
AMOCRM_CLIENT_SECRET = ''
AMOCRM_REDIRECT_URL = ''
AMOCRM_ACCESS_TOKEN = ''
AMOCRM_REFRESH_TOKEN = ''

MAIN_URL = 'https://{}.amocrm.ru{}'

lead_data_from_wp = [
    {
        'name': '',
        'date': '',
        'products': [
            {
                'name': '',
                'sku': '',
                'other': '',
            },
            {
                'name': '',
                'sku': '',
                'other': '',
            }
        ]
    }
]


class AmoCRM:
    def __init__(self):
        self.main_url = MAIN_URL

    def base_request(self, **kwargs) -> dict:
        """ основной запрос """
        headers = {'Authorization': AMOCRM_ACCESS_TOKEN,
                   'Content-Type': 'application/json'}
        req_type = kwargs.get('type')
        response = ''
        try:
            if req_type == 'get':
                response = requests.get(
                    self.main_url.format(AMOCRM_SUBDOMAIN, kwargs.get('endpoint')),
                    headers=headers,
                    params=kwargs.get('params')
                ).json()
            elif req_type == 'post':
                response = requests.post(
                    self.main_url.format(AMOCRM_SUBDOMAIN, kwargs.get('endpoint')),
                    headers=headers,
                    json=kwargs.get('data')
                ).json()
        except json.JSONDecodeError as e:
            logger.exception(e)
        return response

    def get_lead_id(self, lead_id) -> dict:
        """получаем сделку по id"""
        url = '/api/v4/leads/' + str(lead_id)
        return self.base_request(endpoint=url, type='get')

    def post_lead(self, data) -> dict:
        """ создаём сделки """
        list_leads = []
        for lead in data:
            list_name_sku_products = [{product.get('name', ''): product.get('sku', '')} for
                                      product in lead.get('products', [])]
            if list_name_sku_products:
                list_empty_products = self.get_products(data=list_name_sku_products, req_type='not_available')
                if list_empty_products:
                    list_create_products = []
                    for el in list_empty_products:
                        res = next((i for i in lead.get('products') if i['sku'] == el['sku'] and
                                    i['name'] == el['name']), None)
                        list_create_products.append(res)
                    self.post_products(data=list_create_products)
            new_lead = {
                "name": lead.get('name'),
                "custom_fields_values": [
                    {
                        "products": list_name_sku_products
                    }
                ]
            }
            list_leads.append(new_lead)
        url = '/api/v4/leads'
        return self.base_request(endpoint=url, type='post', data=list_leads)

    def get_products_id(self, product_id) -> dict:
        """получаем продукт по id"""
        url = '/api/v2/catalogs/products/' + str(product_id)
        return self.base_request(endpoint=url, type='get')

    def get_products(self, catalog_id, data, req_type='') -> list:
        """ смотрим наши продукты """
        not_available = []
        available = []
        url = '/api/v2/catalogs/' + str(catalog_id) + str('elements')
        try:
            for product in data:
                params = {'filter[name]': product['name'], 'filter[sku]': product['sku']}
                response = self.base_request(endpoint=url, params=params, type='get')
                if response is None:
                    not_available.append(product)
            if req_type == 'not_available':
                return not_available
            elif req_type == 'available':
                return available
            else:
                return [self.base_request(endpoint=url, type='get')]
        except Exception as e:
            logger.exception(e)

    def post_products(self, catalog_id, data) -> list:
        """ создаём продукты """
        url = '/api/v2/catalogs/' + str(catalog_id)
        all_products = []
        for product in data:
            try:
                new_product = {}
                self.base_request(endpoint=url, type='post', data=new_product)
                all_products.append(new_product)
            except requests.exceptions.HTTPError as e:
                logger.exception(e)
        return all_products
