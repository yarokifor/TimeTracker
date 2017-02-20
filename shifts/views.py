from django.shortcuts import render
#from django.http import HttpResponse
from django.http import HttpResponseRedirect 
#from django.template import loader
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from shifts.models import Shift, Event, Profile, Registration
import bleach
import datetime
from django.utils import timezone
import hashlib
import random
import os
from django.core.mail import send_mail, send_mass_mail
import base64

def index(request):
    context = dict()
    if request.user.is_authenticated():
        messages.warning(request,"You are already signed in.")
        return HttpResponseRedirect("/shifts")
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
        messages.error(request, "Incorrect password.")
        return HttpResponseRedirect("/") 

@login_required 
def logout_handler(request):
    logout(request)
    messages.info(request, "You've been logout")
    return HttpResponseRedirect("/")

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
            last_shift.save()
        elif event in Event.REQUIRED_EVENT.keys():
            last_event = Event(time = timezone.now(), event = event, user = request.user)
            last_event.save()
            if event == "IN":
                last_shift = Shift(user = request.user, start = last_event, tasks_completed = "")
            elif event == "OUT":
                last_shift.end = last_event
            last_shift.save()
             
    context = {
        "last_shift": last_shift,
        "last_event": last_event,
        "lastest_events": Event.objects.filter(user = request.user),
        "event_choices": Event.EVENTS,
        "possible_events": Event.REQUIRED_EVENT[last_event.event if last_event != None else None]
    }
    if last_shift != None:
        context['tasks_completed'] = last_shift.tasks_completed[1:-1].split('`,`')

    return render(request, 'shifts.html', context)

@login_required
def export(request):
    daily_hours = []
    
    now_iso = timezone.now().isocalendar()
    total_hours = 0 


    year = int(request.GET.get("year", now_iso[0]))
    week = int(request.GET.get("week", now_iso[1]))
    
    context = {
       "year": year,
       "week": week
    }

    days_of_week = __get_days_in_week(year, week)

    user = request.user

    if request.user.has_perm('shifts.can_view_others'):
        try:
            user = User.objects.get(id = request.GET.get("user"))
        except ObjectDoesNotExist:
            pass

        context['view_user'] = user
        context['users'] = User.objects.all()

    day_shifts_and_hours = []

    for day in days_of_week:
        shifts = Shift.objects.filter(user = user, start__time__year = day.year, start__time__month = day.month, start__time__day = day.day)
        hours = __calculate_hours(shifts)

        if hours == None:
            hours = 0
        else:
            hours = hours.total_seconds()/3600
            total_hours = total_hours + hours

        day_shifts_and_hours.append([day, shifts, hours])
    
    
    context['day_shifts_and_hours'] = day_shifts_and_hours
    context['total_hours'] = total_hours
    context['last_week'] = (day_shifts_and_hours[0][0] - datetime.timedelta(weeks=1)).isocalendar()
    context['next_week'] = (day_shifts_and_hours[0][0] + datetime.timedelta(weeks=1)).isocalendar()
    if request.GET.get("type") == "csv":
        return render(request, 'export.csv', context, content_type="text/csv")
    return render(request, "export.html", context)

def __calculate_hours(shifts):
    '''Returns timedelta of how much time worked..'''

    if shifts == None:
        return 0

    if type(shifts) == Shift:
        shifts = [shifts]

    time = datetime.timedelta(0)
    for shift in shifts:
        if shift.end != None:
            time += shift.end.time - shift.start.time
            for break_out in Event.objects.filter(user = shift.user, event__exact = "BEN", time__gt = shift.start.time, time__lt = shift.end.time):
               time = time - ( break_out.time - Event.objects.filter(user = break_out.user, time__lt = break_out.time, event__exact = "BST").last().time )
    return time

def __get_days_in_week(year=None, week=None):
    '''Returns when a week starts and ends.'''
    if year == None:
        year = datetime.datetime.now().year
    if week == None:
        week = datetime.datetime.now().isocalendar()[1]

    day_zero = datetime.datetime.strptime("%i %i 1"%(year, week), "%Y %W %w")
    days = []
    for day_number in range(7):
        days.append(day_zero + datetime.timedelta(days=day_number))
    return days



@login_required
def profile(request):
    context = dict()
    if request.method == 'POST':
        auto_clock_out = request.POST.get("auto_clock_out")
        if auto_clock_out == "None":
            auto_clock_out = None
        elif auto_clock_out != None:
            try:
                auto_clock_out = datetime.datetime.strptime(auto_clock_out,'%H:%M').time()
            except ValueError:
                auto_clock_out = None
                messages.error(request, "Invalid input.")

        request.user.profile.auto_clock_out = auto_clock_out
        request.user.profile.save()

    return render(request, "profile.html", context)

def register(request):
    context = dict()
    key = request.GET.get('key')
    if key == None:
        messages.error(request, 'Registant doesn\'t exist.')
        return HttpResponseRedirect('/')
    key = base64.urlsafe_b64decode(key)
    key_hash = hashlib.sha512(key).digest()
    registants = Registration.objects.filter(key_hash = key_hash)
    if len(registants) <= 0:
        messages.error(request, 'Registant doesn\'t exist.')
        return HttpResponseRedirect('/')
    elif len(registants) > 1:
        messages.error(request, 'Duplicate key. Something funky is going on and I am not leting you through.')
        return HttpResponseRedirect('/')
    elif request.method == 'GET':
        context['email'] = registants[0].email
        return render(request, 'registration.html', context)
    elif request.method == 'POST':
        #TODO: Add checking for user input
        try:
            User.objects.create_user(
                username = request.POST['username'],
                email = registants[0].email,
                password = request.POST['password'],
                frist_name = request.POST['first_name'],
                last_name = request.POST['last_name'])
        except:
            messages.error(request, 'There was an error creating your account. Please try again.')
            return HttpResponseRedirect('/register?key=%s'%request.GET.get('key'))
        else:
            registants[0].delete()

        messages.info(request, 'Your account was succefully created. Please login.')
        return HttpResponseRedirect('/')

@login_required
def send_registration(request):
    if request.method == 'POST':
        emails = request.POST.get("emails")
        if emails == None:
            messages.error(request, 'No valid emails.')
        emails = emails.split('\n')
        host = request.get_host()

        url = "%s://%s/register?key=%%s"%(
            request.scheme,
            request.get_host(),
            )

        emails_to_send = list()
        for email in emails:
            if '@' in email:
                if len(Registration.objects.filter(email = email)) <= 0:
                    key = os.urandom(33)
                    key_hash = hashlib.sha512(key).digest()
                    key = base64.urlsafe_b64encode(key)
                    user_url = url % key.decode('utf-8')
                    Registration(email = email, key_hash = key_hash).save()

                    msg = '''Hello,
                    You've reviced an invitation to join Netsville's Time Tracker. Please click the link to registrator:
                    
                    %s
                    '''%(user_url)
                     
                    emails_to_send.append((
                        'Time Tracker Registration', #Subject
                        msg,                         #Message
                        'noreply@netsville.com',     #From address
                        [email]))                    #To address
                else:
                    messages.error(request, 'An invitation has already been sent to \'%s\'.' % email)
            else:
                 messages.error(request, '\'%s\' is an invalid email.'% email)

        successfully_delivered = 0
        if len(emails_to_send) > 0: 
            #try:
            successfully_delivered = send_mass_mail(emails_to_send)
            #except:
            #    messages.error(request, 'There was an error sending emails')
            messages.info(request, '%d/%d emails were succfully sent.'%(successfully_delivered, len(emails_to_send)))
        else:
            messages.error(request, 'No emails were succfully valided and therefore there was no attemp to send email.') 
    return render(request, 'send_registration.html')
    
