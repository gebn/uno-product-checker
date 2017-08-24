# -*- coding: utf-8 -*-
from typing import Dict
import logging
import requests
import backoff
import os

import util


_ENDPOINT = 'https://my.uno.net.uk/modules/addons/unobroadband' \
            '/broadbandavailability.php'
_PHONE_NUMBER = util.kms_decrypt_str(os.environ['PHONE_NUMBER'])
_TYPE = os.environ['TYPE']
_EXPECTED_PRODUCTS = set(os.environ['EXPECTED_PRODUCTS'].split(','))
_PUSHOVER_APP_TOKEN = util.kms_decrypt_str(os.environ['PUSHOVER_APP_TOKEN'])


logging.getLogger('chump').setLevel(logging.INFO)  # chump is very loud
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def find_available_products(type_: str, phone_number: str) -> Dict[int, str]:
    """
    Ask Uno for a list of packages available on a line.
    
    :param type_: The type of product to query for, e.g. Phone & Broadband is
                  'phone_broadband'.
    :param phone_number: The line phone number, with no spaces or country code.
    :return: A dictionary of product names, keyed by product ID.
    :raises requests.exceptions.RequestException: If the request repeatedly
                                                  failed, or Uno indicated a
                                                  client-side error.
    """
    @backoff.on_exception(backoff.expo,
                          requests.exceptions.RequestException,
                          max_tries=8,
                          giveup=lambda e: 400 <= e.response.status_code < 500)
    def _request() -> requests.Response:
        """
        Send the query to Uno.
        
        :return: The raw response object.
        :raises requests.exceptions.RequestException: If the request fails.
        """
        response_ = requests.post(_ENDPOINT, data={
                'phone_number': phone_number,
                'type': type_
            })
        response_.raise_for_status()
        return response_

    logger.debug(f'Querying for {type_} products for {phone_number}...')
    response = _request()
    logger.info(f'Request time: {response.elapsed.total_seconds()}s')
    json = response.json()
    products = {product['id']: product['name']
                for _, content in json.items()
                for _, product in content['products'].items()}
    return products


def main():
    """
    Executes the high-level logic of the checker.
    
    :return: 0 on success, 1 on failure.
    """
    try:
        available_products = find_available_products(_TYPE, _PHONE_NUMBER)
        if available_products.keys() != _EXPECTED_PRODUCTS:
            body = '\n'.join(f' - {name}'
                             for _, name in available_products.items())
            logger.info(f'Product list has changed:\n{body}')
            # TODO publish notif to SNS 'Uno service offering has changed'
        else:
            logger.info('No change to available product list')
        return 0
    except requests.exceptions.RequestException:
        logger.exception(f'Failed to retrieve products for {_PHONE_NUMBER}')
        return 1


# noinspection PyUnusedLocal
def lambda_handler(event, context) -> int:
    """
    AWS Lambda entry point.

    :param event: The event that triggered this execution.
    :param context: Current runtime information: http://docs.aws.amazon.com
                    /lambda/latest/dg/python-context-object.html.
    :return: The script exit code. 
    """
    logger.info(f'Event: {event}')
    return main()
