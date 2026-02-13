from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]

# Customize admin site headers
admin.site.site_header = "Market Tick System Administration"
admin.site.site_title = "Market Tick Admin Portal"
admin.site.index_title = "Welcome to Market Tick System"
