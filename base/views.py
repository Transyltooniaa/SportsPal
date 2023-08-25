from django.shortcuts import render,redirect
from django.db.models import Q
from django.http import HttpResponse
from .models import Room,Topic,Message
from django.contrib.auth.models import User 
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .forms import RoomForm
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout

from django.shortcuts import render
from django.http import HttpResponseRedirect
from .forms import RegisterForm

def user_register(request):
    # if this is a POST request we need to process the form data
    template = 'base/login_register.html'
   
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = RegisterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            if User.objects.filter(username=form.cleaned_data['username']).exists():
                return render(request, template, {
                    'form': form,
                    'error_message': 'Username already exists.'
                })
            elif User.objects.filter(email=form.cleaned_data['email']).exists():
                return render(request, template, {
                    'form': form,
                    'error_message': 'Email already exists.'
                })
            elif form.cleaned_data['password'] != form.cleaned_data['password_repeat']:
                return render(request, template, {
                    'form': form,
                    'error_message': 'Passwords do not match.'
                })
            else:
                # Create the user:
                user = User.objects.create_user(
                    form.cleaned_data['username'],
                    form.cleaned_data['email'],
                    form.cleaned_data['password']
                )
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.phone_number = form.cleaned_data['phone_number']
                user.save()
               
                # Login the user
                login(request, user)
               
                # redirect to accounts page:
                return redirect('home')

   # No post data availabe, let's just show the page.
    else:
        form = RegisterForm()

    return render(request, template, {'form': form})


def landingPage(request):
    context = {}
    return render(request,"base/landing.html",context)


def loginPage(request):

    page = 'login'

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request,"Username does not exist")

        user = authenticate(request,username=username,password=password)

        if user is not None:
            login(request,user)
            return redirect('home')
        
        else:
            messages.error(request,"Username or Password is incorrect")
    
    context = {'page':page}
    return render(request,"base/login_register.html",context)




def logoutUser(request):
    logout(request)
    return redirect('home')



def registerPage(request):
    form = UserCreationForm()
    context = {'form':form}
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request,user)
            return redirect('home')
        else:
            messages.error(request,"An error occured during registration")
    return render(request,"base/login_register.html",context)

    


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(Q(topic__name__icontains = q) | Q(name__icontains = q) | Q(description__icontains = q) | Q(host__username__icontains = q))

    topics = Topic.objects.all()
    room_count = rooms.count()
    room_count_topic = rooms.filter(topic__name__icontains = q).count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains = q)).order_by('-created')
    context = {'rooms':rooms,'topics':topics,'room_count':room_count,'room_messages':room_messages , "room_count_topic":room_count_topic}
    return render(request,"base/home.html",context)

    

def room(request,pk): 
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('-created')
    participants = room.participants.all()

    if request.method == "POST":
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room',pk=room.id)
    
    context = {'room':room,'room_messages':room_messages,'participants':participants}
    return render(request,"base/room.html",context )


def userProfile(request,pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user':user,'rooms':rooms,'room_messages':room_messages,'topics':topics}
    return render(request,'base/profile.html',context)



@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.host = request.user
            room.save()
            return redirect('home')
    

    context = {'form':form}
    return render(request,"base/room_form.html",context )



@login_required(login_url='login')
def updateRoom(request,pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    context = {'form':form}

    if request.user != room.host:
        return HttpResponse("You are not allowed here")

    if request.method == "POST":
        form = RoomForm(request.POST,instance=room)
        if form.is_valid():
            form.save()
            return redirect('home')
        

    return render(request,"base/room_form.html",context )



@login_required(login_url='login')
def deleteRoom(request,pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse("You are not allowed here")
    
    if request.method == "POST":
        room.delete()
        return redirect('home')
    
    return render(request,"base/delete.html",{'obj' : room})


@login_required(login_url='login')
def deleteMessage(request,pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse("You are not allowed here")
    
    if request.method == "POST":
        message.delete()
        return redirect('home')
    
    return render(request,"base/delete.html",{'obj' : room})


