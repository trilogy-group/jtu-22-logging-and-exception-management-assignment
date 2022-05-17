import xmltodict
from jsonschema import validate, draft7_format_checker
import logging
from uszipcode import SearchEngine
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s : %(levelname)s : %(name)s : %(message)s")

filehandler = logging.FileHandler('routers.log')
filehandler.setFormatter(formatter)

logger.addHandler(filehandler)

# ISO8601 datetime regex
regex = r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'
match_iso8601 = re.compile(regex).match
zipcode_search = SearchEngine()

class match_iso8601_failed(Exception):
    pass

class parse_xml_failed(Exception):
    pass

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
        else:
            raise match_iso8601_failed
    except match_iso8601_failed:
        logger.error(f"The requestdate - {requestdate} doesn't satisfy ISO 8601")
    return False


def is_nan(x):
    return x != x


def parse_xml(adf_xml):
    # use exception handling
    obj = xmltodict.parse(adf_xml)
    try:
        if obj == None:
            raise parse_xml_failed
    except parse_xml_failed:
        logger.error(f"adf_xml - {adf_xml} couldn't be parsed")
    return obj


def validate_adf_values(input_json):
    logger.info("Initiated validation of adf values")
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
        logger.error("name is incomplete")
        return {"status": "REJECTED", "code": "6_MISSING_FIELD", "message": "name is incomplete"}

    if not email and not phone:
        logger.error("either phone or email is required")
        return {"status": "REJECTED", "code": "6_MISSING_FIELD", "message": "either phone or email is required"}

    # zipcode validation
    res = zipcode_search.by_zipcode(zipcode)
    if not res:
        logger.error("Invalid Postal Code")
        return {"status": "REJECTED", "code": "4_INVALID_ZIP", "message": "Invalid Postal Code"}

    # check for TCPA Consent
    tcpa_consent = False
    for id in input_json['id']:
        if id['@source'] == 'TCPA_Consent' and id['#text'].lower() == 'yes':
            logger.info(f"TCPA Consent granted through {input_json['id']}")
            tcpa_consent = True
    logger.info(f"TCPA Consent: {tcpa_consent}")
    if not email and not tcpa_consent:
        logger.error("Conact Method missing TCPA consent")
        return {"status": "REJECTED", "code": "7_NO_CONSENT", "message": "Contact Method missing TCPA consent"}

    # request date in ISO8601 format
    if not validate_iso8601(input_json['requestdate']):
        logger.error("Invalid DateTime")
        return {"status": "REJECTED", "code": "3_INVALID_FIELD", "message": "Invalid DateTime"}

    logger.info("adf values validated")
    return {"status": "OK"}


def check_validation(input_json):
    logger.info(f"Validation of {input_json} started")
    try:
        process_before_validating(input_json)
        validate(
            instance=input_json,
            schema=schema,
            format_checker=draft7_format_checker,
        )
        response = validate_adf_values(input_json)
        if response['status'] == "REJECTED":
            logger.info(f"{input_json} is rejected")
            return False, response['code'], response['message']
        logger.info(f"{input_json} is successfully validated")
        return True, "input validated", "validation_ok"
    except Exception as e:
        logger.error(f"Validation failed: {e.message}")
        return False, "6_MISSING_FIELD", e.message
