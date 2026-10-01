import os
from abc import ABC, abstractmethod
from google.cloud import storage

class StorageService(ABC):
    @abstractmethod
    def read_file(self, path: str) -> bytes:
        pass
        
    @abstractmethod
    def write_file(self, path: str, data: bytes) -> None:
        pass

class LocalStorage(StorageService):
    def read_file(self, path: str) -> bytes:
        with open(path, "rb") as f:
            return f.read()
            
    def write_file(self, path: str, data: bytes) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

class GCSStorage(StorageService):
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        
    def read_file(self, path: str) -> bytes:
        blob = self.bucket.blob(path)
        return blob.download_as_bytes()
        
    def write_file(self, path: str, data: bytes) -> None:
        blob = self.bucket.blob(path)
        blob.upload_from_string(data)
