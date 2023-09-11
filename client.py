import protocol
from protocol import EmptyInput
from protocol import QuitInput
import socket

# USER ACTIONS:
# "VIEW MANAGERS", "VIEW USERS"
# SEND A PRIVATE MESSAGE: "!talmid2 hello" - a private hello massage to talmid 2

# ADMIN ACTIONS:
# TO MAKE ANOTHER CLIENT ADMIN: PROMOTE "(NAME OF THE USER)"
# TO REMOVE A CLIENT: REMOVE "(NAME OF THE USER)"
# TO MUTE A A CLIENT: MUTE "(NAME OF THE USER)"


messages_received = []

def run_the_client():
    input_chars = []  # will be the user input
    client_socket = socket.socket()
    client_socket.connect((protocol.SERVER_IP, protocol.SERVER_PORT))
    client_socket.setblocking(False)
    print("I joined to the server")
    messages_received.append("I joined to the server")

    while True:
        # if the input is not null, we send it to the server
        try:
            income_message = protocol.receive_msg(client_socket)  # the message is already contains the data about the sender
            print(income_message)
            messages_received.append(income_message)
            if income_message == "You have been kicked out from the chat!":
                messages_received.append(income_message)
                client_socket.close()
                break
        except (BlockingIOError, ValueError):
            pass

        try:

            is_input_ready, input_chars = protocol.get_input(input_chars)
            if is_input_ready is True:  # if the input is ready, we need to prepare for sending
                message = ''.join(input_chars)  # return a decode string
                client_socket.send(protocol.create_msg(message))
                input_chars = []  # reset it for the next input
                if message == "quit" or message == "Quit":
                    raise QuitInput

        except (EmptyInput, QuitInput):
            print("You have left the chat")
            messages_received.append("You have left the chat")
            client_socket.close()
            break


run_the_client()