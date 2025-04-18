from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.contrib import messages
from asgiref.sync import async_to_sync
from django.http import Http404, HttpResponse, JsonResponse
from .models import *
from .forms import ChatmessageCreateForm, NewGroupForm, ChatRoomEditForm

@login_required
def chat_view(request, chatroom_name='public-chat'):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    chat_messages = chat_group.chat_messages.all()[:30]  # Load last 30 messages
    form = ChatmessageCreateForm()

    other_user = None

    # Private chat validation
    if chat_group.is_private:
        if request.user not in chat_group.members.all():
            raise Http404("You are not authorized to access this chat.")
        other_user = next((member for member in chat_group.members.all() if member != request.user), None)

    # Handle group chat membership and email verification
    if chat_group.group_name:
        if request.user not in chat_group.members.all():
            if request.user.emailaddress_set.filter(verified=True).exists():
                chat_group.members.add(request.user)
            else:
                messages.warning(request, "You need to verify your email to join this chat!")
                return redirect('profile-settings')

    # Handling message posting via HTMX
    if request.htmx:
        form = ChatmessageCreateForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.group = chat_group
            message.save()
            context = {
                "message": message,
                "user": request.user,
            }
            return render(request, 'a_rtchat/partials/chat_message_p.html', context)

    context = {
        "chat_messages": chat_messages,
        "form": form,
        "other_user": other_user,
        "chatroom_name": chatroom_name,  # Ensure chatroom name is passed
        "chat_group": chat_group
    }
    return render(request, 'a_rtchat/chat.html', context)


@login_required
def get_or_create_chatroom(request, username):
    if request.user.username == username:
        return redirect('home')

    other_user = get_object_or_404(User, username=username)

    # Check if a private chatroom already exists between users
    existing_chatroom = ChatGroup.objects.filter(is_private=True, members=request.user).filter(members=other_user).first()

    if existing_chatroom:
        chatroom = existing_chatroom
    else:
        chatroom = ChatGroup.objects.create(is_private=True)
        chatroom.members.add(other_user, request.user)

    return redirect('chatroom', chatroom.group_name)


@login_required
def create_groupchat(request):
    form = NewGroupForm()

    if request.method == 'POST':
        form = NewGroupForm(request.POST)
        if form.is_valid():
            new_groupchat = form.save(commit=False)
            new_groupchat.admin = request.user
            new_groupchat.save()
            new_groupchat.members.add(request.user)
            return redirect('chatroom', new_groupchat.group_name)

    return render(request, 'a_rtchat/create_groupchat.html', {'form': form})


@login_required
def chatroom_edit_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    
    # Ensure only the admin can edit the chatroom
    if request.user != chat_group.admin:
        raise Http404()

    form = ChatRoomEditForm(instance=chat_group)
    if request.method == 'POST':
        form = ChatRoomEditForm(request.POST, instance=chat_group)
        if form.is_valid():
            form.save()

            remove_members = request.POST.getlist('remove_members')
            for member_id in remove_members:
                member = User.objects.get(id=member_id)
                chat_group.members.remove(member)
            return redirect('chatroom', chatroom_name)
    context ={
        'form': form,
        'chat_group': chat_group,
    }

    return render(request, 'a_rtchat/chatroom_edit.html', context)


@login_required
def chatroom_delete_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user != chat_group.admin:
        raise Http404()
    
    if request.method =="POST":
        chat_group.delete()
        messages.success(request, 'Chatroom Deleted Successfully !!')
        return redirect('home')
    
    return render(request, 'a_rtchat/chatroom_delete.html',{'chat_group':chat_group})

@login_required
def chatroom_leave_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user not in chat_group.members.all():
        raise Http404()
    
    if request.method == "POST":
        chat_group.members.remove(request.user)
        messages.success(request, 'You have left the chatroom !!')
        return redirect('home')
    

def chat_file_upload(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)

    if request.htmx and request.FILES:
        file = request.FILES['file']
        message = GroupMessage.objects.create(
            file = file,
            author = request.user,
            group = chat_group
        )
        channel_layer = get_channel_layer()
        event = {
            'type': 'message_handler',
            'message_id': message.id,
        }
        async_to_sync(channel_layer.group_send)(
            chatroom_name, event
        )
    return HttpResponse()        