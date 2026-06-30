from django.urls import path
from django.contrib.auth import views as auth_views
from . import views



urlpatterns = [
    # HOME / AUTENTICAÇÃO
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # PÁGINAS PRINCIPAIS
    path('menu/', views.menu_view, name='menu'),
    path('menu/suggestions/', views.menu_search_suggestions, name='menu_search_suggestions'),
    path('tela/', views.screen_user, name='screen_user'),
    path('privacidade/', views.privacy, name='privacy'),
    path('termos/', views.terms, name='terms'),

    # RESET DE SENHA
    path(
        'redefinir-senha/',
        auth_views.PasswordResetView.as_view(
            template_name='mainpage/password_reset.html'
        ),
        name='password_reset'
    ),
    path(
        'redefinir-senha/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='mainpage/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'redefinir-senha/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='mainpage/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),
    path(
        'redefinir-senha/concluido/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='mainpage/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    # PERFIL
    path('upload-photo/', views.upload_photo, name='upload_photo'),
    path('perfil/atualizar/', views.update_profile, name='update_profile'),

    # ITENS
    path('perfil/item/novo/', views.register_item, name='register_item'),
    path('itens/', views.list_item, name='item_list'),
    path('itens/perdidos/', views.items_perdidos, name='items_perdidos'),
    path('itens/encontrados/', views.items_encontrados, name='items_encontrados'),
    path('itens/recentes/', views.recent_items, name='itens_recentes'),
    path('item/<slug:slug>/', views.item_detail, name='item_detail'),
    path('item/editar/<int:id>/', views.edit_item, name='item_edit'),
    path('item/deletar/<int:id>/', views.delete_item, name='item_delete'),
    path("meus-itens/", views.my_itens, name="my_itens"),
    path("itens/devolvidos/", views.items_devolvidos, name="items_devolvidos"),
    path("itens/<int:id>/devolver/", views.marcar_devolvido, name="marcar_devolvido"),
    path("itens/<int:id>/achado/", views.marcar_achado, name="marcar_achado"),
    path("itens/<int:id>/perdido/", views.marcar_perdido, name="marcar_perdido"),
    path('itens/busca-visual/', views.busca_visual, name='busca_visual'),



    # CHAT
    path('chats/', views.chats_list, name='chats_list'),
    path('chats/iniciar/<int:item_id>/', views.chat_start, name='chat_start'),
    path('chats/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('chats/<int:chat_id>/mensagens/', views.chat_messages, name='chat_messages'),
    path('chats/<int:chat_id>/enviar/', views.chat_send_message, name='chat_send_message'),
    path('chats/<int:chat_id>/fechar/', views.chat_close, name='chat_close'),

    # Painéis de controle
    path('painel/bolsista/', views.bolsista_dashboard, name='bolsista_dashboard'),
    path('painel/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('painel/admin/estatisticas/', views.dashboard_admin, name='dashboard_admin'),

    # Painel IoT
    path('painel/iot/', views.iot_dashboard, name='iot_dashboard'),
    path('painel/iot/dispositivo/<uuid:device_id>/', views.iot_device_detail, name='iot_device_detail'),
    path('painel/iot/dispositivo/novo/', views.iot_create_device, name='iot_create_device'),
    path('painel/iot/dispositivo/<uuid:device_id>/toggle/', views.iot_toggle_device, name='iot_toggle_device'),
    path('painel/iot/dispositivo/<uuid:device_id>/excluir/', views.iot_delete_device, name='iot_delete_device'),
    path('painel/iot/logs/', views.iot_logs, name='iot_logs'),
]
