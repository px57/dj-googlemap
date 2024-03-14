
import mailchimp_transactional as MailchimpTransactional

from kernel.interfaces.service import ServiceManager

class Service(ServiceManager):
    def __init__(self):
        pass

    def init(self):
        """
        The constructor method.
        """


    def send_mail(self, *args, **kwargs):
        """
        Send mail method.
        """
        print (args)
        print (kwargs)