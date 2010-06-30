import logging
log = logging.getLogger("MailDataManager")

def catchAllExceptions(func):
    def _(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log.exception(e)
    return _


def applyPatches():
    from Products.MailHost.mailer import SMTPMailer
    old_mailer = getattr(SMTPMailer, 'vote', None) is None
    if old_mailer:
        SMTPMailer.send = catchAllExceptions(SMTPMailer.send)