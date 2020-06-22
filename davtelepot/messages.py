"""Default messages for bot functions."""

davtelepot_messages = {
    'long_message': {
        'file_name': {
            'en': "Long message.html",
            'it': "Messaggio lungo.html",
        },
        'caption': {
            'en': "<b>Long message</b>\n\n"
                  "This message is too long to be sent as individual "
                  "messages.",
            'it': "<b>Messaggio lungo</b>\n\n"
                  "Questo messaggio è troppo lungo per essere inviato come "
                  "messaggi separati.",
        }
    },
    'part': {
        'en': "part",
        'it': "parte",
    },
}

default_admin_messages = {
    'cancel': {
        'button': {
            'en': "↩️ Cancel",
            'it': "↩️ Annulla"
        },
        'done': {
            'en': "↩️ Operation cancelled",
            'it': "↩️ Operazione annullata",
        },
        'lower': {
            'en': "cancel",
            'it': "annulla",
        },
    },
    'confirm': {
        'en': "🔄 Click again to confirm",
        'it': "🔄 Clicka di nuovo per confermare",
    },
    'db_command': {
        'db_sent': {
            'en': "Database sent.",
            'it': "Database inviato.",
        },
        'description': {
            'en': "Ask for bot database via Telegram",
            'it': "Ricevi il database del bot via Telegram",
        },
        'error': {
            'en': "Error sending database.",
            'it': "Errore durante l'invio del database.",
        },
        'file_caption': {
            'en': "Here is bot database.",
            'it': "Ecco il database!"
        },
        'not_sqlite': {
            'en': "Only SQLite databases may be sent via Telegram, since they "
                  "are single-file databases.\n"
                  "This bot has a `{db_type}` database.",
            'it': "Via Telegram possono essere inviati solo database SQLite, "
                  "in quanto composti di un solo file.\n"
                  "Questo bot ha invece un database `{db_type}`."
        },
    },
    'error': {
        'text': {
            'en': "❌️ Error!",
            'it': "❌️ Errore!"
        },
    },
    'errors_command': {
        'description': {
            'en': "Receive bot error log file, if set",
            'it': "Ricevi il file di log degli errori del bot, se impostato"
        },
        'no_log': {
            'en': "Sorry but no errors log file is set.\n"
                  "To set it, use `bot.set_errors_file_name` instance method "
                  "or `Bot.set_class_errors_file_name` class method.",
            'it': "Spiacente ma il file di log degli errori non è stato "
                  "impostato.\n"
                  "Per impostarlo, usa il metodo d'istanza "
                  "`bot.set_errors_file_name` o il metodo di classe "
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
    'father_command': {
        'back': {
            'en': "↩️ Back",
            'it': "↩️ Indietro",
        },
        'del': {
            'done': {
                'en': "✅ Commands deleted",
                'it': "✅ Comandi rimossi",
            },
            'error': {
                'en': "Something went wrong 😕",
                'it': "Qualcosa è andato storto 😕",
            },
            'no_change': {
                'en': "❌ No command stored",
                'it': "❌ Nessun comando salvato",
            },
        },
        'description': {
            'en': "Edit the @BotFather commands",
            'it': "Modifica i comandi con @BotFather",
        },
        'error': {
            'en': "❌ Error! ❌",
            'it': "❌ Errore! ❌",
        },
        'get': {
            'empty': {
                'en': "No command set yet. You may use <code>✏️ Change</code> "
                      "button",
                'it': "Nessun comando impostato ancora. Puoi usare il bottone "
                      "<code>✏️ Modifica</code>",
            },
            'panel': {
                'en': "🤖 <b>BotFather commands</b> ℹ️\n\n"
                      "{commands}",
                'it': "🤖 <b>Comandi su BotFather</b> ℹ️\n\n"
                      "{commands}",
            },
        },
        'modes': [
            {
                'id': "get",
                'name': {
                    'en': "See",
                    'it': "Consulta"
                },
                'symbol': "ℹ️",
                'description': {
                    'en': "See commands stored by @BotFather",
                    'it': "Consulta i comandi salvati su @BotFather"
                },
            },
            {
                'id': "set",
                'name': {
                    'en': "Change",
                    'it': "Modifica"
                },
                'symbol': "✏️",
                'description': {
                    'en': "Change commands stored by @BotFather",
                    'it': "Modifica i comandi salvati su @BotFather"
                },
            },
            {
                'id': "del",
                'name': {
                    'en': "Delete",
                    'it': "Cancella"
                },
                'symbol': "🗑",
                'description': {
                    'en': "Delete commands stored by @BotFather",
                    'it': "Cancella i comandi salvati su @BotFather"
                },
            },
            {
                'id': "settings",
                'name': {
                    'en': "Settings",
                    'it': "Impostazioni"
                },
                'symbol': "⚙️",
                'description': {
                    'en': "Set commands to hide or to add",
                    'it': "Imposta comandi da nascondere o aggiungere"
                },
            },
        ],
        'set': {
            'button': {
                'en': "⚠️ Set these commands 🔧",
                'it': "⚠️ Imposta questi comandi 🔧",
            },
            'done': {
                'en': "✅ Done!",
                'it': "✅ Fatto!",
            },
            'error': {
                'en': "Something went wrong 😕",
                'it': "Qualcosa è andato storto 😕",
            },
            'header': {
                'en': "✏️ <b>Change commands stored by @BotFather 🤖</b>",
                'it': "✏️ <b>Modifica i comandi salvati su @BotFather 🤖</b>",
            },
            'legend': {
                'en': "<b>Legend</b>\n"
                      "✅ <i>Already stored</i>\n"
                      "✏️ <i>New description</i>\n"
                      "☑ <i>New command</i>\n"
                      "❌ <i>Will be removed</i>",
                'it': "<b>Legenda</b>\n"
                      "✅ <i>Già presente</i>\n"
                      "✏️ <i>Nuova descrizione</i>\n"
                      "☑ <i>Nuovo comando</i>\n"
                      "❌ <i>Comando da eliminare</i>",
            },
            'no_change': {
                'en': "❌ No change detected",
                'it': "❌ Nessuna modifica",
            },
        },
        'settings': {
            'browse_records': {
                'en': "✏️ <b>Edit BotFather settings</b> ⚙️\n\n"
                      "Select a record to edit.\n\n"
                      "{commands_list}\n\n"
                      "<i>Legend</i>\n"
                      "➕ Added commands\n"
                      "➖ Hidden commands\n\n"
                      "Showing records from {record_interval[0]} to "
                      "{record_interval[1]} of {record_interval[2]}",
                'it': "✏️ <b>Modifica impostazioni di BotFather</b> ⚙\n\n️"
                      "Seleziona un'impostazione da modificare.\n\n"
                      "{commands_list}\n\n"
                      "<i>Legenda</i>\n"
                      "➕ Comandi aggiunti\n"
                      "➖ Comandi nascosti\n\n"
                      "Record da {record_interval[0]} a "
                      "{record_interval[1]} di {record_interval[2]}",
            },
            'modes': {
                'add': {
                    'add': {
                        'done': {
                            'en': "➕️️ <b>Added additional command</b>\n\n"
                                  "Command: {command}\n"
                                  "Description: {description}",
                            'it': "➕️️ <b>Inserito comando aggiuntivo</b>\n\n"
                                  "Comando: {command}\n"
                                  "Descrizione: {description}",
                        },
                        'popup': {
                            'en': "Write the command to add",
                            'it': "Scrivimi il comando da aggiungere",
                        },
                        'text': {
                            'en': "Write the command to add or /cancel this operation",
                            'it': "Scrivimi il comando da aggiungere o /annulla",
                        },
                    },
                    'description': {
                        'en': "Add command to default list",
                        'it': "Aggiungi un comando dalla lista autogenerata"
                    },
                    'edit': {
                        'done': {
                            'en': "✏️ <b>Edited additional command</b>\n\n"
                                  "Command: {command}\n"
                                  "Description: {description}",
                            'it': "✏️ <b>Comando da nascondere modificato</b>\n\n"
                                  "Comando: {command}\n"
                                  "Descrizione: {description}",
                        },
                    },
                    'error': {
                        'description_too_long': {
                            'en': "<b>Description is too long</b>\n\n"
                                  "Description length must be 3-256 chars.",
                            'it': "<b>Descrizione troppo lunga</b>\n\n"
                                  "La descrizione deve essere di 3-256 caratteri.",
                        },
                        'duplicate_record': {
                            'en': "<b>Duplicate record</b>\n\n"
                                  "Command is already being added to default "
                                  "output. Edit that record if you need to.",
                            'it': "<b>Record già presente</b>\n\n"
                                  "Questo comando è già aggiunto a quelli di "
                                  "default. Modifica il record già presente se "
                                  "necessario.",
                        },
                        'missing_description': {
                            'en': "<b>Missing description</b>\n\n"
                                  "Additional commands must have a description "
                                  "(3-256 chars).",
                            'it': "<b>Descrizione mancante</b>\n\n"
                                  "I comandi aggiuntivi devono avere una "
                                  "descrizione di 3-256 caratteri.",
                        },
                        'unhandled_exception': {
                            'en': "❌ <b>Unhandled exception </b> ⚠️",
                            'it': "❌ <b>Errore imprevisto </b> ⚠️",
                        },
                    },
                    'name': {
                        'en': "Add",
                        'it': "Aggiungi"
                    },
                    'symbol': "➕️",
                },
                'hide': {
                    'add': {
                        'done': {
                            'en': "➖ <b>Added hidden command</b>\n\n"
                                  "Command: {command}\n",
                            'it': "➖ <b>Comando da nascondere aggiunto</b>"
                                  "Comando: {command}\n",
                        },
                        'popup': {
                            'en': "Write the command to hide",
                            'it': "Scrivimi il comando da nascondere",
                        },
                        'text': {
                            'en': "Write the command to hide or /cancel this operation",
                            'it': "Scrivimi il comando da nascondere o /annulla",
                        }
                    },
                    'description': {
                        'en': "Hide command from default list",
                        'it': "Nascondi un comando dalla lista autogenerata"
                    },
                    'edit': {
                        'done': {
                            'en': "✏️ <b>Edited hidden command</b>\n\n"
                                  "Command: {command}\n"
                                  "Description: {description}",
                            'it': "✏️ <b>Comando da nascondere modificato</b>\n\n"
                                  "Comando: {command}\n"
                                  "Descrizione: {description}",
                        },
                    },
                    'name': {
                        'en': "Hide",
                        'it': "Nascondi"
                    },
                    'symbol': "➖️",
                },
                'edit': {
                    'button': {
                        'en': "✏️ Edit record",
                        'it': "✏️ Modifica record"
                    },
                    'description': {
                        'en': "Edit added or hidden commands",
                        'it': "Modifica i comandi aggiunti o nascosti"
                    },
                    'edit': {
                        'popup': {
                            'en': "Write the new description",
                            'it': "Scrivimi la nuova descrizione",
                        },
                        'text': {
                            'en': "Write the new description for command "
                                  "{command} or /cancel",
                            'it': "Scrivimi la nuova descrizione per il  "
                                  "comando {command} o /annulla",
                        },
                        'done': {
                            'en': "✏️ Edit succeeded ✅\n\n"
                                  "Command: {command}\n"""
                                  "Description: {description}",
                            'it': "✏️ Modifica completata ✅\n\n"
                                  "Comando: {command}\n"""
                                  "Descrizione: {description}",
                        }
                    },
                    'name': {
                        'en': "Edit",
                        'it': "Modifica"
                    },
                    'panel': {
                        'delete': {
                            'button': {
                                'en': "❌ Delete record",
                                'it': "❌ Elimina record",
                            },
                            'done': {
                                'popup': {
                                    'en': "Record deleted ✅",
                                    'it': "Record eliminato ✅",
                                },
                                'text': {
                                    'en': "Record deleted ✅",
                                    'it': "Record eliminato ✅",
                                },
                            },
                        },
                        'edit_description': {
                            'button': {
                                'en': "✏️ Edit description",
                                'it': "✏️ Modifica descrizione",
                            },
                        },
                        'text': {
                            'en': "✏️ Edit record ✅\n\n"
                                  "Command: {command}\n"""
                                  "Description: {description}",
                            'it': "✏️ Modifica record\n\n"
                                  "Comando: {command}\n"""
                                  "Descrizione: {description}",
                        },
                    },
                    'symbol': "✏️",
                },
            },
            'panel': {
                'en': "🤖 <b>@BotFather settings</b> ⚙️\n\n"
                      "➕ <i>Additional commands</i>\n"
                      "{additional_commands}\n\n"
                      "➖ <i>Hidden commands</i>\n"
                      "{hidden_commands}",
                'it': "⚙️ <b>Impostazioni di @BotFather</b> 🤖\n\n"
                      "➕ <i>Comandi aggiuntivi</i>\n"
                      "{additional_commands}\n\n"
                      "➖ <i>Comandi nascosti</i>\n"
                      "{hidden_commands}",
            },
        },
        'title': {
            'en': "🤖 <b>BotFather</b>",
            'it': "🤖 <b>BotFather</b>",
        },
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
    'new_version': {
        'title': {
            'en': "🔔 New version installed ✅",
            'it': "🔔 Rilevata nuova versione installata! ✅",
        },
        'last_commit': {
            'en': "Old commit: <code>{old_record[last_commit]}</code>\n"
                  "New commit: <code>{new_record[last_commit]}</code>",
            'it': "Vecchio commit: <code>{old_record[last_commit]}</code>\n"
                  "Nuovo commit: <code>{new_record[last_commit]}</code>",
        },
    },
    'query_button': {
        'error': {
            'en': "Error!",
            'it': "Errore!",
        },
        'file_name': {
            'en': "Query result.csv",
            'it': "Risultato della query.csv",
        },
        'empty_file': {
            'en': "No result to show.",
            'it': "Nessun risultato da mostrare.",
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
    'select_command': {
        'description': {
            'en': "Receive the result of a SELECT query performed on bot "
                  "database",
            'it': "Ricevi il risultato di una query SQL di tipo SELECT "
                  "sul database del bot"
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
    'talk_command': {
        'description': {
            'en': "Choose a user and forward messages to each other",
            'it': "Scegli un utente e il bot farà da tramite inoltrando a "
                  "ognuno i messaggi dell'altro finché non terminerai la "
                  "sessione"
        }
    },
    'updates_available': {
        'header': {
            'en': "🔔 Updates available! ⬇️\n\n"
                  "Click to /restart bot",
            'it': "🔔 Aggiornamenti disponibili! ⬇\n\n"
                  "Clicka qui per fare il /restart",
        },
    },
    'version_command': {
        'all_packages_updated': {
            'en': "⌛️ All packages are updated! ✅",
            'it': "⌛️ Tutti i pacchetti sono aggiornati! ✅",
        },
        'checking_for_updates': {
            'en': "⏳ Checking for updates... ☑️",
            'it': "⏳ Sto cercando aggiornamenti... ☑️",
        },
        'description': {
            'en': "Get packages version and source code last commit",
            'it': "Chiedi la versione dei pacchetti e del codice sorgente",
        },
        'header': {
            'en': "ℹ️ Version information #️⃣\n\n"
                  "Last commit: <code>{last_commit}</code>",
            'it': "ℹ️ Informazioni sulle versioni dei pacchetti #️⃣\n\n"
                  "Ultimo commit: <code>{last_commit}</code>"
        },
        'help_section': None,
        'reply_keyboard_button': {
            'en': "Version #️⃣",
            'it': "Versione #️⃣",
        },
    },
}

default_authorization_messages = {
    'auth_command': {
        'description': {
            'en': "Edit user permissions. To select a user, reply to "
                  "a message of theirs or write their username",
            'it': "Cambia il grado di autorizzazione di un utente "
                  "(in risposta o scrivendone lo username)"
        },
        'unhandled_case': {
            'en': "<code>Unhandled case :/</code>",
            'it': "<code>Caso non previsto :/</code>"
        },
        'instructions': {
            'en': "Reply with this command to a user or write "
                  "<code>/{command} username</code> to edit their permissions.",
            'it': "Usa questo comando in risposta a un utente "
                  "oppure scrivi <code>/{command} username</code> per "
                  "cambiarne il grado di autorizzazione."
        },
        'unknown_user': {
            'en': "Unknown user.",
            'it': "Utente sconosciuto."
        },
        'choose_user': {
            'en': "{n} users match your query. Please select one.",
            'it': "Ho trovato {n} utenti che soddisfano questi criteri.\n"
                  "Per procedere selezionane uno."
        },
        'no_match': {
            'en': "No user matches your query. Please try again.",
            'it': "Non ho trovato utenti che soddisfino questi criteri.\n"
                  "Prova di nuovo."
        }
    },
    'ban_command': {
        'description': {
            'en': "Reply to a user with /ban to ban them",
            'it': "Banna l'utente (da usare in risposta)"
        }
    },
    'auth_button': {
        'description': {
            'en': "Edit user permissions",
            'it': "Cambia il grado di autorizzazione di un utente"
        },
        'confirm': {
            'en': "Are you sure?",
            'it': "Sicuro sicuro?"
        },
        'back_to_user': {
            'en': "Back to user",
            'it': "Torna all'utente"
        },
        'permission_denied': {
            'user': {
                'en': "You cannot appoint this user!",
                'it': "Non hai l'autorità di modificare i permessi di questo "
                      "utente!"
            },
            'role': {
                'en': "You're not allowed to appoint someone to this role!",
                'it': "Non hai l'autorità di conferire questo permesso!"
            }
        },
        'no_change': {
            'en': "No change suggested!",
            'it': "È già così!"
        },
        'appointed': {
            'en': "Permission granted",
            'it': "Permesso conferito"
        }
    },
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

default_useful_tools_messages = {
    'calculate_command': {
        'description': {
            'en': "Do calculations",
            'it': "Calcola",
        },
        'help_section': None,
        'instructions': {
            'en': "🔢 <b>Calculator</b> 🧮\n\n"
                  "Enter an algebraic expression after /calc to get its "
                  "result, or use the command in reply to a message containing "
                  "an expression, or use the keyboard below.\n\n"
                  "- <code>ℹ️</code>: show information about special keys\n",
            'it': "🔢 <b>Calcolatrice</b> 🧮\n\n"
                  "Inserisci un'espressione algebrica dopo /calcola per "
                  "ottenerne il risultato, oppure usa il comando in risposta, "
                  "o ancora usa la tastiera qui sotto.\n\n"
                  "- <code>ℹ️</code>: mostra informazioni sui tasti speciali\n",
        },
        'invalid_expression': {
            'en': "Invalid expression: {error}",
            'it': "Espressione non valida: {error}",
        },
        'language_labelled_commands': {
            'en': "calculate",
            'it': "calcola",
        },
        'message_input': {
            'en': "🔢 <b>Calculator</b> 🧮\n\n"
                  "<i>Enter an expression</i>",
            'it': "🔢 <b>Calcolatrice</b> 🧮\n\n"
                  "<i>Mandami l'espressione</i>",
        },
        'special_keys': {
            'en': "<b>Special keys</b>\n"
                  "- <code>**</code>: exponentiation\n"
                  "- <code>//</code>: floor division\n"
                  "- <code>mod</code>: modulus (remainder of division)\n"
                  "- <code>MR</code>: result of last expression\n"
                  "- <code>ℹ️</code>: show this help message\n"
                  "- <code>💬</code>: write your expression in a message\n"
                  "- <code>⬅️</code>: delete last character\n"
                  "- <code>✅</code>: start a new line (and a new expression)\n",
            'it': "<b>Tasti speciali</b>\n"
                  "- <code>**</code>: elevamento a potenza\n"
                  "- <code>//</code>: quoziente della divisione\n"
                  "- <code>mod</code>: resto della divisione\n"
                  "- <code>MR</code>: risultato dell'espressione precedente\n"
                  "- <code>ℹ️</code>: mostra questo messaggio\n"
                  "- <code>💬</code>: invia un messaggio con l'espressione\n"
                  "- <code>⬅️</code>: cancella ultimo carattere\n"
                  "- <code>✅</code>: vai a capo (inizia una nuova espressione)\n",
        },
        'use_buttons': {
            'en': "Use buttons to enter an algebraic expression.\n\n"
                  "<i>The input will be displayed after you stop typing for a "
                  "while.</i>",
            'it': "Usa i pulsanti per comporre un'espressione algebrica.\n\n"
                  "<i>L'espressione verrà mostrata quando smetterai di "
                  "digitare per un po'.</i>",
        },
        'result': {
            'en': "🔢 <b>Calculator</b> 🧮\n\n"
                  "<i>Expressions evaluation:</i>\n\n"
                  "{expressions}",
            'it': "🔢 <b>Calcolatrice</b> 🧮\n\n"
                  "<i>Risultato delle espresisoni:</i>\n\n"
                  "{expressions}",
        },
    },
    'info_command': {
        'description': {
            'en': "Use this command in reply to get information about a message",
            'it': "Usa questo comando in risposta per ottenere informazioni "
                  "su un messaggio",
        },
        'help_section': None,
        'instructions': {
            'en': "Use this command in reply to a message to get information "
                  "about it.",
            'it': "Usa questo comando in risposta per ottenere informazioni "
                  "su un messaggio.",
        },
        'result': {
            'en': "<i>Here is the information about the selected "
                  "message:</i>\n\n"
                  "<code>{info}</code>",
            'it': "<i>Ecco le informazioni sul messaggio selezionato:</i>\n\n"
                  "<code>{info}</code>",
        },
    },
    'length_command': {
        'description': {
            'en': "Use this command in reply to a message to get its length",
            'it': "Usa questo comando in risposta a un messaggio per sapere "
                  "quanti caratteri contenga",
        },
        'help_section': {
            'description': {
                'en': "Use the /length command in reply to a message to get "
                      "its length.\n"
                      "Beware that emojis may count as multiple characters.",
                'it': "Usa il comando /caratteri in risposta a un messaggio "
                      "per sapere quanti caratteri contenga.\n"
                      "Attenzione alle emoji, che contano come più caratteri.",
            },
            'label': {
                'en': "Length #️⃣",
                'it': "Caratteri #️⃣"
            },
            'name': "length",
        },
        'instructions': {
            'en': "Use this command in reply to a message to get its length.",
            'it': "Usa questo comando in risposta a un messaggio per sapere "
                  "quanti caratteri contenga.",
        },
        'language_labelled_commands': {
            'en': "length",
            'it': "caratteri",
        },
        'result': {
            'en': "<i>According to my calculations, this message is "
                  "</i><code>{n}</code><i> characters long.</i>",
            'it': "<i>Questo messaggio contiene </i><code>{n}</code><i> "
                  "caratteri secondo i miei calcoli.</i>",
        },
    },
    'ping_command': {
        'description': {
            'en': "Check if bot is online",
            'it': "Verifica se il bot è online",
        },
    },
    'when_command': {
        'description': {
            'en': "Use this command in reply to get information about a message",
            'it': "Usa questo comando in risposta per ottenere informazioni "
                  "su un messaggio",
        },
        'help_section': None,
        'forwarded_message': {
            'en': "<b>— Original message —</b>",
            'it': "<b>— Messaggio originale —</b>",
        },
        'instructions': {
            'en': "Use this command in reply to a message to get its original "
                  "sending time.",
            'it': "Usa questo comando in risposta per ottenere l'ora di invio "
                  "di un messaggio.",
        },
        'language_labelled_commands': {
            'en': "when",
            'it': "quando",
        },
        'who_when': {
            'en': "👤 {who}\n"
                  "🗓 {when:%Y-%m-%d ore %H:%M:%S}",
            'it': "👤 {who}\n"
                  "🗓 {when:%Y-%m-%d ore %H:%M:%S}",
        },
    }
}
