import cantools

def load_dbc(path="Voltage check/db/battery.dbc"):
    return cantools.database.load_file(path)

def decode_message(db, msg_id, data):
    message = db.get_message_by_frame_id(msg_id)
    return message.decode(data)
