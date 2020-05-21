import json, jsonpickle
from cogs.utils.tagguessing import createDefIntents, IntentsHandler


class mainHandler():
    def __init__(self, tags):
        self.tags = tags
        self.load_intents()


    def load_intents(self):
        try:
            with open(r'cogs\tagguessing\DMintents.json', 'r') as file:
                encIntents = json.load(file)
            self.intents = jsonpickle.decode(encIntents)
        except:
            print('no intents found, loading default ones')
            createDefIntents.main(self.tags)
            with open(r'cogs\tagguessing\DMintents.json', 'r') as file:
                encIntents = json.load(file)
            self.intents = dict()
            for k, v in encIntents.items():
                self.intents[k] = jsonpickle.decode(v)
            

    def update_intents(self):
        encIntents = dict()
        for k, v in self.intents.items():
            encIntents[k] = jsonpickle.encode(v)
        with open(r'cogs\tagguessing\DMintents.json', 'w') as file:
            json.dump(encIntents, file)

    def clean_word(self, word):
        for itr1 in word:
            if not itr1.isalpha() and not itr1.isdigit():
                while itr1 in word:
                    word = word.replace(itr1, '')
        return word

    def clean_words(self, sentence):
        counter = 1
        splitt = sentence.split(' ')
        retSent = ''
        for itr1 in splitt:
            itr1 = self.clean_word(itr1)
            retSent += itr1
            if counter != len(splitt):
                retSent += ' '
            counter += 1
        return retSent

    def add_command(self, response, sentences, words=None):
        if words == None:
            words = dict()
            for itr1 in sentences:
                for itr2 in itr1.split(' '):
                    itr2 = self.clean_word(itr2)
                    words[itr2] = 1
            self.update_intents()

        if response not in self.intents['patterns']:
            self.intents['patterns'][response] = {'sentences': set(sentences), 'words': words, 'times called': 1}
            self.update_intents()
        else:
            print('item already in dictionary')

    def change_response(self, response, new):
        if response not in self.intents['patterns']:
            print(self.intents['patterns'])
            print('Error! Response does not exist, nothing changed.')
        else:
            if new not in self.intents['patterns']:
                tempStore = self.intents['patterns'][response]
                del self.intents['patterns'][response]
                self.intents['patterns'][new] = tempStore
                self.update_intents()
            else:print('Error! key already exists')

    def delete_command(self, command):
        if command in self.intents['patterns']:
            del self.intents['patterns'][command]
            self.update_intents()
        else:
            print('command not found')

    def add_sentence(self, command, sentence):
        if command not in self.intents['patterns']:
            print('no command found matching given')
        else:
            if sentence in self.intents['patterns'][command]['sentences']:
                print('sentence already exists!')
            else:
                self.intents['patterns'][command]['sentences'].add(sentence)
                for itr1 in sentence.split(' '):
                    cleanWord = self.clean_word(itr1)
                    self.add_word(command, cleanWord, printStatement=False)
                self.update_intents()

    def delete_sentence(self, command, sentence):
        if command not in self.intents['patterns']:
            print('no command found matching given')
        else:
            if sentence not in self.intents['patterns'][command]['sentences']:
                print('no sentence found matching response')
            else:
                self.intents['patterns'][command]['sentences'].discard(sentence)
                self.update_intents()

    def add_word(self, command, word, printStatement=True):
        if command not in self.intents['patterns']:
            print('no command found matching given')
        else:
            if word in self.intents['patterns'][command]['words']:
                if printStatement:
                    print('word already exists')
            else:
                self.intents['patterns'][command]['words'][word] = 1
                self.update_intents()

    def delete_word(self, command, word):
        if command not in self.intents['patterns']:
            print('no command found matching given')
        else:
            if word not in self.intents['patterns'][command]['words']:
                print('no word found matching response')
            else:
                del self.intents['patterns'][command]['words'][word]
                self.update_intents()

    def grab_sentences(self, command):
        if command not in self.intents['patterns']:
            print('no matching command found')
        else:
            return self.intents['patterns'][command]['sentences']

    def grab_words(self, command):
        if command not in self.intents['patterns']:
            print('no matching command found')
        else:
            return self.intents['patterns'][command]['words']

    def interpret(self, text):
        interpreter = IntentsHandler.IntentsHandler(gIntents=self.intents)
        guess = interpreter.getSentenceType(text)
        if guess == False:
            guess = 'Could not determine from given text'
        # if len(guess) > 85:
        #     for itr1 in range(0, len(guess), 85):
        #         if itr1 != 0:
        #             pivot = guess[:itr1].rindex(' ')
        #             guess = guess[:pivot] + '\n' + guess[pivot + 1:]
        return guess

    def correct_guess(self, guess, sentence):
        if guess not in self.intents['patterns']:
            print('error, guess not in intents?')
        else:
            self.intents['patterns'][guess]['sentences'].add(sentence)
            for itr1 in sentence.split(' '):
                itr1 = self.clean_word(itr1)
                if itr1 in self.intents['patterns'][guess]['words']:
                    self.intents['patterns'][guess]['words'][itr1] += 1
                else:
                    self.intents['patterns'][guess]['words'][itr1] = 1
            self.intents['patterns'][guess]['times_called'] += 1
            self.update_intents()







def main():
    myHandler = mainHandler()
    result = myHandler.interpret('How are you?')
    print(result)

if __name__ == '__main__':
    main()