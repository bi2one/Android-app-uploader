# -*- encoding: utf-8 -*-
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from UploadStates import *
import time

username = 'mobitle@mobitle.com'
password = 'mobitle007'

contents_levels = {
    "high" : "gwt-debug-content_rating_level_4-input",
    "mid"  : "gwt-debug-content_rating_level_3-input",
    "low"  : "gwt-debug-content_rating_level_2-input",
    }

supported_languages = {
    "en" : "BASIC",
    "ko" : "ko_KR",
    "fr" : "fr_FR",
    "de" : "de_DE",
    "it" : "it_IT",
    "es" : "es_ES",
    "nl" : "nl_NL",
    "pl" : "pl_PL",
    "cs" : "cs_CZ",
    "pt" : "pt_PT",
    "zh-TW" : "zh_TW",
    "ja" : "ja_JP",
    "ru" : "ru_RU",
    "sv" : "sv_SE",
    "no" : "no_NO",
    "da" : "da_DK",
    "hi" : "hi_IN",
    "iw" : "iw_IL",
    "fi" : "fi_FI",
    }

# defining error types
APK_REUPLOAD, APK_SUCCESS, APK_LIMIT, APK_NEXT, APK_SAME = range(5)
uploader_apk_errors = {
    "same package name" : APK_SAME,
    "Try again" : APK_REUPLOAD,
    u"잠시후 다시" : APK_REUPLOAD,
    u"업로드 한도에 도달했습니다." : APK_LIMIT,
    }

class AndroidUploader(webdriver.Chrome) :
    def __init__(self, username, password) :
        webdriver.Chrome.__init__(self)
        self.get("https://accounts.google.com/ServiceLogin?service=androiddeveloper&passive=true&nui=1&continue=https://market.android.com/publish&followup=https://market.android.com/publish")
        
        self.username = username
        self.password = password
        
        # state initialization
        self.loginState = LoginState(self)
        self.applistState = ApplistState(self)
        self.reuploadState = ReuploadState(self)
        self.successState = SuccessState(self)
        self.limitState = LimitState(self)
        self.sameAppState = SameAppState(self)
        self.nextState = NextState(self)
        self.appUploadState = AppUploadState(self)
        self.removeState = RemoveState(self)

        # base information
        self.feed_data("", [], "", [], 0, 0, "low", "", "")

        # base state
        self.currentState = self.loginState
        # run state
        self.next()

    def feed_data(self, apk_path, image_paths, icon_path, language_elements, app_type, category, contents_level, website, email):
        self.apk_path = apk_path
        self.image_paths = image_paths
        self.icon_path = icon_path
        self.language_elements = language_elements
        self.app_type = app_type
        self.category = category
        self.contents_level = contents_level
        self.website = website
        self.email = email
        self.anonymous_error = None

    def start(self):
        # start from ApplistState
        self.currentState = self.applistState
        self.next()

    def upload(self, apk_path, image_paths, icon_path, language_elements, app_type, category, contents_level, website, email):
        self.feed_data(apk_path, image_paths, icon_path, language_elements, app_type, category, contents_level, website, email)
        self.start()
        
    def next(self):
        self.currentState.safe_run()
        
    def login(self):
        username_input = self.find_element_by_name("Email")
        passwd_input = self.find_element_by_name("Passwd")

        username_input.send_keys(self.username)
        passwd_input.send_keys(self.password)
        passwd_input.send_keys('\n')

    def upload_apk(self):
        try:
            error_div = self.find_element_by_class_name("errorbox-messages").find_element_by_class_name("gwt-HTML")
            behaviors = [behavior for error, behavior in uploader_apk_errors.iteritems() if error in error_div.text]
            self.anonymous_error = error_div.text
            
            if len(behaviors) != 0:
                return behaviors[0]
            else:
                return APK_NEXT
        except NoSuchElementException:
            pass
            
        self.find_element_by_name("Filedata").send_keys(self.apk_path)
        self.find_element_by_id("gwt-debug-app_editor-apk-upload-upload_button").click()

        time.sleep(2)
        try:
            # success
            save_btn = self.find_element_by_id("gwt-debug-bundle_upload-save_button")
            if save_btn.is_displayed():
                save_btn.click()
                return APK_SUCCESS
        except NoSuchElementException:
            # failed
            error_div = self.find_element_by_id("gwt-debug-app_editor-apk-upload-errorBox").find_element_by_class_name("gwt-HTML")
            behaviors = [behavior for error, behavior in uploader_apk_errors.iteritems() if error in error_div.text]

            if len(behaviors) != 0:
                return behaviors[0]
            self.anonymous_error = error_div.text
            
        return APK_NEXT
            
    def app_upload_click(self):
        self.find_element_by_id("gwt-debug-applistinguploadHyperlink").click()

    def wait_for_apk_input(self):
        self.wait_for_name("Filedata")
        
    def wait_for_name(self, name):
        while True:
            try:
                return self.find_element_by_name(name)
            except NoSuchElementException, err:
                continue

    def wait_for_id(self, id):
        while True:
            try:
                return self.find_element_by_id(id)
            except NoSuchElementException, err:
                continue

    def clear_text_input(self, element):
        element.send_keys("\b" * 40)

    def save(self):
        time.sleep(1)
        save_button = self.find_element_by_id("gwt-debug-multiple_apk-save_button")
        save_button.click()
        
        while "..." in save_button.text:
            pass

    def publish(self):
        time.sleep(1)
        self.find_element_by_id("gwt-debug-multiple_apk-publish_button").click()

    def wait_for_upload_apk(self):
        time.sleep(2)

    def wait_for_applist_page(self):
        load_status = self.wait_for_id("gwt-debug-applistinglistLoadStatus")
        while load_status.is_displayed():
            pass
        
    def get_applist_page(self):
        self.get("https://market.android.com/publish/Home")
        self.wait_for_applist_page()
        
    def upload_contact_agree(self):
        website_input = self.find_element_by_id("gwt-debug-website")
        email_input = self.find_element_by_id("gwt-debug-email")

        # clear fields
        self.clear_text_input(website_input)
        self.clear_text_input(email_input)
        
        website_input.send_keys(self.website)
        email_input.send_keys(self.email)

        # agree
        self.find_element_by_id("gwt-debug-meets_guidelines-input").click()
        self.find_element_by_id("gwt-debug-export_laws-input").click()
        
    def upload_contents_level(self) :
        self.find_element_by_id(contents_levels[self.contents_level]).click()
        
    def upload_type_category(self):
        # type
        uploader.find_element_by_id("gwt-debug-type").find_elements_by_tag_name("option")[self.app_type].click()
        # category
        uploader.find_element_by_id("gwt-debug-app_categories").find_elements_by_tag_name("option")[self.category].click()

    def upload_detail_text(self):
        for language in self.language_elements:
            # TODO: language마다 상단 tabbar를 클릭해야 함
            title = self.find_element_by_id("gwt-debug-app_editor-locale-title-text_box")
            title.send_keys(language.title)

            description = self.find_element_by_id("gwt-debug-app_editor-locale-description-text_area")
            description.send_keys(language.description)

    def upload_language(self):
        time.sleep(1)
        languages = [x.language for x in self.language_elements]
        basic_lang = [lang for lang, lang_name in supported_languages.iteritems() if lang_name == "BASIC"][0]

        add_lang_button = self.find_element_by_id("gwt-debug-add_language_link")
        add_lang_button.click()
        time.sleep(1)
        
        for language in languages:
            if (language == basic_lang):
                continue
            
            lang_name = supported_languages[language]
            lang_name_input = self.find_element_by_name(lang_name)
            lang_name_input.click()
            time.sleep(1)

        submit = self.find_element_by_id("gwt-debug-add_language_ok")
        submit.click()
        
        if basic_lang not in languages:
            time.sleep(1)
            basic_removal_button = self.find_element_by_class_name("close")
            basic_removal_button.click()

    def move_to_apk_tab(self):
        self.find_element_by_id("gwt-debug-multiple_apk-apk_list_tab").click()
        time.sleep(1)
        
    def remove_apk(self):
        self.find_element_by_id("gwt-debug-apk_list-delete_link-4").click()
        time.sleep(2)

    def upload_icon(self):
        time.sleep(2)
        icon_input = self.find_element_by_id("gwt-debug-app_editor-hi_res_icon-upload_form-upload_box")
        icon_input.send_keys(self.icon_path)

        # submit
        self.find_element_by_id("gwt-debug-app_editor-hi_res_icon-upload_form-upload_button").click()

    def upload_capture(self):
        for path_index in range(len(self.image_paths)):
            time.sleep(2)
            if path_index != 0 :
                more_capture_btn = self.find_element_by_id("gwt-debug-app_editor-screen_shot-add_another_link")
                more_capture_btn.click()
            
            capture_input = self.find_element_by_id("gwt-debug-app_editor-screen_shot-upload_form-upload_box")
            capture_input.send_keys(self.image_paths[path_index])
            
            capture_submit = self.find_element_by_id("gwt-debug-app_editor-screen_shot-upload_form-upload_button")
            capture_submit.click()

class LanguageElement:
    def __init__(self, language, title, description):
        self.language = language
        self.title = title
        self.description = description

if __name__ == '__main__' :
    uploader = AndroidUploader(username, password)
    koElement = LanguageElement("ko", "ko title", "ko description")

    uploader.upload("/Users/bi2one/Desktop/packages/mobitle603.apk",
                    ["/Users/bi2one/Desktop/packages/screenshots/602_1.png",
                     "/Users/bi2one/Desktop/packages/screenshots/602_1.png"],
                    "/Users/bi2one/Desktop/images/icon/610.png",
                    [koElement],
                    1,
                    6,
                    "low",
                    "http://mobitle.com",
                    "mobitle@mobitle.com",
                    )
