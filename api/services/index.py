import shutil
import tempfile
from pathlib import Path

from fastapi import UploadFile
from ktem.index.base import BaseIndex
from ktem.index.file.index import FileIndex
from ktem.index.file.ui import FileIndexPage
from theflow.settings import settings as flowsettings

from api.app import app
from api.schemas.index import IndexInfo


class IndexService:
    def __init__(self):
        pass

    def _get(self, index: BaseIndex):
        return IndexInfo(
            id=index.id,
            name=index.name,
            index_type=index.__class__.__qualname__,
            config=index.config,
        )

    def list_indices(self):
        indices: list[BaseIndex] = app.index_manager.indices
        return [self._get(index) for index in indices]

    def get_index(self, index_id: int) -> IndexInfo:
        index = app.index_manager.info().get(index_id)
        if index is None:
            raise LookupError(f"Index with id {index_id} not found")
        return self._get(index)

    def delete_index(self, index_id: int):
        app.index_manager.delete_index(index_id)

    def create_index(self, name: str, config: dict, index_type: str) -> IndexInfo:
        index = app.index_manager.build_index(name, config, index_type)
        app.index_manager.start_index(index.id, name, config, index_type)
        return self._get(index)

    def list_files(self, user_id: str, index_id: int, name_pattern: str = ""):
        index = app.index_manager.info().get(index_id)
        if index is None:
            raise LookupError(f"Index with id {index_id} not found")
        if not isinstance(index, FileIndex):
            raise TypeError(f"Index with id {index_id} is not a FileIndex")
        return get_wrapper(index).list_file(user_id, name_pattern)

    def list_groups(self, user_id: str, index_id: int):
        index = app.index_manager.info().get(index_id)
        if index is None:
            raise LookupError(f"Index with id {index_id} not found")
        if not isinstance(index, FileIndex):
            raise TypeError(f"Index with id {index_id} is not a FileIndex")
        wrapper = get_wrapper(index)
        files, _ = wrapper.list_file(user_id)
        return wrapper.list_group(user_id, files)

    def index_files(
        self,
        user_id: str,
        index_id: int,
        files: list[UploadFile],
        reindex: bool = False,
    ):
        index = app.index_manager.info().get(index_id)
        if index is None:
            raise LookupError(f"Index with id {index_id} not found")
        if not isinstance(index, FileIndex):
            raise TypeError(f"Index with id {index_id} is not a FileIndex")

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
            settings={},
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
