import json
from pydoc_data.topics import topics
from turtle import pos
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse 
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .models import Item, Message, Room, Topic , Message, UserProfile, QuizScore
from .forms import CompleteProfileForm, CustomUserCreationForm, RoomForm ,UserForm
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login , logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import JsonResponse
import razorpay


# rooms = [
#     {'id':1 ,'name':'lets learn python'},
#     {'id':2 ,'name':'design with me'},
#     {'id':3 ,'name':'frontend developers'}
# ]

def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        usern = request.POST.get('username')
        password = request.POST.get('password')
        login_type = request.POST.get('login_type')
        print(login_type)
        try:
            user = User.objects.get(username=usern)
        except:
            messages.error(request,'User does not exist') 
        user =  authenticate(request, username= usern,password=password)
        if user is not None:
            if(login_type=='student'):
                login(request,user)
                return redirect('home')
            elif(login_type=='mentor'):
                login(request,user)
                return redirect('home_mentor')
        else:
            messages.error(request,'Username or Password does not exist')
    context ={'page':page}
    return render(request,'base/login_register.html',context)


def logout_user(request):
    logout(request)
    return redirect(reverse('home'))

def registerPage(request):
    # page = 'register'
    form = CustomUserCreationForm()
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():   
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")


    return render(request, 'base/login_register.html', {'form': form})

def home(request):
    q = request.GET.get('q') if request.GET.get('q')!=None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
        )
    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))
    context = {'rooms': rooms, 'topics': topics,'room_count': room_count , 'room_messages':room_messages}
    return render(request,'base/home.html',context)

def home_mentor(request):
    q = request.GET.get('q') if request.GET.get('q')!=None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
        )
    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))
    context = {'rooms': rooms, 'topics': topics,'room_count': room_count , 'room_messages':room_messages}
    return render(request,'base/home_mentor.html',context)

def room(request,pk):
    room = Room.objects.get(id = pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()
    if request.method == 'POST': 
       message = Message.objects.create(
           user = request.user,
           room = room,
           body = request.POST.get('body') 
       )
       room.participants.add(request.user)
       return redirect('room', pk=room.id)
    context = {'room':room,'room_messages':room_messages,'participants':participants}
    return render(request, 'base/room.html',context)

def room2(request,pk):
    room = Room.objects.get(id = pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()
    if request.method == 'POST': 
       message = Message.objects.create(
           user = request.user,
           room = room,
           body = request.POST.get('body') 
       )
       room.participants.add(request.user)
       return redirect('room', pk=room.id)
    context = {'room':room,'room_messages':room_messages,'participants':participants}
    return render(request, 'base/room2.html',context)

def userProfile(request,pk):
    user = User.objects.get(id=pk)
    try:
        user_profile = UserProfile.objects.get(user=user)

        # Filter non-null fields from the UserProfile model
        non_null_fields = {
            'summary': user_profile.summary,
            'github': user_profile.github,
            'linkedin': user_profile.linkedin,
            'industry': user_profile.industry,
            'job_role': user_profile.job_role,
            'personal_details': user_profile.personal_details,
        }

    except UserProfile.DoesNotExist:
        # If UserProfile does not exist, set non_null_fields to an empty dictionary
        non_null_fields = {}
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context={'user':user,'rooms':rooms,'room_messages':room_messages,'topics':topics, 'profile_data': non_null_fields}
    return render(request,'base/profile.html',context)

def mentorProfile(request, pk):
    user = get_object_or_404(User, id=pk)

    try:
        user_profile = UserProfile.objects.get(user=user)

        # Filter non-null fields from the UserProfile model
        non_null_fields = {
            'summary': user_profile.summary,
            'github': user_profile.github,
            'linkedin': user_profile.linkedin,
            'industry': user_profile.industry,
            'job_role': user_profile.job_role,
            'personal_details': user_profile.personal_details,
        }

    except UserProfile.DoesNotExist:
        # If UserProfile does not exist, set non_null_fields to an empty dictionary
        non_null_fields = {}

    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user, 'rooms': rooms, 'room_messages': room_messages, 'topics': topics, 'profile_data': non_null_fields}
    return render(request, 'base/mentor_profile.html', context)

@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name = topic_name)
        Room.objects.create(
            host =request.user,
            topic = topic,
            name = request.POST.get('name'),
            description = request.POST.get('description')
        )
    
        return redirect('home_mentor')
    context = { 'form' : form ,'topics':topics}
    return render(request, 'base/room_form.html' ,context)

@login_required(login_url='login')
def updateRoom(request,pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    if request.user!= room.host :
        return HttpResponse('You are not allowed here')
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name = topic_name)
        form = RoomForm(request.POST, instance=room)
        room.name = request.POST.get('name')
        room.topic = topic

        room.description = request.POST.get('description')
        room.save()
        return redirect('home_mentor')
    context = {'form':form,'topics':topics,'room':room}
    return render(request , 'base/room_form.html', context)

@login_required(login_url='login')
def deleteRoom(request,pk):
    room = Room.objects.get(id=pk)
    if request.user!= room.host :
        return HttpResponse('You are not allowed here') 
    if request.method == 'POST':
        room.delete()
        return redirect('home_mentor')
    return render(request,'base/delete.html',{'obj':room})

@login_required(login_url='login')
def deleteMessage(request,pk):
    message = Message.objects.get(id=pk)
    if request.user!= message.user :
        return HttpResponse('You are not allowed here') 
    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request,'base/delete.html',{'obj':message})


@login_required(login_url='login')
def updateUser(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = CompleteProfileForm(request.POST, instance=user_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            return redirect('user-profile', pk=user.id)
    else:
        user_form = UserForm(instance=user)
        profile_form = CompleteProfileForm(instance=user_profile)

    return render(request, 'base/update-user.html', {'user_form': user_form, 'profile_form': profile_form})

@login_required(login_url='login')
def updateMentor(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = CompleteProfileForm(request.POST, instance=user_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            return redirect('mentor-profile', pk=user.id)
    else:
        user_form = UserForm(instance=user)
        profile_form = CompleteProfileForm(instance=user_profile)

    return render(request, 'base/update-mentor.html', {'user_form': user_form, 'profile_form': profile_form})

def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q')!=None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request,'base/topics.html',{'topics':topics})


def activityPage(request):
    room_messages = Message.objects.all()
    return render(request,'base/activity.html',{'room_messsages':room_messages})

@login_required(login_url='login')
def video(request):
    q = request.GET.get('q') if request.GET.get('q')!=None else ''
    obj = Item.objects.filter(
        Q(videotitle__icontains=q) |
        Q(video__icontains=q) 
        # Q(description__icontains=q)
        )
    
    topics = Topic.objects.all()[0:5]
    # room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))
    context = { 'topics': topics, 'obj':obj}
    
  
    return render(request,'base/courses.html',context)

client = razorpay.Client(auth=('rzp_test_lINBOTtTOEAiAR','rq76uXRs3pkubhB3GoLBi0A9'))
@login_required(login_url='login')
def subscription(request):
    order_amount = 10000
    order_currency = "INR"
    payment_order = client.order.create(dict(amount = order_amount,currency = order_currency,payment_capture =1))
    payment_order_id = payment_order['id']
    context = {
        'amount' : 10,
        'api_key':'rzp_test_lINBOTtTOEAiAR',
        'order_id':payment_order_id
    }
    return render(request,'base/contact.html',context)
from django.db.models import Count
from django.db.models import F
def analysisDashboard(request,pk):
    host_user = User.objects.get(username=pk)
    # Get all rooms with the specified host
    rooms = Room.objects.filter(host=host_user)
    total_participants_count = 0
    for room in rooms:
        total_participants_count += room.participants.count()
    total_rooms_count = rooms.count()
    average_participants_per_room = (total_participants_count // total_rooms_count) if total_rooms_count > 0 else 0
    room_with_max_participants = max(rooms, key=lambda room: room.participants.count(), default=None)
    room_with_max_participants_name = room_with_max_participants.name if room_with_max_participants else None
    topic_of_max_participants = room_with_max_participants.topic.name if room_with_max_participants else None
    unique_topics = rooms.values('topic__name').distinct()
    unique_topics_data = list(rooms.values('topic__name').annotate(total_participants=Count('participants')))
    unique_topics_data_json = json.dumps(unique_topics_data)
    topic_names = [entry['topic__name'] for entry in unique_topics_data]
    total_participants_topic = [entry['total_participants'] for entry in unique_topics_data]
    longest_running_room = Room.objects.filter(host=host_user).annotate(active_duration=F('updated') - F('created')).order_by('-active_duration').first()
    # print(unique_topics_data)
    context = {
        'host_username': pk,
        'rooms': rooms,
        'total_participants_count': total_participants_count,
        'total_rooms_count': total_rooms_count,
        'room_with_max_participants_name': room_with_max_participants_name,
        'topic_of_max_participants': topic_of_max_participants,
        'unique_topics':unique_topics,
        'unique_topics_data': unique_topics_data,
        'unique_topics_data_json': unique_topics_data_json,
        'topic_names':topic_names,
        'total_participants_topic':total_participants_topic,
        'average_participants_per_room':average_participants_per_room,
        'longest_running_room':longest_running_room,
        
    }

    return render(request, 'base/analysis_dashboard.html', context)

## profile building 
@login_required(login_url='login')
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    form = CompleteProfileForm(request.POST or None, instance=user_profile)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('profile')  # Redirect to the profile page

    return render(request, 'profile.html', {'form': form})
    
def user_interests(request, user_id):
    user_profile = UserProfile.objects.get(user_id=user_id)
    interests = user_profile.get_interests()
    related_rooms = Room.objects.filter(topic__name__in=interests)
    return render(request, 'base/user_interests.html', {'user_profile': user_profile, 'interests': interests,'rooms':related_rooms})


from django.shortcuts import render
from .forms import VideoForm
from .models import Video

def upload_video(request):
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.uploaded_by = request.user
            video.save()
            return redirect('video_list')  # Redirect to the video list page
    else:
        form = VideoForm()
    return render(request, 'base/upload-video.html', {'form': form})

def video_list(request):
    videos = Video.objects.all()
    return render(request, 'base/video_list.html', {'videos': videos})



def video_list_student(request):
    videos = Video.objects.all()
    return render(request, 'base/video_list_student.html', {'videos': videos})


def assessments(request):
    # Your logic for the assessments view
    return render(request, 'base/assessments.html')

def scores(request):
    # Your logic for the assessments view
    return render(request, 'base/scores.html')


def save_quiz_score(request):
    if request.method == 'POST':
        category = request.POST.get('category')
        score = int(request.POST.get('score'))
        # Assuming the user is authenticated and you have their email
        user = request.user
        # Save the quiz score to the database
        QuizScore.objects.create(user=user, category=category, score=score)
        return JsonResponse({'message': 'Quiz score saved successfully'})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)