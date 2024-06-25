Installation:

This program requires Python 3 and the sqlite3 package. By default, sqlite3 now comes bundled with Python installations, but if you're using an older version
you may have to install it manually. Use this command:

pip install sqlite3

Other than this requirement alterlog runs entirely on vanilla python. Note that this may change in the future, depending on what features might be 
added (a GUI comes to mind). Nevertheless, this program is ultimately a prototype. It should be considered a rough draft, and will be rewritten in a more user-
friendly style in the future. 


Usage and Options:

To run the program, use this command. You may have to add your python installation to your PATH:

python alterlog.py

You will be given the option to set a root password. No encryption is performed, and the password is not strictly required even when set. This feature is a mock-up and the 
application should NOT be considered secure, even when a root password is set. Subsequent logins will require the root password if it is set.

Once initialization is complete, the user will need to create a profile using the 'create_profile' command. A profile name is required, and a password may optionally be 
provided. An arbitrary number of profiles are allowed. Once the profile exists, the user may log in to that profile with the login command. Logging in allows the user to 
send, view, and delete messages. Using the 'msg' command allows you to write a message with a subject and body, and specify which other profiles it will be available to. If 
no profiles are provided, it will be sent to all of them.

Viewing a message requires knowing its id. Use the 'viewall' command to view unread messages, then look in detail at the message by using 'view [id]'. Once the message is 
viewed by a profile, it will still be available, but it will not show up in the 'viewall' command. Use 'viewall Y' to enable viewing already-read messages.

Deleting a message also requirs knowing its id. Use the 'viewmine' command to see which messages the current profile has sent. Then, use 'delete [id]' to delete that 
message. Deleting a message removes it everywhere.

Bug reporting:

As this is a prototype program there are bound to be bugs. Submit bugs to the Github issue page or tell me directly. I will try to have them fixed quickly. This program will 
be the template for the eventual complete app, so it is important to have the control flow and SQL functions be as bug-free as possible.