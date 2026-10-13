from app.db.models import AppSetting
from app.repositories.base import SqlAlchemyRepository


class SettingsRepository(SqlAlchemyRepository[AppSetting]):
    model = AppSetting

    def get_value(self, key: str) -> dict | None:
        setting = self.get(key)
        return setting.value if setting else None

    def set_value(self, key: str, value: dict) -> None:
        setting = self.get(key)
        if setting is None:
            self.add(AppSetting(key=key, value=value))
        else:
            setting.value = value
            self.session.flush()
