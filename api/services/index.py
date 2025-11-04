import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from ktem.db.engine import engine
from ktem.db.models import Agent
from ktem.index.base import BaseIndex
from ktem.index.file.index import FileIndex
from ktem.index.file.ui import FileIndexPage
from sqlalchemy import select
from sqlalchemy.orm import Session
from theflow.settings import settings as flowsettings
from theflow.utils.modules import import_dotted_string

from api.app import app
from api.core.utils import populate_agent_settings
from api.schemas.index import FileInfo, GroupInfo, IndexInfo


class IndexService:
    def __init__(self):
        pass

    def _get_info(self, index: BaseIndex):
        return IndexInfo(
            id=index.id,
            name=index.name,
            index_type=index.__class__.__qualname__,
            config=index.config,
        )

    def _get_qualname(self, index_type: str):
        for key in app.index_manager.index_types.keys():
            if key.split(".")[-1] == index_type:
                return key
        raise ValueError(f'Index type "{index_type}" not found')

    def _get_shortname(self, index_type: str):
        return index_type.split(".")[-1]

    def _get_index(self, index_id: int) -> BaseIndex:
        index = app.index_manager.info().get(index_id)
        if index is None:
            raise LookupError(f"Index with id {index_id} not found")
        return index

    def _get_file_index(self, index_id: int) -> FileIndex:
        index = self._get_index(index_id)
        if not isinstance(index, FileIndex):
            raise TypeError(f"Index with id {index_id} is not a FileIndex")
        return index

    def list_indices(self):
        indices: list[BaseIndex] = app.index_manager.indices
        return [self._get_info(index) for index in indices]

    def list_index_types(self):
        return [
            self._get_shortname(key) for key in app.index_manager.index_types.keys()
        ]

    def get_index(self, index_id: int) -> IndexInfo:
        index = self._get_index(index_id)
        return self._get_info(index)

    def delete_index(self, index_id: int):
        app.index_manager.delete_index(index_id)

    def create_index(
        self, name: str, index_type: str, config: dict[str, Any] | None = None
    ) -> IndexInfo:
        index_type = self._get_qualname(index_type)
        if config is None:
            config = {}
        index = app.index_manager.build_index(name, config, index_type)
        app.index_manager.start_index(index.id, name, index.config, index_type)
        return self._get_info(index)

    def update_index(
        self,
        index_id: int,
        name: str | None = None,
        config: dict[str, Any] | None = None,
    ):
        index: BaseIndex = self._get_index(index_id)
        new_name: str = index.name
        new_config: dict[str, Any] = index.config
        if name is not None:
            new_name = name
        if config is not None:
            new_config = config
        # update in db
        app.index_manager.update_index(index_id, new_name, new_config)
        # update in memory
        index.name = new_name
        index.config = new_config

    def list_files(self, user_id: str, index_id: int, name_pattern: str = ""):
        index = self._get_file_index(index_id)
        _, df = get_wrapper(index).list_file(user_id, name_pattern)
        records = df.to_dict(orient="records")
        file_infos = [FileInfo(**r) for r in records]
        return file_infos

    def list_groups(self, user_id: str, index_id: int):
        index = self._get_file_index(index_id)
        wrapper = get_wrapper(index)
        files, _ = wrapper.list_file(user_id)
        groups, _ = wrapper.list_group(user_id, files)
        return [GroupInfo(**r) for r in groups]

    def create_group(
        self, user_id: str, index_id: int, group_name: str, file_ids: list[str]
    ):
        index = self._get_file_index(index_id)
        FileGroup = index._resources["FileGroup"]
        with Session(engine) as session:
            current_group = (
                session.query(FileGroup)  # type: ignore
                .filter_by(user=user_id, name=group_name)
                .first()
            )
            if current_group:
                raise ValueError(f"Group with name '{group_name}' already exists")
            new_group = FileGroup(  # type: ignore
                name=group_name,
                data={"files": file_ids},
                user=user_id,
            )
            session.add(new_group)
            session.commit()

    def update_group(
        self,
        user_id: str,
        index_id: int,
        group_id: str,
        group_name: str | None,
        file_ids: list[str] | None,
    ):
        index = self._get_file_index(index_id)
        FileGroup = index._resources["FileGroup"]
        with Session(engine) as session:
            current_group = session.get(FileGroup, group_id)  # type: ignore
            if not current_group:
                raise LookupError(f"Group with id '{group_id}' not found")
            current_group.name = group_name or current_group.name
            if file_ids is not None:
                current_group.data = {"files": file_ids}
            session.add(current_group)
            session.commit()

    def delete_group(self, user_id: str, index_id: int, group_id: str):
        index = self._get_file_index(index_id)
        FileGroup = index._resources["FileGroup"]
        with Session(engine) as session:
            current_group = session.get(FileGroup, group_id)  # type: ignore
            if not current_group:
                raise LookupError(f"Group with id '{group_id}' not found")
            session.delete(current_group)
            session.commit()

    def get_admin_settings(self, index_type: str) -> dict[str, Any]:
        index_type = self._get_qualname(index_type)
        index_cls: type[BaseIndex] = import_dotted_string(index_type, safe=False)
        return index_cls.get_admin_settings()

    def get_index_settings(self, index_id: int) -> dict[str, Any]:
        index = self._get_index(index_id)
        return index.get_user_settings()

    def delete_file(self, user_id: str, index_id: int, file_id: str) -> str | None:
        idx = self._get_file_index(index_id)
        file_name = None
        with Session(engine) as session:
            source = session.execute(
                select(idx._resources["Source"]).where(  # type: ignore
                    idx._resources["Source"].id == file_id  # type: ignore
                )
            ).first()
            if source:
                file_name = source[0].name
                session.delete(source[0])

            vs_ids, ds_ids = [], []
            index = session.execute(
                select(idx._resources["Index"]).where(  # type: ignore
                    idx._resources["Index"].source_id == file_id  # type: ignore
                )
            ).all()
            for each in index:
                if each[0].relation_type == "vector":
                    vs_ids.append(each[0].target_id)
                elif each[0].relation_type == "document":
                    ds_ids.append(each[0].target_id)
                session.delete(each[0])
            session.commit()

        if vs_ids:
            idx._vs.delete(vs_ids)
        idx._docstore.delete(ds_ids)

        return file_name

    def delete_all_files(self, user_id: str, index_id: int):
        for file_info in self.list_files(user_id, index_id):
            self.delete_file(user_id, index_id, file_info.id)

    def index_files(
        self,
        user_id: str,
        agent_id: str,
        files: list[UploadFile],
        reindex: bool = False,
    ):
        with Session(engine) as session:
            agent = session.get(Agent, agent_id)
            if agent is None:
                raise LookupError(f"Agent with id {agent_id} not found")
            index_id = agent.index_id
            if index_id is None:
                raise LookupError(f"Agent with id {agent_id} has no index assigned")
        index = self._get_file_index(index_id)

        settings = populate_agent_settings(
            agent.settings or {}, index, agent.reasoning_id
        )

        wrapper = get_wrapper(index)

        upload_dir = tempfile.mkdtemp()
        file_paths = []
        for file in files:
            filename = file.filename
            if not filename:
                raise ValueError("Uploaded file must have a filename")
            with open(Path(upload_dir) / filename, "wb") as tmp:
                shutil.copyfileobj(file.file, tmp)
                file_paths.append(tmp.name)

        ret = yield from self._index_fn(
            ui=wrapper,
            index=index,
            files=file_paths,
            urls="",
            settings=settings,
            user_id=user_id,
            reindex=reindex,
        )

        try:
            shutil.rmtree(upload_dir)
        except Exception as e:
            print(f"Error removing temporary upload dir {upload_dir}: {e}")

        return ret

    def _index_fn(
        self,
        ui: FileIndexPage,
        index: FileIndex,
        files: list[str],
        urls: str,
        settings: dict,
        user_id: str,
        reindex: bool = False,
    ):
        if urls:
            files = [it.strip() for it in urls.split("\n")]
            errors = ui.validate_urls(files)
        else:
            if not files:
                raise ValueError("No files or URLs provided for indexing")
            files, unzip_errors = ui._may_extract_zip(
                files, flowsettings.KH_ZIP_INPUT_DIR
            )
            errors = ui.validate_files(files)
            errors.extend(unzip_errors)

        if errors:
            raise ValueError(f"Validation errors: {errors}")

        print(f"Indexing {len(files)} files...")

        # get the pipeline
        indexing_pipeline = index.get_indexing_pipeline(
            settings,
            user_id,  # type: ignore
        )

        outputs, debugs = [], []
        # stream the output
        output_stream = indexing_pipeline.stream(files, reindex=reindex)  # type: ignore
        try:
            while True:
                response = next(output_stream)
                if response is None:
                    continue
                if response.channel == "index":
                    if response.content["status"] == "success":
                        outputs.append(f"\u2705 | {response.content['file_name']}")
                    elif response.content["status"] == "failed":
                        outputs.append(
                            f"\u274c | {response.content['file_name']}: "
                            f"{response.content['message']}"
                        )
                elif response.channel == "debug":
                    debugs.append(response.text)
                yield "\n".join(outputs), "\n".join(debugs)
        except StopIteration as e:
            results, index_errors, docs = e.value
        except Exception as e:
            debugs.append(f"Error: {e}")
            yield "\n".join(outputs), "\n".join(debugs)
            return

        n_successes = len([_ for _ in results if _])
        if n_successes:
            print(f"Successfully index {n_successes} files")
        n_errors = len([_ for _ in errors if _])
        if n_errors:
            print(f"Have errors for {n_errors} files")

        return results


def get_wrapper(index: FileIndex) -> FileIndexPage:
    if not hasattr(index, "_index_ui_cls"):
        raise AttributeError(f"Index with id {index.id} has no _index_ui_cls attribute")
    if not issubclass(index._index_ui_cls, FileIndexPage):
        raise TypeError(
            f"_index_ui_cls of index with id {index.id} is not a FileIndexPage subclass"
        )

    class Wrapper(FileIndexPage):
        def __init__(self, index):
            self._index = index
            self._supported_file_types_str = self._index.config.get(
                "supported_file_types", ""
            )
            self._supported_file_types = [
                each.strip() for each in self._supported_file_types_str.split(",")
            ]

    wrapper = Wrapper(index)

    return wrapper
