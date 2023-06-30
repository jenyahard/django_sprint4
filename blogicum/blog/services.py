from django.db.models.query import QuerySet
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Count

from blog.models import Post


def get_posts() -> QuerySet[Post]:
    '''Отправляет запрос в БД формата:
    Вход - **filters: dict[str, str]
    Возвращает - QuerySet[Post]
    '''
    return annotate(Post.objects.select_related(
        'author',
        'location',
        'category',
    ).filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    ))


def annotate(querset: QuerySet[Post]) -> QuerySet[Post]:
    '''Добавляет аннотацию для подсчета количества комментариев
    '''
    return (querset
            .annotate(comment_count=Count('comment'))
            .order_by('-pub_date')
            )


def paginator_custom(self, objects: QuerySet):
    '''Пагинатор:
    Вход - self, objects: QuerySet
    Возвращает - Page
    '''
    paginate_by = 10
    paginator = Paginator(objects, paginate_by)
    page_number = self.request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
