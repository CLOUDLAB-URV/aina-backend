from copy import deepcopy
from typing import Any

import ktem.db.models as _
from ktem.rerankings.manager import reranking_models_manager as rerankings

from api.schemas.rerankings import RerankingCreate, RerankingInfo

_


class RerankingService:
    def __init__(self):
        self.manager = rerankings

    def _process_vendor_info(self, info: dict[str, Any]) -> tuple[str, str]:
        vendor_qualname = info["spec"].pop("__type__", "UnknownVendor")
        vendor_name = vendor_qualname.split(".")[-1]
        return vendor_name, vendor_qualname

    def _reranking_exists(self, reranking_name: str):
        if reranking_name not in self.manager.info():
            raise LookupError(f"Reranking '{reranking_name}' not found")

    def _vendor_exists(self, vendor_name: str):
        if vendor_name not in self.manager.vendors():
            raise LookupError(f"Vendor '{vendor_name}' not found")

    def list_rerankings(self) -> dict[str, RerankingInfo]:
        res = {}
        for name, info in self.manager.info().items():
            info = deepcopy(info)
            vendor_name, vendor_qualname = self._process_vendor_info(info)
            res[name] = RerankingInfo(
                **info, vendor_name=vendor_name, vendor_qualname=vendor_qualname
            )
        return res

    def get_reranking(self, reranking_name: str) -> RerankingInfo:
        self._reranking_exists(reranking_name)
        info = self.manager.info()[reranking_name]
        info = deepcopy(info)
        vendor_name, vendor_qualname = self._process_vendor_info(info)
        return RerankingInfo(
            **info, vendor_name=vendor_name, vendor_qualname=vendor_qualname
        )

    def delete_reranking(self, reranking_name: str):
        self._reranking_exists(reranking_name)
        self.manager.delete(reranking_name)

    def update_reranking(
        self, reranking_name: str, spec: dict[str, Any], default: bool = False
    ):
        self._reranking_exists(reranking_name)
        reranking = self.manager.info()[reranking_name]
        spec["__type__"] = reranking["spec"]["__type__"]
        self.manager.update(reranking_name, spec, default)

    def add_reranking(self, reranking: RerankingCreate):
        spec = reranking.spec
        spec["__type__"] = self.get_vendor_qualname(reranking.vendor_name)
        self.manager.add(reranking.name, spec, reranking.default)

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
