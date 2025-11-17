from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Literal, Optional, Tuple, Type

import boto3
from botocore.exceptions import ClientError
from sqlalchemy import Table
from sqlalchemy.orm import DeclarativeBase
from sqlmodel import AutoString, SQLModel

AttributeType = Literal["S", "N", "B"]
TYPE_MAPPING: dict[Type[Any], AttributeType] = {
    str: "S",
    int: "N",
    float: "N",
    bytes: "B",
}


@dataclass
class TableSpec:
    table_name: str
    partition_key: str
    partition_key_type: Optional[AttributeType] = "S"
    sort_key: Optional[str] = None
    sort_key_type: Optional[AttributeType] = "S"


@dataclass
class TableCreateResult:
    created: bool
    error: Optional[str] = None


TableCreateResults = dict[str, TableCreateResult]


class DynamoDBTableManager:
    def __init__(self):
        self.session = boto3.Session()
        self.dynamodb = self.session.resource("dynamodb")
        self.client = self.session.client("dynamodb")

    def create_table_if_not_exists(
        self,
        table_name: str,
        partition_key: str,
        partition_key_type: Optional[AttributeType] = "S",
        sort_key: Optional[str] = None,
        sort_key_type: Optional[AttributeType] = "S",
        wait: bool = True,
    ) -> bool:
        """Create DynamoDB table with proper schema"""
        try:
            self.client.describe_table(TableName=table_name)
            print(f"DynamoDB table '{table_name}' already exists.")
            return False
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                key_schema = [{"AttributeName": partition_key, "KeyType": "HASH"}]
                attribute_definitions = [
                    {
                        "AttributeName": partition_key,
                        "AttributeType": partition_key_type,
                    }
                ]

                if sort_key:
                    key_schema.append({"AttributeName": sort_key, "KeyType": "RANGE"})
                    attribute_definitions.append(
                        {"AttributeName": sort_key, "AttributeType": sort_key_type}
                    )

                print(f"Creating DynamoDB table '{table_name}'...")
                table = self.dynamodb.create_table(
                    TableName=table_name,
                    KeySchema=key_schema,
                    AttributeDefinitions=attribute_definitions,
                    BillingMode="PAY_PER_REQUEST",
                )

                if wait:
                    table.wait_until_exists()
                return True
            else:
                raise

    def create_tables_if_not_exists(
        self, tables: list[TableSpec], wait: bool = True, max_workers: int = 5
    ) -> TableCreateResults:
        """Create multiple DynamoDB tables concurrently.

        Args:
            tables (list): List of dicts with keys: 'table_name', 'partition_key',
            optional 'sort_key'

            max_workers (int): Number of threads to use.

        Returns:
            dict: Mapping table_name -> { 'created': bool, 'error': str (optional) }
        """
        if not tables:
            return {}

        results: TableCreateResults = {}

        def _create_one(t: TableSpec) -> Tuple[Optional[str], TableCreateResult]:
            name = t.table_name
            try:
                partition_key = t.partition_key
                sort_key = t.sort_key
                created = self.create_table_if_not_exists(
                    table_name=name,
                    partition_key=partition_key,
                    partition_key_type=t.partition_key_type,
                    sort_key=sort_key,
                    sort_key_type=t.sort_key_type,
                    wait=wait,
                )
                return name, TableCreateResult(created=created)
            except Exception as e:
                return name, TableCreateResult(created=False, error=str(e))

        if wait:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_table = {executor.submit(_create_one, t): t for t in tables}
                for fut in as_completed(future_to_table):
                    name, res = fut.result()
                    key = name or f"<unknown-{id(fut)}>"
                    results[key] = res
        else:
            for t in tables:
                name, res = _create_one(t)
                key = name or f"<unknown-{id(t)}>"
                results[key] = res

        return results

    def create_table_from_sqlalchemy(
        self, model: type[DeclarativeBase | SQLModel], wait: bool = True
    ) -> TableCreateResult:
        """
        Given a SQLAlchemy or SQLModel table class, extract metadata
        and create DynamoDB table.
        """
        if not hasattr(model, "__table__"):
            raise ValueError(f"Object {model} does not have a __table__ attribute.")
        table: Table = getattr(model, "__table__")

        table_name = table.name

        pk_columns = table.primary_key.columns.items()
        if not pk_columns:
            raise ValueError(f"Table {table_name} has no primary key defined.")

        pk, pk_col = pk_columns[0]
        try:
            pk_type = pk_col.type.python_type
        except NotImplementedError:
            if isinstance(pk_col.type, AutoString):
                pk_type = str
            else:
                raise ValueError(
                    f"Cannot determine type of primary key column {pk} "
                    f"in table {table_name}"
                )

        sk, sk_col = pk_columns[1] if len(pk_columns) > 1 else (None, None)
        sk_type = None
        if sk is not None and sk_col is not None:
            try:
                sk_type = sk_col.type.python_type
            except NotImplementedError:
                if isinstance(sk_col.type, AutoString):
                    sk_type = str
                else:
                    raise ValueError(
                        f"Cannot determine type of sort key column {sk} "
                        f"in table {table_name}"
                    )

        try:
            created = self.create_table_if_not_exists(
                table_name=table_name,
                partition_key=pk,
                partition_key_type=TYPE_MAPPING.get(pk_type, None),
                sort_key=sk,
                sort_key_type=TYPE_MAPPING.get(sk_type, None) if sk_type else None,
                wait=wait,
            )
            return TableCreateResult(created=created)
        except Exception as e:
            return TableCreateResult(created=False, error=str(e))

    def create_tables_from_sqlalchemy(
        self,
        models: list[type[DeclarativeBase | SQLModel]],
        wait: bool = True,
        max_workers: int = 5,
    ) -> TableCreateResults:
        """
        Given a list of SQLAlchemy or SQLModel models,
        create corresponding DynamoDB tables.
        """
        table_specs: list[TableSpec] = []

        for model in models:
            if not hasattr(model, "__table__"):
                raise ValueError(f"Object {model} does not have a __table__ attribute.")
            table: Table = getattr(model, "__table__")

            pk_columns = [col.name for col in table.primary_key]
            if not pk_columns:
                raise ValueError(f"Table {table.name} has no primary key defined.")

            partition_key = pk_columns[0]
            sort_key = pk_columns[1] if len(pk_columns) > 1 else None

            i = TableSpec(
                table_name=table.name,
                partition_key=partition_key,
                sort_key=sort_key,
            )
            table_specs.append(i)

        return self.create_tables_if_not_exists(
            table_specs, wait=wait, max_workers=max_workers
        )

    def drop_table_if_exists(self, table_name: str, wait: bool = False) -> bool:
        """Delete DynamoDB table if it exists."""
        try:
            table = self.dynamodb.Table(table_name)
            table.delete()
            if wait:
                table.wait_until_not_exists()
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return False
            else:
                raise e

    def drop_tables_if_exists(
        self, table_names: list[str], wait: bool = False, max_workers: int = 5
    ) -> dict[str, bool]:
        """Delete multiple DynamoDB tables concurrently.

        Args:
            table_names (list): List of table names to delete.

            max_workers (int): Number of threads to use.

        Returns:
            dict: Mapping table_name -> bool (True if deleted, False if not found)
        """
        results: dict[str, bool] = {}

        def _delete_one(name: str) -> Tuple[str, bool]:
            try:
                deleted = self.drop_table_if_exists(name, wait=wait)
                return name, deleted
            except Exception:
                return name, False

        if wait:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_table = {
                    executor.submit(_delete_one, name): name for name in table_names
                }
                for fut in as_completed(future_to_table):
                    name, res = fut.result()
                    results[name] = res
        else:
            for name in table_names:
                name, res = _delete_one(name)
                results[name] = res

        return results

    def drop_table_from_sqlalchemy(
        self,
        model: type[DeclarativeBase | SQLModel],
        wait: bool = False,
    ) -> bool:
        """
        Given a SQLAlchemy or SQLModel model,
        delete the corresponding DynamoDB table.
        """
        if not hasattr(model, "__table__"):
            raise ValueError(f"Object {model} does not have a __table__ attribute.")
        table: Table = getattr(model, "__table__")
        return self.drop_table_if_exists(table.name, wait=wait)

    def drop_tables_from_sqlalchemy(
        self,
        models: list[type[DeclarativeBase | SQLModel]],
        wait: bool = False,
        max_workers: int = 5,
    ) -> dict[str, bool]:
        """
        Given a list of SQLAlchemy or SQLModel models,
        delete corresponding DynamoDB tables.
        """
        table_names: list[str] = []

        for model in models:
            if not hasattr(model, "__table__"):
                raise ValueError(f"Object {model} does not have a __table__ attribute.")
            table: Table = getattr(model, "__table__")
            table_names.append(table.name)

        return self.drop_tables_if_exists(
            table_names, wait=wait, max_workers=max_workers
        )
