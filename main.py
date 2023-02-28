import logging
import os

import boto3
import certifi
from bson.json_util import dumps, loads
from fastapi import FastAPI, Depends, UploadFile, Form, HTTPException
from fastapi.security import HTTPBasicCredentials
from pymongo import MongoClient

from auth import auth
from controllers.release_controller import ReleaseController
from models import CreateReleaseDto
from utils.check_naming import check_format

app = FastAPI()

logging.basicConfig(level=logging.INFO)

db_url = os.getenv("DB_URL")
endpoint_url = os.getenv("AWS_ENDPOINT_URL")
public_url = os.getenv("PUBLIC_URL")
bucket_name = os.getenv("AWS_BUCKET_NAME")
region_name = os.getenv("AWS_REGION_NAME")
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

logging.info(f"DB_URL: {db_url}")
logging.info(f"AWS_ENDPOINT_URL: {endpoint_url}")
logging.info(f"PUBLIC_URL: {public_url}")
logging.info(f"AWS_BUCKET_NAME: {bucket_name}")
logging.info(f"AWS_REGION_NAME: {region_name}")
logging.info(f"AWS_ACCESS_KEY_ID: {aws_access_key_id}")
logging.info(f"AWS_SECRET_ACCESS_KEY: {aws_secret_access_key}")


mongo_client = MongoClient(db_url, tlsCAFile=certifi.where() if db_url.startswith("mongodb+srv") else None)
s3_client = boto3.client('s3',
                         aws_access_key_id=aws_access_key_id,
                         aws_secret_access_key=aws_secret_access_key,
                         region_name=region_name,
                         endpoint_url=endpoint_url,
                         )

# controller
release_controller = ReleaseController(client=mongo_client, s3_client=s3_client)


@app.post("/release")
async def create_release(name: str = Form(...),
                         version: str = Form(...),
                         files: list[UploadFile] = Form(...),
                         credentials: HTTPBasicCredentials = Depends(auth)):
    """
    Create a new release
    :return:
    """
    # check if name follows the format
    if not check_format(name):
        raise HTTPException(status_code=400, detail="Name must follow the format: [a-z0-9-]+")

    inserted_id = release_controller.post(release=CreateReleaseDto(name=name, version=version, files=files))
    return {"id": str(inserted_id)}


@app.get("/release")
async def list_releases(page: int = 1, per: int = 10):
    """
    Get a list of releases
    :param page: Current page, starting at 1
    :param per: Number of releases per page, starting at 10
    :return:
    """
    releases = release_controller.list(page=page, per=per)
    return releases


@app.get("/release/names")
async def list_release_names():
    """
    Get a list of release names
    :return:
    """
    names = release_controller.list_names()
    return names


@app.get("/release/versions/{name}")
async def list_release_versions(name: str) -> list[str]:
    """
    Get a list of release versions
    :return:
    """
    versions = release_controller.list_versions(name=name)
    return versions


@app.get("/release/{name}/{version}")
async def get_release_by_version(name: str, version: str):
    """
    Get list by version
    :return:
    """
    release = release_controller.get(version=version, name=name)
    return loads(dumps(release))


@app.delete("/release/{name}/{version}")
async def delete_release_by_version(name: str, version: str, credentials: HTTPBasicCredentials = Depends(auth)):
    """
    Delete a release by version
    :param version:
    :return:
    """
    release_controller.delete(version=version, name=name)
    return {"message": "Release deleted"}
