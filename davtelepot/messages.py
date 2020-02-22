"""Default messages for bot functions."""

default_admin_messages = {
    'talk_command': {
        'description': {
            'en': "Choose a user and forward messages to each other",
            'it': "Scegli un utente e il bot farà da tramite inoltrando a "
                  "ognuno i messaggi dell'altro finché non terminerai la "
                  "sessione"
        }
    },
    'restart_command': {
        'description': {
            'en': "Restart bots",
            'it': "Riavvia i bot"
        },
        'restart_scheduled_message': {
            'en': "Bots are being restarted, after pulling from repository.",
            'it': "I bot verranno riavviati in pochi secondi, caricando "
                  "prima le eventuali modifiche al codice."
        },
        'restart_completed_message': {
            'en': "<i>Restart was successful.</i>",
            'it': "<i>Restart avvenuto con successo.</i>"
        }
    },
    'stop_command': {
        'description': {
            'en': "Stop bots",
            'it': "Ferma i bot"
        },
        'text': {
            'en': "Are you sure you want to stop all bots?\n"
                  "To make them start again you will have to ssh-log "
                  "in server.\n\n"
                  "To restart the bots remotely use the /restart command "
                  "instead (before starting over, a <code>git pull</code> "
                  "is performed).",
            'it': "Sei sicuro di voler fermare i bot?\n"
                  "Per farli ripartire dovrai accedere al server.\n\n"
                  "Per far ripartire i bot da remoto usa invece il comando "
                  "/restart (prima di ripartire farò un "
                  "<code>git pull</code>)."
        }
    },
    'stop_button': {
        'stop_text': {
            'en': "Stop bots",
            'it': "Ferma i bot"
        },
        'cancel': {
            'en': "Cancel",
            'it': "Annulla"
        },
        'confirm': {
            'en': "Do you really want to stop all bots?",
            'it': "Vuoi davvero fermare tutti i bot?"
        },
        'stopping': {
            'en': "Stopping bots...",
            'it': "Arresto in corso..."
        },
        'cancelled': {
            'en': "Operation was cancelled",
            'it': "Operazione annullata"
        }
    },
    'db_command': {
        'description': {
            'en': "Ask for bot database via Telegram",
            'it': "Ricevi il database del bot via Telegram"
        },
        'not_sqlite': {
            'en': "Only SQLite databases may be sent via Telegram, since they "
                  "are single-file databases.\n"
                  "This bot has a `{db_type}` database.",
            'it': "Via Telegram possono essere inviati solo database SQLite, "
                  "in quanto composti di un solo file.\n"
                  "Questo bot ha invece un database `{db_type}`."
        },
        'file_caption': {
            'en': "Here is bot database.",
            'it': "Ecco il database!"
        },
        'db_sent': {
            'en': "Database sent.",
            'it': "Database inviato."
        }
    },
    'query_command': {
        'description': {
            'en': "Receive the result of a SQL query performed on bot "
                  "database",
            'it': "Ricevi il risultato di una query SQL sul database del bot"
        },
        'help': {
            'en': "Write a SQL query to be run on bot database.\n\n"
                  "<b>Example</b>\n"
                  "<code>/query SELECT * FROM users WHERE 0</code>",
            'it': "Invia una query SQL da eseguire sul database del bot.\n\n"
                  "<b>Esempio</b>\n"
                  "<code>/query SELECT * FROM users WHERE 0</code>"
        },
        'no_iterable': {
            'en': "No result to show was returned",
            'it': "La query non ha restituito risultati da mostrare"
        },
        'exception': {
            'en': "The query threw this error:",
            'it': "La query ha dato questo errore:"
        },
        'result': {
            'en': "Query result",
            'it': "Risultato della query"
        }
    },
    'select_command': {
        'description': {
            'en': "Receive the result of a SELECT query performed on bot "
                  "database",
            'it': "Ricevi il risultato di una query SQL di tipo SELECT "
                  "sul database del bot"
        }
    },
    'query_button': {
        'error': {
            'en': "Error!",
            'it': "Errore!"
        },
        'file_name': {
            'en': "Query result.csv",
            'it': "Risultato della query.csv"
        },
        'empty_file': {
            'en': "No result to show.",
            'it': "Nessun risultato da mostrare."
        }
    },
    'log_command': {
        'description': {
            'en': "Receive bot log file, if set",
            'it': "Ricevi il file di log del bot, se impostato"
        },
        'no_log': {
            'en': "Sorry but no log file is set.\n"
                  "To set it, use `bot.set_log_file_name` instance method or "
                  "`Bot.set_class_log_file_name` class method.",
            'it': "Spiacente ma il file di log non è stato impostato.\n"
                  "Per impostarlo, usa il metodo d'istanza "
                  "`bot.set_log_file_name` o il metodo di classe"
                  "`Bot.set_class_log_file_name`."
        },
        'sending_failure': {
            'en': "Sending log file failed!\n\n"
                  "<b>Error:</b>\n"
                  "<code>{e}</code>",
            'it': "Inviio del messaggio di log fallito!\n\n"
                  "<b>Errore:</b>\n"
                  "<code>{e}</code>"
        },
        'here_is_log_file': {
            'en': "Here is the complete log file.",
            'it': "Ecco il file di log completo."
        },
        'log_file_first_lines': {
            'en': "Here are the first {lines} lines of the log file.",
            'it': "Ecco le prime {lines} righe del file di log."
        },
        'log_file_last_lines': {
            'en': "Here are the last {lines} lines of the log file.\n"
                  "Newer lines are at the top of the file.",
            'it': "Ecco le ultime {lines} righe del file di log.\n"
                  "L'ordine è cronologico, con i messaggi nuovi in alto."
        }
    },
    'errors_command': {
        'description': {
            'en': "Receive bot error log file, if set",
            'it': "Ricevi il file di log degli errori del bot, se impostato"
        },
        'no_log': {
            'en': "Sorry but no errors log file is set.\n"
                  "To set it, use `bot.set_errors_file_name` instance method"
                  "or `Bot.set_class_errors_file_name` class method.",
            'it': "Spiacente ma il file di log degli errori non è stato "
                  "impostato.\n"
                  "Per impostarlo, usa il metodo d'istanza "
                  "`bot.set_errors_file_name` o il metodo di classe"
                  "`Bot.set_class_errors_file_name`."
        },
        'empty_log': {
            'en': "Congratulations! Errors log is empty!",
            'it': "Congratulazioni! Il log degli errori è vuoto!"
        },
        'sending_failure': {
            'en': "Sending errors log file failed!\n\n"
                  "<b>Error:</b>\n"
                  "<code>{e}</code>",
            'it': "Inviio del messaggio di log degli errori fallito!\n\n"
                  "<b>Errore:</b>\n"
                  "<code>{e}</code>"
        },
        'here_is_log_file': {
            'en': "Here is the complete errors log file.",
            'it': "Ecco il file di log degli errori completo."
        },
        'log_file_first_lines': {
            'en': "Here are the first {lines} lines of the errors log file.",
            'it': "Ecco le prime {lines} righe del file di log degli errori."
        },
        'log_file_last_lines': {
            'en': "Here are the last {lines} lines of the errors log file.\n"
                  "Newer lines are at the top of the file.",
            'it': "Ecco le ultime {lines} righe del file di log degli "
                  "errori.\n"
                  "L'ordine è cronologico, con i messaggi nuovi in alto."
        }
    },
    'maintenance_command': {
        'description': {
            'en': "Put the bot under maintenance",
            'it': "Metti il bot in manutenzione"
        },
        'maintenance_started': {
            'en': "<i>Bot has just been put under maintenance!</i>\n\n"
                  "Until further notice, it will reply to users "
                  "with the following message:\n\n"
                  "{message}",
            'it': "<i>Il bot è stato messo in manutenzione!</i>\n\n"
                  "Fino a nuovo ordine, risponderà a tutti i comandi con il "
                  "seguente messaggio\n\n"
                  "{message}"
        },
        'maintenance_ended': {
            'en': "<i>Maintenance ended!</i>",
            'it': "<i>Manutenzione terminata!</i>"
        }
    },
    'version_command': {
        'reply_keyboard_button': {
            'en': "Version #️⃣",
            'it': "Versione #️⃣",
        },
        'description': {
            'en': "Get source code version",
            'it': "Chiedi la versione del codice sorgente",
        },
        'help_section': None,
        'result': {
            'en': "Last commit: {last_commit}\n"
                  "davtelepot version: {davtelepot_version}",
            'it': "Ultimo commit: {last_commit}"
                  "Version di davtelepot: {davtelepot_version}",
        },
    }
}

default_authorization_denied_message = {
    'en': "You are not allowed to use this command, sorry.",
    'it': "Non disponi di autorizzazioni sufficienti per questa richiesta, spiacente.",
}

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

default_talk_messages = {
    'admin_session_ended': {
        'en': 'Session with user {u} ended.',
        'it': 'Sessione terminata con l\'utente {u}.',
    },
    'admin_warning': {
        'en': (
            'You are now talking to {u}.\n'
            'Until you end this session, your messages will be '
            'forwarded to each other.'
        ),
        'it': (
            'Sei ora connesso con {u}.\n'
            'Finché non chiuderai la connessione, i messaggi che scriverai '
            'qui saranno inoltrati a {u}, e ti inoltrerò i suoi.'
        ),
    },
    'end_session': {
        'en': 'End session?',
        'it': 'Chiudere la sessione?',
    },
    'help_text': {
        'en': 'Press the button to search for user.',
        'it': 'Premi il pulsante per scegliere un utente.',
    },
    'search_button': {
        'en': "🔍 Search for user",
        'it': "🔍 Cerca utente",
    },
    'select_user': {
        'en': 'Which user would you like to talk to?',
        'it': 'Con quale utente vorresti parlare?',
    },
    'user_not_found': {
        'en': (
            "Sory, but no user matches your query for\n"
            "<code>{q}</code>"
        ),
        'it': (
            "Spiacente, ma nessun utente corrisponde alla ricerca per\n"
            "<code>{q}</code>"
        ),
    },
    'instructions': {
        'en': (
            'Write a part of name, surname or username of the user you want '
            'to talk to.'
        ),
        'it': (
            'Scrivi una parte del nome, cognome o username dell\'utente con '
            'cui vuoi parlare.'
        ),
    },
    'stop': {
        'en': 'End session',
        'it': 'Termina la sessione',
    },
    'user_session_ended': {
        'en': 'Session with admin {u} ended.',
        'it': 'Sessione terminata con l\'amministratore {u}.',
    },
    'user_warning': {
        'en': (
            '{u}, admin of this bot, wants to talk to you.\n'
            'Until this session is ended by {u}, your messages will be '
            'forwarded to each other.'
        ),
        'it': (
            '{u}, amministratore di questo bot, vuole parlare con te.\n'
            'Finché non chiuderà la connessione, i messaggi che scriverai '
            'qui saranno inoltrati a {u}, e ti inoltrerò i suoi.'
        ),
    },
}

default_unknown_command_message = {
    'en': "Unknown command! Touch /help to read the guide and available commands.",
    'it': "Comando sconosciuto! Fai /help per leggere la guida e i comandi."
}
