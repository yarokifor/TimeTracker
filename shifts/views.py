from django.shortcuts import render
#from django.http import HttpResponse
from django.http import HttpResponseRedirect 
#from django.template import loader
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from shifts.models import Shift, Event
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
    last_shift = Shift.objects.filter(user = request.user).last()
    last_event = Event.objects.filter(user = request.user).last()

    if request.method == 'POST':
        event = request.POST.get("event")
        if event == "task" and last_shift != None:
            tasks = last_shift.tasks_completed
            task = bleach.clean(request.POST['desc']).replace('`','\'')
            if tasks == "":
                last_shift.tasks_completed = '`%s`' % task
            else:
                last_shift.tasks_completed = '%s,`%s`' % (tasks, task)
        elif event in Event.REQUIRED_EVENT.keys():
            last_event = Event(time = datetime.datetime.now(), event = event, user = request.user)
            if event == "IN":
                last_event.save()
                last_shift = Shift(user = request.user, start = last_event, tasks_completed = "")
            elif event == "OUT":
                last_shift.end = last_event

            last_event.save()
        last_shift.save()
             
    context = {
        "error": request.GET.get("error"),
        "last_shift": last_shift,
        "last_event": last_event,
        "event_choices": Event.EVENTS,
        "possible_events": Event.REQUIRED_EVENT[last_event.event if last_event != None else None]
    }

    return render(request, 'shifts.html', context)
