from django.contrib import admin
from pov.models import About, Blog, Category, Comment


class BlogAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug' : ('title',)} # Generate automated slug when create the title 
    list_display = ('title', 'category', 'author', 'status' , 'is_featured') #Display the modal names on administration
    search_fields = ('id', 'title', 'category__category_name', 'status') #Data Search on administration
    list_editable = ('is_featured',) #Editable booleans on administration

class AboutAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        count = About.objects.all().count()
        if count == 0:
            return True
        else:
            return False

admin.site.register(Category)
admin.site.register(Blog, BlogAdmin)
admin.site.register(About, AboutAdmin)
admin.site.register(Comment)