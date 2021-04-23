import pyotp
import logging
from datetime import datetime, timedelta
from datetime import date

from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.db import IntegrityError, models, transaction

from model_utils.models import TimeStampedModel

log = logging.getLogger(__name__)


class OTPManagement(TimeStampedModel):
    """
    Manage otp for reset password
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    status = models.CharField(max_length=30, choices=(
        ('unused', _(u'Unused')),
        ('used', _(u'Used')),
        ('verified', _(u'Verfied')),
        ('expired', _(u'expired')),
    ))
    secret = models.CharField(max_length=40, help_text='Secret key used for veryfying otp')

    class Meta:
        unique_together = ('otp', 'status', 'secret')

    @classmethod
    def check_previous_otp(cls, user):
        """
        Return True if previous otp generated in 30 seconds before
        """
        now = datetime.now()
        earlier = now - timedelta(seconds=30)
        results = cls.objects.filter(user=user, status='unused', created__range=(earlier, now))
        if results.exists():
            return True
        return False

    @classmethod
    def save_otp(cls, user):
        self = cls()
        otp, secret = self.create_otp()
        try:
            cls.objects.get_or_create(
                user=user,
                otp=otp,
                secret=secret,
                status='unused'
            )
            log.info("Current OTP: {}".format(otp))
            log.info("Otp saved for user: {}".format(user.username))
            return otp
        except Exception as error:
            log.error("Error while saving otp. The error is {}".format(str(error)))
            return None

    @classmethod
    def verify_otp(cls, otp, mobile_number):
        obj = cls.get_obj(otp, mobile_number)
        self = cls()
        if not obj:
            return None
        try:
            otp_obj = self.get_otp_object(obj.secret)
            if otp_obj.verify(otp, valid_window=1):
                obj.status = 'verified'
                obj.save()
                log.info("OTP {} status changed to verified".format(otp))
                return True
            return False
        except Exception as error:
            log.error("Error while verifying OTP. The error is {}".format(str(error)))
            return None

    @classmethod
    def is_valid_otp(cls, otp, mobile_number):
        try:
            obj = cls.objects.get(otp=otp)
            if obj.user.extrafields.phone == mobile_number:
                obj.status = 'used'
                log.info("OTP {} status changed to used".format(otp))
                obj.save()
                return obj, True
            return None, False
        except Exception as error:
            log.info("Error while validating OTP. The error is {}".format(str(error)))
            return None, False

    @classmethod
    def get_obj(cls, otp, mobile_number):
        """
        Returns otp
        """
        try:
            return cls.objects.get(Q(user__extrafields__phone=mobile_number, otp=otp) | Q(user__email=mobile_number, otp=otp))
        except Exception as e:
            return None

    def get_new_secret(cls):
        """
        Returns secret key
        """
        return pyotp.random_base32()

    def get_otp_object(self, secret):
        """
        Creates new OTP
        """
        time_based_otp = pyotp.TOTP(secret, interval=70)
        return time_based_otp

    def create_otp(self):
        secret = self.get_new_secret()
        obj = self.get_otp_object(secret)
        return obj.now(), secret

