# FastAPI S3-Compatible Object Storage API

This is a FastAPI-based application that provides an API for interacting with any S3-compatible object storage system (e.g., Amazon S3, MinIO, DigitalOcean Spaces, etc.). The API includes endpoints for uploading, retrieving, deleting, and listing objects in the S3-compatible storage. It supports operations like object retrieval, metadata inspection, and file uploads via HTTP requests.

## Features

- **Get List of Objects**: List objects stored in the S3-compatible bucket.
- **Get Object Info**: Retrieve metadata for a specific object in the bucket.
- **Download Object**: Download a specific object from the S3-compatible storage.
- **Delete Object**: Delete a specific object from the S3-compatible storage.
- **Upload Object**: Upload a file to a specific path in the S3-compatible storage.

## Prerequisites

To run this application, you'll need:

- Python 3.7 or higher.
- Access to an S3-compatible object storage service (e.g., AWS S3, MinIO, DigitalOcean Spaces, etc.).
- S3-compatible credentials (Access Key and Secret Key).
- Required Python dependencies (see below).

## Setup

### 1. Install Dependencies

Install the necessary dependencies by running:

```bash
pip install fastapi[all] boto3
```

`boto3` is the AWS SDK for Python and is compatible with any S3-compatible object storage system.

### 2. Configure Environment Variables

Set the following environment variables in the `.env` file to configure access to the S3-compatible storage:

- `S3_ACCESS_KEY`: The access key for your S3-compatible instance.
- `S3_SECRET_KEY`: The secret key for your S3-compatible instance.
- `S3_ENDPOINT`: The endpoint (URL) of your S3-compatible service.
- `S3_BUCKET`: The name of the bucket you want to interact with.

Example for setting environment variables in Linux/macOS:

```bash
export S3_ACCESS_KEY='your-access-key'
export S3_SECRET_KEY='your-secret-key'
export S3_ENDPOINT='http://localhost:9000'  # or the endpoint of your S3-compatible service
export S3_BUCKET='your-bucket-name'
```

On Windows, use the `set` command to define environment variables:

```cmd
set S3_ACCESS_KEY=your-access-key
set S3_SECRET_KEY=your-secret-key
set S3_ENDPOINT=http://localhost:9000
set S3_BUCKET=your-bucket-name
```

### 3. Source the Environment Variables
Once you configure the environment variables, run the following command to source them:

```bash
source .env
```

### 4. Run the Application

Once the environment variables are set, you can start the FastAPI application with Uvicorn:

```bash
uvicorn main:app --reload
```

This will run the API server locally on `http://127.0.0.1:8000`. You can now access the endpoints via this URL.

## Endpoints

### 1. `GET /objects`
**Description**: Retrieves a list of objects from the S3-compatible bucket.

- **Query Parameter**: 
  - `prefix` (required): Base64 encoded prefix to filter objects.
- **Response**: 
  - A JSON list of objects in the specified path.

Example:

```bash
GET /objects?prefix=<base64-encoded-prefix>
```

### 2. `GET /object_info`
**Description**: Retrieves metadata information about a specific object.

- **Query Parameter**:
  - `path` (required): Base64 encoded object path.
- **Response**: 
  - A JSON object with metadata for the requested object.

Example:

```bash
GET /object_info?path=<base64-encoded-path>
```

### 3. `GET /object`
**Description**: Downloads a specific object.

- **Query Parameter**:
  - `path` (required): Base64 encoded object path.
- **Response**: 
  - A binary file download (attachment).

Example:

```bash
GET /object?path=<base64-encoded-path>
```

### 4. `DELETE /object`
**Description**: Deletes a specific object from the bucket.

- **Query Parameter**:
  - `path` (required): Base64 encoded object path.
- **Response**: 
  - A JSON response indicating success or failure.

Example:

```bash
DELETE /object?path=<base64-encoded-path>
```

### 5. `POST /object`
**Description**: Uploads a file to a specific path in the S3-compatible bucket.

- **Query Parameter**:
  - `path` (required): Base64 encoded path where the file will be uploaded.
  - `file` (required): The file to upload.
- **Response**:
  - A JSON response indicating success or failure.

Example:

```bash
POST /object?path=<base64-encoded-path>
Content-Type: multipart/form-data
file=<file>
```

## Error Handling

The application will raise HTTP exceptions with appropriate status codes (500 Internal Server Error) if any operation fails while interacting with the S3-compatible storage. The error messages will be returned as JSON responses with details of the failure.

## CORS Support

The application has CORS (Cross-Origin Resource Sharing) enabled by default to allow all origins to interact with the API. You can modify the `origins` list in the `app.add_middleware` configuration to restrict allowed origins.

## Example Request

To upload a file to a path, use the following `curl` command:

```bash
curl -X 'POST' \
  'http://localhost:8000/object?path=cGF0aA==' \
  -F 'file=@/path/to/your/file.txt'
```

This command uploads a file to the base64 decoded path `path`.

## Notes

- All object paths and prefixes should be URL-encoded before base64 encoding to ensure they are correctly processed.
- The API assumes your S3-compatible instance is correctly configured and accessible. If there are issues with the S3 connection, the application will return HTTP 500 errors with the appropriate error details.

## Conclusion

This FastAPI application offers a simple and flexible way to interact with any S3-compatible object storage. You can list, retrieve, upload, and delete objects using a RESTful API, with support for CORS and error handling.