import uuid
import logging
import time
import boto3
import botocore
from boto3.dynamodb.conditions import Key
import dynamodbgeo
from datetime import datetime, timedelta

from fast_api_als import constants
from fast_api_als.utils.boto3_utils import get_boto3_session
"""
    the self.table.some_operation(), return a json object and you can find the http code of the executed operation as this :
    res['ResponseMetadata']['HTTPStatusCode']
    
    write a commong function that logs this response code with appropriate context data
"""

logging.basicConfig(filename="applicationLogs.txt", filemode='w',level=logging.DEBUG,  format = '%(asctime)s %(levelname)s: %(message)s',)

def dbOperationsLogger(response, dbOperation):
    respCode = response.get('ResponseMetadata').get('HTTPStatusCode')
    if(respCode>=200 and respCode<300):
        logging.info("Response status code received: {0} for operation: {1}".format(respCode, dbOperation))
    else:
        errorCode = response.get("Error").get("Code")
        logging.error("Error Code: {2}, Response status code received: {0} for operation: {1}".format(respCode, dbOperation, errorCode))



class DBHelper:
    def __init__(self, session: boto3.session.Session):
        self.session = session
        self.ddb_resource = session.resource('dynamodb', config=botocore.client.Config(max_pool_connections=99))
        self.table = self.ddb_resource.Table(constants.DB_TABLE_NAME)
        self.geo_data_manager = self.get_geo_data_manager()
        self.dealer_table = self.ddb_resource.Table(constants.DEALER_DB_TABLE)
        self.get_api_key_author("Initialize_Connection")

    def get_geo_data_manager(self):
        try:
            config = dynamodbgeo.GeoDataManagerConfiguration(self.session.client('dynamodb', config=botocore.client.Config(max_pool_connections=99)), constants.DEALER_DB_TABLE)
            geo_data_manager = dynamodbgeo.GeoDataManager(config)
            return geo_data_manager
        except Exception as e:
            logging.error("Error getting geo data manager, error log: {0}".format(e))
            return None

    def insert_lead(self, lead_hash: str, lead_provider: str, response: str):
        item = {
            'pk': f'LEAD#{lead_hash}',
            'sk': lead_provider,
            'response': response,
            'ttl': datetime.fromtimestamp(int(time.time())) + timedelta(days=constants.LEAD_ITEM_TTL)
        }

        try:
            res = self.table.put_item(Item=item)
            dbOperationsLogger(res, "Inserting lead")
        except Exception as e:
            dbOperationsLogger(e, "Inserting lead")

    def insert_oem_lead(self, uuid: str, make: str, model: str, date: str, email: str, phone: str, last_name: str,
                        timestamp: str, make_model_filter_status: str, lead_hash: str, dealer: str, provider: str,
                        postalcode: str):

        item = {
            'pk': f"{make}#{uuid}",
            'sk': f"{make}#{model}",
            'gsipk': f"{make}#{date}",
            'gsisk': "0#0",
            'make': make,
            'model': model,
            'email': email,
            'phone': phone,
            'last_name': last_name,
            'timestamp': timestamp,
            'conversion': "0",
            "make_model_filter_status": make_model_filter_status,
            "lead_hash": lead_hash,
            "dealer": dealer,
            "3pl": provider,
            "postalcode": postalcode,
            'ttl': datetime.fromtimestamp(int(time.time())) + timedelta(days=constants.OEM_ITEM_TTL)
        }
        try:
            res = self.table.put_item(Item=item)
            dbOperationsLogger(res,"Inserting oem lead")
        except Exception as e:
            dbOperationsLogger(e, "Inserting oem lead")


    def check_duplicate_api_call(self, lead_hash: str, lead_provider: str):
        
        try:
            res = self.table.get_item(
                Key={
                    'pk': f"LEAD#{lead_hash}",
                    'sk': lead_provider
                }
            )
            dbOperationsLogger(res, "Checking for duplicate api call")
            item = res.get('Item')
            if not item:
                return {
                    "Duplicate_Api_Call": {
                        "status": False,
                        "response": "No_Duplicate_Api_Call"
                    }
                }
            else:
                return {
                    "Duplicate_Api_Call": {
                        "status": True,
                        "response": item['response']
                    }
                }
        except botocore.exceptions.ClientError as e:
            dbOperationsLogger(e, "Checking for duplicate api call")
            return None
        except Exception as e:
            logging.error("Error occurred while checking for duplicate api call, error: {0}".format(e))
            return None

    def accepted_lead_not_sent_for_oem(self, oem: str, date: str):
        try:
            res = self.table.query(
                IndexName='gsi-index',
                KeyConditionExpression=Key('gsipk').eq(f"{oem}#{date}")
                                    & Key('gsisk').begins_with("0#0")
            )
            dbOperationsLogger(res, "Accepted lead not sent for oem")
            return res.get('Items', [])
        except Exception as e:
            dbOperationsLogger(e, "Accepted lead not sent for oem")
            return []

    def update_lead_sent_status(self, uuid: str, oem: str, make: str, model: str):
        try:
            res = self.table.get_item(
                Key={
                    'pk': f"{uuid}#{oem}"
                }
            )
            item = res['Item']
            if not item:
                return False
            item['gsisk'] = "1#0"
        except botocore.exceptions.ClientError as e:
            dbOperationsLogger(e, "Get item for update lead sent status")
            return False
        try:
            res = self.table.put_item(Item=item)
            return True
        except botocore.exceptions.ClientError as e:
            dbOperationsLogger(e, "Put item for update lead sent status")
            return False

    def get_make_model_filter_status(self, oem: str):
        try:
            res = self.table.get_item(
                Key={
                    'pk': f"OEM#{oem}",
                    'sk': 'METADATA'
                }
            )
            dbOperationsLogger(res,"Get make model filter status")
            if res['Item'].get('settings', {}).get('make_model', "False") == 'True':
                return True
            return False

        except Exception as e:
            dbOperationsLogger(e, "Get make model filter status")
            return False

    def verify_api_key(self, apikey: str):
        try:
            res = self.table.query(
                IndexName='gsi-index',
                KeyConditionExpression=Key('gsipk').eq(apikey)
            )
            dbOperationsLogger(res, "Verify api key")
            item = res.get('Items', [])
            if len(item) == 0:
                return False
            return True
        except Exception as e:
            dbOperationsLogger(e, "Verfiy api key")
            return False

    def get_auth_key(self, username: str):
        try:
            res = self.table.query(
                KeyConditionExpression=Key('pk').eq(username)
            )
            dbOperationsLogger(res, "Get auth key")
            item = res['Items']
            if len(item) == 0:
                return None
            return item[0]['sk']
        except Exception as e:
            dbOperationsLogger(e, "get auth key")
            return None

    def set_auth_key(self, username: str):

        try:
            self.delete_3PL(username)
            apikey = str(uuid.uuid4())
            res = self.table.put_item(
                Item={
                    'pk': username,
                    'sk': apikey,
                    'gsipk': apikey
                }
            )
            dbOperationsLogger(res, "set auth key")
            return apikey
        except Exception as e:
            dbOperationsLogger(e, "set auth key") 
            return None

    def register_3PL(self, username: str):
        try:
            res = self.table.query(
                KeyConditionExpression=Key('pk').eq(username)
            )
            item = res.get('Items', [])
            if len(item):
                return None
            return self.set_auth_key(username)
        except Exception as e:
            dbOperationsLogger(e, " register_3PL")
            return None

    def set_make_model_oem(self, oem: str, make_model: str):

        try:
            item = self.fetch_oem_data(oem)
            item['settings']['make_model'] = make_model
            res = self.table.put_item(Item=item)
            dbOperationsLogger(res, "set make model oem")
        except Exception as e:
            dbOperationsLogger(e, "set make model oem")

    def fetch_oem_data(self, oem, parallel=False):
        try:
            res = self.table.get_item(
                Key={
                    'pk': f"OEM#{oem}",
                    'sk': "METADATA"
                }
            )
            dbOperationsLogger(res, "fetch oem data")
            if 'Item' not in res:
                return {}
            if parallel:
                return {
                    "fetch_oem_data": res['Item']
                }
            else:
                return res['Item']
        except Exception as e:
            dbOperationsLogger(e, "fetch oem data")
            return None

    def create_new_oem(self, oem: str, make_model: str, threshold: str):
        try:
            res = self.table.put_item(
                Item={
                    'pk': f"OEM#{oem}",
                    'sk': "METADATA",
                    'settings': {
                        'make_model': make_model
                    },
                    'threshold': threshold
                }
            )
            dbOperationsLogger(res, "create new oem")
        except Exception as e:
            dbOperationsLogger(e, "create new oem")

    def delete_oem(self, oem: str):
        try:
            res = self.table.delete_item(
                Key={
                    'pk': f"OEM#{oem}",
                    'sk': "METADATA"
                }
            )
            dbOperationsLogger(res, "delete oem")
        except Exception as e:
            dbOperationsLogger(e, "delete oem")

    def delete_3PL(self, username: str):
        authkey = self.get_auth_key(username)
        if authkey:
            res = self.table.delete_item(
                Key={
                    'pk': username,
                    'sk': authkey
                }
            )
            dbOperationsLogger(res, "delete 3PL")

    def set_oem_threshold(self, oem: str, threshold: str):
        item = self.fetch_oem_data(oem)
        if item == {}:
            return {
                "error": f"OEM {oem} not found"
            }
        item['threshold'] = threshold
        res = self.table.put_item(Item=item)
        dbOperationsLogger(res, "set oem threshold")
        return {
            "success": f"OEM {oem} threshold set to {threshold}"
        }

    def fetch_nearest_dealer(self, oem: str, lat: str, lon: str):
        query_input = {
            "FilterExpression": "oem = :val1",
            "ExpressionAttributeValues": {
                ":val1": {"S": oem},
            }
        }
        logging.info("Fetching nearest dealer")
        res = self.geo_data_manager.queryRadius(
            dynamodbgeo.QueryRadiusRequest(
                dynamodbgeo.GeoPoint(lat, lon),
                50000,  # radius = 50km
                query_input,
                sort=True
            )
        )
        if len(res) == 0:
            return {}
        res = res[0]
        dealer = {
            'id': {
                '#text': res['dealerCode']['S']
            },
            'vendorname': res['dealerName']['S'],
            'contact': {
                'address': {
                    'postalcode': res['dealerZip']['S']
                }
            }
        }
        return dealer

    def get_dealer_data(self, dealer_code: str, oem: str):
        if not dealer_code:
            return {}
        res = self.dealer_table.query(
            IndexName='dealercode-index',
            KeyConditionExpression=Key('dealerCode').eq(dealer_code) & Key('oem').eq(oem)
        )
        dbOperationsLogger(res, "Get dealer data")
        res = res['Items']
        if len(res) == 0:
            return {}
        res = res[0]
        return {
            'postalcode': res['dealerZip'],
            'rating': res['Rating'],
            'recommended': res['Recommended'],
            'reviews': res['LifeTimeReviews']
        }

    def insert_customer_lead(self, uuid: str, email: str, phone: str, last_name: str, make: str, model: str):
        item = {
            'pk': uuid,
            'sk': 'CUSTOMER_LEAD',
            'gsipk': email,
            'gsisk': uuid,
            'gsipk1': f"{phone}#{last_name}",
            'gsisk1': uuid,
            'oem': make,
            'make': make,
            'model': model,
            'ttl': datetime.fromtimestamp(int(time.time())) + timedelta(days=constants.OEM_ITEM_TTL)
        }
        res = self.table.put_item(Item=item)
        dbOperationsLogger(res, "insert customer lead")

    def lead_exists(self, uuid: str, make: str, model: str):
        lead_exist = False
        if self.get_make_model_filter_status(make):
            res = self.table.query(
                KeyConditionExpression=Key('pk').eq(f"{make}#{uuid}") & Key('sk').eq(f"{make}#{model}")
            )
            dbOperationsLogger(res, "lead exists, get make model filter status")
            if len(res['Items']):
                lead_exist = True
        else:
            res = self.table.query(
                KeyConditionExpression=Key('pk').eq(f"{make}#{uuid}")
            )
            dbOperationsLogger(res, "lead exists")
            if len(res['Items']):
                lead_exist = True
        return lead_exist

    def check_duplicate_lead(self, email: str, phone: str, last_name: str, make: str, model: str):
        logging.info("Checking for duplicate lead")
        email_attached_leads = self.table.query(
            IndexName='gsi-index',
            KeyConditionExpression=Key('gsipk').eq(email)
        )
        dbOperationsLogger(email_attached_leads, "email attached leads")
        phone_attached_leads = self.table.query(
            IndexName='gsi1-index',
            KeyConditionExpression=Key('gsipk1').eq(f"{phone}#{last_name}")
        )
        dbOperationsLogger(phone_attached_leads, "phone attached leads")
        customer_leads = email_attached_leads['Items'] + phone_attached_leads['Items']

        for item in customer_leads:
            if self.lead_exists(item['pk'], make, model):
                return {"Duplicate_Lead": True}
        return {"Duplicate_Lead": False}

    def get_api_key_author(self, apikey):
        res = self.table.query(
            IndexName='gsi-index',
            KeyConditionExpression=Key('gsipk').eq(apikey)
        )
        dbOperationsLogger(res, "get api key author")
        item = res.get('Items', [])
        if len(item) == 0:
            return "unknown"
        return item[0].get("pk", "unknown")

    def update_lead_conversion(self, lead_uuid: str, oem: str, converted: int):
        res = self.table.query(
            KeyConditionExpression=Key('pk').eq(f"{oem}#{lead_uuid}")
        )
        dbOperationsLogger(res, "get lead from uuid")
        items = res.get('Items')
        if len(items) == 0:
            return False, {}
        item = items[0]
        item['oem_responded'] = 1
        item['conversion'] = converted
        item['gsisk'] = f"1#{converted}"
        res = self.table.put_item(Item=item)
        dbOperationsLogger(res, "update lead conversion")
        return True, item


def verify_response(response_code):
    if not response_code == 200:
        pass
    else:
        pass


session = get_boto3_session()
db_helper_session = DBHelper(session)
