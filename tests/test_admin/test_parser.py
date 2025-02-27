from typing import List

from pydantic import BaseModel
from typing_extensions import get_origin

from fastapi_amis_admin import amis
from fastapi_amis_admin.admin.parser import AmisParser
from fastapi_amis_admin.models import Field, IntegerChoices

amis_parser = AmisParser()


class Role(BaseModel):
    id: int = Field(..., title="ID")
    name: str = Field(..., title="名称")


def test_field_str():
    class User(BaseModel):
        name: str = Field("123456", title="姓名", min_length=2, max_length=10)

    modelfield = User.__fields__["name"]
    # formitem
    formitem = amis_parser.as_form_item(modelfield, set_default=True)
    assert formitem.type == "input-text"
    assert formitem.label == "姓名"
    assert formitem.minLength == 2  # type: ignore
    assert formitem.maxLength == 10  # type: ignore
    assert formitem.value == "123456"
    # filter
    filteritem = amis_parser.as_form_item(modelfield, is_filter=True, set_default=True)
    assert filteritem.type == "input-text"
    assert filteritem.label == "姓名"
    assert hasattr(filteritem, "minLength") is False
    assert hasattr(filteritem, "maxLength") is False
    assert filteritem.value is None
    # table column
    column = amis_parser.as_table_column(modelfield)
    assert column.type is None
    assert column.label == "姓名"


def test_field_int():
    class User(BaseModel):
        age: int = Field(18, title="年龄")

    modelfield = User.__fields__["age"]
    # formitem
    formitem = amis_parser.as_form_item(modelfield, set_default=True)
    assert formitem.type == "input-number"
    assert formitem.label == "年龄"
    assert formitem.value == 18
    # filter
    filteritem = amis_parser.as_form_item(modelfield, is_filter=True, set_default=True)
    assert filteritem.type == "input-text"  # 搜索时,数字类型的字段使用文本框.可使用[>,<,>=,<=,!=]等符号.
    assert filteritem.label == "年龄"
    assert filteritem.value is None
    # table column
    column = amis_parser.as_table_column(modelfield)
    assert column.type is None
    assert column.label == "年龄"


def test_field_bool():
    class User(BaseModel):
        is_admin: bool = Field(True, title="是否管理员")

    modelfield = User.__fields__["is_admin"]
    # formitem
    formitem = amis_parser.as_form_item(modelfield, set_default=True)
    assert formitem.type == "switch"
    assert formitem.label == "是否管理员"
    assert formitem.value
    # filter
    filteritem = amis_parser.as_form_item(modelfield, is_filter=True, set_default=True)
    assert filteritem.type == "switch"
    assert filteritem.label == "是否管理员"
    assert filteritem.value is None
    # table column
    column = amis_parser.as_table_column(modelfield)
    assert column.type == "switch"
    assert column.label == "是否管理员"


def test_field_choices():
    class UserStatus(IntegerChoices):
        NORMAL = 1, "正常"
        DISABLED = 2, "禁用"

    class User(BaseModel):
        status: UserStatus = Field(UserStatus.NORMAL, title="状态")

    modelfield = User.__fields__["status"]
    # formitem
    formitem = amis_parser.as_form_item(modelfield, set_default=True)
    assert formitem.type == "select"
    assert formitem.label == "状态"
    assert formitem.value == 1
    assert formitem.options == [  # type: ignore
        {"label": "正常", "value": 1},
        {"label": "禁用", "value": 2},
    ]
    # filter
    filteritem = amis_parser.as_form_item(modelfield, is_filter=True, set_default=True)
    assert filteritem.type == "select"
    assert filteritem.label == "状态"
    assert filteritem.value is None
    assert filteritem.options == [  # type: ignore
        {"label": "正常", "value": 1},
        {"label": "禁用", "value": 2},
    ]
    # table column
    column = amis_parser.as_table_column(modelfield)
    assert column.type == "mapping"
    assert column.label == "状态"
    assert set(column.map.keys()) == {1, 2}  # type: ignore


def test_field_datetime():
    from datetime import datetime

    class User(BaseModel):
        created_at: datetime = Field(None, title="创建时间")

    modelfield = User.__fields__["created_at"]
    # formitem
    formitem = amis_parser.as_form_item(modelfield, set_default=True)
    assert formitem.type == "input-datetime"
    assert formitem.label == "创建时间"
    # filter
    filteritem = amis_parser.as_form_item(modelfield, is_filter=True, set_default=True)
    assert filteritem.type == "input-datetime-range"
    assert filteritem.label == "创建时间"
    assert filteritem.value is None
    # table column
    column = amis_parser.as_table_column(modelfield)
    assert column.type == "datetime"
    assert column.label == "创建时间"


def test_field_list():
    class User(BaseModel):
        tags: List[str] = Field([], title="标签")
        email: List[str] = Field([], title="邮箱列表", amis_form_item=amis.InputArray(items=amis.InputText(type="input-email")))

    # test tags
    modelfield = User.__fields__["tags"]
    assert modelfield.type_ == str
    assert get_origin(modelfield.outer_type_) is list
    # formitem
    formitem = amis_parser.as_form_item(modelfield, set_default=True)
    assert formitem.type == "input-array"
    assert formitem.name == "tags"
    assert formitem.label == "标签"
    assert formitem.value == []
    assert formitem.items.type == "input-text"  # type: ignore

    # test email
    modelfield = User.__fields__["email"]
    assert modelfield.type_ == str
    assert get_origin(modelfield.outer_type_) is list
    # formitem
    formitem = amis_parser.as_form_item(modelfield)
    assert formitem.type == "input-array"
    assert formitem.name == "email"
    assert formitem.items.type == "input-email"  # type: ignore


def test_field_model():
    class User(BaseModel):
        role: Role = Field(None, title="角色")
        roles: List[Role] = Field([], title="角色列表")

    modelfield = User.__fields__["role"]
    assert modelfield.type_ == Role
    assert issubclass(modelfield.type_, BaseModel)
    # formitem
    formitem = amis_parser.as_form_item(modelfield, set_default=True)

    assert formitem.type == "input-sub-form"
    assert formitem.name == "role"
    assert formitem.label == "角色"
    assert formitem.form.body[0].name == "id"  # type: ignore
    assert formitem.form.body[1].name == "name"  # type: ignore

    modelfield2 = User.__fields__["roles"]
    assert modelfield2.type_ == Role
    assert issubclass(modelfield2.type_, BaseModel)
    assert get_origin(modelfield2.outer_type_) is list
    # formitem
    formitem = amis_parser.as_form_item(modelfield2, set_default=True)
    assert formitem.type == "input-array"
    assert formitem.name == "roles"
    assert formitem.label == "角色列表"
    assert formitem.items.type == "input-sub-form"  # type: ignore
    assert formitem.items.labelField == "name"  # type: ignore


# test alias param
def test_field_param_alias():
    class User(BaseModel):
        name: str = Field(..., title="姓名", alias="username")
        role: Role = Field(None, title="角色", alias="user_role")

    modelfield = User.__fields__["name"]
    # formitem
    formitem = amis_parser.as_form_item(modelfield, set_default=True)
    assert formitem.name == "username"

    role_field = User.__fields__["role"]
    # formitem
    formitem = amis_parser.as_form_item(role_field, set_default=True)
    assert formitem.name == "user_role"
