from collections.abc import Callable
from typing import Any, ClassVar

from pydantic import BaseModel, Field
from tmt import Logger, Plan, Test
from tmt.utils import GeneralError


class FmfIdModel(BaseModel):
    """Represents fmf-id data in JSON output."""
    name: str
    url: str | None = None
    path: str | None = None
    ref: str | None = None

    @classmethod
    def from_fmf_id(cls, fmf_id: Any) -> "FmfIdModel":
        """Create FmfIdModel from a tmt FmfId object."""
        return cls(
            name=fmf_id.name,
            url=fmf_id.url,
            path=fmf_id.path.as_posix() if fmf_id.path is not None else None,
            ref=fmf_id.ref,
        )


class ObjectModel(BaseModel):
    """Common structure for both Test and Plan objects in JSON output."""
    name: str
    contact: list[str]
    tag: list[str]
    summary: str | None = None
    description: str | None = None
    url: str | None = None
    ref: str | None = None
    tier: str | None = None
    id: str | None = None
    fmf_id: FmfIdModel = Field(alias="fmf-id")

    @classmethod
    def from_tmt_object(cls, obj: Test | Plan) -> "ObjectModel":
        """Create ObjectModel from a tmt Test or Plan object."""
        return cls(
            name=obj.name,
            contact=obj.contact,
            tag=obj.tag,
            summary=obj.summary,
            description=obj.description,
            url=obj.web_link(),
            ref=obj.fmf_id.ref,
            tier=obj.tier,
            id=getattr(obj, 'id', None),
            **{"fmf-id": FmfIdModel.from_fmf_id(obj.fmf_id)},
        )

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True  # Allow both fmf_id and fmf-id
        json_encoders: ClassVar[dict[type[FmfIdModel], Callable[[FmfIdModel], dict[str, Any]]]] = {
            FmfIdModel: lambda v: v.model_dump(),
        }
        alias_generator = None  # fmf_id vs fmf-id


class TestAndPlanModel(BaseModel):
    """Combined Test and Plan data for JSON output."""
    test: ObjectModel
    plan: ObjectModel

    @classmethod
    def from_tmt_objects(cls, test: Test, plan: Plan) -> "TestAndPlanModel":
        """Create TestAndPlanModel from tmt Test and Plan objects."""
        return cls(
            test=ObjectModel.from_tmt_object(test),
            plan=ObjectModel.from_tmt_object(plan),
        )


def _serialize_json(data: BaseModel, logger: Logger) -> str:
    """
    Helper function to serialize data to JSON with error handling.

    :param data: Data to serialize
    :param logger: Logger instance for logging
    :return: JSON string
    :raises: GeneralError if JSON serialization fails
    """
    try:
        logger.debug("Serializing data to JSON")
        return data.model_dump_json(by_alias=True)  # fmf_id vs fmf-id
    except Exception as err:
        logger.fail("Failed to serialize data to JSON")
        raise GeneralError("Failed to generate JSON output") from err


def generate_test_json(test: Test, logger: Logger) -> str:
    """
    Generate JSON data for a test.

    :param test: Test object to convert
    :param logger: Logger instance for logging
    :return: JSON string with test data
    :raises: GeneralError if JSON generation fails
    """
    logger.debug("Generating JSON data for test")
    data = ObjectModel.from_tmt_object(test)
    result = _serialize_json(data, logger)
    logger.debug("JSON data generated")
    return result


def generate_plan_json(plan: Plan, logger: Logger) -> str:
    """
    Generate JSON data for a plan.

    :param plan: Plan object to convert
    :param logger: Logger instance for logging
    :return: JSON string with plan data
    :raises: GeneralError if JSON generation fails
    """
    logger.debug("Generating JSON data for plan")
    data = ObjectModel.from_tmt_object(plan)
    result = _serialize_json(data, logger)
    logger.debug("JSON data generated")
    return result


def generate_testplan_json(test: Test, plan: Plan, logger: Logger) -> str:
    """
    Generate JSON data for both test and plan.

    :param test: Test object to convert
    :param plan: Plan object to convert
    :param logger: Logger instance for logging
    :return: JSON string with test and plan data
    :raises: GeneralError if JSON generation fails
    """
    logger.debug("Generating JSON data for test and plan")
    data = TestAndPlanModel.from_tmt_objects(test, plan)
    result = _serialize_json(data, logger)
    logger.debug("JSON data generated")
    return result
