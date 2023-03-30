from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required


@login_required
def course_chat_room(request, course_id):
    try:
        # pobierz kurs o podanym id, do którego jest zapisany bieżący użytkownik
        course = request.user.courses_joined.get(id=course_id)
    except:
        # pobierz kurs o podanym id, do którego jest zapisany bieżący użytkownik
        return HttpResponseForbidden()
    return render(request, 'chat/room.html', {'course': course})
