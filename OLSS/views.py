from django.shortcuts import render, redirect, get_object_or_404
from .forms import LoginForm, PasswordResetForm, ResultForm, EditProfileForm, BookForm, DocumentForm, TimelineForm
from .models import Student, NoticeBoard, Attendance, ExamSchedule, Homework, HomeworkSubmission, ClassTimeTable, Result, Subject, Bus, Stoppage, Book, Activity, Certificate, Document, Timeline
from django.contrib import messages
import random
from django.core.mail import send_mail
from datetime import date
from .utils import student_login_required
from .models import Hostel
from django.http import JsonResponse
from django.utils import timezone


def register(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        dob = request.POST.get('dob', '').strip()
        gender = request.POST.get('gender', '').strip()
        password = request.POST.get('password', '').strip()
        photo = request.FILES.get('photo')
        if not all([name, email, phone_number, dob, gender, password]):
            messages.error(request, 'Please fill all the required fields.')
            return render(request, 'register.html')
        if Student.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered!')
            return render(request, 'register.html')
        if Student.objects.filter(phone_number=phone_number).exists():
            messages.error(request, 'This phone_number is already registered!')
            return render(request, 'register.html')
        student = Student(
            name=name,
            email=email,
            phone_number=phone_number,
            gender=gender,
            dob=dob,
            password=password,
            photo=photo
        )
        student.save()
        messages.success(request, 'Registration successful! You can now log in.')
        return redirect('login')
    return render(request, 'register.html')

def student_login(request):
    if request.session.get('student_id'):
        return redirect('home1')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                student = Student.objects.get(email=email, password=password)
                request.session['student_id'] = student.id
                return redirect('home1')
            except Student.DoesNotExist:
                return render(request, 'login.html', {'form': form, 'error': 'Email or Password is Wrong!'})
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout(request):
    try:
        del request.session['student_id']
    except KeyError:
        pass
    return redirect('home')

def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            dob = form.cleaned_data['dob']
            try:
                student = Student.objects.get(email=email, dob=dob)
                temp_password = str(random.randint(100000, 999999))
                student.password = temp_password
                student.save()
                send_mail(
                    'Temporary Password',
                    f'Your temporary password is: {temp_password}. Please log in and change your password.',
                    'your_email@example.com',
                    [email],
                    fail_silently=False,
                )
                return render(request, 'password_reset.html',
                              {'form': form, 'success':'A temporary password has been sent to your email.'})
            except Student.DoesNotExist:
                return render(request, 'password_reset.html',
                              {'form': form, 'error': 'Invalid email or date of birth.'})
    else:
        form = PasswordResetForm()
    return render(request, 'password_reset.html', {'form': form})

def change_password(request):
    if request.method == 'POST':
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']
        student_id = request.session.get('student_id')
        if student_id:
            student = Student.objects.get(id=student_id)
            if student.password != old_password:
                messages.error(request, 'Old password does not match.')
                return render(request, 'change_password.html')
            if new_password != confirm_password:
                messages.error(request, 'New password and confirm password do not match.')
                return render(request, 'change_password.html')
            student.password = new_password
            student.save()
            messages.success(request, 'Password changed successfully. Please log in again.')
            return redirect('login')
        else:
            messages.error(request, 'User not logged in.')
            return redirect('login')
    return render(request, 'change_password.html')

def home(request):
    if request.session.get('student_id'):
        return redirect('home1')
    return render(request, 'home.html')
def features(request):
    return render(request, 'features.html')
def demo(request):
    return render(request, 'demo.html')
def works(request):
    return render(request, 'works.html')
def support(request):
    return render(request, 'support.html')

@student_login_required
def base(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('login')
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return redirect('login')
    return render(request, 'base.html', {'student': student})

@student_login_required
def home1(request):
    return render(request, 'home1.html')

@student_login_required
def profile(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('login')
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return redirect('login')
    return render(request, 'profile.html', {'student': student})

def edit_profile(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = EditProfileForm(instance=student)
    return render(request, 'edit_profile.html', {'form': form})

@student_login_required
def time(request):
    selected_class = request.GET.get("class_name")
    if selected_class:
        time = ClassTimeTable.objects.filter(class_name=selected_class).order_by("day", "start_time")
    else:
        time = ClassTimeTable.objects.all().order_by("class_name", "day", "start_time")
    classes = ClassTimeTable.CLASS_CHOICES
    return render(request, "time.html", {
        "time": time,
        "classes": classes,
        "selected_class": selected_class,
    })

@student_login_required
def notices(request):
    notices = NoticeBoard.objects.all()
    return render(request, 'notices.html',{'notices': notices})

@student_login_required
def attendance(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('login')
    student = Student.objects.get(id=student_id)
    if student.is_teacher:
        if request.method == 'POST':
            for s in Student.objects.filter(is_teacher=False):
                status = request.POST.get(f'status_{s.id}', 'Absent')
                att, created = Attendance.objects.get_or_create(student=s, date=date.today())
                att.status = status
                att.save()
            messages.success(request, "Attendance updated successfully!")
        students = Student.objects.filter(is_teacher=False)
        attendance_status_list = []
        for s in students:
            att = Attendance.objects.filter(student=s, date=date.today()).first()
            status = att.status if att else 'Absent'
            attendance_status_list.append((s, status))
        return render(request, 'attendance_teacher.html', {
            'attendance_status_list': attendance_status_list,
            'today_date': date.today()
        })
    else:
        attendance_list = Attendance.objects.filter(student=student)
        attendance_by_date = {a.date: a.status for a in attendance_list}
        return render(request, 'attendance_student.html', {
            'attendance_by_date': attendance_by_date,
            'today_date': date.today()
        })

@student_login_required
def homework(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('login')
    student = Student.objects.get(id=student_id)
    if request.method == "POST":
        if student.is_teacher:
            title = request.POST.get("title")
            subject = request.POST.get("subject")
            description = request.POST.get("description")
            deadline = request.POST.get("deadline")
            file = request.FILES.get("file")
            Homework.objects.create(
                teacher=student,
                title=title,
                subject=subject,
                description=description,
                deadline=deadline,
                file=file
            )
        else:
            homework_id = request.POST.get("homework_id")
            homework = Homework.objects.get(id=homework_id)
            answer_text = request.POST.get("answer_text")
            answer_file = request.FILES.get("answer_file")
            HomeworkSubmission.objects.create(
                homework=homework,
                student=student,
                answer_text=answer_text,
                answer_file=answer_file
            )
        return redirect("homework")
    homeworks = Homework.objects.all().order_by("-created_at")
    homework_data = []
    for hw in homeworks:
        submissions = hw.submissions.all() if student.is_teacher else None
        is_submitted = hw.submissions.filter(student=student).exists() if not student.is_teacher else None
        homework_data.append({
            "homework": hw,
            "submissions": submissions,
            "is_submitted": is_submitted
        })
    return render(request, "homework.html", {
        "homework_data": homework_data,
        "student": student
    })

@student_login_required
def exam(request):
    schedules = ExamSchedule.objects.all().order_by("class_name", "day", "start_time")
    return render(request, "exam.html", {"schedules": schedules})

@student_login_required
def results(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('login')
    student = Student.objects.get(id=student_id)
    if student.is_teacher:
        if request.method == "POST":
            form = ResultForm(request.POST)
            if form.is_valid():
                result = form.save(commit=False)
                result.teacher = student
                result.save()
                return redirect("results")
        else:
            form = ResultForm()
        results = Result.objects.all().order_by('-id')
        return render(request, "results.html", {
            "form": form,
            "student": student,
            "results": results,
        })
    else:
        results = student.results.all()
        return render(request, "results.html", {
            "results": results,
            "student": student
        })

@student_login_required
def subject(request):
    subjects = Subject.objects.all()
    context = {
        'subjects': subjects
    }
    return render(request, 'subject.html', context)

@student_login_required
def teacher(request):
    teachers = Student.objects.filter(is_teacher=True)
    context = {
        'teachers': teachers
    }
    return render(request, 'teacher.html', context)

@student_login_required
def bus(request):
    query = request.GET.get("q")
    buses = Bus.objects.prefetch_related("stoppages").all()
    if query:
        buses = buses.filter(stoppages__stoppage_name__icontains=query).distinct()
    return render(request, "bus.html", {"buses": buses, "query": query})

@student_login_required
def seating(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('student_login')

    student = get_object_or_404(Student, id=student_id)
    return render(request, 'seating.html', {'student': student})

@student_login_required
def library(request):
    return render(request, 'libary.html')
@student_login_required
def hostel_list(request):
    hostels = Hostel.objects.prefetch_related('rooms').all()
    return render(request, 'hostel.html', {'hostels': hostels})

@student_login_required
def about(request):
    return render(request, 'about.html')

@student_login_required
def fees(request):
    return render(request, 'fees.html')

@student_login_required
def library(request):
    books = Book.objects.all().order_by("book_class", "subject", "title")
    form = None
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('login')
    student = Student.objects.get(id=student_id)
    if student.is_librarian:
        if request.method == "POST":
            if "add_book" in request.POST:
                form = BookForm(request.POST)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Book added successfully!")
                    return redirect("library")
            elif "edit_book" in request.POST:
                book_id = request.POST.get("book_id")
                book = get_object_or_404(Book, id=book_id)
                form = BookForm(request.POST, instance=book)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Book updated successfully!")
                    return redirect("library")
            elif "delete_book" in request.POST:
                book_id = request.POST.get("book_id")
                book = get_object_or_404(Book, id=book_id)
                book.delete()
                messages.success(request, "Book deleted successfully!")
                return redirect("library")
        else:
            form = BookForm()

    return render(request, "library.html", {
        "books": books,
        "form": form,
        "student": student
    })

@student_login_required
def activities_page(request):
    student_id = request.session.get("student_id")
    student = get_object_or_404(Student, id=student_id)
    activities = Activity.objects.filter(student=student)
    return render(request, "activities.html", {"activities": activities, "student": student})
@student_login_required
def certificates_page(request):
    student_id = request.session.get("student_id")
    student = get_object_or_404(Student, id=student_id)
    certificates = Certificate.objects.filter(student=student)
    return render(request, "certificates.html", {"certificates": certificates, "student": student})
@student_login_required
def student_documents(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    documents = student.documents.all()
    form = DocumentForm()
    return render(request, 'documents.html', {
        'student': student,
        'documents': documents,
        'form': form
    })

def add_document(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.student = student
            doc.save()
            return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'errors': form.errors})

def update_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'errors': form.errors})

def delete_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    if request.method == "POST":
        doc.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})



















@student_login_required
def timeline(request):
    if request.method == 'POST':
        form = TimelineForm(request.POST, request.FILES)
        if form.is_valid():
            status = form.save(commit=False)
            student_id = request.session.get('student_id')
            if student_id:
                student = Student.objects.get(id=student_id)
                status.student = student
                status.save()
                messages.success(request, 'Post uploaded successfully.')
                return redirect('timeline')
            else:
                messages.error(request, 'You are not logged in.')
                return redirect('timeline')
    else:
        form = TimelineForm()

    statuses = Timeline.objects.all().order_by('-timestamp')

    # Detect file type for template
    for s in statuses:
        if s.content:
            ext = s.content.name.split('.')[-1].lower()
            s.is_image = ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
            s.is_video = ext in ['mp4', 'mov', 'avi', 'mkv', 'webm']
        else:
            s.is_image = False
            s.is_video = False

    return render(request, 'timeline.html', {'statuses': statuses, 'form': form})


@student_login_required
def delete_timeline(request, status_id):
    timeline_obj = get_object_or_404(Timeline, id=status_id)
    student_id = request.session.get('student_id')
    if student_id and timeline_obj.student.id == student_id:
        timeline_obj.delete()
        messages.success(request, 'The timeline has been deleted.')
    else:
        messages.error(request, 'You do not have permission to delete this timeline.')
    return redirect('timeline')
