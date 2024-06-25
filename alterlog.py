#rename this program later

"""
Program operation:

Before doing anything:
-make sure any imports are present if you need to install anything

On first setup (i.e. no database file detected):
1: Ask if the user would like to set a root password
    -if no input or "no", continue
    -if yes, prompt them for the password and have them retype it for security
        -if they dont match, ask again and loop. If they do, continue
    -compute a salt, hash the password
2: create the database file
3: set up the Profiles table, Messages table
    -Profiles contains id, string name, password hash, password salt, serialized list of messages they can view, serialized list of messages they have already viewed
    -Messages contains id, author id, string subject, string body, published date, 'everyone can view' boolean
4: display help menu
5: continue to CLI mode

On subsequent runs, immediately enter CLI mode

CLI Mode:
    Available commands:
        1: login
            input: profile name, password (optional)
            output: logs the user in if the password is accepted and the account exists

        2: view
            input: msg number (not the id)
            output: display of the message in a pleasing format

        3: msg
            input: none or a list of profile names
            function: 
                1: prompt the user for a subject, up to 180 characters
                2: prompt the user for a message to send, an arbitrary number of characters (4096 is a good num)
                3: display the message back to the user, ask if it looks right
                4: insert the message into the database, based on the ids of the users in the profile list. If it was None, display it to all

        4: delete
            input: a message id to delete
            output: a confirmation message if theyre allowed to delete it

        5: reset
            input: none
            function: 
                1: asks user to confirm (Y/N)
                2: if not "Y" or "yes", bail
                3: delete the database file and close the program

        6: viewall
            input: none
            output: re-displays all the available messages in a table, ordered by most recent publish date

        7: logout
            input: none
            output: logs the user out, back to the root

        8: viewmine
            input: none
            output: all the existing messages the user has sent
        
        9: createprofile
            input: profile name, password
            output: creates the profile and logs the user into it. If the profile already exists, fail and display a message

        10: exit
            input: none
            output: closes the program

        11: help
            input: none
            output: help menu explaining each command

    Mode of Operation:
        1: Prompt the user to log in or create a profile
        2: On login or profile creation, display all messages, like how the viewall command works
        3: repeatedly allow the user to enter commands until the program closes
"""

import os
import hashlib
import sqlite3

from datetime import datetime

DB_PATH = "alterlog.db"

CREATE_PROFILES_TABLE_QRY = """
    CREATE TABLE IF NOT EXISTS Profiles (
        id               INTEGER PRIMARY KEY AUTOINCREMENT
        ,name            TEXT
        ,pwd_hash        BLOB
        ,pwd_salt        INT
    );
"""

CREATE_LINKING_TABLE_QRY = """
    CREATE TABLE IF NOT EXISTS Profile_Message_Link ( 
        profile_id          INT 
        ,message_id         INT 
        ,already_viewed     BOOLEAN DEFAULT FALSE
        ,FOREIGN KEY(profile_id) REFERENCES Profiles(id) ON DELETE CASCADE
        ,FOREIGN KEY(message_id) REFERENCES Messages(id) ON DELETE CASCADE 
    ); --TODO need an index on profile id and message id
"""

CREATE_LINKING_INDEX_QRY = """
    CREATE INDEX IF NOT EXISTS idx_Profile_Message_Link 
    ON Profile_Message_Link 
    (profile_id, message_id);
"""

CREATE_MESSAGES_TABLE_QRY = """
    CREATE TABLE IF NOT EXISTS Messages (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT --alias for ROWID in sqlite
        ,author_id              INT 
        ,subject                TEXT
        ,body                   TEXT
        ,published_date         DATETIME
        ,available_to_everyone  BOOLEAN
        ,FOREIGN KEY(author_id) REFERENCES Profiles(id) ON DELETE CASCADE
    );
"""

RESET_DB_QRY = """
    DROP TABLE Profiles;
    DROP TABLE Profile_Message_Link;
    DROP TABLE Messages;
"""

#TODO Enhancement for later: turn this into a list of help commands that can be printed individually or combined 
#eventually: have "delete profile" ability
HELP_MSG = """
Available commands:

    login: 
        log in to a profile
        input: login [profilename] [password]
        output: Welcome message if the password is correct, error message otherwise otherwise.
    logout: 
        log out of the current profile
        input: logout
        output: No output. Silently logs the profile out.
    view: 
        view a single message in detail
        input: view [msgnum]
        output:
    viewall: 
        view all messages the current profile has available, sorted by most recent
        input: viewall [Y/N see already viewed messages]
        output: a table of messages
    viewmine: 
        view a list of all messages the current profile has sent
        input: viewmine
        output: a table of messages
    msg:
        write a message to be delivered to other profiles
        input: msg [space-separated list of profiles to send to]
        output: Prompts for a subject, then a body. 
    delete
        delete a message that the current profile has written, and remove it everywhere
        input: delete [msgnum]
        output: no output, message is deleted silently
    reset
        resets the entire application back to its install state
        NOTE: testing purposes only! 
        input: reset
        output: deletes all profiles and messages, removes the root password, and closes the program
    create_profile
        generates a new profile with an optional password
        input: 
        output:
    help
        input: help
        output: displays this help message
    exit
        input: exit
        output: Silently terminates the program
"""




class CLIController:
    def __init__(self, conn : sqlite3.Connection):
        #needs info on the current profile, the connection, and maybe(?) the cursor
        #ALL OF THE BELOW FUNCTIONS SHOULD RETURN TRUE IF EXECUTION SHOULD CONTINUE, FALSE OTHERWISE
        self.conn = conn
        self.profile = None
        pass

    def login(self, profile_name, password):

        if self.profile is None:

            cur = self.conn.cursor()
            res = cur.execute("SELECT id, pwd_hash, pwd_salt FROM Profiles WHERE name = ?", [profile_name])
            tab = res.fetchone()

            if tab is None:
                print(f"Profile with name {profile_name} does not exist")
            else:
                profile_id, stored_hash, stored_salt = tab["id"], tab["pwd_hash"], tab["pwd_salt"] #TODO broken, does not work
                if stored_hash == 0 and stored_salt == 0: #no password on the account
                    self.profile = profile_id
                else:
                    given_hash = get_hash(password, stored_salt)
                    if given_hash == stored_hash:
                        self.profile = profile_id
                    else:
                        print("Password does not match stored password")

        else:
            print("Already signed in. Log out to log in as another account")

        return True

    def logout(self):
        self.profile = None
        return True

    def view(self, msg_viewnum): #TODO not secure, anyone who knows the id of a message can view it regardless of whether it was sent to them.
        cur = self.conn.cursor()
        res = cur.execute("SELECT name, subject, body, available_to_everyone FROM Messages m INNER JOIN Profiles p ON p.id = m.author_id WHERE m.id = ?", [msg_viewnum])
        if res is not None:
            name, subject, body, sent_to_all = res.fetchone()
            print(f"From: {name}")
            print(f"Subject: {subject}")
            print(f"{body}\n\n")

            if not sent_to_all:
                cur.execute("UPDATE Profile_Message_Link SET already_viewed = TRUE WHERE profile_id = ? AND message_id = ?", [self.profile, msg_viewnum])
                self.conn.commit()
        else:
            print("No message with that ID found")
        return True

    def viewall(self, show_already_viewed): 
        cur = self.conn.cursor()
        res = cur.execute("SELECT message_id FROM Profile_Message_Link WHERE profile_id = ?", [self.profile])
        msg_ids = res.fetchall()

        #select messages from message table where message id matches or available to all is TRUE
        res = cur.execute( 
            """
                SELECT m.id, p.name, m.subject, m.published_date 
                FROM Profile_Message_Link l
                INNER JOIN Messages m
                    ON m.id = l.message_id 
                INNER JOIN Profiles p
                    ON p.id = m.author_id
                WHERE already_viewed = ? AND l.profile_id = ?
                ORDER BY m.published_date DESC
            """, [show_already_viewed, self.profile])
        tab = res.fetchall()

        #if we wanted to get rid of this two-query step, we would need to remove available_to_everyone and make insertion use a cross apply/cross join
        res = cur.execute("SELECT m.id, p.name, subject, published_date FROM Messages m LEFT JOIN Profiles p ON m.author_id = p.id WHERE m.available_to_everyone IS TRUE")
        tab += res.fetchall()

        self.print_table(tab)

        return True

    def viewmine(self): 
        cur = self.conn.cursor()

        res = cur.execute("SELECT name FROM Profiles WHERE id = ?", [self.profile])
        name = cur.fetchone()[0]

        res = cur.execute("SELECT id, ? AS name, subject, published_date FROM Messages WHERE author_id = ?", [name, self.profile])
        tab = res.fetchall()
        #get the author's name in an independent query, no need for joining since theyre all the same


        self.print_table(tab)

        return True

    def msg(self, recipients : list):
        #params should be a list of profiles
        send_to_all = len(recipients) == 0
        subj = input("Input subject: ")
        body = input("Input body: ")

        
        cur = self.conn.cursor()
        cur.execute("INSERT INTO Messages (author_id, subject, body, published_date, available_to_everyone) VALUES (?, ?, ?, ?, ?);",
                    [self.profile, subj, body, datetime.now().isoformat(), send_to_all])
        
        if not send_to_all:
            res = cur.execute("SELECT max(id) FROM Messages;")
            message_id = res.fetchone()[0]

            #currently has to be dynamic because of how sqlite works
            #NOT SECURE! Change this when you move to a non-prototype version
            sql_statement = f"""
                INSERT INTO Profile_Message_Link (profile_id, message_id) 
                SELECT id, ? FROM profiles WHERE name IN ({"'"+"','".join(recipients)+"'"})
                ;"""
            cur.execute(sql_statement, [message_id])


        self.conn.commit()
        return True

    def delete(self, msg_id):

        cur = self.conn.cursor()
        res = cur.execute("SELECT id, author_id FROM Messages WHERE id = ? AND author_id = ?", [msg_id, self.profile])
        if res.fetchone() is None:
            print("Message does not exist or you do not have access")
        else:
            cur.execute("DELETE FROM Messages WHERE id = ? AND author_id = ?", [msg_id, self.profile])
        self.conn.commit()
        return True

    def reset(self):
        cur = self.conn.cursor()
        cur.executescript(RESET_DB_QRY)
        self.conn.commit()
        return False

    def create_profile(self, profile_name : str, pwd : str = None):
        profile_name = profile_name.replace(" ", "_")
        digest = 0
        salt = 0
        if pwd is not None:
            salt = os.urandom(8)
            digest = get_hash(pwd, salt)

        cur = self.conn.cursor()
        res = cur.execute("SELECT * FROM Profiles WHERE name = ?", [profile_name])
        if res.fetchone() is None:
            cur.execute("INSERT INTO Profiles (name, pwd_hash, pwd_salt) VALUES (?, ?, ?)", [profile_name, digest, salt])
            self.conn.commit()
        else:
            print("Profile with that name already exists")
        return True

    def help(self):
        print(HELP_MSG)
        return True

    def exit(self): #kept because later we might use exit() to do cleanup tasks
        return False
    
    def print_table(self, table):
        #assume terminal width is 80 characters
        #only prints message id, name, subject, and date
        #let name take up 20 chars, id take 4, date take 10, subject take the rest
        #TODO finish the pretty print
        print("id | name | subject | date")
        for t in table:
            print(f"{t["id"]}|{t["name"]}|{t["subject"]}|{t["published_date"]}")

    def translate_input(self, instr : str): #returns whether execution should continue after this
        in_arr = instr.lower().split() #TODO not pythonic, probably a better way of doing this. ALSO WE NEED TO DO BOUNDS CHECKING, WHAT IF THERE ARE <1 SPACES?!
        opcode = in_arr[0]
        params = []
        if len(in_arr) > 1:
            params = in_arr[1:]

        ret = False

        if self.profile is None and opcode in ['logout', 'view', 'viewall', 'msg', 'delete']:
            print("Must be logged in to complete this action")
            return True
        
        if len(params) == 0 and opcode in ['create_profile', 'login', 'view', 'delete']:
            print("Not enough arguments supplied. See help menu")
            return True

        if opcode == 'login': #probably a more pythonic way to do this
            if len(params) == 1:
                params.append('')
            profile, pwd = params
            ret = self.login(profile, pwd)
        elif opcode == 'logout':
            ret = self.logout()
        elif opcode == 'view':
            ret = self.view(int(params[0]))
        elif opcode == 'viewall':
            show_already_viewed = False
            if len(params) > 0:
                show_already_viewed = params[0].upper() == 'Y'
            ret = self.viewall(show_already_viewed)
        elif opcode == 'viewmine':
            ret = self.viewmine()
        elif opcode == 'msg':
            ret = self.msg(params)
        elif opcode == 'delete':
            ret = self.delete(int(params[0]))
        elif opcode == 'reset':
            ret = self.reset()
        elif opcode == 'create_profile':
            if len(params) == 1:
                params.append(None)
            ret = self.create_profile(params[0], params[1])
        elif opcode == 'help':
            ret = self.help()
        elif opcode == 'exit':
            ret = self.exit()
        else:
            print("Unrecognized command")
            ret = True

        return ret


def get_hash(pwd, salt):
    hasher = hashlib.sha256()
    hasher.update(bytes([ord(c) for c in pwd]))
    hasher.update(salt)

    return hasher.digest()


def setup_db(conn : sqlite3.Connection):
    cur = conn.cursor()
    cur.execute(CREATE_MESSAGES_TABLE_QRY)
    cur.execute(CREATE_LINKING_TABLE_QRY)
    cur.execute(CREATE_PROFILES_TABLE_QRY)
    cur.execute(CREATE_LINKING_INDEX_QRY)
    conn.commit()
    cur.close()


def validate_root(conn : sqlite3.Connection):
    #return True if the user's input matches the root password or if a root password is explicitly not set, False otherwise
    #if the root entry just doesnt exist, ask the user if they want to create a root password
    #TODO clean this function up a bit, try/except/finally block
    cur = conn.cursor()

    res = cur.execute("SELECT pwd_hash, pwd_salt FROM Profiles WHERE id = 0") #id 0 is reserved for the root
    row = res.fetchone()

    if row is None:
        create_pwd = input("Would you like to create a root password? Y/N: ").strip().upper()
        if create_pwd[0] == 'Y':
            pwd = input("Input root password: ")
            salt = os.urandom(8)

            digest = get_hash(pwd, salt)

            cur.execute("INSERT INTO Profiles (id, name, pwd_hash, pwd_salt) VALUES (0, ?, ?, ?)", ['root', digest, salt])

        else:
            cur.execute("INSERT INTO Profiles (id, name, pwd_hash, pwd_salt) VALUES (0, 'root', 0, 0)")

        return True
    
    else:
        target_hash, salt = row

        if target_hash == 0 and salt == 0:
            return True
        
        given_pwd = input("Input root password: ")

        hasher = hashlib.sha256()
        hasher.update(bytes([ord(c) for c in given_pwd]))
        hasher.update(salt)

        if hasher.digest() == target_hash:
            return True

        print("Passwords don't match")
    
    return False


def main():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        sqlite3.register_adapter(datetime.date, lambda x : x.isoformat()) #TODO change this so the format is nicer ('YYYY-MM-DD HH:MM:SS')
        setup_db(conn)

        if validate_root(conn):
            controller = CLIController(conn)
            controller.help()

            while controller.translate_input(input("")):
                pass

    return 0

if __name__ == "__main__":
    main()