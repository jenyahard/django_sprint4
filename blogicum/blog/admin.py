from django.contrib import admin

from blog.models import Category, Post, Location


admin.site.site_title = 'Администрирование блога'
admin.site.site_header = 'Администрирование блога'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'slug']
    search_fields = ['title', 'description', 'slug']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'pub_date', 'location', 'category']
    list_filter = ['author', 'location', 'category']
    search_fields = ['title', 'text']
    list_editable = ['category']
    date_hierarchy = 'pub_date'
    fieldsets = (
        (None, {
            'fields': ('title', 'author', 'location', 'category')
        }),
        ('Additional Information', {
            'fields': ('text', 'pub_date'),
            'classes': ('collapse',),
        }),
    )
