from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    path('add_new_listing/', views.add_new_listing, name='add-new-listing'),
    path('house-list/', views.house_list, name='house_list'),
    path('house/<int:property_id>/', views.house_detail, name='house_detail'),
    path('house/<int:property_id>/submit_review/', views.submit_review, name='submit_review'),
    path('my-listings/', views.my_listings, name='my_listings'),
    path('edit-listing/<int:property_id>/', views.edit_listing, name='edit_listing'),
    path('delete-listing/<int:property_id>/', views.delete_listing, name='delete_listing'),
    path('profile-settings/', views.profile_settings, name='profile_settings'),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('about-us/', views.about_us, name='about-us'),
    path('terms-conditions/', views.terms_conditions, name='terms-conditions'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
]
