import json, jsonpickle
import random
from cogs.utils.tagguessing import createDefIntents


class IntentsHandler(object):
    def __init__(self, gIntents=None):
        if gIntents==None:
            try:
                with open(r'tagguessing\DMintents.json', 'r') as file:
                    loadData = json.load(file)
            except:
                createDefIntents.main()
                with open(r'tagguessing\DMintents.json', 'r') as file:
                    loadData = json.load(file)
            self.intents = jsonpickle.decode(loadData)

        else:
            self.intents = gIntents

    def getSentenceType(self, sentence):

        foundFlag = False
        for itr1 in self.intents['patterns'].keys():
            if sentence in self.intents['patterns'][itr1]['sentences']:
                foundFlag = True
                sentenceType = itr1
                break
        if not foundFlag:
            relScale = dict()
            for itr2 in self.intents['patterns']:
                relScale[itr2] = 0
                for itr3 in sentence.split(' '):
                    for itr4 in itr3:
                        if not itr4.isalpha() or not itr4.isdigit():
                            itr3.replace(itr4, '')
                    if itr3 in self.intents['patterns'][itr2]['words']:
                        if self.intents['patterns'][itr2]['times_called'] != 0:
                            addAmt = self.intents['patterns'][itr2]['words'][itr3] / \
                                     self.intents['patterns'][itr2]['times_called']
                        else:
                            addAmt = 1
                        relScale[itr2] += addAmt
            sentenceTypeCount = 0
            curMaxes = []
            for itr4 in relScale.keys():
                if relScale[itr4] > sentenceTypeCount:
                    sentenceTypeCount = relScale[itr4]
                    sentenceType = itr4
                    curMaxes = [curMaxes]
                elif relScale[itr4] == sentenceTypeCount:
                    curMaxes.append(curMaxes)
            if len(curMaxes) > 1 and sentenceTypeCount > 0:
                print('randomly choosing from:', curMaxes)
                sentenceType = curMaxes[random.randint(0, len(curMaxes) - 1)]

            if sentenceTypeCount == 0:
                print('no matching words found, unable to handle sentence')
                return False
            else:
                foundFlag = True
        if foundFlag:
            return sentenceType
        else:
            return False