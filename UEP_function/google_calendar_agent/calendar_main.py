from google_calendar_agent.authorize import get_authorization_url
from google_calendar_agent.event import create_new_event, delete_event

def main():
    service = get_authorization_url()
    num = int(input("1. create a new item in google calendar, 2. delete a event:"))
    if (num == 1):
        create_new_event(service)
    elif (num == 2):
        keyword = input("Enter keyword or title: ")
        delete_event(service, keyword)

if __name__ == "__main__":
    main()


