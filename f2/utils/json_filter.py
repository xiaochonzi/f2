# path: f2/utils/json_filter.py

import json

from typing import Any
from jsonpath_ng import parse


class JSONModel:

    def __init__(self, data: Any):
        self._data = data
        self._cache = {}  # 缓存解析后的 JSONPath 表达式

    def _parse_expression(self, jsonpath_expr: str):
        """
        缓存 JSONPath 表达式解析器，避免重复解析。

        Args:
            jsonpath_expr: str: JSONPath 表达式

        Returns:
            jsonpath_ng.jsonpath.JsonPath: JSONPath 表达式解析器
        """
        if jsonpath_expr not in self._cache:
            self._cache[jsonpath_expr] = parse(jsonpath_expr)
        return self._cache[jsonpath_expr]

    def _get_attr_value(self, jsonpath_expr: str):
        """
        根据 JSONPath 表达式获取单一属性值。

        Args:
            jsonpath_expr: str: JSONPath 表达式

        Returns:
            Union[str, int, float, bool]: 属性值
        """
        expr = self._parse_expression(jsonpath_expr)
        matches = expr.find(self._data)
        if not matches:
            return None
        # 如果只有一个结果，直接返回值；多个结果返回列表
        return (
            matches[0].value
            if len(matches) == 1
            else [match.value for match in matches]
        )

    def _get_list_attr_value(self, jsonpath_expr: str, as_json: bool = False):
        """
        获取列表属性值，支持字段缺失时补全 None。

        Args:
            jsonpath_expr: str: JSONPath 表达式
            as_json: bool: 是否返回 JSON 字符串

        Returns:
            List[Union[str, int, float, bool]]: 属性值列表
        """
        # 提取父级路径和子级路径
        if "[*]" in jsonpath_expr:
            idx = jsonpath_expr.find("[*]")
            parent_expr_str = jsonpath_expr[: idx + 3]  # 包含 [*]
            child_expr_str = jsonpath_expr[idx + 3 :]  # [*] 之后的部分
        else:
            # 如果没有 [*]，则整个路径作为父级路径
            parent_expr_str = jsonpath_expr
            child_expr_str = ""

        parent_expr = self._parse_expression(parent_expr_str)
        parent_matches = parent_expr.find(self._data)

        values = []
        if child_expr_str:
            # 存在子级路径，需要在每个父级元素中查找子属性
            child_expr = self._parse_expression(f'$.{child_expr_str.lstrip(".")}')
            for match in parent_matches:
                parent_value = match.value
                # 在当前父级元素中查找子属性
                child_matches = child_expr.find(parent_value)
                if child_matches:
                    # 假设每个父级元素中子属性只匹配一个值
                    values.append(child_matches[0].value)
                else:
                    values.append(None)  # 子级路径缺失时补全 None
        else:
            # 没有子级路径，父级匹配结果即为值
            values = [match.value for match in parent_matches]

        # 返回 JSON 字符串或列表
        return json.dumps(values, ensure_ascii=False) if as_json else values
