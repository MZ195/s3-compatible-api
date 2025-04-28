from MinIO import *
from base64 import b64decode

from fastapi import FastAPI, HTTPException, status
from fastapi import File, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dotenv import load_dotenv

import os

# Load environment variables from the .env file
load_dotenv()

s3 = MinIO(
  s3_access_key=os.environ['S3_ACCESS_KEY'],
  s3_access_secrect=os.environ['S3_SECRET_KEY'],
  s3_endpoint=os.environ['S3_ENDPOINT'],
  s3_bucket=os.environ['S3_BUCKET'],
)

origins = ["*"]
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/objects")
def get_objects_handler(prefix):
  prefix = b64decode(prefix).decode('utf-8')
  result, err = s3.get_bucket_objects(prefix)
  if result:
    return JSONResponse(content=result, status_code=status.HTTP_200_OK)
  raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=err,
    )

@app.get("/object_info")
def get_object_info_handler(path):
  path = b64decode(path).decode('utf-8')
  result, err = s3.get_object_info(path)
  if result:
    return JSONResponse(content=result, status_code=status.HTTP_200_OK)
  raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=err,
    )

@app.get("/object")
def get_object_handler(path):
  path = b64decode(path).decode('utf-8')
  file_name, file_content = s3.get_object(path)
  file_name = file_name.encode('latin-1').decode('latin-1')
  return Response(
    content = file_content,
    headers = {
      'Content-Disposition': 'attachment;filename={}'.format(file_name),
      'Content-Type': 'application/octet-stream',
      'Access-Control-Expose-Headers': 'Content-Disposition'
    }
  )

@app.delete("/object")
def delete_object_handler(path):
  path = b64decode(path).decode('utf-8')
  result, err = s3.delete_object(path)
  if result:
    return JSONResponse(content=result, status_code=status.HTTP_200_OK)
  raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=err,
    )

@app.post("/object")
def put_object_handler(path, file: UploadFile = File(...)):
  path = b64decode(path).decode('utf-8')
  file_name = file.filename
  result, err = s3.put_object('{}{}'.format(path, file_name), file.file.read())
  if result:
    return JSONResponse(content={"msg": "hey"}, status_code=status.HTTP_200_OK)
  raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=err,
    )
