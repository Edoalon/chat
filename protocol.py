import msvcrt
import time

SERVER_IP = "127.0.0.1"
SERVER_PORT = 1235
LENGTH_LEN = 4  # which part of the message indicates about the message length
GENERAL_NAME = "talmid"  # clients general username


def create_msg(data):
    # change the data to bytes and add the length before
    length_of_data = str(len(str(data)))
    zfill_length = length_of_data.zfill(LENGTH_LEN)
    full_message = zfill_length + str(data)
    return full_message.encode()

def receive_msg(our_socket):
    # decode the receive message
    length_of_message = int(our_socket.recv(LENGTH_LEN).decode())
    data = our_socket.recv(length_of_message).decode()
    if data == "quit" or data == "Quit":  # if the client want to disconnect
        raise QuitInput
    return data


def fill_messages_to_send_list(clients_list, sender_client, message, messages_to_send):
    # does not fill with the sender address
    for check_socket in clients_list:
        if check_socket is sender_client:
            pass  # so we do not want to add this
        else:
            messages_to_send.append((check_socket, message))

def get_input(input_chars):
    # get the chars we have already received and continue get another char by char so we don't block.
    # helps us receive and send messages at the same time
    # if the first char is enter we raise an empty input exception
    is_input_ready = False
    if msvcrt.kbhit():
        char = msvcrt.getch()
        if ord(char) == 13:  # if enter
            if len(input_chars) == 0:
                raise EmptyInput  # the input is null
            else:
                is_input_ready = True  # the input is ready to be sent
        elif ord(char) == 8:  # we do not want the delete button to change the meaning (we cancel the different between 12 and 123 delete)
            if len(input_chars) != 0:
                input_chars.pop()
        else:
            input_chars.append(char.decode('utf-8'))  # we continue to add the chars to our list
    return is_input_ready, input_chars

def create_name_for_client(name, num):
    # create a number according to the client number. for example, the second client can get the name: talmid2
    if type(name) is str:
        return name + str(num)

def get__current_time():
    # return the current time
    return time.strftime("%H:%M")

def is_an_admin_want_to_remove(a_message, my_dict):
    # check if a client wants to remove other client. if he is an admin we will check on the server side
    # we will check it step by step
    if a_message[0:7] != "REMOVE ":
        return False
    socket_to_be_removed, end_name_part_char = is_name_in_message(7, a_message, my_dict)  # check if the name is valid
    if socket_to_be_removed is False:  # if there is not such user to remove
        return False
    else:
        return socket_to_be_removed

def is_an_admin_want_to_promote(a_message, my_dict):
    # check if a client wants to promote other client. if he is an admin we will check on the server side
    # we will check it step by step
    if a_message[0:8] != "PROMOTE ":
        return False
    name_part = a_message[8:]
    socket_to_be_promoted_address, end_name_part_char = is_name_in_message(8, a_message, my_dict)  # check if the name is valid
    if socket_to_be_promoted_address is False:  # if there is not such user to promote
        return False
    else:
        return socket_to_be_promoted_address

def is_an_admin_want_to_mute(a_message, my_dict):
    # check if a client wants to promote other client. if he is an admin we will check on the server side
    # we will check it step by step
    if a_message[0:5] != "MUTE ":
        return False
    socket_to_be_muted_address, end_name_part_char = is_name_in_message(5, a_message, my_dict)  # check if the name is valid
    if socket_to_be_muted_address is False:  # if there is not such user to mute
        return False
    else:
        return socket_to_be_muted_address

def is_user_want_a_private_message(a_message, my_dict):
    # check if a client wants to send a private message to other client.
    if a_message[0:1] != "!":
        return False, -1
    receiver_socket_address, end_name_part_char = is_name_in_message(1, a_message, my_dict)  # check if the name is valid
    if receiver_socket_address is False:  # if there is not such user to send to a private message
        return False, -1
    else:
        return receiver_socket_address, end_name_part_char  # in the server part we send the relevant part of the message by the end char

def is_name_in_message(start_char, a_message, my_dict):
    # check if there is a username in the message (starts with a specific char)
    name = ""
    end_char = start_char
    for i in a_message[start_char:]:
        name += i
        end_char += 1
        socket_to_be_address = get_key_from_value(name, my_dict)  # return false or the socket address with the found username
        if socket_to_be_address is not False:
            return socket_to_be_address, end_char  # return the socket address and the last char, so we know where the name part is over
    return False, -1

def get_key_from_value(val, my_dict):
    # return a key according to his value
    for key, value in my_dict.items():
        if val == value:
            return key
    return False


def check_the_admins_list(clients_list, admins_list):
    # if the admins list is empty, we give the first client in the client list to be an admin
    if len(admins_list) == 0:
        if len(clients_list) != 0:  # first we check if there even is a client to give him the admin
            admins_list.append(clients_list[0])
    return None

class EmptyInput (Exception):
    pass

class QuitInput (Exception):
    pass


