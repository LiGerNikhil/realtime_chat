from django.forms import ModelForm
from django import forms
from .models import *

class ChatmessageCreateForm(ModelForm):
    class Meta:
        model = GroupMessage
        fields =  ['body']
        widgets = {
            'body': forms.TextInput(attrs={'placeholder':'Add Message...','class':'p-4 text-black', 'maxlength':'300', 'autofocus':True}),
        }

class NewGroupForm(ModelForm):
     class Meta:
         model = ChatGroup
         fields = ['groupchat_name']
         widgets = {
             'groupchat_name': forms.TextInput(attrs={
                 'placeholder':'Add Name...',
                 'class':'p-4 text-black',
                 'maxlength':'50',
                 'autofocus':True}),
         }       

class ChatRoomEditForm(ModelForm):
    class Meta:
        model = ChatGroup
        fields = ['groupchat_name']
        widgets ={
            'groupchat_name': forms.TextInput(attrs={
               'placeholder':'Add Name...',
               'class':'p-4 text-xl font-bold mb-4',
               'maxlength':'300',
            }),
        }         