"""Interface text in English and German.

Every visible string is written in English and passed through t(). The German text is looked up
by the English text, so a string with no German entry shows in English rather than failing.
tests/test_i18n.py checks that every t() call in the UI has a German entry.
"""

from adb_toolkit.core.settings import ENGLISH, GERMAN, LANGUAGES

# The name of each language, written in that language, for the language picker.
LANGUAGE_NAMES = {ENGLISH: "English", GERMAN: "Deutsch"}

_active = ENGLISH

_GERMAN: dict[str, str] = {
    # Navigation and screen titles
    "Apps": "Apps",
    "ADB Tools": "ADB-Werkzeuge",
    "Fastboot": "Fastboot",
    "Files": "Dateien",
    "Capture": "Aufnahme",
    "Console": "Konsole",
    "Settings": "Einstellungen",
    "Updates": "Updates",
    "About": "Info",
    "Tools": "Werkzeuge",
    "App": "App",
    "Fastboot Tools": "Fastboot-Werkzeuge",
    "Set up platform-tools": "Platform-Tools einrichten",
    "Updating scrcpy": "scrcpy wird aktualisiert",
    "Downloads Google's adb and fastboot and adds them to your PATH.":
        "Lädt adb und fastboot von Google herunter und fügt sie Ihrem PATH hinzu.",
    "Downloads scrcpy so the phone's screen can be mirrored and controlled.":
        "Lädt scrcpy herunter, damit der Bildschirm des Telefons gespiegelt und gesteuert werden kann.",
    "Continue without scrcpy": "Ohne scrcpy fortfahren",
    "Keep the current version": "Aktuelle Version behalten",
    "Checking": "Wird geprüft",
    "Installing": "Wird installiert",
    "Downloading": "Wird heruntergeladen",
    "Downloading {done} of {total} MB": "Wird heruntergeladen: {done} von {total} MB",
    "{done} of {total} MB": "{done} von {total} MB",
    "Try again": "Erneut versuchen",
    "Wait for the running task to finish.": "Warten Sie, bis die laufende Aufgabe fertig ist.",
    "Connected to {address}": "Verbunden mit {address}",
    "Could not connect to {address}.": "Verbindung zu {address} nicht möglich.",
    "Could not add platform-tools to PATH: {error}": "Platform-Tools konnten nicht zum PATH hinzugefügt werden: {error}",
    "Platform-tools updated.": "Platform-Tools aktualisiert.",

    # Devices and the sidebar
    "Connect Wi-Fi": "WLAN verbinden",
    "Refresh devices": "Geräte aktualisieren",
    "No device": "Kein Gerät",
    "Connect a phone": "Telefon verbinden",
    "Choose a device": "Gerät wählen",
    "No devices connected": "Keine Geräte verbunden",
    "No device connected": "Kein Gerät verbunden",
    "No device selected": "Kein Gerät ausgewählt",
    "Ready": "Bereit",
    "Ready · {transport}": "Bereit · {transport}",
    "Fastboot mode": "Fastboot-Modus",
    "Unauthorized": "Nicht autorisiert",
    "Offline": "Offline",
    "No permissions": "Keine Berechtigung",
    "Recovery": "Wiederherstellung",
    "Sideload": "Sideload",
    "Connect over Wi-Fi": "Per WLAN verbinden",
    "Address": "Adresse",
    "Enter an address like 192.168.1.20:5555.": "Geben Sie eine Adresse wie 192.168.1.20:5555 ein.",
    "Enter the address shown under Wireless debugging.":
        "Geben Sie die Adresse ein, die unter „Drahtloses Debugging“ angezeigt wird.",
    "Connect": "Verbinden",
    "Cancel": "Abbrechen",
    "Reboot": "Neu starten",
    "Reboot system": "Neu starten",
    "Reboot to recovery": "In die Wiederherstellung starten",
    "Reboot to bootloader": "In den Bootloader starten",
    "Restart into Android.": "Zu Android neu starten.",
    "Sideload an update or factory reset.": "Update oder Werksreset per Sideload.",
    "Switch to fastboot mode.": "In den Fastboot-Modus wechseln.",
    "Stay in fastboot mode.": "Im Fastboot-Modus bleiben.",
    "Not every phone supports this.": "Nicht jedes Telefon unterstützt das.",
    "Rebooting the phone.": "Das Telefon wird neu gestartet.",
    "Rebooting to recovery.": "Wird in die Wiederherstellung gestartet.",
    "Rebooting to the bootloader.": "Wird in den Bootloader gestartet.",
    "Rebooting": "Wird neu gestartet",
    "Commands for a phone booted into Android.": "Befehle für ein Telefon mit gestartetem Android.",
    "Commands for a phone in bootloader mode.": "Befehle für ein Telefon im Bootloader-Modus.",
    "Connect a phone to reboot it.": "Verbinden Sie ein Telefon, um es neu zu starten.",
    "The phone is in fastboot mode. Use Fastboot Tools instead.":
        "Das Telefon ist im Fastboot-Modus. Verwenden Sie stattdessen die Fastboot-Werkzeuge.",
    "The phone is {state}.": "Das Telefon ist {state}.",
    "Reboot to the bootloader from ADB Tools first.":
        "Starten Sie zuerst über die ADB-Werkzeuge in den Bootloader neu.",
    "The device is not ready for this command.": "Das Gerät ist für diesen Befehl nicht bereit.",
    "The reboot did not go through.": "Der Neustart ist nicht gelungen.",
    "The phone is in fastboot mode": "Das Telefon ist im Fastboot-Modus",
    "Reboot to Android to manage apps.": "Starten Sie zu Android neu, um Apps zu verwalten.",
    "Allow USB debugging on the phone": "USB-Debugging auf dem Telefon erlauben",
    "Accept the prompt on the phone.": "Bestätigen Sie die Abfrage auf dem Telefon.",
    "The device is {state}": "Das Gerät ist {state}",
    "Connect a phone with USB debugging on.": "Verbinden Sie ein Telefon mit aktiviertem USB-Debugging.",
    "Reconnect the cable.": "Schließen Sie das Kabel erneut an.",
    "Connect a phone with USB debugging on to use these.":
        "Verbinden Sie ein Telefon mit aktiviertem USB-Debugging, um diese Funktionen zu nutzen.",
    "No file chosen": "Keine Datei gewählt",
    "adb devices": "adb devices",

    # Apps
    "Search packages": "Pakete suchen",
    "Reload packages": "Pakete neu laden",
    "Packages on the selected phone. Uninstalling removes an app for this user.":
        "Pakete auf dem ausgewählten Telefon. Deinstallieren entfernt eine App für diesen Benutzer.",
    "All": "Alle",
    "User": "Benutzer",
    "System": "System",
    "Removed": "Entfernt",
    "{total} packages": "{total} Pakete",
    "{shown} of {total}": "{shown} von {total}",
    "0 of {total}": "0 von {total}",
    "No packages match": "Keine Pakete gefunden",
    "Loading packages": "Pakete werden geladen",
    "Could not list packages": "Pakete konnten nicht aufgelistet werden",
    "Restore": "Wiederherstellen",
    "Uninstall": "Deinstallieren",
    "Uninstall {package}?": "{package} deinstallieren?",
    "Removed for this user only. Its data stays on the phone.":
        "Nur für diesen Benutzer entfernt. Die Daten bleiben auf dem Telefon.",
    "The app and its data are deleted.": "Die App und ihre Daten werden gelöscht.",
    "Uninstalled {package}": "{package} deinstalliert",
    "The uninstall did not finish.": "Die Deinstallation wurde nicht abgeschlossen.",
    "Restored {package}": "{package} wiederhergestellt",
    "The restore did not finish.": "Die Wiederherstellung wurde nicht abgeschlossen.",
    "Removed system app": "Entfernte System-App",
    "System app": "System-App",
    "User app": "Benutzer-App",

    # Files
    "Install apps and copy files between this computer and the selected phone.":
        "Apps installieren und Dateien zwischen diesem Computer und dem ausgewählten Telefon kopieren.",
    "Install an app": "App installieren",
    "Install an APK file on the selected phone. Its data is kept.":
        "Installiert eine APK-Datei auf dem ausgewählten Telefon. Die Daten bleiben erhalten.",
    "Choose APK": "APK wählen",
    "Choose an APK": "APK wählen",
    "Install": "Installieren",
    "Installing {name}": "{name} wird installiert",
    "Installed {name}": "{name} installiert",
    "The install did not finish.": "Die Installation wurde nicht abgeschlossen.",
    "Send a file to the phone": "Datei an das Telefon senden",
    "Copies a file from this computer to the phone.": "Kopiert eine Datei von diesem Computer auf das Telefon.",
    "Choose file": "Datei wählen",
    "Choose a file to send": "Datei zum Senden wählen",
    "Folder on the phone": "Ordner auf dem Telefon",
    "Send": "Senden",
    "Sending {name}": "{name} wird gesendet",
    "Sent {name} to the phone.": "{name} an das Telefon gesendet.",
    "Get a file from the phone": "Datei vom Telefon holen",
    "Copies a file from the phone to a folder you choose.":
        "Kopiert eine Datei vom Telefon in einen Ordner Ihrer Wahl.",
    "File on the phone": "Datei auf dem Telefon",
    "Choose folder and get": "Ordner wählen und holen",
    "Choose where to save the file": "Wählen Sie, wo die Datei gespeichert wird",
    "Getting {name}": "{name} wird geholt",
    "Saved {name} to {folder}": "{name} in {folder} gespeichert",
    "The transfer did not finish.": "Die Übertragung wurde nicht abgeschlossen.",
    "The phone path must start with /.": "Der Pfad auf dem Telefon muss mit / beginnen.",

    # Capture
    "Screenshot": "Screenshot",
    "Saves what the screen shows now, as a PNG.": "Speichert, was der Bildschirm gerade zeigt, als PNG.",
    "Take screenshot": "Screenshot aufnehmen",
    "Taking screenshot": "Screenshot wird aufgenommen",
    "Save screenshot": "Screenshot speichern",
    "Saved {name}": "{name} gespeichert",
    "The screenshot did not finish.": "Der Screenshot wurde nicht abgeschlossen.",
    "Screen recording": "Bildschirmaufnahme",
    "Records the screen as an MP4 video, for the length you choose.":
        "Nimmt den Bildschirm als MP4-Video auf, für die gewählte Dauer.",
    "Length": "Dauer",
    "10 s": "10 s",
    "30 s": "30 s",
    "3 min": "3 Min.",
    "The phone stops a recording after 3 minutes at most.":
        "Das Telefon beendet eine Aufnahme spätestens nach 3 Minuten.",
    "Start recording": "Aufnahme starten",
    "Save recording": "Aufnahme speichern",
    "Recording for {seconds} seconds": "Aufnahme läuft: {seconds} Sekunden",
    "The recording did not finish.": "Die Aufnahme wurde nicht abgeschlossen.",
    "Save a screenshot or a recording of the selected phone's screen to this computer.":
        "Speichern Sie einen Screenshot oder eine Aufnahme des Bildschirms des ausgewählten Telefons auf diesem Computer.",

    # Console
    "Run": "Ausführen",
    "Run an adb or fastboot command, and read what it prints.":
        "Führen Sie einen adb- oder fastboot-Befehl aus und lesen Sie die Ausgabe.",
    "The console adds the selected phone. Flashing, unlocking, uninstalling and sideloading have their own screens.":
        "Die Konsole verwendet das ausgewählte Telefon. Flashen, Entsperren, Deinstallieren und Sideloaden haben eigene Bildschirme.",
    "Exit code {code}": "Exitcode {code}",
    "(no output)": "(keine Ausgabe)",

    # ADB Tools: mirroring, sideload
    "Screen mirroring": "Bildschirmspiegelung",
    "Show the phone's screen in a window on this computer.":
        "Zeigt den Bildschirm des Telefons in einem Fenster auf diesem Computer.",
    "Start": "Starten",
    "Stop": "Stoppen",
    "Install scrcpy": "scrcpy installieren",
    "Mirror and control": "Spiegeln und steuern",
    "Mouse and keyboard control the phone from its window.":
        "Maus und Tastatur steuern das Telefon über sein Fenster.",
    "Keep the phone awake": "Telefon wach halten",
    "Stops the phone from sleeping while it is mirrored.":
        "Verhindert, dass das Telefon in den Ruhezustand geht, solange es gespiegelt wird.",
    "Turn off the phone's screen": "Bildschirm des Telefons ausschalten",
    "The phone's own screen stays dark while you use the window.":
        "Der eigene Bildschirm des Telefons bleibt dunkel, während Sie das Fenster nutzen.",
    "Show touches": "Berührungen anzeigen",
    "Draws a dot where each touch lands.": "Zeigt einen Punkt, wo jede Berührung landet.",
    "Maximum size": "Maximale Größe",
    "Scales the window down. Original keeps the phone's resolution.":
        "Verkleinert das Fenster. Original behält die Auflösung des Telefons.",
    "Original": "Original",
    "1440 px": "1440 px",
    "1080 px": "1080 px",
    "720 px": "720 px",
    "scrcpy is not installed.": "scrcpy ist nicht installiert.",
    "Connect a phone to mirror it.": "Verbinden Sie ein Telefon, um es zu spiegeln.",
    "The phone must be ready before it can be mirrored.":
        "Das Telefon muss bereit sein, bevor es gespiegelt werden kann.",
    "Mirroring {title}.": "{title} wird gespiegelt.",
    "Select a ready phone first.": "Wählen Sie zuerst ein bereites Telefon aus.",
    "scrcpy closed.": "scrcpy wurde geschlossen.",
    "Sideload a ROM or update": "ROM oder Update sideloaden",
    "Installs a ZIP through recovery. Choose Apply update from ADB on the phone first.":
        "Installiert eine ZIP-Datei über die Wiederherstellung. Wählen Sie zuerst auf dem Telefon „Update über ADB anwenden“.",
    "Choose ZIP": "ZIP wählen",
    "Choose a ROM or update": "ROM oder Update wählen",
    "Start sideload on the phone first, from its recovery menu.":
        "Starten Sie zuerst auf dem Telefon im Wiederherstellungsmenü den Sideload.",
    "Sideloading {name}": "{name} wird sideloaded",
    "Sideloaded {name}": "{name} sideloaded",
    "The sideload did not finish.": "Das Sideload wurde nicht abgeschlossen.",

    # Fastboot: flashing
    "Flash a partition": "Partition flashen",
    "Writes an image to one partition. Use only an image made for this exact phone.":
        "Schreibt ein Image in eine Partition. Verwenden Sie nur ein Image, das für genau dieses Telefon gemacht wurde.",
    "Choose image": "Image wählen",
    "Choose an image": "Image wählen",
    "List partitions": "Partitionen auflisten",
    "No partitions were listed.": "Es wurden keine Partitionen aufgelistet.",
    "Flash": "Flashen",
    "Flashing needs an unlocked bootloader. A wrong image can stop the phone from starting.":
        "Flashen setzt einen entsperrten Bootloader voraus. Ein falsches Image kann verhindern, dass das Telefon startet.",
    "Choose a partition and an image first.": "Wählen Sie zuerst eine Partition und ein Image.",
    "Flash {partition}?": "{partition} flashen?",
    "This writes {image} to the {partition} partition. The app cannot undo it.":
        "Dies schreibt {image} in die Partition {partition}. Die App kann das nicht rückgängig machen.",
    "Type {partition} to confirm.": "Geben Sie {partition} zur Bestätigung ein.",
    "Flashing {partition}": "{partition} wird geflasht",
    "Flashed {partition}.": "{partition} wurde geflasht.",
    "The flash did not finish.": "Das Flashen wurde nicht abgeschlossen.",
    "The phone is not in fastboot mode.": "Das Telefon ist nicht im Fastboot-Modus.",

    # Updates
    "Check for updates": "Nach Updates suchen",
    "Check the platform-tools and this app against their latest releases.":
        "Prüfen Sie die Platform-Tools und diese App auf die neuesten Versionen.",
    "Google's adb and fastboot, from the SDK feed.": "adb und fastboot von Google, aus dem SDK-Feed.",
    "This app, from its latest GitHub release.": "Diese App, aus der neuesten GitHub-Version.",
    "Not checked yet": "Noch nicht geprüft",
    "Up to date": "Aktuell",
    "No release yet": "Noch keine Version",
    "Update available: {version}": "Update verfügbar: {version}",
    "Install update": "Update installieren",
    "Install {version}": "{version} installieren",
    "Release page": "Versionsseite",
    "View {version}": "{version} ansehen",
    "Not installed": "Nicht installiert",

    # Settings
    "How the window looks.": "So sieht das Fenster aus.",
    "Appearance": "Darstellung",
    "Light or dark. The change applies at once.": "Hell oder dunkel. Die Änderung wirkt sofort.",
    "Light": "Hell",
    "Dark": "Dunkel",
    "Text size": "Textgröße",
    "Makes the text on every screen larger or smaller.": "Macht den Text auf allen Bildschirmen größer oder kleiner.",
    "Small": "Klein",
    "Default": "Standard",
    "Large": "Groß",
    "Language": "Sprache",
    "The language of the window. Messages from adb and fastboot stay in English.":
        "Die Sprache des Fensters. Meldungen von adb und fastboot bleiben auf Englisch.",

    # About
    "A workbench for adb and fastboot.": "Eine Werkbank für adb und fastboot.",
    "Version {version}": "Version {version}",
    "Made by {name}": "Von {name}",
    "Links": "Links",
    "Where the project lives.": "Wo das Projekt zu Hause ist.",
    "Website": "Webseite",
    "Source code": "Quellcode",

}


def activate_language(code: str) -> None:
    """Choose the language the next text is shown in. An unknown code means English."""
    global _active
    _active = code if code in LANGUAGES else ENGLISH


def language() -> str:
    return _active


def t(text: str, **values) -> str:
    """The text in the active language. Values fill the {name} placeholders."""
    shown = _GERMAN.get(text, text) if _active == GERMAN else text
    return shown.format(**values) if values else shown
