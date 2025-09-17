from rest_framework import permissions
from django.utils import timezone
from datetime import timedelta

class CanManageAppointment(permissions.BasePermission):
    """
    Custom permission to manage appointments.
    - Clients can only create and view their own appointments
    - Barbers can view and update their appointments
    - Barbershop owners can manage all appointments in their barbershop
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Allow read access to owners and involved parties
        if request.method in permissions.SAFE_METHODS:
            return (user.is_staff or
                    user == obj.customer.customer or
                    user == obj.barber or
                    user == obj.barbershop.owner)
        
        # Only allow updates if the appointment is not in the past
        if obj.start_datetime < timezone.now():
            return False
            
        # Allow modification based on role
        if user.role == 'CLIENT':
            # Clients can only cancel their own appointments
            return (user == obj.customer.customer and
                    request.method == 'PATCH' and
                    request.data.get('status') == 'CANCELLED')
        elif user.role == 'BARBER':
            # Barbers can update status of their appointments
            return user == obj.barber
        elif user.role == 'OWNER':
            # Owners can manage all appointments in their barbershop
            return user == obj.barbershop.owner
            
        return False

def check_barber_availability(barber, barbershop, start_datetime, end_datetime):
    """
    Check if a barber is available for a given time slot.
    """
    from apps.appointments.models import Appointment, BarberSchedule
    
    # Check if the time falls within the barber's schedule
    weekday = start_datetime.weekday()
    schedule = BarberSchedule.objects.filter(
        barber=barber,
        barbershop=barbershop,
        weekday=weekday,
        is_available=True
    ).first()
    
    if not schedule:
        return False, "Barber is not scheduled for this day"
    
    # Check if the appointment falls within the schedule
    if (start_datetime.time() < schedule.start_time or
            end_datetime.time() > schedule.end_time):
        return False, "Appointment time is outside barber's working hours"
    
    # Check for overlapping appointments
    overlapping = Appointment.objects.filter(
        barber=barber,
        start_datetime__lt=end_datetime,
        end_datetime__gt=start_datetime,
        status__in=['PENDING', 'CONFIRMED']
    ).exists()
    
    if overlapping:
        return False, "Time slot conflicts with another appointment"
    
    return True, "Time slot is available"