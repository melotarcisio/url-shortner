"""
This is an old module I developed that is very useful, I use it to make small apps that don't require 
a lot of security, like this demo.

It's a simple ORM that has methods responsible for generating the main queries used in a Postgres DB.

To scale the project, I would implement something more robust like SQL Alchemy, which deals with possible 
security issues such as SQL injection and has a well-defined development pattern.
"""

from .utils import get_to_set, normalize
from typing import List, Dict, Optional, Any, Literal, Tuple

import psycopg2

from time import sleep
from datetime import datetime

from core.settings import settings


def connect(tentative: int = 10) -> psycopg2.extensions.connection:
    try:
        host = settings.POSTGRES_SERVER
        user = settings.POSTGRES_USER
        password = settings.POSTGRES_PASSWORD
        port = settings.DB_PORT
        dbname = settings.POSTGRES_DB
        conn_string = (
            f"host={host} user={user} dbname={dbname} password={password} port={port}"
        )
        return psycopg2.connect(conn_string)
    except Exception as e:
        if tentative > 0:
            sleep(3)
            return connect(tentative - 1)
        else:
            raise e


class Connection:
    def __init__(self):
        self.conn = connect()

    def _cursor(self, try_times=5) -> psycopg2.extensions.cursor:
        if self.is_alive():
            return self.conn.cursor()
        elif try_times > 0:
            self.reconnect()
            return self._cursor()
        raise ConnectionRefusedError("Error getting cursor, connection is dead")

    def is_alive(self) -> bool:
        try:
            self.conn.cursor().execute("select 1")
            return True
        except Exception:
            return False

    def reconnect(self) -> None:
        self.conn = connect()

    def execute(self, query: str, *params) -> Optional[List[Dict[str, Any]]]:
        try:
            result = ""
            cursor = self._cursor()
            cursor.execute(query, params)
            self._commit()
            try:
                result = cursor.fetchall()
            except Exception:
                result = None
            cursor.close()
            return result
        except Exception as e:
            self._rollback()
            raise e

    def execute_raw(self, query: str) -> Optional[List[Dict[str, Any]]]:
        try:
            result = ""
            cursor = self._cursor()
            cursor.execute(query)
            self._commit()
            try:
                result = cursor.fetchall()
            except Exception:
                result = None
            cursor.close()
            return result
        except Exception as e:
            self._rollback()
            raise e

    def close(self):
        self.conn.close()

    def insert_dict(
        self, table: str, data: Dict[str, str], key: str = None
    ) -> Optional[int]:
        try:
            cursor = self._cursor()
            to_return = None

            columns = '", "'.join(data.keys())
            values = ", ".join(normalize(data.values()))
            query = 'insert into {0} ("{1}") values ({2})'.format(
                table, columns, values
            )

            if key:
                query += f" returning {key}"
                cursor.execute(query)
                to_return = cursor.fetchone()[0]

            else:
                cursor.execute(query)

            self._commit()
            cursor.close()
            return to_return
        except Exception as e:
            self._rollback()
            raise e

    def insert_list(self, table: str, data: List[Dict[str, str]]) -> None:
        for item in data:
            self.insert_dict(table, item)

    def upsert(self, table: str, data: Dict[str, Any], primary_key: List[str]) -> None:
        try:
            cursor = self._cursor()
            columns = '", "'.join(data.keys())
            values = ", ".join(normalize(data.values()))
            to_set = get_to_set(data, primary_key)
            primary_key = '", "'.join(primary_key)
            query = """
                    insert into {0} ("{1}") values ({2}) on conflict ("{3}") do update set {4}
                """.format(
                table, columns, values, primary_key, to_set
            )
            cursor.execute(query)
            self._commit()
            cursor.close()
        except Exception as e:
            self._rollback()
            raise e

    def delete(self, table: str, data: Dict[str, Any] = {}) -> None:
        try:
            cursor = self._cursor()
            where = []
            for k, v in data.items():
                if isinstance(v, list):
                    where.append('"{0}" in ({1})'.format(k, ", ".join(normalize(v))))
                else:
                    where.append('"{0}" = {1}'.format(k, normalize([v])[0]))
            where = " and ".join(where)
            query = "delete from {0} where {1}".format(table, where)
            cursor.execute(query)
            self._commit()
            cursor.close()
        except Exception as e:
            self._rollback()
            raise e

    def update(
        self, table: str, data: Dict[str, Any], where_dict: Dict[str, Any]
    ) -> None:
        try:
            cursor = self._cursor()
            to_set = get_to_set(data)
            where = []
            for k, v in where_dict.items():
                if isinstance(v, list):
                    where.append('"{0}" in ({1})'.format(k, ", ".join(normalize(v))))
                else:
                    where.append('"{0}" = {1}'.format(k, normalize([v])[0]))
            where = " and ".join(where)
            query = "update {0} set {1} where {2}".format(table, to_set, where)
            cursor.execute(query)
            self._commit()
            cursor.close()
        except Exception as e:
            self._rollback()
            raise e

    def select_raw(self, query: str, *params) -> Optional[List[Dict[str, Any]]]:
        try:
            cursor = self._cursor()
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            # pylint: disable=C3001
            prevent_datetime = lambda arr: [
                x if not isinstance(x, datetime) else x.strftime("%Y-%m-%d %H:%M:%S")
                for x in arr
            ]
            result = [
                dict(zip(columns, prevent_datetime(row))) for row in cursor.fetchall()
            ]
            cursor.close()
            return result
        except Exception as e:
            self._rollback()
            raise e

    def select(
        self,
        table: str,
        where: dict = None,
        order_by: Optional[Tuple[str, Literal["asc", "desc"]]] = None,
        clause: Optional[Literal["and", "or"]] = "and",
    ) -> Optional[List[Dict[str, Any]]]:
        where_clause = self.get_where(where, clause=clause) if where else "1=1"
        query = (
            f"SELECT * FROM {table} WHERE {where_clause} {self.get_order_by(order_by)}"
        )
        return self.select_raw(query)

    def _commit(self) -> None:
        self.conn.commit()

    def _rollback(self) -> None:
        self.conn.rollback()

    @staticmethod
    def get_where(
        where_dict: Dict[str, str], clause: Literal["and", "or"] = "and"
    ) -> str:
        where = []
        for k, v in where_dict.items():
            if isinstance(v, list):
                where.append('"{0}" in ({1})'.format(k, ", ".join(normalize(v))))
            else:
                where.append('"{0}" = {1}'.format(k, normalize([v])[0]))
        where = f" {clause} ".join(where)
        return where

    @staticmethod
    def get_order_by(order_by: Optional[Tuple[str, Literal["asc", "desc"]]]) -> str:
        if not order_by:
            return ""

        return f'ORDER BY "{order_by[0]}" {order_by[1]}'
