import xmltodict
from jsonschema import validate, draft7_format_checker
import logging
from uszipcode import SearchEngine
import re

logging.basicConfig(format="%(levelname)s: %(asctime)s: %(message)s")

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
        logging.info("Validating ISO8601 Request Date")
        if match_iso8601(requestdate) is not None:
            return True
    except Exception as e:
        logging.error(f"Request Date {requestdate} Iso8601 Validation failed:  {e.message} ")
    return False


def is_nan(x):
    return x != x


def parse_xml(adf_xml):
    # use exception handling
    try:
        logging.info("Parsing adf xml")
        obj = xmltodict.parse(adf_xml)
        logging.info("Parse Successful")
        return obj
    except Exception as e:
        logging.error(f"Parse failed: {e.message}")
        raise Exception("Parsing Error")


def validate_adf_values(input_json):
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
        logging.info("Incomplete name adf validation rejected")
        return {"status": "REJECTED", "code": "6_MISSING_FIELD", "message": "name is incomplete"}

    if not email and not phone:
        logging.info("Phone or email missing adf validation rejected")
        return {"status": "REJECTED", "code": "6_MISSING_FIELD", "message": "either phone or email is required"}

    # zipcode validation
    res = zipcode_search.by_zipcode(zipcode)
    if not res:
        logging.info(f"Invalid Postal code - {zipcode} adf validation rejected")
        return {"status": "REJECTED", "code": "4_INVALID_ZIP", "message": "Invalid Postal Code"}

    # check for TCPA Consent
    logging.info("Checking TCPA Consent")
    tcpa_consent = False
    for id in input_json['id']:
        if id['@source'] == 'TCPA_Consent' and id['#text'].lower() == 'yes':
            tcpa_consent = True

    if not email and not tcpa_consent:
        logging.info("Missing TCPA Consent adf validation rejected")
        return {"status": "REJECTED", "code": "7_NO_CONSENT", "message": "Contact Method missing TCPA consent"}

    # request date in ISO8601 format
    if not validate_iso8601(input_json['requestdate']):
        requestdate = input_json['requestdate']
        logging.info(f"Invalid Datetime - {requestdate} adf validation rejected")
        return {"status": "REJECTED", "code": "3_INVALID_FIELD", "message": "Invalid DateTime"}

    return {"status": "OK"}


def check_validation(input_json):
    try:
        logging.info("Processing json before validating")
        process_before_validating(input_json)
        logging.info("Validating schema")
        validate(
            instance=input_json,
            schema=schema,
            format_checker=draft7_format_checker,
        )
        logging.info("Validating adf values")
        response = validate_adf_values(input_json)
        logging.info("Validation finished")
        if response['status'] == "REJECTED":
            return False, response['code'], response['message']
        return True, "input validated", "validation_ok"
    except Exception as e:
        logging.error(f"Validation failed: {e.message}")
        return False, "6_MISSING_FIELD", e.message
