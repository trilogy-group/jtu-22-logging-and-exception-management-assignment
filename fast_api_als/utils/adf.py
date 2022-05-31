import xmltodict
from jsonschema import validate, draft7_format_checker
import logging
from uszipcode import SearchEngine
import re

logger = logging.getLogger(__name__)

# ISO8601 datetime regex
regex = r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'
match_iso8601 = re.compile(regex).match
zipcode_search = SearchEngine()


def process_before_validating(input_json):
    if isinstance(input_json['adf']['prospect']['id'], dict):
        input_json['adf']['prospect']['id'] = [input_json['adf']['prospect']['id']]
    if isinstance(input_json['adf']['prospect']['customer']['contact'].get('email', {}), str):
        input_json['adf']['prospect']['customer']['contact']['email'] = {
            '@preferredcontact': '0',
            '#text': input_json['adf']['prospect']['customer']['contact']['email']
        }
    if isinstance(input_json['adf']['prospect']['vehicle'].get('price', []), dict):
        input_json['adf']['prospect']['vehicle']['price'] = [input_json['adf']['prospect']['vehicle']['price']]


def validate_iso8601(requestdate):
    try:
        if match_iso8601(requestdate) is not None:
            return True
    except:
        logger.warning(f'validate_iso8601 called with requestdate: {requestdate}')
    return False


def is_nan(x):
    return x != x


def parse_xml(adf_xml):
    # use exception handling
    try:
        obj = xmltodict.parse(adf_xml)
        return obj
    except Exception as e:
        logger.info(f'xml parse error {e} for adf_xml: {adf_xml}')


def validate_adf_values(input_json):
    logger.info(f'Validate_adf_values called with {input_json}')
    input_json = input_json['adf']['prospect']
    zipcode = input_json['customer']['contact']['address']['postalcode']
    email = input_json['customer']['contact'].get('email', None)
    phone = input_json['customer']['contact'].get('phone', None)
    names = input_json['customer']['contact']['name']
    make = input_json['vehicle']['make']

    first_name, last_name = False, False
    for name_part in names:
        if name_part.get('@part', '') == 'first' and name_part.get('#text', '') != '':
            first_name = True
        if name_part.get('@part', '') == 'last' and name_part.get('#text', '') != '':
            last_name = True

    if not first_name or not last_name:
        logger.info('input_json missing first_name or last_name field')
        return {"status": "REJECTED", "code": "6_MISSING_FIELD", "message": "name is incomplete"}

    if not email and not phone:
        logger.info('input_json missing both email and phone fields')
        return {"status": "REJECTED", "code": "6_MISSING_FIELD", "message": "either phone or email is required"}

    # zipcode validation
    res = zipcode_search.by_zipcode(zipcode)
    if not res:
        logger.info('input_json contains invalid postalcode field')
        return {"status": "REJECTED", "code": "4_INVALID_ZIP", "message": "Invalid Postal Code"}

    # check for TCPA Consent
    tcpa_consent = False
    for id in input_json['id']:
        if id['@source'] == 'TCPA_Consent' and id['#text'].lower() == 'yes':
            logger.info(f'tcpa_consent is true for id: {id}')
            tcpa_consent = True
    if not email and not tcpa_consent:
        logger.info(f'input_json missing email or does not have TCPA consent')
        return {"status": "REJECTED", "code": "7_NO_CONSENT", "message": "Contact Method missing TCPA consent"}

    # request date in ISO8601 format
    if not validate_iso8601(input_json['requestdate']):
        logger.info('input_json has missing or invalid format requestdate field')
        return {"status": "REJECTED", "code": "3_INVALID_FIELD", "message": "Invalid DateTime"}

    return {"status": "OK"}


def check_validation(input_json):
    try:
        process_before_validating(input_json)
        validate(
            instance=input_json,
            schema=schema,
            format_checker=draft7_format_checker,
        )
        response = validate_adf_values(input_json)
        if response['status'] == "REJECTED":
            return False, response['code'], response['message']
        return True, "input validated", "validation_ok"
    except Exception as e:
        logger.error(f"Validation failed: {e.message}")
        return False, "6_MISSING_FIELD", e.message
