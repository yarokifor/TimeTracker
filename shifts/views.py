from django.shortcuts import render
#from django.http import HttpResponse
from django.http import HttpResponseRedirect 
#from django.template import loader
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
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
def shifts(request):
    is_clocked_out = None
    last_shift = None
    last_event = None
    try:
        last_shift = Shift.objects.get(user__id__exact=request.user.id)
    except Shift.DoesNotExist:
        #User has never done a shift...
        is_clocked_out = True 
    else:
        try:
            last_event = Event.objects.filter(shift__id__exact = last_shift.id).order_by('time').first()
            if last_event.event  == "OUT":
                is_clocked_out = True
            else:
                is_clocked_out = False
        except Event.DoesNotExist:
            #Werid. User has a shift but doesn't have any events associated with it.
            lastShift.delete()
            is_clocked_out = True


    if request.method == 'POST':
        event = request.POST['event']
        if event == 'task':
            task = Task(shift = lastShift, description = bleach.clean(request.POST['desc']))
            task.save()
        elif event == 'IN':
           if is_clocked_out:
                last_shift = Shift(user = request.user)
                last_shift.save()
                last_event = Event(shift = last_shift, event = "IN", time = datetime.datetime.now())
        else:
            if event in [item[0] for item in Event.EVENTS]:
                last_event = Event(shift = last_shift, event = event, time = datetime.datetime.now())
             
    context = {
        "error": request.GET.get("error"),
        "last_event": last_event,
        "event_choices": Event.EVENTS,
    }
    return render(request, 'shifts.html', context)
