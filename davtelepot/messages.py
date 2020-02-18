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

default_language_messages = {
    'language_command': {
        'name': {
            'en': "/language",
            'it': "/lingua"
        },
        'alias': {
            'en': "Language 🗣",
            'it': "Lingua 🗣"
        },
        'reply_keyboard_button': {
            'en': "Language 🗣",
            'it': "Lingua 🗣"
        },
        'description': {
            'en': "Change language settings",
            'it': "Cambia le impostazioni della lingua"
        }
    },
    'language_button': {
        'description': {
            'en': "Change language settings",
            'it': "Cambia le impostazioni della lingua"
        },
        'language_set': {
            'en': "Selected language: English 🇬🇧",
            'it': "Lingua selezionata: Italiano 🇮🇹"
        }
    },
    'language_panel': {
        'text': {
            'en': "<b>Choose a language</b>",
            'it': "<b>Seleziona una lingua</b>"
        }
    }
}

default_suggestion_messages = {
    'suggestions_command': {
        'command': "/suggestion",
        'aliases': [
            "/suggestions", "/ideas",
            "/suggerimento", "/suggerimenti", "idee"
        ],
        'reply_keyboard_button': {
            'en': "Ideas 💡",
            'it': "Idee 💡"
        },
        'description': {
            'en': "Send a suggestion to help improve the bot",
            'it': "Invia un suggerimento per aiutare a migliorare il bot"
        },
        'prompt_text': {
            'en': (
                "Send a suggestion to bot administrator.\n\n"
                "Maximum 1500 characters (extra ones will be ignored).\n"
                "If you need more space, you may create a telegra.ph topic and link it here.\n\n"
                "/cancel if you misclicked."
            ),
            'it': (
                "Inserisci un suggerimento da inviare agli amministratori.\n\n"
                "Massimo 1500 caratteri (quelli in più non verranno registrati).\n"
                "Se ti serve maggiore libertà, puoi per esempio creare un topic "
                "su telegra.ph e linkarlo qui!\n\n"
                "/annulla se hai clickato per errore."
            ),
        },
        'prompt_popup': {
            'en': (
                "Send a suggestion"
            ),
            'it': (
                "Inserisci un suggerimento"
            ),
        },
        'entered_suggestion': {
            'text': {
                'en': (
                    "Entered suggestions:\n\n"
                    "<code>{suggestion}</code>\n\n"
                    "Do you want to send it to bot administrators?"
                ),
                'it': (
                    "Suggerimento inserito:\n\n"
                    "<code>{suggestion}</code>\n\n"
                    "Vuoi inviarlo agli amministratori?"
                ),
            },
            'buttons': {
                'send': {
                    'en': "Send it! 📧",
                    'it': "Invia! 📧",
                },
                'cancel': {
                    'en': "Cancel ❌",
                    'it': "Annulla ❌",
                },
            }
        },
        'received_suggestion': {
            'text': {
                'en': (
                    "💡 We received a new suggestion! 💡\n\n"
                    "{user}\n\n"
                    "<code>{suggestion}</code>\n\n"
                    "#suggestions  #{bot.name}"
                ),
                'it': (
                    "💡 Abbiamo ricevuto un nuovo suggerimento! 💡\n\n"
                    "{user}\n\n"
                    "<code>{suggestion}</code>\n\n"
                    "#suggestions  #{bot.name}"
                ),
            },
            'buttons': {
                'new': {
                    'en': "New suggestion 💡",
                    'it': "Nuovo suggerimento 💡",
                },
            },
        },
        'invalid_suggestion': {
            'en': "Invalid suggestion.",
            'it': "Suggerimento non valido."
        },
        'cancel_messages': {
            'en': ['cancel'],
            'it': ['annulla', 'cancella'],
        },
        'operation_cancelled': {
            'en': "Operation cancelled.",
            'it': "Operazione annullata con successo.",
        },
        'suggestion_sent': {
            'popup': {
                'en': "Thanks!",
                'it': "Grazie!",
            },
            'text': {
                'en': (
                    "💡 Suggestion sent, thank you! 💡\n\n"
                    "<code>{suggestion}</code>\n\n"
                    "#suggestions #{bot.name}"
                ),
                'it': (
                    "💡 Suggerimento inviato, grazie! 💡\n\n"
                    "<code>{suggestion}</code>\n\n"
                    "#suggerimenti #{bot.name}"
                ),
            },
        }
    },
    'suggestions_button': {
        'file_name': {
            'en': "Suggestions.csv",
            'it': "Suggerimenti.csv",
        },
        'file_caption': {
            'en': "Here is the suggestions file.",
            'it': "Ecco il file dei suggerimenti.",
        }
    },
    'see_suggestions': {
        'command': "/getsuggestions",
        'aliases': [
            "/vedisuggerimenti",
        ],
        'description': {
            'en': "Get a file containing all suggestions",
            'it': "Richiedi un file con tutti i suggerimenti"
        },
    }
}
