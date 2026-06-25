from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # API REST (cada app tem suas próprias rotas)
    path('api/', include('accounts.api.urls')),
    path('api/', include('items.api.urls')),
    path('api/', include('chats.api.urls')),
    path('api/iot/', include('iot.api.urls')),

    # Site web
    path('', include('mainpage.urls')),
    
    # Allauth
    path('accounts/', include('allauth.urls')),
]

# Serve arquivos de mídia do banco de dados (funciona no Render)
from find.storage import serve_db_media

urlpatterns += [
    path('media-db/<path:path>', serve_db_media, name='serve_db_media'),
]
