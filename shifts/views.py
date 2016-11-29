from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect 
from django.template import loader
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.core.exceptions import ObjectDoesNotExist 
from shifts.models import Shift, Event, Task
import bleach
import datetime

def index(request):
    template = loader.get_template('login.html')
    context = dict()
    if "error" in request.GET:
        context["error"] = request.GET['error']
    return HttpResponse(template.render(context,request))

@require_http_methods(['POST'])
def login(request):
    username = request.POST['username'] 
    password = request.POST['password']
    user = authenticate(username=username,password=password)
    if user is not None:
        login(request, login)
        return HttpResponseRedirect("/shifts")
    else:
        return HttpResponseRedirect("/?error=invalidLogin") 

@login_required 
def shifts(request):
    template = loader.get_template('shifts.html')
    is_clocked_out = None
    lastShift = None
    try:
        last_shift = Shift.objects.filter(user__id__exact=request.user.id).order_by('id').first()
    except DoesNotExist:
        #User has never done a shift...
        is_clocked_out = True 
    else:
        try:
            last_event = Event.objects.filter(shift__id__exact=last_shift.id).order_by('time').first()
            if last_event.event  == "OUT":
                is_clocked_out = True
            else:
                is_clocked_out = False
        except DoesNotExist:
            #Werid. User has a shift but doesn't have any events associated with it.
            lastShift.delete()
            is_clocked_out = True



    if request.method == 'GET':
        context = dict()
        return HttpResponse(template.render(context))
    elif request.method == 'POST':
        event = request.POST['event']
        if event == 'task':
            task = Task(shift = lastShift, description = bleach.clean(request.POST['desc']))
            task.save()
        elif event == 'clock_in':
           if is_clocked_out:
               last_shift = Shift(user = request.User)
               last_shift.save()
               model_to_save = Event(shift = last_shift, event = "IN", time = datetime.datetime.now())

        elif event == 'clock_out':
               model_to_save = Event(shift = last_shift, event = "OUT", time = datetime.datetime.now())

        elif event == 'break_start':
               model_to_save = Event(shift = last_shift, event = "BST", time = datetime.datetime.now())

        elif event == 'break_end':
               model_to_save = Event(shift = last_shift, event = "BEN", time = datetime.datetime.now())

        model_to_save.save()
             
    return HttpResponse()
