import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

vk_session = vk_api.VkApi(token='vk1.a.XxX-REL08Ur8M2Jt9OWWzvxXbY-nEguPAkTvUDPn-MJioeQWpABE6JiYSIgagwutheKW7cH-EFVG_zMPRuEO0JsZpYn6uBumeV9Ne46uLyK3S8eIEqLXtF_L4ecWNGqULIpQmUtn38aD-kprS2L6W3PP-4NP5R3CXNQRmgMmwZihnQYds2BcbAPdOebfs6WEIV90DMobhqznGX5Q3DzWKg')

session_api = vk_session.get_api()
longpool = VkLongPoll(vk_session)

def send_some_msg(id, some_text):
    vk_session.method("messages.send", {"user_id":id, "message":some_text,"random_id":0})

for event in longpool.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            msg = event.text.lower()
            id = event.user_id
            if msg == "hi":
                send_some_msg(id, "Hi friend!")