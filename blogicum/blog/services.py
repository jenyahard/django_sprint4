from django.db.models.query import QuerySet

from blog.models import Post


def get_posts(**filters: dict[str, str]) -> QuerySet[Post]:
    '''Отправляет запрос в БД формата:
    Вход - **filters: dict[str, str]
    Возвращает - QuerySet[Post]
    '''
    return Post.objects.select_related(
        'author',
        'location',
        'category',
    ).filter(**filters)
