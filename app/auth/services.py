from functools import lru_cache

from app.auth.clients import AuthenticationClient
from app.auth.types import AuthUser, Company
from app.config import config


class AuthenticationService:
    def __init__(self) -> None:
        self._client: AuthenticationClient | None = None

    def start(self) -> None:
        self._client = AuthenticationClient(
            base_url=config.AUTHENTICATION_API_URL,
            timeout_seconds=config.AUTHENTICATION_API_TIMEOUT,
        )

    def stop(self) -> None:
        if self._client is None:
            return
        return self._client.close()

    @property
    def client(self) -> AuthenticationClient:
        if client := self._client:
            return client
        raise ValueError("Authentication service is not started, use .start method")

    def get_users(
        self,
        company_id: int,
        permission_level: str | None = None,
        permissions_feature: str | None = None,
    ) -> list[AuthUser]:
        return self.client.get_users(
            company_id=company_id,
            permission_level=permission_level,
            permissions_feature=permissions_feature,
        )

    def get_company(self, company_id: int) -> Company:
        return self.client.get_company(company_id=company_id)


authentication = AuthenticationService()


def get_users(
    company_id: int,
    permission_level: str | None = None,
    permissions_feature: str | None = None,
) -> list[AuthUser]:
    """Fetch users from authentication service"""
    return authentication.get_users(
        company_id=company_id,
        permission_level=permission_level,
        permissions_feature=permissions_feature,
    )


@lru_cache(maxsize=100)
def get_company(company_id: int) -> Company:
    return authentication.get_company(company_id=company_id)
