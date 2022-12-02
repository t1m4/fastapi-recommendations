import httpx

from app.auth.types import AuthUser, AuthUsers, Company
from app.auth.utils import create_jwt_token
from app.types import StrDict

# bind variable to httpx.HTTPError to ability to abstract from `httpx` module
HTTPError = httpx.HTTPError


class AuthenticationClient:
    def __init__(self, base_url: str, timeout_seconds: int) -> None:
        self.client = httpx.Client(base_url=base_url, timeout=timeout_seconds)

    def close(self) -> None:
        self.client.close()

    @staticmethod
    def _admin_user_headers() -> StrDict:
        # NOTE: Remove for public
        internal_user_data = {}
        internal_jwt = create_jwt_token(
            payload=internal_user_data,
            key="",  # Currently, the internal token is signed by an empty key
        )
        return {"X-INTERNAL-AUTHORIZATION": internal_jwt}

    def get_users(
        self,
        company_id: int,
        permission_level: str | None = None,
        permissions_feature: str | None = None,
    ) -> list[AuthUser]:

        params: StrDict = {"company_id": company_id}
        if permission_level is not None:
            params["permission_level"] = permission_level
        if permissions_feature is not None:
            params["permissions_feature"] = permissions_feature

        response = self.client.get("/_api/authentication/v1/users", params=params)
        response.raise_for_status()

        users = AuthUsers.parse_obj(obj=response.json())
        return users.__root__

    def get_company(self, company_id: int) -> Company:
        response = self.client.get(
            url=f"/_api/authentication/v1/companies/{company_id}/",
            headers=self._admin_user_headers(),
        )
        response.raise_for_status()
        return Company(**response.json())
