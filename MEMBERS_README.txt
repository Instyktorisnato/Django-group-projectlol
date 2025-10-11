
Добавлены возможности управления участниками:
- Поле role в модели User: choices = ['creator','admin','moder','helper']
- Страница /accounts/participants/ - доступна модерам, админам и создателю.
- Действия: delete, ban/unban; и смена роли (admins не могут выдавать роль admin/creator).
Что нужно сделать после распаковки:
1) Применить миграции: python manage.py makemigrations accounts && python manage.py migrate
2) Перезапустить сервер.
3) Зайти под пользователем-создателем и назначить роли по необходимости.
