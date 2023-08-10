# tcp-chatroom
10.128.47.14 49153
- private chat : menu, login,...
- exit chat
- old message display
- send files

    - limit message length 
      - calculate dataDict+message length
      - dataDict+message must < 4096 bytes

    - critical case:
      - user might send messages during file_sending
        - Sol 1: block Write
        - Sol 2: handle all inputs
        - Sol 3: research `sendall` function for other methods{"text": "\\FILE README.md", "array": "\\TO *"}