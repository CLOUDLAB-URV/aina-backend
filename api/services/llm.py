from copy import deepcopy
from typing import Any

import ktem.db.models as _
from ktem.llms.manager import llms

from api.schemas.llms import LlmCreate, LlmInfo

_


class LlmService:
    def __init__(self):
        self.manager = llms

    def _process_vendor_info(self, info: dict[str, Any]) -> tuple[str, str]:
        """Extract and process vendor information from LLM info."""
        vendor_qualname = info["spec"].pop("__type__", "UnknownVendor")
        vendor_name = vendor_qualname.split(".")[-1]
        return vendor_name, vendor_qualname

    def _llm_exists(self, llm_name: str):
        if llm_name not in self.manager.info():
            raise LookupError(f"LLM '{llm_name}' not found")

    def _vendor_exists(self, vendor_name: str):
        if vendor_name not in self.manager.vendors():
            raise LookupError(f"Vendor '{vendor_name}' not found")

    def list_llms(self) -> dict[str, LlmInfo]:
        res = {}
        for name, info in self.manager.info().items():
            info = deepcopy(info)
            vendor_name, vendor_qualname = self._process_vendor_info(info)
            res[name] = LlmInfo(
                **info, vendor_name=vendor_name, vendor_qualname=vendor_qualname
            )
        return res

    def get_llm(self, llm_name: str) -> LlmInfo:
        self._llm_exists(llm_name)
        info = self.manager.info()[llm_name]
        info = deepcopy(info)
        vendor_name, vendor_qualname = self._process_vendor_info(info)
        return LlmInfo(**info, vendor_name=vendor_name, vendor_qualname=vendor_qualname)

    def delete_llm(self, llm_name: str):
        self._llm_exists(llm_name)
        self.manager.delete(llm_name)

    def update_llm(self, llm_name: str, spec: dict, default: bool = False):
        self._llm_exists(llm_name)
        llm = self.manager.info()[llm_name]
        spec["__type__"] = llm["spec"]["__type__"]
        self.manager.update(llm_name, spec, default)

    def add_llm(self, llm: LlmCreate):
        spec = llm.spec
        spec["__type__"] = self.get_vendor_qualname(llm.vendor_name)
        self.manager.add(llm.name, spec, llm.default)

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
