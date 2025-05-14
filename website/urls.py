from django.urls import include, path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('tickets/create/', views.create_ticket, name='create_ticket'),
    path('tickets/', views.my_tickets, name='my_tickets'),
    path('tickets_list/', views.ticket_list, name='tickets_list'),
    path('tickets/assign/', views.assign_tickets, name='assign_tickets'),
    path('tickets/assign/<int:ticket_id>/', views.assign_ticket, name='assign_ticket'),
    path('tickets/edit/<int:ticket_id>/', views.edit_ticket, name='edit_ticket'),
    path('tickets/delete_ticket/<int:ticket_id>/', views.delete_ticket, name='delete_ticket'),
    path('tickets/agent/', views.agent_tickets, name='agent_tickets'),
    path('tickets/resolve/<int:ticket_id>/', views.resolve_ticket, name='resolve_ticket'),
    path('agent/dashboard/', views.agent_dashboard, name='agent_dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin_home/', views.admin_home, name='admin_home'),
    path('tickets/comment/<int:ticket_id>/', views.add_comment, name='add_comment'),
    path('tickets/unassign/<int:ticket_id>/', views.unassign_ticket, name='unassign_ticket'),
    path('agent_home/', views.agent_home, name='agent_home'),
    path("__reload__/", include("django_browser_reload.urls")),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
