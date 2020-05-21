import json, jsonpickle
import random



def main(tags):
    print('loading default intents')

    myIntents = {'patterns': dict(), 'times_called': 0}
    for tag in tags:
        myIntents['patterns'][tag] = {'sentences': set(), 'words': dict(), 'times_called': 0}
    dumpIntents = dict()
    for k, v in myIntents.items():
        dumpIntents[k] = jsonpickle.encode(v)
    with open(r'cogs\tagguessing\DMintents.json', 'w') as file:
        json.dump(dumpIntents, file)
    # print('loading default intents')
    #
    # myIntents = {'patterns':
    #                  {'Hello! How are you': {'sentences': {'hi how are you', 'how are you', 'how are you doing',
    #                                                        'greetings', 'ello', 'hello', 'hi'},
    #                                          'words': {'hi': 0, 'are': 0, 'you': 0, 'how': 0, 'doing': 0,
    #                                                    'greetings': 0, 'ello': 0, 'hello': 0},
    #                                          'times_called': 0},
    #
    #                   'Have a good night!': {'sentences': {'goodbye', 'bye', 'good night',
    #                                                        'see you', 'later'},
    #                                          'words': {'bye': 0, 'goodbye': 0, 'good': 0, 'you': 0, 'see': 0,
    #                                                    'later': 0, 'night': 0},
    #                                          'times_called': 0
    #                                          }
    #                   },
    #
    #              'times_called': 0
    #              }
    # dumpIntents = dict()
    # for k, v in myIntents.items():
    #     dumpIntents[k] = jsonpickle.encode(v)
    # with open(r'cogs\tagguessing\DMintents.json', 'w') as file:
    #     json.dump(dumpIntents, file)



