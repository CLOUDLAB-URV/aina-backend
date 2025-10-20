from copy import deepcopy
from typing import Any

import ktem.db.models as _
from ktem.embeddings.manager import embedding_models_manager as embeddings

from api.schemas.embeddings import EmbeddingCreate, EmbeddingInfo

_


class EmbeddingService:
    def __init__(self):
        self.manager = embeddings

    def _process_vendor_info(self, info: dict[str, Any]) -> tuple[str, str]:
        vendor_qualname = info["spec"].pop("__type__", "UnknownVendor")
        vendor_name = vendor_qualname.split(".")[-1]
        return vendor_name, vendor_qualname

    def _embeddings_exists(self, embedding_name: str):
        if embedding_name not in self.manager.info():
            raise LookupError(f"Embedding model '{embedding_name}' not found")

    def _vendor_exists(self, vendor_name: str):
        if vendor_name not in self.manager.vendors():
            raise LookupError(f"Vendor '{vendor_name}' not found")

    def list_embeddings(self) -> dict[str, EmbeddingInfo]:
        res = {}
        for name, info in self.manager.info().items():
            info = deepcopy(info)
            vendor_name, vendor_qualname = self._process_vendor_info(info)
            res[name] = EmbeddingInfo(
                **info, vendor_name=vendor_name, vendor_qualname=vendor_qualname
            )
        return res

    def get_embedding(self, embedding_name: str) -> EmbeddingInfo:
        self._embeddings_exists(embedding_name)
        info = self.manager.info()[embedding_name]
        info = deepcopy(info)
        vendor_name, vendor_qualname = self._process_vendor_info(info)
        return EmbeddingInfo(
            **info, vendor_name=vendor_name, vendor_qualname=vendor_qualname
        )

    def delete_embedding(self, embedding_name: str):
        self._embeddings_exists(embedding_name)
        self.manager.delete(embedding_name)

    def update_embedding(
        self, embedding_name: str, spec: dict[str, Any], default: bool = False
    ):
        self._embeddings_exists(embedding_name)
        embedding = self.manager.info()[embedding_name]
        spec["__type__"] = embedding["spec"]["__type__"]
        self.manager.update(embedding_name, spec, default)

    def add_embedding(self, embedding: EmbeddingCreate):
        spec = embedding.spec
        spec["__type__"] = self.get_vendor_qualname(embedding.vendor_name)
        self.manager.add(embedding.name, spec, embedding.default)

    def list_vendors(self):
        return list(self.manager.vendors().keys())

    def get_vendor_desc(self, vendor_name: str):
        self._vendor_exists(vendor_name)
        return self.manager.vendors()[vendor_name].describe()

    def get_vendor_qualname(self, vendor_name: str):
        self._vendor_exists(vendor_name)
        return (
            self.manager.vendors()[vendor_name].__module__
            + "."
            + self.manager.vendors()[vendor_name].__qualname__
        )
