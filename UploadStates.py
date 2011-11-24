# -*- encoding: utf-8 -*-
import upload, logging, traceback, sys, os
import logging.config
from logging.handlers import RotatingFileHandler
from selenium.common.exceptions import ElementNotVisibleException, NoSuchElementException

DEBUG = True
REUPLOAD_LIMIT = 5

# logger configuring
logging.config.fileConfig('log.conf')
base_logger = logging.getLogger('base')
traceback_logger = logging.getLogger('traceback')

class UploadState:
    def __init__(self, uploader):
        self.uploader = uploader
        
    def run(self):
        pass

    def safe_run(self):
        if DEBUG:
            self.run()
        else:
            try:
                self.run()
            except ElementNotVisibleException, NoSuchElementException:
                base_logger.error("selenium error", extra={ "apk_filename" : self.uploader.apk_path,
                                                            "error_type"   : "SELENIUM" })
                traceback_logger.critical(traceback.format_exc(), extra={ "apk_filename" : self.uploader.apk_path })
                self.uploader.get_applist_page()
            except :
                base_logger.critical("python error", extra={ "apk_filename" : self.uploader.apk_path,
                                                             "error_type"   : "CRITICAL" })
                traceback_logger.critical(traceback.format_exc(), extra={ "apk_filename" : self.uploader.apk_path })
                self.uploader.get_applist_page()

class LoginState(UploadState):
    def __init__(self, uploader):
        UploadState.__init__(self, uploader)

    def run(self):
        self.uploader.login()
        self.uploader.wait_for_applist_page()

        # change state
        self.uploader.currentState = self.uploader.applistState

class ApplistState(UploadState):
    def __init__(self, uploader):
        UploadState.__init__(self, uploader)

    def run(self):
        self.uploader.app_upload_click()
        self.uploader.wait_for_apk_input()

        # change state
        self.uploader.currentState = self.uploader.appUploadState
        self.uploader.next()

class AppUploadState(UploadState):
    def __init__(self, uploader):
        UploadState.__init__(self, uploader)
        self.upload_code_table = { upload.APK_REUPLOAD : self.uploader.reuploadState,
                                   upload.APK_SUCCESS  : self.uploader.successState,
                                   upload.APK_LIMIT    : self.uploader.limitState,
                                   upload.APK_SAME     : self.uploader.sameAppState,
                                   upload.APK_NEXT     : self.uploader.nextState,
                                   }

    def run(self):
        upload_code = self.uploader.upload_apk()
        self.uploader.wait_for_upload_apk()
        self.uploader.currentState = self.upload_code_table[upload_code]
        self.uploader.next()

class ReuploadState(UploadState):
    def __init__(self, uploader):
        UploadState.__init__(self, uploader)
        self.last_apk_filename = None
        self.last_apk_count = 0

    def run(self):
        if self.last_apk_filename == self.uploader.apk_path:
            self.last_apk_count += 1
        else:
            self.last_apk_filename = self.uploader.apk_path
            self.last_apk_count = 0

        # 횟수 제한
        if last_apk_count > REUPLOAD_LIMIT:
            base_logger.info("limit exceeded(upload failed)", extra={ "apk_filename" : self.uploader.apk_path,
                                                                      "error_type"   : "REUPLOAD" })
        else :
            base_logger.info("reupload", extra={ "apk_filename" : self.uploader.apk_path,
                                                 "error_type"   : "REUPLOAD" })
            self.uploader.currentState = self.uploader.appUploadState
            self.uploader.next()

class SuccessState(UploadState):
    def __init__(self, uploader):
        UploadState.__init__(self, uploader)

    def run(self):
        self.uploader.upload_capture()
        self.uploader.upload_icon()
        self.uploader.save()
        self.uploader.upload_language()
        self.uploader.upload_detail_text()
        self.uploader.upload_type_category()
        self.uploader.upload_contents_level()
        self.uploader.upload_contact_agree()
        self.uploader.save()
        if !DEBUG:
            self.uploader.publish()
        base_logger.info("upload complete", extra={ "apk_filename" : self.uploader.apk_path,
                                                    "error_type"   : "SUCCESS" })

        if DEBUG:
            self.uploader.currentState = self.uploader.removeState
            self.uploader.next()
        else:
            self.uploader.get_applist_page()

class LimitState(UploadState):
    def __init__(self, uploader):
        UploadState.__init__(self, uploader)

    def run(self):
        base_logger.info("limit exceeded", extra={ "apk_filename" : self.uploader.apk_path,
                                                   "error_type"   : "LIMIT" })
        if !DEBUG:
            # self.uploader.get_applist_page()
            # self.uploader.close()
            pass

class SameAppState(UploadState):
    def __init__(self, uploader):
        UploadState.__init__(self, uploader)

    def run(self):
        base_logger.warning("pass apk(same apk exists)", extra={ "apk_filename" : self.uploader.apk_path,
                                                                 "error_type"   : "SAME" })
        if !DEBUG:
            self.uploader.get_applist_page()

class NextState(UploadState):
    def __init__(self, uploader):
        UploadState.__init__(self, uploader)

    def run(self):
        base_logger.warning("pass apk, anonymous - (%s)" % (self.uploader.anonymous_error),
                            extra={ "apk_filename" : self.uploader.apk_path,
                                    "error_type"   : "NEXT" })
        if !DEBUG:
            self.uploader.get_applist_page()

class RemoveState(UploadState):
    def __init__(self, uploader):
        UploadState.__init__(self, uploader)

    def run(self):
        self.uploader.move_to_apk_tab()
        self.uploader.remove_apk()
        self.uploader.get_applist_page()


# if __name__ == "__main__":
#     try:
#         a = [1]
#         a[3]
#     except:
#         base_logger.error("selenium error", extra={ "apk_filename" : "apk123",
#                                                     "error_type"   : "SELENIUM" })
#         traceback_logger.critical(traceback.format_exc(), extra={ "apk_filename" : "apk123" })
        
