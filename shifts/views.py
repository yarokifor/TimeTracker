from django.shortcuts import render
#from django.http import HttpResponse
from django.http import HttpResponseRedirect 
#from django.template import loader
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from shifts.models import Shift, Event, Task
import bleach
import datetime

def index(request):
    context = {"error": request.GET.get("error")}
    if request.user.is_authenticated():
        return HttpResponseRedirect("/shifts?error=already_authenticated")
    return render(request, 'login.html', context)

@require_http_methods(['POST'])
def login_handler(request):
    username = request.POST['username'] 
    password = request.POST['password']
    user = authenticate(username=username,password=password)
    if user is not None:
        login(request, user)
        return HttpResponseRedirect("/shifts")
    else:
        return HttpResponseRedirect("/?error=invalid_login") 

@login_required 
def logout_handler(request):
    logout(request)
    return HttpResponseRedirect("/?message=succesful_logout")

@login_required 
def shifts(request):
    last_shift = None
    last_event = Event.objects.filter(shift__user = request.user).order_by("time").last()

    if last_event != None:
        last_shift = last_event.shift
    
    if request.method == 'POST':
        event = request.POST['event']
        if event == 'task':
            task = Task(shift = last_shift, description = bleach.clean(request.POST['desc']))
            task.save()
        else:
            if event in [item[0] for item in Event.EVENTS]:
                if event == 'IN':
                    last_shift = Shift(user = request.user)
                    last_shift.save()
                last_event = Event(shift = last_shift, event = event, time = datetime.datetime.now())
                last_event.save()
             
    context = {
        "error": request.GET.get("error"),
        "last_event": last_event,
        "tasks": Task.objects.filter(shift = last_shift),
        "event_choices": Event.EVENTS,
    }

    return render(request, 'shifts.html', context)
