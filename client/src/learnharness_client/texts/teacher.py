"""Teacher area and central administration."""

from __future__ import annotations


class TeacherTexts:
    # Teacher area
    TEACHER_MENU = "Lehrkraft-Bereich …"
    TEACHER_TITLE = "Lehrkraft-Bereich"
    TEACHER_SET_PASSWORD_INTRO = (
        "Lege einmalig ein Passwort für den Lehrkraft-Bereich fest. Kinder brauchen es nicht."
    )
    TEACHER_PASSWORD = "Passwort:"
    TEACHER_PASSWORD_REPEAT = "Wiederholen:"
    TEACHER_PASSWORD_A11Y = "Passwort für den Lehrkraft-Bereich"
    TEACHER_PASSWORD_TOO_SHORT = "Das Passwort braucht mindestens 6 Zeichen."
    TEACHER_PASSWORD_MISMATCH = "Die beiden Passwörter stimmen nicht überein."
    TEACHER_PASSWORD_WRONG = "Das Passwort stimmt nicht."
    TEACHER_UNLOCK = "Öffnen"
    TEACHER_INTRO = (
        "Profile auf diesem Computer verwalten. Änderungen gelten sofort. "
        "Der Lernfortschritt auf dem Lernserver bleibt davon unberührt."
    )
    TEACHER_PROFILES_A11Y = "Lernprofile auf diesem Computer"
    TEACHER_PROFILE_ROW = "{pseudonym} · Level {level} · {experience}"
    TEACHER_CURRENT = " (gerade angemeldet)"
    TEACHER_LEVEL = "Freigeschaltetes Level:"
    TEACHER_LEVEL_A11Y = "Freigeschaltetes LearnAgent-Level"
    TEACHER_APPLY_LEVEL = "Level übernehmen"
    TEACHER_RESET = "Fortschritt zurücksetzen"
    TEACHER_DELETE = "Profil löschen"
    TEACHER_CHANGE_PASSWORD = "Passwort ändern …"
    TEACHER_RESET_CONFIRM = (
        "Level, gespeicherten Fortschritt und Kurzanleitung von {pseudonym} zurücksetzen?"
    )
    TEACHER_DELETE_CONFIRM = "Profil {pseudonym} endgültig von diesem Computer löschen?"
    TEACHER_CANNOT_DELETE_CURRENT = (
        "Das gerade angemeldete Profil kann nicht gelöscht werden. Melde dich mit einem "
        "anderen Profil an oder starte LearnHarness neu."
    )
    TEACHER_NO_PROFILES = "Auf diesem Computer gibt es noch keine Profile."

    # Central administration (teacher area)
    TEACHER_ADMIN = "Zentrale Verwaltung …"
    TEACHER_CENTRAL_NOTICE = (
        "Dieser PC ist mit der zentralen Verwaltung verbunden. Level, Zurücksetzen und "
        "Löschen änderst du dort im Browser; hier siehst du den Stand vom letzten Abgleich."
    )
    ADMIN_TITLE = "Zentrale Verwaltung"
    ADMIN_INTRO = (
        "Trage die Adresse der Verwaltung und den Zugangs-Token für diesen PC ein. Den Token "
        "legst du in der Verwaltung unter „API-Zugänge“ an. Ohne Netz arbeitet die App mit "
        "dem Stand vom letzten Abgleich weiter."
    )
    ADMIN_URL = "Adresse:"
    ADMIN_URL_A11Y = "Adresse der zentralen Verwaltung"
    ADMIN_URL_PLACEHOLDER = "z. B. http://verwaltung:8000"
    ADMIN_TOKEN = "Token:"
    ADMIN_TOKEN_A11Y = "Zugangs-Token für diesen PC"
    ADMIN_GROUP = "Gruppe:"
    ADMIN_GROUP_A11Y = "Gruppe dieses PCs"
    ADMIN_GROUP_PLACEHOLDER = "Optional, z. B. AG Montag – leer: alle Kinder"
    ADMIN_SAVE_AND_SYNC = "Speichern und abgleichen"
    ADMIN_DISCONNECT = "Verbindung trennen"
    ADMIN_SYNC_OK = "Abgleich erfolgreich. Die Profile sind auf dem neuesten Stand."
    ADMIN_SYNC_OFFLINE = (
        "Die Verwaltung ist nicht erreichbar. Prüfe die Adresse und das Netz. Die App "
        "arbeitet mit dem Stand auf diesem PC weiter."
    )
    ADMIN_SYNC_UNAUTHORIZED = (
        "Der Token wurde nicht angenommen. Lege in der Verwaltung einen neuen an."
    )
    ADMIN_SYNC_DISABLED = "Dieser PC nutzt nur lokale Profile."
    ADMIN_START_OFFLINE = (
        "Die zentrale Verwaltung ist gerade nicht erreichbar. Du kannst trotzdem lernen; "
        "dein Fortschritt wird später übertragen."
    )
