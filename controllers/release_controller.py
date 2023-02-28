import logging
import os
from os.path import join
from typing import List

from fastapi import HTTPException
from pydantic import HttpUrl
from pymongo import MongoClient

from controllers.controller import Controller
from models import Release, Pagination, CreateReleaseDto

bucket_name = os.getenv("AWS_BUCKET_NAME")
endpoint_url = os.getenv("AWS_ENDPOINT_URL")
public_url = os.getenv("PUBLIC_URL")


class ReleaseController(Controller):
    def __init__(self, client: MongoClient, s3_client):
        super().__init__(client=client)
        self.collection.create_index([("name", 1), ("version", 1)], unique=True)
        self.s3_client = s3_client

    def list(self, page: int, per: int) -> Pagination[Release]:
        """
        Get a list of releases
        :param page: Current page, starting at 1
        :param per: Number of releases per page, starting at 10
        :return:
        """
        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be greater than 0")

        if per < 1:
            raise HTTPException(status_code=400, detail="Per must be greater than 0")

        results = list(
            self.collection.find({}, {"_id": 0}).skip((page - 1) * per).limit(per).sort([("name", 1), ("version", -1)]))
        total = self.collection.count_documents({})
        total_pages = total // per + 1
        return Pagination(page=page, per=per, total=total, total_pages=total_pages, items=results)

    def list_names(self) -> List[str]:
        """
        Get a list of release names
        :return:
        """
        results = list(self.collection.distinct("name"))
        return results

    def list_versions(self, name: str) -> List[str]:
        """
        Get a list of release versions
        :return:
        """
        results = list(self.collection.distinct("version", {"name": name}))
        return results

    def post(self, release: CreateReleaseDto):
        """
        Create a new release
        :return:
        """
        # check if release already exists in s3 bucket, if so, raise error
        key = join(release.name, release.version)
        prev_release = self.collection.find_one({"name": release.name, "version": release.version}, {"_id": 0})
        if prev_release:
            raise HTTPException(status_code=400, detail="Release already exists")

        # upload files using s3
        urls: list[HttpUrl] = []
        for file in release.files:
            self.s3_client.upload_fileobj(file.file, bucket_name, join(key, file.filename))
            urls.append(f"{public_url}/{release.name}/{release.version}/{file.filename}")

        try:
            inserted_id = self.collection.insert_one(release.to_release(urls=urls).to_dict()).inserted_id
        except Exception as e:
            logging.error(e)
            raise HTTPException(status_code=400, detail="Cannot create release")
        return inserted_id

    def get(self, name: str, version: str) -> Release:
        """
        Get list by version and name
        :return:
        """
        release = self.collection.find_one({"version": version, "name": name}, {"_id": 0})
        if not release:
            raise HTTPException(status_code=404, detail="Release not found")
        return release

    def delete(self, name: str, version: str):
        """
        Delete a release by version and name
        :param name: name of release
        :param version: version of release
        :return:
        """
        # delete from db
        item = self.collection.find_one({"version": version, "name": name}, {"_id": 0})
        result = self.collection.delete_one({"version": version, "name": name})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Release not found")

        # delete files from s3
        for asset in item["assets"]:
            key = asset.replace(f"{public_url}/", "")
            logging.info(f"Deleting {key}")
            self.s3_client.delete_object(Bucket=bucket_name, Key=key)

        return result
