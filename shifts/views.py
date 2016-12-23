from django.shortcuts import render
#from django.http import HttpResponse
from django.http import HttpResponseRedirect 
#from django.template import loader
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from shifts.models import Shift, Event, Profile
import bleach
import datetime
import calendar

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
            last_event.save()
            if event == "IN":
                last_shift = Shift(user = request.user, start = last_event, tasks_completed = "")
            elif event == "OUT":
                last_shift.end = last_event
        last_shift.save()
             
    context = {
        "error": request.GET.get("error"),
        "last_shift": last_shift,
        "tasks_completed": last_shift.tasks_completed[1:-1].split('`,`'),
        "last_event": last_event,
        "lastest_events": Event.objects.filter(user = request.user),
        "event_choices": Event.EVENTS,
        "possible_events": Event.REQUIRED_EVENT[last_event.event if last_event != None else None]
    }

    return render(request, 'shifts.html', context)

@login_required
def export(request):
    daily_hours = []
    
    now_iso = datetime.datetime.now().isocalendar()
    total_hours = 0


    year = int(request.GET.get("year", now_iso[0]))
    week = int(request.GET.get("week", now_iso[1]))
    
    start_of_week,end_of_week = __get_week_range(year, week)

    shifts_of_this_week = Shift.objects.filter(user=request.user, start__time__gte = start_of_week, start__time__lte = end_of_week)
     
    shifts_and_hours = []
    for shift in shifts_of_this_week:
        if __calculate_hours(shift) != None:
            hours = __calculate_hours(shift).total_seconds()
        else:
            hours = 0

        shifts_and_hours.append([shift, hours/3600])
        total_hours = total_hours + hours
    
    context = {
       "shifts_and_hours": shifts_and_hours,
       "total_hours": total_hours/3600,
       "start_of_week": start_of_week,
       "end_of_week": end_of_week,
       "year": start_of_week.isocalendar()[0],
       "week": start_of_week.isocalendar()[1]
    }
    return render(request, "export.html", context)

def __calculate_hours(shifts):
    '''Returns timedelta of how much time worked..'''

    if shifts == None:
        return 0

    if type(shifts) == Shift:
        shifts = [shifts]

    time = None
    
    for shift in shifts:
        if shift.end != None:
            time = shift.end.time - shift.start.time
            for break_out in Event.objects.filter(user = shift.user, event__exact = "BEN", time__gt = shift.start.time, time__lt = shift.end.time):
               time = time - ( break_out.time - Event.objects.filter(user = break_out.user, time__lt = break_out.time, event__exact = "BST").last().time )
    return time

def __get_week_range(year=None, week=None):
    '''Returns when a week starts and ends.'''
    if year == None:
        year = datetime.datetime.now().year
    if week == None:
        week = datetime.datetime.now().isocalendar()[1]

    day_zero = datetime.date(year, 1, 4)
    day_zero = day_zero + datetime.timedelta(weeks=(week-1), days=day_zero.weekday())
    day_six = day_zero + datetime.timedelta(days=7, seconds=-1)

    return day_zero, day_six

@login_required
def profile(request):
    context = dict()
    if request.method == 'POST':
        auto_clock_out = request.POST.get("auto_clock_out")
        if auto_clock_out == "None":
            auto_clock_out = None
        else:
            try:
                auto_clock_out = datetime.datetime.strptime(auto_clock_out,'%H:%M').time()
            except ValueError:
                auto_clock_out = None
                context['error'] = 'invalid_value'

        request.user.profile.auto_clock_out = auto_clock_out
        request.user.profile.save()

    return render(request, "profile.html", context)
