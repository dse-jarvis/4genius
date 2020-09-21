import http.client

import ssl
import json
from io import StringIO


"""
"
" The client interact with Waston Kownledge Catalog using Waston data API(beta)
" docu: https://cloud.ibm.com/apidocs/watson-data-api#introduction
" docu: https://developer.ibm.com/api/view/watsondata-prod:watson-data:title-Watson_Data_API#Introduction
" docu: https://tools.ietf.org/html/rfc6902
"
"""

class AnalyticsEngineClient():
    
    def __init__(self, host,instance_display_name=None, uid=None, pwd=None, token=None, verbose=True):
        """
        @param::token: authentication token in string
        @param::host: host url in string
        return catalog client instance
        """
        if host == None:
            raise Exception('The host url is required.') 
        
        if instance_display_name == None:
            raise Exception('Analytics Engine display name is required.') 
        else:
            self.instance_display_name = instance_display_name
            
        if uid == None and pwd==None and token==None:
            raise Exception('The uid/pwd and authentication token can not be empty at the same time.')
        
        self.host = host
        # retrieve auth token
        if token == None:
            self.__get_auth_token__(uid,pwd)
        else:
            self.token = token   
            
        if self.token != None:
            self.__get_jobs_auth_token__(self.token, self.instance_display_name)
        else:
            raise Exception('Something went wrong, during getting jobs auth token') 
        # debug info
        if verbose:
            print('Initialize Cloud Pak For Data: sucessfully!')


    """
    "
    " udpate feature following RFC6902
    " e.g. [{ "op": "replace", "path": "/dumps", "value": "foo" }]
    " replace the value of node specified by path "/dumps" to "foo"
    " docu: https://cloud.ibm.com/apidocs/watson-data-api#clone-an-asset
    " docu: https://tools.ietf.org/html/rfc6902
    "
    """
    def update_asset(self, asset_id, metadata):
        """
        @param string::asset_id: the asset id.
        @param string::metadata: the stringified json object
        return the updated metadata document of specified asset
        """
        if asset_id == None:
            raise Exception('The asset id is required.')
        if metadata == None:
            raise Exception('The metadata document is required.')
        
        method = '/v2/assets/%s?catalog_id=%s'%(asset_id,self.catalog_id)
        payloads = metadata
        response = self.__PATCH__(method, payloads)
        return self.__jsonify__(response)
    
    def delete_asset(self, asset_id):
        """
        @param string:asset_id: asset id
        return None
        """
        if asset_id == None:
            raise Exception('The asset id is required.')
        method = '/v2/assets/%s?catalog_id=%s'%(asset_id,self.catalog_id)
        response = self.__DELETE__(method)
        return response
    
    def create_asset_type(self, name, metadata):
        """
        @param string::name: the name of asset type
        @param string::metadata: the stringified json object
        return the metadata document of created asset
        """
        if metadata == None:
            raise Exception('The asset type metadata document is required.')
        if name == None:
            raise Exception('The asset type name is required.')
            
        method = '/v2/asset_types/%s?catalog_id=%s'%(name,self.catalog_id)
        payloads = metadata
        response = self.__PUT__(method, payloads)
        return self.__jsonify__(response)

    """
    "
    " get attachment of the asset in catalog. it takes 4 steps(api calls) to download the attachments
    " docu: https://cloud.ibm.com/apidocs/watson-data-api#get-asset
    "
    """
    def download_attachment(self, asset_id):
        """
        """
        if self.token == None:
            raise Exception('Authentication token is required.')
            
        url = self.__get_attachment_url__(asset_id)
        if url:
            conn = http.client.HTTPSConnection(
                  self.host,
                  context = ssl._create_unverified_context()
            )
            headers = {
                'authorization': 'Bearer %s'%(self.token),
                'cache-control': 'no-cache'
            }
            conn.request("GET", url, headers=headers)
            res = conn.getresponse()
            return res.read() 
    
    """
    "
    " the asset metadata document has three major section: metadata, enitity and attachment.
    " the attributes are under entity section and customizable.
    " docu: https://cloud.ibm.com/apidocs/watson-data-api#assets
    "
    """
    def get_attribute(self, asset_id, type_name='feature_asset'):
        """
        @param string::asset_id: asset id
        @param string::name: the name of asset type
        return the specified attribute value
        """
        if asset_id == None:
            raise Exception('the asset id is required.')
        method = '/v2/assets/%s/attributes/%s?catalog_id=%s'%(asset_id,type_name,self.catalog_id)
        response = self.__GET__(method)
        return self.__jsonify__(response)
    
    def get_all_instances(self):
        """
        return all the analytics instance details
        """
        method = '/zen-data/v2/serviceInstance?type=spark'
        response = self.__GET__(method)
        return self.__jsonify__(response)
    
    def get_all_volumes(self):
        """
        return all the analytics instance details
        """
        method = '/zen-data/v2/serviceInstance?type=volumes'
        response = self.__GET__(method)
        return self.__jsonify__(response)
    
    def get_instance_id(self, instance_display_name):
        """
        @param string::instance_display_name: display name on the AE instance
        returns instance id for the AE instance 
        """
        method = '/zen-data/v2/serviceInstance?type=spark'
        response = self.__GET__(method)
        response_dict = json.loads(response)
        id = None
        if len(response_dict["requestObj"]) == 0:
            return self.__jsonify__(json.dumps({"id":id}))
        else:
            for val in response_dict["requestObj"]:
                if val["ServiceInstanceDisplayName"] == instance_display_name:
                    id = val["ID"]
                    return self.__jsonify__(json.dumps({"id":id}))
    
        return self.__jsonify__(json.dumps({"id":id}))
    

    def get_instance_details(self, instance_display_name=None, instance_id=None ):
        """
        @param string::instance_display_name: display name on the AE instance
        returns instance id for the AE instance 
        """
        
        if instance_display_name == None and instance_id ==None:
            raise Exception("Both instance_display_name and instance_id can't be None")
        method = '/zen-data/v2/serviceInstance?type=spark'
        response = self.__GET__(method)
        response_dict = json.loads(response)
        result = {}
        if len(response_dict["requestObj"]) == 0:
            return self.__jsonify__(json.dumps(result))
        else:
            for val in response_dict["requestObj"]:
                if val["ServiceInstanceDisplayName"] == instance_display_name or val["ID"] == instance_id:
                    result = val
                    return self.__jsonify__(json.dumps(result))
        return self.__jsonify__(json.dumps(result))
    
#     'Spark jobs endpoint': '$HOST/ae/spark/v2/1386d43d77d84ec9ab513ef31ec2e6c3/v2/jobs',
#      'View history server': '$HOST/ae/spark/v2/1386d43d77d84ec9ab513ef31ec2e6c3/historyui/'},
#     def get_spark_job_endpoint(self, instance_display_name):
        
    
    def update_attribute(self, asset_id, ops, type_name='feature_asset'):
        """
        @param string::asset_id: asset id
        @param string::ops: the stringified json object based on RFC6902
        @param string::name: the name of feature type
        return the updated attributes
        """
        if asset_id == None:
            raise Exception('The asset id is required.')
        if ops == None:
            raise Exception('The patch operation data is required.')
            
        method = '/v2/assets/%s/attributes/%s?catalog_id=%s'%(asset_id, type_name, self.catalog_id)
        payloads = ops
        response = self.__PATCH__(method, payloads)
        return self.__jsonify__(response)
    
    """
    "
    " get the attachment url of given asset
    " docu: https://cloud.ibm.com/apidocs/watson-data-api#get-asset
    " docu: https://cloud.ibm.com/apidocs/watson-data-api#get-an-attachment
    "
    """
    def __get_attachment_url__(self, asset_id):
        """
        @param string::asset_id: asset id
        return the attachment download url
        """
        if asset_id == None:
            raise Exception('the asset id is required.')
        
        # get asset metadata
        metadata = self.__get_asset_metadata__(asset_id)
        attachment_id = None
        if 'attachments' in metadata:
            for m in metadata['attachments']:
                if m['asset_type'] == 'data_asset':
                    attachment_id = m['id']
                    break
        # get attachment id
        if attachment_id == None:
            return None
        else:
            method = '/v2/assets/%s/attachments/%s?catalog_id=%s'%(asset_id,attachment_id,self.catalog_id)
            data = self.__GET__(method)
            return self.__jsonify__(data)['url']
            
    """
    "
    " get the metadata of a asset
    " docu: https://cloud.ibm.com/apidocs/watson-data-api#get-an-asset
    "
    """ 
    def __get_asset_metadata__(self, asset_id):
        """
        @param string::asset_id: the asset id
        return the asset major metadata document
        """
        if asset_id == None:
            raise Exception('the asset id is required.')
            
        method = '/v2/assets/%s?catalog_id=%s'%(asset_id,self.catalog_id)
        data = self.__GET__(method)
        return self.__jsonify__(data)
    
    """
    "
    " authenicate user by username and password and get the authentication token 
    " docu: https://cloud.ibm.com/apidocs/watson-data-api#creating-an-iam-bearer-token
    "
    """
    def __get_auth_token__(self, uid, pwd, verbose=False):
        """
        @param::uid: username
        @param::pwd: password
        return authentication token
        """
        if uid == None or pwd == None:
            raise Exception('the username and password are both required.')
        
        
        conn = http.client.HTTPSConnection(
              self.host,
              context = ssl._create_unverified_context()
        )
        
        headers = {
            'content-type': "application/json",
            'cache-control': "no-cache",
            'password':pwd,
            'username':uid
        }
        method = '/v1/preauth/validateAuth'
        conn.request("GET", method, headers=headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        self.token = self.__jsonify__(data)['accessToken']
        return self.token
    
    def __get_jobs_auth_token__(self, token, display_name, verbose=False):
        """
        @param::token: token
        @param::AE instance display name: display_name
        return jobs authentication token
        """
        if token == None:
            raise Exception('Platform token is required.')
        
        
        conn = http.client.HTTPSConnection(
              self.host,
              context = ssl._create_unverified_context()
        )
        
        headers = {
            'content-type': "application/json",
            'cache-control': "no-cache",
            'Authorization': 'Bearer {}'.format(token)
        }
        payload = json.dumps({"serviceInstanceDisplayname": display_name})
        
        method = "/zen-data/v2/serviceInstance/token"
        conn.request("POST", method, headers=headers, body= payload)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        self.job_token = self.__jsonify__(data)['AccessToken']
        return self.job_token
            
        
    
    def __GET__(self, method, headers=None):
        """
        @param string:: method: the API method
        @param dict:: header: the http GET request header
        return the response data
        """
        if self.token == None:
            raise Exception('Authentication token is required.')
            
        if method == None:
            raise Exception('The API method is required.')
            
        conn = http.client.HTTPSConnection(
              self.host,
              context = ssl._create_unverified_context()
        )
        
        if headers == None:
            headers = {
                'authorization': 'Bearer %s'%(self.token),
                'cache-control': 'no-cache',
                'accept': 'application/json',
                'content-type': 'application/json'
            }
        
        
        conn.request("GET", method, headers=headers)
        res = conn.getresponse()
        return res.read().decode("utf-8")
    
    def __DELETE__(self, method, headers=None):
        """
        @param string:: method: the API method
        @param dict:: header: the http GET request header
        return the response data
        """
        if self.token == None:
            raise Exception('Authentication token is required.')
            
        if method == None:
            raise Exception('The API method is required.')
            
        conn = http.client.HTTPSConnection(
              self.host,
              context = ssl._create_unverified_context()
        )
        
        if headers == None:
            headers = {
                'authorization': 'Bearer %s'%(self.token),
                'cache-control': 'no-cache',
                'accept': 'application/json',
                'content-type': 'application/json'
            }
        
        
        conn.request("DELETE", method, headers=headers)
        res = conn.getresponse()
        return res.read().decode("utf-8")
    
    def __POST__(self, method, payloads=None, headers=None):
        """
        @param string:: method: the method API
        @param dict:: payloads: the payload of POST request
        @param dict:: headers: the header of POST request
        @return string:: the decoded response content
        """
        
        if self.token == None:
            raise Exception('Authentication token is required.')
            
        if method == None:
            raise Exception('The API method is required.')
            
        conn = http.client.HTTPSConnection(
              self.host,
              context = ssl._create_unverified_context()
        )
        
        if headers == None:
            headers = {
                'authorization': 'Bearer %s'%(self.token),
                'cache-control': "no-cache",
                'accept': 'application/json',
                'content-type': 'application/json'
                }
            
        conn.request("POST", method, payloads, headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        return data
    
    def __PUT__(self, method, payloads=None, headers=None):
        """
        @param string:: method: the method API
        @param dict:: payloads: the payload of POST request
        @param dict:: headers: the header of POST request
        @return string:: the decoded response content
        """
        
        if self.token == None:
            raise Exception('Authentication token is required.')
            
        if method == None:
            raise Exception('The API method is required.')
            
        conn = http.client.HTTPSConnection(
              self.host,
              context = ssl._create_unverified_context()
        )
        
        if headers == None:
            headers = {
                'authorization': 'Bearer %s'%(self.token),
                'cache-control': "no-cache",
                'accept': 'application/json',
                'content-type': 'application/json'
                }
            
        conn.request("PUT", method, payloads, headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        return data
    
    def __PATCH__(self, method, payloads=None, headers=None):
        """
        @param string:: method: the method API
        @param dict:: payloads: the payload of POST request
        @param dict:: headers: the header of POST request
        @return string:: the decoded response content
        """
        
        if self.token == None:
            raise Exception('Authentication token is required.')
            
        if method == None:
            raise Exception('The API method is required.')
            
        conn = http.client.HTTPSConnection(
              self.host,
              context = ssl._create_unverified_context()
        )
        
        if headers == None:
            headers = {
                'authorization': 'Bearer %s'%(self.token),
                'cache-control': "no-cache",
                'accept': 'application/json',
                'content-type': 'application/json'
                }
            
        conn.request("PATCH", method, payloads, headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        return data
        
    
    def __jsonify__(self, dumps):
        """
        @param::dumps: json dumps in string
        return json object
        """
        dumps_io = StringIO(dumps)
        return json.load(dumps_io)
        


#         ┌─┐       ┌─┐
#      ┌──┘ ┴───────┘ ┴──┐
#      │                 │
#      │       ───       │
#      │  ─┬┘       └┬─  │
#      │                 │
#      │       ─┴─       │
#      │                 │
#      └───┐         ┌───┘
#          │         │
#          │         │
#          │         │
#          │         └──────────────┐
#          │                        │
#          │                        ├─┐
#          │                        ┌─┘
#          │                        │
#          └─┐  ┐  ┌───────┬──┐  ┌──┘
#            │ ─┤ ─┤       │ ─┤ ─┤
#            └──┴──┘       └──┴──┘
#                 BLESSING FROM 
#           THE BUG-FREE MIGHTY BEAST