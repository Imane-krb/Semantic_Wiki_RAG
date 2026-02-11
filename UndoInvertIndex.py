



def maxIndex(arrayAbstractIndex):
    L=[]
    for x in arrayAbstractIndex:
        L.append(max(x[1]))
    return max(L)

#print(abstractInvertedIndex["<p"])
def Undo_Invert_Index(abstractInvertedIndex):

    if abstractInvertedIndex:

        arrayAbstractIndex = [[k, abstractInvertedIndex[k]] for k in abstractInvertedIndex]
        #print(arrayAbstractIndex)


        wordPos = 0
        abstract = ""
        current_x=[]
        S=maxIndex(arrayAbstractIndex)

        while wordPos<S:
            for i in range(len(arrayAbstractIndex)):
                x= arrayAbstractIndex[i]
                if wordPos in x[1]:
                    abstract = abstract + str(x[0] + ' ')
                    current_x=x
                    wordPos = wordPos + 1
                    break

        #print(current_x)
        #print(wordPos)
        return abstract
    
    return abstractInvertedIndex
    