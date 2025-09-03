from .models import Student

def student(request):
    student_id = request.session.get('student_id')
    if student_id:
        try:
            student = Student.objects.get(id=student_id)
            return {'student': student}
        except Student.DoesNotExist:
            pass
    return {'student': None}
