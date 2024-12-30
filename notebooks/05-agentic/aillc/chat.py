# %%
# Libraries

from .agents import Agent
from enum import Enum
from .llm import LLM
from .html_render import render_html_chat
import json



# %%
# Chatting interface


class ChatTurn(Enum):
    respondent = 'respondent'
    asker = 'asker'

class ChatState(Enum):
    ongoing = 'ongoing'
    terminated = 'terminated'



class Chat:

    def __init__(self, asker:Agent, respondent:Agent, entry_question, background_asker="", background_responder=""):
        self.asker = asker
        self.respondent = respondent
        self.entry_question = entry_question
        
        self.asker_messages = [
            {"role":"system", "content":self.asker.system_message() + background_asker}
        ]
        self.respondent_messages = [
            {"role":"system", "content":self.respondent.system_message() + background_responder},
            {"role":"user", "content":self.entry_question, "tags":["entry"]}
        ]

        self.turn  = ChatTurn.respondent
        self.state = ChatState.ongoing
        self.outcome = None
        self.name = "chat"


    def extend_thread(self, message, tags = []):
        if self.turn == ChatTurn.respondent:
            self.respondent_messages.append({"role":"assistant", "content":message, "tags":tags})
            self.asker_messages.append({"role":"user", "content":message, "tags":tags})
            self.turn = ChatTurn.asker
        else:
            self.respondent_messages.append({"role":"user", "content":message, "tags":tags})
            self.asker_messages.append({"role":"assistant", "content":message, "tags":tags})
            self.turn = ChatTurn.respondent
    
    def get_thread_length(self):
        return len(self.respondent_messages)

    def get_current_messages(self):
        if self.turn == ChatTurn.respondent:
            return self.respondent_messages
        else:
            return self.asker_messages
        
    def get_current_agent(self):
        if self.turn == ChatTurn.respondent:
            return self.respondent
        else:
            return self.asker
    
    def reply(self, json = False):
        current_messages = self.get_current_messages()
        model = self.get_current_agent().parameters['model']
        answer = LLM.get_response(current_messages, model, json)
        return answer


    def display(self, last_only = False):
        messages = self.respondent_messages
        if last_only:
            if messages:
                msg = messages[-1]
                role = "ASKER" if msg['role'] == 'user' else "RESPONDER"
                print(f"{role}:\n{msg['content']}\n\n")
        else:
            for msg in messages:
                role = "ASKER" if msg['role'] == 'user' else "RESPONDER"
                print(f"{role}:\n{msg['content']}\n\n")


    # Saving

    def to_html(self, html_file = None, full=False):
        
        htmls = render_html_chat(self.asker.agent_name, self.respondent.agent_name, 
                                    self.asker_messages, self.respondent_messages, full)
        
        if html_file is None:
            html_file = f"{self.name}.html"

        with open(html_file, "w", encoding='utf-8') as file:
            file.write(htmls['direct'])

        if full:
            html_invert = html_file.replace(".html", "-invert.html")
            with open(html_invert, "w", encoding='utf-8') as file:
                file.write(htmls['invert'])  

    def to_text(self, filename = None):
        sep = "-"*70
        if filename is None:
            filename = f"{self.name}.txt"
        with open(filename, "w", encoding = 'utf-8') as f:
            for msg in self.respondent_messages:
                f.write(f"{sep}\n")
                f.write(f"role: {msg['role']}\n")
                if 'tags' in msg and len(msg['tags']) > 0:
                    tags = "; ".join(msg['tags'])
                    f.write(f"tags: {tags}\n")
                f.write(f"{sep}\n")
                f.write(f"{msg['content']}\n")

    def to_dict(self):
        conversation = {
            "turn" : self.turn.value,
            "respondent_messages" : self.respondent_messages,
            "asker_messages": self.asker_messages
        }
        return conversation

    def to_json(self, filename = None):
        filename = filename or f"{self.name}.json"
        with open(filename, "w") as f:
            json.dump(self.to_dict(), f, indent=4)

    # Loading 

    def from_dict(self, conversation):
        self.turn = ChatTurn(conversation['turn'])
        self.respondent_messages = conversation['respondent_messages']
        self.asker_messages = conversation['asker_messages']

    def read_json(self, filename = None):
        filename = filename or f"{self.name}.json"
        with open(filename, "r") as f:
            conversation = json.load(f)
        self.from_dict(conversation)

    # Length and rewind

    def len(self):
        return len(self.asker_messages) - 1
    
    def rewind_to(self, new_length):
        if new_length < 0 or new_length > self.len():
            raise ValueError(f"New length should be >= 0 and <= {self.len()}")
        old_length = self.len()
        if new_length == old_length:
            return
        self.asker_messages = self.asker_messages[:new_length+1]
        self.respondent_messages = self.respondent_messages[:new_length+2]
        if (old_length - new_length) % 2 == 1:
            if self.turn == ChatTurn.respondent:
                self.turn = ChatTurn.asker
            else:
                self.turn = ChatTurn.respondent            





# %%
