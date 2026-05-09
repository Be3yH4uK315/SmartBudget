from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator


def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_encoders={Decimal: float},
    )


class CategoryLimitRequest(CamelModel):
    category_id: int = Field(..., gt=0)
    limit_amount: Decimal = Field(..., ge=0)


class CreateBudgetRequest(CamelModel):
    categories: list[CategoryLimitRequest] = Field(default_factory=list)
    total_limit_amount: Decimal | None = Field(default=None, ge=0)
    is_auto_renew: bool = False


class PatchCategoryLimitRequest(CamelModel):
    category_id: int = Field(..., gt=0)
    limit_amount: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_limit(self):
        if self.limit_amount is None:
            raise ValueError("limitAmount is required")
        return self


class PatchBudgetRequest(CamelModel):
    total_limit_amount: Decimal | None = Field(default=None, ge=0)
    is_auto_renew: bool | None = None
    categories: list[PatchCategoryLimitRequest] | None = None


class CategoryResponse(CamelModel):
    category_id: int
    limit_amount: Decimal
    spent_amount: Decimal

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
        json_encoders={Decimal: float},
    )


class CategorySettingsResponse(CamelModel):
    category_id: int
    limit_amount: Decimal

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
        json_encoders={Decimal: float},
    )


class BudgetResponse(CamelModel):
    total_limit_amount: Decimal
    spent_amount: Decimal
    is_auto_renew: bool
    categories: list[CategoryResponse]


class BudgetSettingsResponse(CamelModel):
    total_limit_amount: Decimal
    is_auto_renew: bool
    categories: list[CategorySettingsResponse]


class DashboardCategoryResponse(CamelModel):
    category_id: int
    amount: Decimal
    transaction_type: str


class DashboardBudgetResponse(CamelModel):
    categories: list[DashboardCategoryResponse]
    total_limit_amount: Decimal


class CreateBudgetResponse(CamelModel):
    budget_id: str
