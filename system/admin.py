from django.contrib import admin
from .models import Car, Order, PrivateMsg, ChatRoom, ChatMessage, ChatBotResponse
# Register your models here.

class CarAdmin(admin.ModelAdmin):
    list_display = ("car_name", "image", "company_name")

class OrderAdmin(admin.ModelAdmin):
    list_display = ("car_name", "date_from", "date_to", "dealer_name",)

class PrivateMsgAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "message")

class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("room_id", "status", "created_at", "updated_at")

class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("room", "sender_type", "created_at", "is_read")

class ChatBotResponseAdmin(admin.ModelAdmin):
    list_display = ("intent", "keywords", "is_active", "priority")

admin.site.register(Car, CarAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(PrivateMsg, PrivateMsgAdmin)
admin.site.register(ChatRoom, ChatRoomAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)
admin.site.register(ChatBotResponse, ChatBotResponseAdmin)
