from boto3 import resource
from pathlib import Path
from time import time
import json

# Helper function to convert bytes to a human-readable file size
def human_readable_size(bytes):
    # Define the suffixes for each size unit (e.g., KB, MB, GB, etc.)
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

    # If the size is zero, return '0 B'
    if bytes == 0:
        return "0 B"

    # Calculate the appropriate unit (e.g., KB, MB, etc.)
    i = 0
    while bytes >= 1024 and i < len(units) - 1:
        bytes /= 1024.0  # Divide by 1024 to convert to next unit
        i += 1
    
    # Return the size rounded to two decimal places with the corresponding unit
    return f"{bytes:.2f} {units[i]}"

# MinIO class for interacting with an S3-compatible object storage service
class MinIO():
    def __init__(self, s3_access_key, s3_access_secrect, s3_endpoint, s3_bucket):
        """
        Initializes the MinIO class with S3 connection parameters.

        :param s3_access_key: Access key for authentication with the S3 service.
        :param s3_access_secrect: Secret key for authentication with the S3 service.
        :param s3_endpoint: The S3 endpoint URL (e.g., MinIO or AWS S3 endpoint).
        :param s3_bucket: The name of the bucket to interact with.
        """
        self.s3 = self._get_s3_resource(s3_access_key, s3_access_secrect, s3_endpoint)
        self.bucket = s3_bucket
        self.cache = self.load_cache()  # Load the cache on initialization

    def _get_s3_resource(self, s3_access_key, s3_access_secrect, s3_endpoint):
        """
        Private method to set up the S3 resource using boto3.

        :param s3_access_key: The access key to authenticate.
        :param s3_access_secrect: The secret key to authenticate.
        :param s3_endpoint: The endpoint URL of the S3 service.
        :return: An S3 resource object.
        """
        s3 = resource(
            "s3",
            aws_access_key_id = s3_access_key,
            aws_secret_access_key = s3_access_secrect,
            endpoint_url = s3_endpoint,
        )
        return s3

    def calculate_folder_size(self, prefix, cache):
        """
        Recursively calculates the total size of a folder and its contents.

        :param prefix: The folder path in the S3 bucket.
        :param cache: A dictionary used to cache folder sizes.
        :return: The total size of the folder in bytes.
        """
        objs = self.s3.meta.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix, Delimiter='/')
        folders = objs.get('CommonPrefixes', None)
        files = objs.get('Contents', None)

        total_size = 0

        # Recursively calculate the size of any subfolders
        if folders:
            for folder in folders:
                folder_name = folder['Prefix'].replace(prefix, '')[:-1]
                total_size += self.calculate_folder_size("{}{}/".format(prefix, folder_name), cache)

        # Sum up the sizes of files in the folder
        if files:
            for file in files:
                total_size += file['Size']
  
        # Cache the calculated size for this folder
        cache[prefix] = total_size

        return total_size

    def load_cache(self):
        """
        Loads the cache from a local JSON file, if available, and checks if the cache is still valid.

        :return: The cache dictionary with folder sizes or a fresh cache if expired.
        """
        cache = {}
        my_file = Path("{}.json".format(self.bucket))  # Cache file named after the bucket
        if my_file.exists():
            with my_file.open() as read_file:
                cache = json.load(read_file)
                # Refresh the cache if it is older than 15 minutes (900 seconds)
                if cache['time'] < time() + 900:
                    cache = self.refresh_cache(cache)
        else:
            # No cache exists, so create a fresh one
            cache = self.refresh_cache(cache)
        return cache

    def get_buckets(self):
        """
        Fetches a list of all buckets available in the S3 service.

        :return: A list of bucket names.
        """
        buckets = []
        for bucket in self.s3.buckets.all():
            buckets.append(bucket.name)
        return buckets
    
    def create_bucket(self, bucket_name):
        """
        Creates a new S3 bucket.

        :param bucket_name: The name of the bucket to create.
        :return: True if the bucket is successfully created.
        """
        try:
            self.s3.create_bucket(Bucket=bucket_name)
        except Exception as e:
            print(e)
            exit(0)  # Exit if the bucket creation fails
        return True

    def delete_bucket(self, bucket_name):
        """
        Deletes an existing S3 bucket.

        :param bucket_name: The name of the bucket to delete.
        :return: True if the bucket is successfully deleted.
        """
        try:
            self.s3.Bucket(bucket_name).delete()
        except Exception as e:
            print(e)
            exit(0)  # Exit if the bucket deletion fails
        return True

    def get_bucket_objects(self, prefix=''):
        """
        Lists objects (files and folders) in the specified S3 bucket and prefix.

        :param prefix: The folder or prefix to filter objects by.
        :return: A dictionary containing 'folders' and 'files' information.
        """
        response = {}

        try:
            objs = self.s3.meta.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix, Delimiter='/')
            folders = objs.get('CommonPrefixes', None)
            files = objs.get('Contents', None)

            response['folders'] = []
            response['files'] = []
            response['prefix'] = objs.get('Prefix').split('/')[:-1]  # Extract prefix parts
            response['bucket'] = objs.get('Name')

            # Add folder details to the response
            if folders:
                for folder in folders:
                    folder_name = folder['Prefix'].replace(prefix, '')[:-1]
                    folder_size = self.cache.get(folder['Prefix'], 0)  # Get cached folder size
                    response['folders'].append({
                        "name": folder_name,
                        "path": folder['Prefix'],
                        "size": human_readable_size(folder_size),
                        "url": "?prefix={}".format(folder['Prefix'])
                    })
            
            # Add file details to the response
            if files:
                for file in files:
                    response['files'].append({
                        "key": file['Key'].replace(prefix, ''),
                        "last_modified": str(file['LastModified']),
                        "size": human_readable_size(file['Size']),
                        "path": file['Key']
                    })

        except Exception as e:
            print(e)
            return None, str(e)

        return response, None

    def get_object(self, path):
        """
        Fetches the content of an object (file) from the S3 bucket by its path.

        :param path: The key (path) of the object to fetch.
        :return: The name of the file and its content.
        """
        content_object = self.s3.Object(self.bucket, path)
        file_name = path.split('/')[-1]  # Extract the file name from the path
        file_content = content_object.get()['Body'].read()  # Read the content of the file
        return file_name, file_content

    def get_object_info(self, key):
        """
        Retrieves metadata of an object in the S3 bucket.

        :param key: The key (path) of the object to fetch metadata for.
        :return: A dictionary containing the metadata or an error message.
        """
        try:
            response = self.s3.meta.client.head_object(Bucket=self.bucket, Key=key)

            object_details = {
                'Size': human_readable_size(response['ContentLength']),
                'LastModified': str(response['LastModified']),
                'ContentType': response['ContentType'],
                'ETag': response['ETag'],
                'Metadata': response.get('Metadata', {})
            }

            return object_details, None
        except Exception as e:
            print(e)
            return None, e

    def delete_object(self, key):
        """
        Deletes an object from the S3 bucket by its key.

        :param key: The key (path) of the object to delete.
        :return: A message indicating success or failure.
        """
        try:
            response = self.s3.meta.client.delete_object(Bucket=self.bucket, Key=key)

            # Check if the deletion was successful (HTTPStatusCode 204)
            if response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 204:
                message = {"message": f"Object '{key}' deleted successfully from bucket '{self.bucket}'."}
            else:
                message = {"message": f"Failed to delete object '{key}' from bucket '{self.bucket}'."}

            return message, None
        except Exception as e:
            print(e)
            return None, f"Could not delete object '{key}' , {e}"

    def put_object(self, key, data):
        """
        Uploads a new object (file) to the S3 bucket.

        :param key: The key (path) where the object will be stored.
        :param data: The content of the object to upload.
        :return: A message indicating success or failure.
        """
        try:
            s3object = self.s3.Object(self.bucket, key)
            response = s3object.put(Body=(data))

            # Check for successful upload (HTTPStatusCode 200)
            if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                return {"message": f"Failed to add Object '{key}'."}
            return {"message": f"Object '{key}' was added successfully."}, None
        except Exception as e:
            print(e)
            return None, str(e)
        
    def refresh_cache(self, cache):
        """
        Refreshes the cache by recalculating the size of all folders in the S3 bucket.

        :param cache: The existing cache to be refreshed.
        :return: The updated cache dictionary.
        """
        objs = self.s3.meta.client.list_objects_v2(Bucket=self.bucket, Prefix='', Delimiter='/')
        folders = objs.get('CommonPrefixes', None)

        if folders:
            # Recalculate the size for each folder
            for folder in folders:
                folder_name = folder['Prefix']
                cache[folder_name] = self.calculate_folder_size(folder_name, cache)

        # Save the refreshed cache to a local file
        my_file = Path("{}.json".format(self.bucket))
        with my_file.open('w') as result_file:
            cache['time'] = time()  # Add the current timestamp
            json.dump(cache, result_file, indent=2, default=str)
        return cache
