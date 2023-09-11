import protocol
import socket
import select
from protocol import QuitInput

server_socket = socket.socket()
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((protocol.SERVER_IP, protocol.SERVER_PORT))
server_socket.listen()
print("Server is ready, waiting for clients to join")

clients_sockets = []
messages_to_send = []
clients_by_order = []  # the order of all the clients that has joined to the server ((including the disconnects)
hard_coded = []  # list of admins
name_for_address = {}  # each client will have a name according to his address
muted_clients = []

def prepare_message(is_self_sending, socket_data, a_message, admins_list):
    # if the client is an admin we will add @ before the message, and if this is a self sending we start with "ME" instead of the full name
    if socket_data in admins_list:
        if is_self_sending:
            return protocol.get__current_time() + " @Me: " + a_message
        else:
            return protocol.get__current_time() + " @" + name_for_address[socket_data.getpeername()] + ": " + a_message
    else:
        if is_self_sending:
            return protocol.get__current_time() + " Me: " + a_message
        else:
            return protocol.get__current_time() + " " + name_for_address[socket_data.getpeername()] + ": " + a_message


def prepare_a_quit_message(socket_data):
    return protocol.get__current_time() + " " + name_for_address[socket_data.getpeername()] + " has left the chat!"

def prepare_a_remove_message(is_self_sending, socket_data):
    # message for client who has been removed by an admin
    if is_self_sending:  # the message for the removed user
        return "You have been kicked out from the chat!"
    else:  # the message to all the other clients
        return protocol.get__current_time() + " " + name_for_address[socket_data.getpeername()] + " has been kicked out from the chat!"


def prepare_a_join_message(socket_data):
    return protocol.get__current_time() + " " + name_for_address[socket_data.getpeername()] + " has joined the chat!"

def prepare_a_became_an_admin_message(is_self_sending, socket_data):
    if is_self_sending:  # the message for the promoted user
        return "You promoted, you are an admin now!"
    else:  # the message to all the other clients
        return protocol.get__current_time() + " " + name_for_address[socket_data.getpeername()] + " is an admin now"

def prepare_a_mute_action(is_self_sending, socket_data):
    if is_self_sending:  # the message for the promoted user
        return "You are muted, you cannot speak here"
    else:  # the message to all the other clients
        return protocol.get__current_time() + " " + name_for_address[socket_data.getpeername()] + " is muted now"

def prepare_a_private_message(is_self_sending, socket_data, a_message):
    if is_self_sending:  # the message for the sending user
        return protocol.get__current_time() + " !Me:" + a_message
    else:  # the message for the private user receiver
        return protocol.get__current_time() + " !" + name_for_address[socket_data.getpeername()] + ":" + a_message


def remove_client_action(socket_data, is_removed):
    # get a socket that needs to be removed and do all the remove action
    if is_removed is True:  # if an admin removed the client:
        socket_data = return_socket_according_to_address(socket_data, clients_sockets)  # we know it can not be false
        print(prepare_a_remove_message(False, socket_data))  # inform the server:
    else:
        print(prepare_a_quit_message(socket_data))
    clients_sockets.remove(socket_data)  # delete from the list
    del name_for_address[socket_data.getpeername()]  # delete from dictionary
    if socket_data in hard_coded:  # if the removed user is an admin we update the admins list
        hard_coded.remove(socket_data)
        protocol.check_the_admins_list(clients_sockets, hard_coded)
    if socket_data in muted_clients:  # if the removed user is a muted client we update the muted list
        muted_clients.remove(socket_data)
    socket_data.close()

def deal_with_removed_socket(socket_to_be_removed_address):
    # IF A USER HAS BEEN REMOVED WE WILL DO THE NEXT ACTIONS:
    # we want the socket, not the address
    socket_to_be_removed = return_socket_according_to_address(socket_to_be_removed_address, clients_sockets)
    # inform the other clients
    protocol.fill_messages_to_send_list(clients_sockets, socket_to_be_removed, prepare_a_remove_message(False, socket_to_be_removed), messages_to_send)
    # inform the removed client
    socket_to_be_removed.send(protocol.create_msg(prepare_a_remove_message(True, socket_to_be_removed)))
    # we no longer have the removed socket so we can remove him
    remove_client_action(socket_to_be_removed_address, True)

def deal_with_promoted_socket(socket_to_be_promoted_address):
    # we want the socket, not the address
    socket_to_be_prompted = return_socket_according_to_address(socket_to_be_promoted_address, clients_sockets)
    # add the user to the admins list
    hard_coded.append(socket_to_be_prompted)
    # inform the other clients
    protocol.fill_messages_to_send_list(clients_sockets, socket_to_be_prompted, prepare_a_became_an_admin_message(False, socket_to_be_prompted), messages_to_send)
    # inform the promoted client
    messages_to_send.append((socket_to_be_prompted, prepare_a_became_an_admin_message(True, socket_to_be_prompted)))

def deal_with_muted_socket(socket_to_be_muted_address):
    # we want the socket, not the address
    socket_to_be_muted = return_socket_according_to_address(socket_to_be_muted_address, clients_sockets)
    # add the user to the admins list
    muted_clients.append(socket_to_be_muted)
    # inform the other clients
    protocol.fill_messages_to_send_list(clients_sockets, socket_to_be_muted, prepare_a_mute_action(False, socket_to_be_muted), messages_to_send)
    # inform the muted client
    messages_to_send.append((socket_to_be_muted, prepare_a_mute_action(True, socket_to_be_muted)))

def deal_with_private_message(socket_to_receive_a_private_message_address, income_message, msg_starts_char, check_socket):
    # we want the socket, not the address
    socket_to_receive_a_private_message = return_socket_according_to_address(socket_to_receive_a_private_message_address, clients_sockets)
    private_msg = income_message[int(msg_starts_char):]
    messages_to_send.append((check_socket, prepare_a_private_message(True, check_socket, private_msg)))
    messages_to_send.append((socket_to_receive_a_private_message, prepare_a_private_message(False, check_socket, private_msg)))

def deal_with_normal_message(check_socket, income_message):
    # in this case the user just want to send a normal message. we let him do it unless he is muted
    if check_socket not in muted_clients:
        general_income_message = prepare_message(False, check_socket, income_message, hard_coded)  # now we have the full message we want to send and display to the other clients
        protocol.fill_messages_to_send_list(clients_sockets, check_socket, general_income_message, messages_to_send)
        self_income_message = prepare_message(True, check_socket, income_message, hard_coded)
        messages_to_send.append((check_socket, self_income_message))
        print(general_income_message)
    else:
        messages_to_send.append((check_socket, prepare_a_mute_action(True, check_socket)))  # we only send to the muted user that he cannot send messages

def join_client_actions(check_socket, new_client, client_address):
    # do all the action after the server accepted a new client
    if len(hard_coded) == 0:  # in the first connection we have to nominate an admin
        hard_coded.append(new_client)
    clients_by_order.append(check_socket)
    count_clients = len(clients_by_order)  # the name will be given by the joining order
    name_for_address[client_address] = protocol.create_name_for_client(protocol.GENERAL_NAME, count_clients)  # give the client his name
    clients_sockets.append(new_client)
    print(prepare_a_join_message(new_client))
    protocol.fill_messages_to_send_list(clients_sockets, new_client, prepare_a_join_message(new_client), messages_to_send)  # inform the other users that a new user has joined


def show_all_users():
    # return a string of all the users that are connected to the server
    users = "The users are: "
    for user in clients_sockets:
        users += name_for_address[user.getpeername()] + ", "
    return users[:-2]

def show_all_admins():
    # return a string of all the admins that are connected to the server
    admins = "The managers are: "
    for admin in hard_coded:
        admins += name_for_address[admin.getpeername()] + ", "
    return admins[:-2]

def return_socket_according_to_address(socket_address, clients_list):
    # if the address is a socket in the clients list we return the socket, if not we return false
    for check in clients_list:
        if socket_address == check.getpeername():
            return check
    return False


def run_the_server():
    while True:
        read_list, write_list, error_list = select.select(clients_sockets + [server_socket], clients_sockets, [])

        # READ MESSAGES FROM CLIENT

        # now we go on our read list and check if there is a new client or a new message
        for check_socket in read_list:

            if check_socket is server_socket:
                # SO WE HAVE A NEW CLIENT
                new_client, client_address = server_socket.accept()
                join_client_actions(check_socket, new_client, client_address)

            else:
                # SO WE HAVE A NEW MESSAGE
                try:
                    income_message = protocol.receive_msg(check_socket)
                    # NOW WE CHECK IF THERE IS A SPECIAL ACTION IN THE MESSAGE LIKE REMOVING OR PROMOTING:
                    socket_to_be_removed_address = protocol.is_an_admin_want_to_remove(income_message, name_for_address)
                    socket_to_be_promoted_address = protocol.is_an_admin_want_to_promote(income_message, name_for_address)
                    socket_to_be_muted_address = protocol.is_an_admin_want_to_mute(income_message, name_for_address)
                    socket_to_receive_a_private_message_address, msg_starts_char = protocol.is_user_want_a_private_message(
                        income_message, name_for_address)
                    # check remove action:
                    if socket_to_be_removed_address is not False and check_socket in hard_coded:  # it will be false if the user do not want to remove or if he is not an admin
                        deal_with_removed_socket(socket_to_be_removed_address)

                    # check promote action:

                    elif socket_to_be_promoted_address is not False and check_socket in hard_coded:  # it will be false if the user do not want to promote or if he is not an admin
                        deal_with_promoted_socket(socket_to_be_promoted_address)

                    # check mute action:
                    elif socket_to_be_muted_address is not False and check_socket in hard_coded:  # it will be false if the user do not want to mute or if he is not an admin
                        deal_with_muted_socket(socket_to_be_muted_address)

                    # check private message:
                    elif socket_to_receive_a_private_message_address is not False:
                        deal_with_private_message(socket_to_receive_a_private_message_address, income_message, msg_starts_char, check_socket)

                    # check view managers action:
                    elif income_message == "view managers":
                        messages_to_send.append((check_socket, show_all_admins()))

                    # check view users action:
                    elif income_message == "view users":
                        messages_to_send.append((check_socket, show_all_users()))

                    # a normal message, we just need to send it
                    else:
                        deal_with_normal_message(check_socket, income_message)

                except (ValueError, ConnectionResetError,
                        QuitInput):  # if the income message is 04None ("") so we close connection
                    protocol.fill_messages_to_send_list(clients_sockets, check_socket,
                                                        prepare_a_quit_message(check_socket), messages_to_send)
                    remove_client_action(check_socket, False)

        # SEND MESSAGES TO THE CLIENTS:

        # now we go on our write list and check if there messages that need to be sent

        for message_to_send in messages_to_send:
            to_send_socket, data = message_to_send
            if to_send_socket in write_list and to_send_socket in clients_sockets:
                to_send_socket.send(protocol.create_msg(data))
                messages_to_send.remove(message_to_send)


run_the_server()