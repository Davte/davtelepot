"""Default messages for bot functions."""

default_help_messages = {
    'help_command': {
        'header': {
            'en': "<b>{bot.name} commands</b>\n\n"
                  "{commands}",
            'it': "<b>Comandi di {bot.name}</b>\n\n"
                  "{commands}",
        },
        'text': {
            'en': "<b>Guide</b>",
            'it': "<b>Guida</b>"
        },
        'reply_keyboard_button': {
            'en': "Help 📖",
            'it': "Guida 📖"
        },
        'description': {
            'en': "Help",
            'it': "Aiuto"
        },
        'access_denied_message': {
            'en': "Ask for authorization. If your request is accepted, send "
                  "/help command again to read the guide.",
            'it': "Chiedi di essere autorizzato: se la tua richiesta "
                  "verrà accolta, ripeti il comando /help per leggere "
                  "il messaggio di aiuto."
        },
        'back_to_help_menu': {
            'en': "Back to guide menu 📖",
            'it': "Torna al menu Guida 📖",
        },
    },
    'commands_button_label': {
            'en': "Commands 🤖",
            'it': "Comandi 🤖",
    },
}
