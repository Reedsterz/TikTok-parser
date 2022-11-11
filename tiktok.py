import sqlite3, argparse, json, xlsxwriter

def create_conn(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
    except Error as e:
        print(e)

    return conn

def parse_users(conn):
    c = conn.cursor()
    c.execute("""
    select
    uid, customID, nickname, signature
    from
    AwemeContactsV4
    """)

    records = c.fetchall()
    dict_user = {}

    for record in records:
        dict_user[record["uid"]] =  {}
        dict_user[record["uid"]]["customID"] = record["customID"]
        dict_user[record["uid"]]["nickname"] = record["nickname"]
        dict_user[record["uid"]]["signature"] = record["signature"]

    return dict_user

def parse_participants(conversationId, conn):
    c = conn.cursor()
    c.execute("""
    select
    userID,
    belongingConversationIdentifier
    from
    TIMParticipantORM
    """)

    records = c.fetchall()
    participants = []
    for record in records:
        if record["belongingConversationIdentifier"] == conversationId:
            participants.append(record["userID"])

    return participants

def parse_att(att):
    if att["nickname"]:
        print("nickname")
    elif att["secUID"]:
        print("secUID")

def parse_message(conn, dict_user, chat_db):
    c = conn.cursor()
    c.execute("""
    select
    identifier,
    belongingConversationIdentifier, sender,
    datetime(localCreatedAt, "unixepoch", "localtime") as timestamp,
    json_extract(content, '$.text') as message,
    json_extract(content, '$.tips') as localresponse,
    CASE
    	WHEN json_extract(content, '$.text') IS NULL then content
    END as attachments,
    CASE
    	WHEN deleted = 1 THEN "Yes"
    	WHEN deleted = 0 THEN "No"
    END as deleted,
    CASE
    	WHEN hasRead = 1 THEN "Yes"
    	WHEN hasRead = 0 THEN "No"
    END as hasRead
    from TIMMessageORM
    """)

    records = c.fetchall()
    list_message = []

    for record in records:
        conversationID = record["belongingConversationIdentifier"]

        participants = parse_participants(record["belongingConversationIdentifier"], conn)
        list_participants = []
        for participant in participants:
            list_participants.append(dict_user.get(str(participant), "{} : Unknown".format(str(participant))))

        sender = dict_user.get(record["sender"], "Unknown")
        timestamp = record["timestamp"]
        message = record["message"]
        if record["localresponse"] is not None:
            message = record["localresponse"]

        deleted = record["deleted"]
        hasRead = record["hasRead"]

        try:
            json.loads(record["attachments"])
            att = "stickers"
        except:
            att = ""
        finally:
            message_tuple = (conversationID, list_participants, sender, timestamp, message, deleted, hasRead, att)
            list_message.append(message_tuple)
            continue

    return list_message

def parse_message2(conn, dict_user, chat_db):
    c = conn.cursor()
    c.execute("""
    select
    identifier,
    belongingConversationIdentifier, sender,
    datetime(localCreatedAt, "unixepoch", "localtime") as timestamp,
    content,
    CASE
    	WHEN deleted = 1 THEN "Yes"
    	WHEN deleted = 0 THEN "No"
    END as deleted,
    CASE
    	WHEN hasRead = 1 THEN "Yes"
    	WHEN hasRead = 0 THEN "No"
    END as hasRead
    from TIMMessageORM
    """)

    records = c.fetchall()
    list_message = []

    for record in records:
        conversationID = record["belongingConversationIdentifier"]

        participants = parse_participants(record["belongingConversationIdentifier"], conn)
        list_participants = []
        for participant in participants:
            list_participants.append(dict_user.get(str(participant), "{} : Unknown".format(str(participant))))

        sender = dict_user.get(str(record["sender"]), "Unknown")
        timestamp = record["timestamp"]

        deleted = record["deleted"]
        hasRead = record["hasRead"]
        content, att = '', ''
        try:
            content = json.loads(record["content"])
            if ("text" in content):
                content = content["text"]
            elif ("tips" in content):
                content = content["tips"]
            else:
                content = ''
                att = "stickers"
        except:
            att = ""
        finally:
            message_tuple = (conversationID, list_participants, sender, timestamp, content, deleted, hasRead, att)
            list_message.append(message_tuple)
            continue

    return list_message

def print_participants(records):
    participants = ""
    for idx, record in enumerate(records):
        if 'customID' in record:
            participant = 'Participant {}:\nCustomID: {} \nNickname: {} \n'.format(str(idx + 1), record['customID'], record['nickname'])
        else:
            participant = 'Participant {}:\nUnknown\n'.format(str(idx + 1))
        participants += participant

    return participants

def print_senders(record):

    if 'customID' in record:
        sender = 'CustomID: {}\nNickname: {}'.format(record['customID'], record['nickname'])
    else:
        sender = 'Unknown'

    return sender

def write_excel(list_message, title):
    wb = xlsxwriter.Workbook("./{}.xlsx".format(title))
    worksheet = wb.add_worksheet()
    row = 1
    col = 0

    worksheet.write(0, col, '#')
    worksheet.write(0, col + 1, 'Conversation ID')
    worksheet.write(0, col + 2, 'Participants')
    worksheet.write(0, col + 3, 'Sender')
    worksheet.write(0, col + 4, 'Timestamp')
    worksheet.write(0, col + 5, 'Message')
    worksheet.write(0, col + 6, 'Deleted')
    worksheet.write(0, col + 7, 'Read')
    worksheet.write(0, col + 8, 'Attachments')

    try:
        for record in list_message:
            worksheet.write(row, col, row)
            worksheet.write(row, col + 1, str(record[0]))
            worksheet.write(row, col + 2, print_participants(record[1]))
            worksheet.write(row, col + 3, print_senders(record[2]))
            worksheet.write(row, col + 4, str(record[3]))
            worksheet.write(row, col + 5, str(record[4]))
            worksheet.write(row, col + 6, str(record[5]))
            worksheet.write(row, col + 7, str(record[6]))
            worksheet.write(row, col + 8, str(record[7]))
            row = row + 1
    except Exception as e:
        print(e)

    wb.close()

def main():
    print("===TikTok Parser===")

    parser = argparse.ArgumentParser(description = "===TikTok Parser===")
    required_args = parser.add_argument_group("required_args")
    required_args.add_argument("-u", required = True, help = "User database file")
    required_args.add_argument("-f", required = True, help = "Chat database file")
    required_args.add_argument("-o", required = True, help = "Output file")
    args = parser.parse_args()

    user_db = args.u
    chat_db = args.f
    output_file = args.o

    conn_user = create_conn(user_db)
    dict_user = parse_users(conn_user)
    conn_msg = create_conn(chat_db)
    list_message = parse_message2(conn_msg, dict_user, chat_db)
    write_excel(list_message, output_file)

if __name__ == "__main__":
    main()
