import os
import time
import random
import sys
import traceback
import hashlib # For enhanced security
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFillRoundFlatButton, MDFlatButton
from kivymd.uix.slider import MDSlider
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.fitimage import FitImage
from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivy.uix.modalview import ModalView
from kivy.utils import platform
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore 

# --- 1. SYSTEM STABILITY & CRASH HANDLER ---
# యాప్ ఎప్పుడైనా క్రాష్ అయితే, అది ఎందుకు జరిగిందో ఒక ఫైల్ లో రాస్తుంది.
# దీనివల్ల యూజర్ కి వెంటనే తెలియకపోయినా, డెవలపర్ కి ఉపయోగపడుతుంది.
def global_exception_handler(ex_type, ex_value, ex_traceback):
    error_msg = "".join(traceback.format_exception(ex_type, ex_value, ex_traceback))
    print(f"CRASH LOG: {error_msg}")
    try:
        # Saving log to internal storage for safety
        log_path = "/storage/emulated/0/PrasadApp/crash_log.txt"
        with open(log_path, "w") as f:
            f.write(error_msg)
    except:
        pass

sys.excepthook = global_exception_handler

# బ్లాక్ స్క్రీన్ తో స్టార్ట్ అయితే గ్లిచ్ లు కనిపించవు
Window.clearcolor = (0, 0, 0, 1)

# --- 2. ADVANCED SPATIAL AUDIO ENGINE ---
class NativeAudioPlayer:
    def __init__(self):
        self.player = None
        self.equalizer = None
        self.virtualizer = None 
        self.bass_boost = None
        self.is_prepared = False
        self.session_id = 0
        self.device_optimized = False
        
        # ఆండ్రాయిడ్ నేటివ్ లైబ్రరీలను లోడ్ చేయడం
        if platform == 'android':
            try:
                from jnius import autoclass
                self.MediaPlayer = autoclass('android.media.MediaPlayer')
                self.AudioEffect = autoclass('android.media.audiofx.AudioEffect')
                self.Equalizer = autoclass('android.media.audiofx.Equalizer')
                self.Virtualizer = autoclass('android.media.audiofx.Virtualizer')
                self.BassBoost = autoclass('android.media.audiofx.BassBoost')
                self.player = self.MediaPlayer()
                self.device_optimized = True
            except Exception as e:
                print(f"Audio Engine Warning: {str(e)}")

    def load(self, path):
        """ మ్యూజిక్ ఫైల్ ని లోడ్ చేసి ప్లే చేయడానికి సిద్ధం చేస్తుంది """
        if self.player:
            try:
                self.release_effects()
                self.player.reset()
                self.player.setDataSource(path)
                self.player.prepare()
                self.is_prepared = True
                self.session_id = self.player.getAudioSessionId()
                self.setup_effects()
            except Exception as e:
                self.is_prepared = False
                print(f"Load Error: {str(e)}")

    def setup_effects(self):
        """ 3D ఆడియో ఎఫెక్ట్స్ ని హార్డ్ వేర్ లెవల్ లో సెట్ చేస్తుంది """
        if platform == 'android' and self.player:
            try:
                self.equalizer = self.Equalizer(0, self.session_id)
                self.equalizer.setEnabled(True)
                
                self.virtualizer = self.Virtualizer(0, self.session_id)
                self.virtualizer.setEnabled(False)
                
                self.bass_boost = self.BassBoost(0, self.session_id)
                self.bass_boost.setEnabled(False)
            except: pass

    def release_effects(self):
        """ పాత ఎఫెక్ట్స్ ని మెమరీ నుండి తొలగిస్తుంది """
        try:
            if self.equalizer: self.equalizer.release()
            if self.virtualizer: self.virtualizer.release()
            if self.bass_boost: self.bass_boost.release()
        except: pass

    def toggle_spatial_audio(self, state):
        """ 9.1 వర్చువల్ సరౌండ్ సౌండ్ ని ఆన్/ఆఫ్ చేస్తుంది """
        if not self.virtualizer: self.setup_effects()
        if self.virtualizer:
            try:
                self.virtualizer.setEnabled(state)
                if state and self.virtualizer.getStrengthSupported():
                    # మాక్సిమం స్ట్రెంత్ (1000) ఇస్తుంది
                    self.virtualizer.setStrength(1000)
                return True
            except: return False
        return False

    def open_system_dolby(self):
        """ ఫోన్ సిస్టమ్ డాల్బీ సెట్టింగ్స్ ఓపెన్ చేస్తుంది """
        if platform == 'android':
            try:
                from jnius import autoclass, cast
                activity = autoclass('org.kivy.android.PythonActivity').mActivity
                Intent = autoclass('android.content.Intent')
                Settings = autoclass('android.provider.Settings')
                intent = Intent(Settings.ACTION_SOUND_SETTINGS)
                activity.startActivity(intent)
                return True
            except: return False
        return False

    def is_complete(self):
        """ పాట పూర్తయ్యిందో లేదో చెక్ చేస్తుంది """
        if self.player and self.is_prepared:
            try:
                pos = self.player.getCurrentPosition()
                dur = self.player.getDuration()
                if dur > 0 and pos >= (dur - 1200):
                    return True
            except: pass
        return False

    # బేసిక్ కంట్రోల్స్ (Play, Pause, Stop, Seek)
    def play(self):
        if self.player and self.is_prepared: self.player.start()
    def pause(self):
        if self.player and self.player.isPlaying(): self.player.pause()
    def stop(self):
        if self.player: self.player.stop(); self.player.reset()
    def seek(self, seconds):
        if self.player and self.is_prepared:
            try: self.player.seekTo(int(seconds * 1000))
            except: pass
    def get_pos(self):
        if self.player and self.is_prepared:
            try: return self.player.getCurrentPosition() / 1000.0
            except: return 0
        return 0
    def get_duration(self):
        if self.player and self.is_prepared:
            try: return self.player.getDuration() / 1000.0
            except: return 0
        return 0
    
    def get_art(self, path, save_path):
        """ పాటలోని ఫోటోను బయటకు తీస్తుంది """
        if platform == 'android':
            try:
                from jnius import autoclass
                retr = autoclass('android.media.MediaMetadataRetriever')()
                retr.setDataSource(path)
                art = retr.getEmbeddedPicture()
                if art:
                    data = bytes([b % 256 for b in art])
                    with open(save_path, 'wb') as f: f.write(data)
                    return True
            except: pass
        return False

# --- 3. COMPLETE UI ARCHITECTURE (KV LANG) ---
KV = '''
#:import NoTransition kivy.uix.screenmanager.NoTransition

# గ్లాస్ ఎఫెక్ట్ కార్డు డిజైన్
<GlassCard@MDCard>:
    orientation: 'vertical'
    padding: "20dp"
    spacing: "15dp"
    radius: [26,]
    md_bg_color: [1, 1, 1, 0.25]
    line_color: [1, 1, 1, 0.45]
    line_width: 1.8
    elevation: 4
    ripple_behavior: True
    
# ఫోల్డర్ ఐటమ్ డిజైన్
<FolderItem@GlassCard>:
    icon: "folder"
    text: "Folder"
    icon_color: [1, 1, 1, 1]
    size_hint_y: None
    height: "150dp"
    MDIcon:
        icon: root.icon
        font_size: "54sp"
        halign: "center"
        theme_text_color: "Custom"
        text_color: root.icon_color
        pos_hint: {"center_x": .5}
    MDLabel:
        text: root.text
        halign: "center"
        bold: True
        theme_text_color: "Custom"
        text_color: [1, 1, 1, 1]
        font_style: "Subtitle1"

# సాంగ్ లిస్ట్ ఐటమ్
<SongListItem>:
    text_color: [1, 1, 1, 1]
    secondary_text_color: [0.9, 0.9, 0.9, 1]
    theme_text_color: "Custom"
    secondary_theme_text_color: "Custom"
    on_release: app.play_song_from_list(root.path)
    IconLeftWidget:
        icon: "music-circle"
        theme_text_color: "Custom"
        text_color: [1, 0.8, 0, 1]

# స్క్రీన్ మేనేజర్
ScreenManager:
    transition: NoTransition()
    
    # --- LOCK SCREEN (SECURITY) ---
    Screen:
        name: 'lock'
        MDFloatLayout:
            md_bg_color: [0, 0, 0, 1] 
            FitImage:
                source: app.wallpaper_path
                opacity: 0.88
                allow_stretch: True
                keep_ratio: False
            
            MDLabel:
                text: "PRASAD'S VAULT PRO"
                halign: "center"
                pos_hint: {"center_x": 0.5, "center_y": 0.84}
                font_style: "H3"
                bold: True
                theme_text_color: "Custom"
                text_color: [1, 1, 1, 1]
                outline_color: [0,0,0,0.6]
                outline_width: 2

            MDTextField:
                id: pin_input
                hint_text: "ENTER SECURITY PIN"
                password: True
                mode: "fill"
                fill_color_normal: [1, 1, 1, 0.18]
                text_color_normal: [1, 1, 1, 1]
                pos_hint: {"center_x": 0.5, "center_y": 0.55}
                size_hint_x: 0.58
                input_filter: "int"
                line_color_focus: [1, 0.8, 0, 1]

            MDBoxLayout:
                orientation: 'horizontal'
                adaptive_size: True
                spacing: "15dp"
                pos_hint: {"center_x": 0.5, "center_y": 0.40}
                
                MDRaisedButton:
                    text: "UNLOCK"
                    md_bg_color: [1, 0.8, 0, 1]
                    text_color: [0, 0, 0, 1]
                    font_size: "18sp"
                    elevation: 10
                    on_release: app.check_pin_logic()
                
                MDFlatButton:
                    text: "Forgot PIN?"
                    theme_text_color: "Custom"
                    text_color: [1, 1, 1, 0.9]
                    font_size: "16sp"
                    on_release: app.show_forgot_pin_dialog()

            MDLabel:
                text: "AUTHENTICATION REQUIRED"
                halign: "center"
                font_style: "Caption"
                bold: True
                theme_text_color: "Custom"
                text_color: [1, 1, 1, 0.55]
                pos_hint: {"center_x": 0.5, "center_y": 0.30}

            # Version Tag
            MDLabel:
                text: "v3.5 (Ultra Max)"
                halign: "center"
                font_style: "Overline"
                theme_text_color: "Custom"
                text_color: [1, 1, 1, 0.3]
                pos_hint: {"center_x": 0.5, "bottom": 1}
                padding: [0, 20]

    # --- MAIN SCREEN ---
    Screen:
        name: 'main'
        MDFloatLayout:
            md_bg_color: [0.04, 0.04, 0.04, 0.6]

            MDBottomNavigation:
                panel_color: [0.08, 0.08, 0.08, 0.98]
                text_color_active: [1, 0.8, 0, 1]

                # --- HOME TAB ---
                MDBottomNavigationItem:
                    name: 'screen_home'
                    text: 'Home'
                    icon: 'home-variant'
                    MDFloatLayout:
                        FitImage:
                            source: app.wallpaper_path
                            opacity: 0.75
                            allow_stretch: True
                            keep_ratio: False
                        
                        MDBoxLayout:
                            orientation: 'vertical'
                            padding: "24dp"
                            spacing: "28dp"
                            
                            MDBoxLayout:
                                orientation: 'horizontal'
                                adaptive_height: True
                                spacing: "10dp"
                                MDLabel:
                                    text: "Welcome back,"
                                    font_style: "H4"
                                    bold: True
                                    theme_text_color: "Custom"
                                    text_color: [1, 1, 1, 1]
                                    adaptive_size: True
                                MDIcon:
                                    icon: "emoticon-happy-outline"
                                    theme_text_color: "Custom"
                                    text_color: [1, 0.8, 0, 1]
                                    font_size: "40sp"
                                    size_hint: None, None
                                    size: "44dp", "44dp"
                                    pos_hint: {"center_y": .5}
                                MDLabel:
                                    text: "Prasad"
                                    font_style: "H4"
                                    bold: True
                                    theme_text_color: "Custom"
                                    text_color: [1, 1, 1, 1]
                                    adaptive_height: True

                            MDLabel:
                                text: "PERSONAL LIBRARIES"
                                font_style: "Overline"
                                theme_text_color: "Custom"
                                text_color: [1, 0.8, 0, 1]
                                adaptive_height: True

                            MDGridLayout:
                                cols: 2
                                spacing: "24dp"
                                size_hint_y: None
                                height: self.minimum_height
                                
                                # Folder 1: Gallery
                                FolderItem:
                                    icon: "image-multiple-outline"
                                    text: "Gallery"
                                    icon_color: [0.2, 0.8, 1, 1]
                                    on_release: app.file_manager_gallery_open()
                                
                                # Folder 2: Music
                                FolderItem:
                                    icon: "music-box-outline"
                                    text: "Music"
                                    icon_color: [1, 0.4, 0.4, 1]
                                    on_release: app.file_manager_open()
                                
                                # Folder 3: Movies
                                FolderItem:
                                    icon: "movie-play-outline"
                                    text: "Movies"
                                    icon_color: [0.4, 0.9, 0.4, 1]
                                    on_release: app.file_manager_video_open()
                                
                                # Folder 4: Documents (Fixed Icon)
                                FolderItem:
                                    icon: "file-document-multiple-outline"
                                    text: "Documents"
                                    icon_color: [1, 0.8, 0.2, 1]
                                    on_release: app.file_manager_docs_open()
                            
                            MDLabel:
                                text: "" 

                # --- MUSIC TAB ---
                MDBottomNavigationItem:
                    name: 'screen_music'
                    text: 'Music'
                    icon: 'music'
                    on_tab_press: app.scan_music()
                    MDFloatLayout:
                        FitImage:
                            source: app.wallpaper_path
                            opacity: 0.55
                            allow_stretch: True
                            keep_ratio: False
                        
                        MDBoxLayout:
                            orientation: 'vertical'
                            
                            # Header with Scan Button
                            MDBoxLayout:
                                size_hint_y: None
                                height: "75dp"
                                padding: "15dp"
                                spacing: "15dp"
                                md_bg_color: [0, 0, 0, 0.4]
                                
                                MDLabel:
                                    text: "Your Tracks"
                                    font_style: "H5"
                                    bold: True
                                    theme_text_color: "Custom"
                                    text_color: [1, 1, 1, 1]
                                    pos_hint: {"center_y": 0.5}
                                    
                                MDRaisedButton:
                                    text: "SCAN DEVICE"
                                    icon: "refresh"
                                    pos_hint: {"center_y": 0.5}
                                    md_bg_color: [1, 0.8, 0, 1]
                                    text_color: [0, 0, 0, 1]
                                    elevation: 6
                                    on_release: app.scan_music()
                                    
                                MDIconButton:
                                    icon: "folder-music"
                                    theme_text_color: "Custom"
                                    text_color: [1, 1, 1, 1]
                                    pos_hint: {"center_y": 0.5}
                                    on_release: app.file_manager_open()

                            RecycleView:
                                viewclass: 'SongListItem'
                                data: app.music_list_data
                                RecycleBoxLayout:
                                    default_size: None, dp(78)
                                    default_size_hint: 1, None
                                    size_hint_y: None
                                    height: self.minimum_height
                                    orientation: 'vertical'
                                    padding: "14dp"

                # --- SETTINGS TAB ---
                MDBottomNavigationItem:
                    name: 'screen_settings'
                    text: 'Settings'
                    icon: 'equalizer'
                    MDFloatLayout:
                        FitImage:
                            source: app.wallpaper_path
                            opacity: 0.55
                            allow_stretch: True
                            keep_ratio: False
                        
                        MDBoxLayout:
                            orientation: 'vertical'
                            padding: "24dp"
                            spacing: "20dp"
                            MDLabel:
                                text: "Professional Audio Engine"
                                font_style: "H4"
                                bold: True
                                theme_text_color: "Custom"
                                text_color: [1, 1, 1, 1]
                                adaptive_height: True
                            
                            GlassCard:
                                size_hint_y: None
                                height: "110dp"
                                orientation: 'horizontal'
                                padding: "20dp"
                                on_release: app.open_system_settings()
                                MDIcon:
                                    icon: "dolby"
                                    theme_text_color: "Custom"
                                    text_color: [1, 1, 1, 1]
                                    font_size: "38sp"
                                    pos_hint: {"center_y": .5}
                                MDBoxLayout:
                                    orientation: 'vertical'
                                    padding: [18, 0]
                                    MDLabel:
                                        text: "Native Dolby Atmos"
                                        bold: True
                                        theme_text_color: "Custom"
                                        text_color: [1, 1, 1, 1]
                                    MDLabel:
                                        text: "Advanced system sound setting"
                                        font_style: "Caption"
                                        theme_text_color: "Custom"
                                        text_color: [1, 1, 1, 0.5]
                            
                            GlassCard:
                                size_hint_y: None
                                height: "110dp"
                                orientation: 'horizontal'
                                padding: "20dp"
                                MDIcon:
                                    icon: "surround-sound-7-1"
                                    theme_text_color: "Custom"
                                    text_color: [1, 1, 1, 1]
                                    font_size: "38sp"
                                    pos_hint: {"center_y": .5}
                                MDBoxLayout:
                                    orientation: 'vertical'
                                    padding: [18, 0]
                                    MDLabel:
                                        text: "Spatial Audio (9.1)"
                                        bold: True
                                        theme_text_color: "Custom"
                                        text_color: [1, 1, 1, 1]
                                    MDLabel:
                                        text: "Hardware layer virtualizer"
                                        font_style: "Caption"
                                        theme_text_color: "Custom"
                                        text_color: [1, 1, 1, 0.5]
                                MDSwitch:
                                    active: False
                                    on_active: app.toggle_surround(*args)
                                    pos_hint: {"center_y": .5}
                            MDLabel:
                                text: "" 

            # MINI PLAYER
            MDCard:
                size_hint: (0.96, None)
                height: "82dp"
                pos_hint: {"center_x": 0.5, "y": 0.1} 
                radius: [20,]
                md_bg_color: [0.12, 0.12, 0.12, 0.96]
                elevation: 8
                opacity: app.mini_player_opacity
                on_release: app.open_full_player()
                MDBoxLayout:
                    padding: "10dp"
                    spacing: "16dp"
                    FitImage:
                        id: mini_art
                        source: app.current_art
                        size_hint: (None, 1)
                        width: "62dp"
                        radius: [14,]
                    MDBoxLayout:
                        orientation: 'vertical'
                        justify_content: 'center'
                        MDLabel:
                            text: app.current_title
                            bold: True
                            theme_text_color: "Custom"
                            text_color: [1, 1, 1, 1]
                            shorten: True
                            font_style: "Subtitle1"
                        MDLabel:
                            text: "Now Playing"
                            font_style: "Caption"
                            theme_text_color: "Custom"
                            text_color: [1, 0.8, 0, 0.8]
                    MDIconButton:
                        icon: "pause-circle" if app.is_playing else "play-circle"
                        theme_text_color: "Custom"
                        text_color: [1, 0.8, 0, 1]
                        icon_size: "48sp"
                        on_release: app.toggle_play()
'''

class SongListItem(TwoLineAvatarIconListItem):
    path = StringProperty()

class PrasadProApp(MDApp):
    music_list_data = ListProperty([])
    current_title = StringProperty("No Track Selected")
    current_art = StringProperty("album_art.jpg") 
    is_playing = BooleanProperty(False)
    mini_player_opacity = NumericProperty(0)
    
    # --- SMART WALLPAPER PATH ---
    # Default is the APK bundled one
    wallpaper_path = StringProperty("wallpaper.jpg") 
    
    current_song_index = -1
    all_songs_list = [] 
    
    # SECURITY STATE
    security_attempts = 0
    SECURITY_QUESTION = "What is your favorite color?"
    SECURITY_ANSWER = "blue"
    
    setup_dialog = None
    forgot_dialog = None
    master_dialog = None
    exit_dialog = None
    
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Amber"
        
        # SECURE STORAGE INIT
        self.store = JsonStore('vault_secrets.json')
        Window.bind(on_keyboard=self.events)
        
        # UNIVERSAL PERMISSIONS
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE, 
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.MODIFY_AUDIO_SETTINGS
            ])
        except: pass
        
        # --- WALLPAPER LOGIC (Hybrid) ---
        # 1. Check custom user folder first
        custom_wp = "/storage/emulated/0/PrasadApp/wallpaper.jpg"
        if os.path.exists(custom_wp):
            self.wallpaper_path = custom_wp
        else:
            # 2. Use bundled asset
            self.wallpaper_path = "wallpaper.jpg"
        
        self.player = NativeAudioPlayer()
        
        # FILE MANAGERS SETUP
        self.fm_music = MDFileManager(exit_manager=self.close_fm, select_path=self.select_path, ext=['.mp3', '.flac', '.m4a'])
        self.fm_video = MDFileManager(exit_manager=self.close_fm_video, select_path=self.select_video, ext=['.mp4', '.mkv', '.avi'])
        self.fm_gallery = MDFileManager(exit_manager=self.close_fm_gallery, select_path=self.select_generic, ext=['.jpg', '.png', '.jpeg'])
        self.fm_docs = MDFileManager(exit_manager=self.close_fm_docs, select_path=self.select_generic, ext=['.pdf', '.txt', '.doc'])
        
        self.fm = self.fm_music
        return Builder.load_string(KV)

    # --- EXIT DIALOG LOGIC ---
    def events(self, instance, keyboard, keycode, text, modifiers):
        if keycode == 27: # Android Back Button
            if self.root.current == 'main':
                self.show_exit_dialog()
                return True
            else:
                return False
        return False

    def show_exit_dialog(self):
        if not self.exit_dialog:
            self.exit_dialog = MDDialog(
                title="Exit Vault?",
                text="Do you want to close Prasad's Vault Pro?",
                buttons=[
                    MDFlatButton(text="CANCEL", on_release=lambda x: self.exit_dialog.dismiss()),
                    MDRaisedButton(text="EXIT", md_bg_color=[1, 0, 0, 1], on_release=self.stop_app)
                ],
            )
        self.exit_dialog.open()

    def stop_app(self, *args):
        try: self.player.stop()
        except: pass
        MDApp.get_running_app().stop()

    def on_start(self):
        if not self.store.exists('security'):
            Clock.schedule_once(lambda x: self.show_setup_popup(), 1)

    # --- SECURITY LOGIC ---
    def show_setup_popup(self):
        if not self.setup_dialog:
            content = MDBoxLayout(orientation='vertical', spacing="12dp", height="200dp", size_hint_y=None)
            self.new_user_pin = MDTextField(hint_text="Create User PIN (4-digits)", input_filter="int", max_text_length=4)
            self.new_master_pin = MDTextField(hint_text="Create Master PIN (Backup)", input_filter="int", max_text_length=4)
            content.add_widget(self.new_user_pin)
            content.add_widget(self.new_master_pin)
            
            self.setup_dialog = MDDialog(
                title="ACTIVATE MASTER PIN",
                text="Welcome! Please set your security codes for the first time.",
                type="custom",
                content_cls=content,
                buttons=[
                    MDRaisedButton(text="ACTIVATE & SAVE", on_release=lambda x: self.save_initial_pins())
                ],
                auto_dismiss=False
            )
        self.setup_dialog.open()

    def save_initial_pins(self):
        u_pin = self.new_user_pin.text
        m_pin = self.new_master_pin.text
        if len(u_pin) == 4 and len(m_pin) == 4:
            self.store.put('security', user_pin=u_pin, master_pin=m_pin)
            self.setup_dialog.dismiss()
            toast("Security Shield Activated!")
        else:
            toast("PINs must be 4 digits!")

    def check_pin_logic(self):
        if not self.store.exists('security'):
            self.show_setup_popup()
            return
        entered_pin = self.root.ids.pin_input.text
        try:
            saved_user_pin = self.store.get('security')['user_pin']
            if entered_pin == saved_user_pin:
                self.root.current = 'main'
                self.security_attempts = 0
                toast("Access Granted")
            else:
                toast("Invalid Security PIN")
        except:
            self.show_setup_popup()

    def show_forgot_pin_dialog(self):
        if not self.store.exists('security'):
            toast("Setup PIN first!")
            return
        if not self.forgot_dialog:
            self.answer_field = MDTextField(hint_text="Enter Answer")
            self.forgot_dialog = MDDialog(
                title="Security Recovery",
                text=f"{self.SECURITY_QUESTION}",
                type="custom",
                content_cls=self.answer_field,
                buttons=[
                    MDFlatButton(text="CANCEL", on_release=lambda x: self.forgot_dialog.dismiss()),
                    MDFlatButton(text="VERIFY", on_release=lambda x: self.verify_security_answer())
                ],
            )
        self.forgot_dialog.open()

    def verify_security_answer(self):
        if self.answer_field.text.lower() == self.SECURITY_ANSWER:
            saved_pin = self.store.get('security')['user_pin']
            toast(f"Verified! Your PIN is {saved_pin}")
            self.forgot_dialog.dismiss()
            self.security_attempts = 0
        else:
            self.security_attempts += 1
            toast(f"Security Alert: Attempt {self.security_attempts}/2")
            if self.security_attempts >= 2:
                self.forgot_dialog.dismiss()
                self.show_master_code_dialog()

    def show_master_code_dialog(self):
        if not self.master_dialog:
            self.master_field = MDTextField(hint_text="Enter Master PIN", input_filter="int")
            self.master_dialog = MDDialog(
                title="MASTER UNLOCK",
                text="Too many failed attempts.\nEnter your Backup Master PIN.",
                type="custom",
                content_cls=self.master_field,
                buttons=[
                    MDRaisedButton(text="FORCE UNLOCK", md_bg_color=[1,0,0,1], on_release=lambda x: self.verify_master_code())
                ],
            )
        self.master_dialog.open()

    def verify_master_code(self):
        saved_master = self.store.get('security')['master_pin']
        if self.master_field.text == saved_master:
            toast("MASTER OVERRIDE ACCEPTED")
            self.master_dialog.dismiss()
            self.root.current = 'main'
            self.security_attempts = 0
        else:
            toast("SECURITY BREACH DETECTED")

    # --- UI SYNC ---
    def on_current_art(self, instance, value):
        try: self.root.ids.mini_art.source = value
        except: pass
        if hasattr(self, 'full_player_bg'): self.full_player_bg.source = value
        if hasattr(self, 'full_player_art'): self.full_player_art.source = value

    # --- SCAN ENGINE (DEEP) ---
    def scan_music(self):
        if len(self.music_list_data) > 0: 
            toast("Library Updated")
            return
        toast("Deep Scanning Device...")
        new_data = []
        self.all_songs_list = []
        
        search_paths = [
            "/storage/emulated/0/Music", 
            "/storage/emulated/0/Download",
            "/storage/emulated/0/WhatsApp/Media/WhatsApp Audio",
            "/storage/emulated/0/PrasadApp",
            "/storage/emulated/0/Recordings",
            "/storage/emulated/0/Snaptube/download",
            "/storage/emulated/0/DCIM"
        ]
        
        count = 0
        for folder in search_paths:
            if os.path.exists(folder):
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        if file.lower().endswith(('.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg')):
                            full_path = os.path.join(root, file)
                            item = {'text': file, 'secondary_text': f"{os.path.basename(root)}", 'path': full_path}
                            new_data.append(item)
                            self.all_songs_list.append(full_path)
                            count += 1
        self.music_list_data = new_data
        if count > 0: toast(f"Found {count} tracks")
        else: toast("No music found")

    def play_song_from_list(self, path):
        if path in self.all_songs_list:
            self.current_song_index = self.all_songs_list.index(path)
        self.play_song(path, os.path.basename(path))

    def play_song(self, path, title):
        self.current_title = title
        self.player.load(path)
        self.player.play()
        self.is_playing = True
        self.mini_player_opacity = 1
        
        self.current_art = "album_art.jpg" 
        def force_sync_art(dt):
            unique_name = f"vault_cached_{int(time.time()*1000)}.jpg"
            temp_path = os.path.join(os.getcwd(), unique_name)
            if self.player.get_art(path, temp_path):
                self.current_art = temp_path
            else:
                self.current_art = "album_art.jpg"
        Clock.schedule_once(force_sync_art, 0.18)
        Clock.unschedule(self.update_music_state)
        Clock.schedule_interval(self.update_music_state, 1)

    def toggle_play(self):
        if self.is_playing: self.player.pause(); self.is_playing = False
        else: self.player.play(); self.is_playing = True

    def play_next(self, *args):
        if not self.all_songs_list: return
        self.current_song_index = (self.current_song_index + 1) % len(self.all_songs_list)
        path = self.all_songs_list[self.current_song_index]
        self.play_song(path, os.path.basename(path))

    def play_prev(self, *args):
        if not self.all_songs_list: return
        self.current_song_index = (self.current_song_index - 1) % len(self.all_songs_list)
        path = self.all_songs_list[self.current_song_index]
        self.play_song(path, os.path.basename(path))

    def update_music_state(self, dt):
        if not self.is_playing: return
        if self.player.is_complete():
            self.play_next()
            return
        if hasattr(self, 'seek_slider') and self.seek_slider:
            pos = self.player.get_pos(); dur = self.player.get_duration()
            if dur > 0:
                self.seek_slider.max = dur; self.seek_slider.value = pos
                curr_min, curr_sec = divmod(int(pos), 60)
                tot_min, tot_sec = divmod(int(dur), 60)
                if hasattr(self, 'lbl_time'):
                    self.lbl_time.text = f"{curr_min:02}:{curr_sec:02} / {tot_min:02}:{tot_sec:02}"

    def on_slider_seek(self, instance, touch):
        if instance.collide_point(*touch.pos): self.player.seek(instance.value)

    # --- WORKING FOLDERS ---
    def file_manager_gallery_open(self): self.fm_gallery.show("/storage/emulated/0/")
    def close_fm_gallery(self, *args): self.fm_gallery.close()
    def file_manager_video_open(self): self.fm_video.show("/storage/emulated/0/")
    def close_fm_video(self, *args): self.fm_video.close()
    def file_manager_docs_open(self): self.fm_docs.show("/storage/emulated/0/")
    def close_fm_docs(self, *args): self.fm_docs.close()

    def select_video(self, path):
        self.close_fm_video(); self.open_external_intent(path, "video/*")

    def select_generic(self, path):
        self.fm_gallery.close(); self.fm_docs.close()
        mime = "image/*" if path.lower().endswith(('.jpg', '.png', '.jpeg')) else "*/*"
        self.open_external_intent(path, mime)

    def open_external_intent(self, path, mime):
        if platform == 'android':
            try:
                from jnius import autoclass, cast
                StrictMode = autoclass('android.os.StrictMode')
                StrictMode.disableDeathOnFileUriExposure()
                activity = autoclass('org.kivy.android.PythonActivity').mActivity
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                File = autoclass('java.io.File')
                uri = Uri.fromFile(File(path))
                intent = Intent(Intent.ACTION_VIEW)
                intent.setDataAndType(uri, mime)
                cast('android.app.Activity', activity).startActivity(intent)
            except: toast("App not found for this type")

    def open_system_settings(self):
        if not self.player.open_system_dolby(): toast("Dolby Settings unavailable")

    def toggle_surround(self, instance, value):
        if self.player.toggle_spatial_audio(value): toast(f"Spatial Audio: {'ACTIVE' if value else 'OFF'}")

    # --- FULL PLAYER OVERLAY ---
    def open_full_player(self):
        self.modal = ModalView(size_hint=(1, 1), background_color=[0,0,0,1], overlay_color=[0,0,0,1])
        content = MDFloatLayout()
        
        self.full_player_bg = FitImage(source=self.current_art, opacity=0.38)
        content.add_widget(self.full_player_bg)
        
        content.add_widget(MDLabel(text="NOW PLAYING", halign="center", pos_hint={"center_y": 0.95}, theme_text_color="Custom", text_color=[1, 0.8, 0, 1], font_style="Overline", bold=True))
        
        self.full_player_art = FitImage(source=self.current_art, size_hint=(None, None), size=("330dp", "330dp"), pos_hint={"center_x": .5, "center_y": .66}, radius=[32,])
        card = MDCard(size_hint=(None, None), size=("330dp", "330dp"), pos_hint={"center_x": .5, "center_y": .66}, radius=[32,], elevation=14)
        card.add_widget(self.full_player_art)
        content.add_widget(card)
        
        self.full_player_label = MDLabel(text=self.current_title, halign="center", pos_hint={"center_y": 0.46}, bold=True, font_style="H5", theme_text_color="Custom", text_color=[1, 1, 1, 1], padding=[25, 0])
        content.add_widget(self.full_player_label)
        
        self.lbl_time = MDLabel(text="00:00 / 00:00", halign="center", pos_hint={"center_y": 0.39}, theme_text_color="Custom", text_color=[1, 1, 1, 0.7], font_style="Caption")
        content.add_widget(self.lbl_time)
        
        self.seek_slider = MDSlider(min=0, max=100, value=0, pos_hint={"center_x": .5, "center_y": 0.33}, size_hint=(0.9, None), color=[1, 0.8, 0, 1])
        self.seek_slider.bind(on_touch_up=self.on_slider_seek)
        content.add_widget(self.seek_slider)
        
        controls = MDBoxLayout(orientation='horizontal', spacing="40dp", adaptive_size=True, pos_hint={"center_x": .5, "center_y": .20})
        btn_prev = MDIconButton(icon="skip-previous", icon_size="58sp", theme_text_color="Custom", text_color=[1,1,1,1], on_release=self.play_prev)
        self.btn_play_full = MDIconButton(icon="pause-circle" if self.is_playing else "play-circle", icon_size="95sp", theme_text_color="Custom", text_color=[1, 0.8, 0, 1], on_release=lambda x: self.toggle_full_play())
        btn_next = MDIconButton(icon="skip-next", icon_size="58sp", theme_text_color="Custom", text_color=[1,1,1,1], on_release=self.play_next)
        
        controls.add_widget(btn_prev)
        controls.add_widget(self.btn_play_full)
        controls.add_widget(btn_next)
        content.add_widget(controls)
        
        # MINIMIZE BUTTON
        minimize_btn = MDFillRoundFlatButton(
            text="MINIMIZE", 
            pos_hint={"center_x": 0.5, "center_y": 0.08},
            md_bg_color=[1, 1, 1, 0.1],
            text_color=[1, 1, 1, 0.8],
            font_size="14sp",
            on_release=self.modal.dismiss
        )
        content.add_widget(minimize_btn)
        
        min_arrow = MDIconButton(icon="chevron-down", pos_hint={"center_x": .5, "top": 0.99}, theme_text_color="Custom", text_color=[1, 1, 1, 1], on_release=self.modal.dismiss)
        content.add_widget(min_arrow)
        
        self.modal.add_widget(content)
        self.modal.open()
        self.bind(current_title=lambda inst, val: setattr(self.full_player_label, 'text', val))

    def toggle_full_play(self):
        self.toggle_play(); self.btn_play_full.icon = "pause-circle" if self.is_playing else "play-circle"

    # --- MAIN FILE MANAGER CALL ---
    def file_manager_open(self): 
        # FIX: Opens Music File Manager when clicking Folder
        self.fm_music.show("/storage/emulated/0/")
        
    def close_fm(self, *args): self.fm_music.close()
    def select_path(self, path): self.close_fm(); self.play_song(path, os.path.basename(path))

if __name__ == '__main__':
    PrasadProApp().run()
