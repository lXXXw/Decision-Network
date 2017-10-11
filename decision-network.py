import copy
import re
from decimal import Decimal
def main():
    # BN, queryList, utl = constructBN("input03.txt")

    # answerQuery(queryList, BN, utl)

    # debug run
    runTestCases()



def runTestCases():
    for i in range(1, 12):
        if i < 10:
            inputPath = 'testCases/input0'+str(i)+'.txt'
        else:
            inputPath = 'testCases/input'+str(i)+'.txt'
        print 'Running ', inputPath, ': '
        BN, queryList, utl = constructBN(inputPath)
        answerQuery(queryList, BN, utl)
        print 'Answer:'
        getAnswer(i)

def getAnswer(i):
    if i < 10:
        outputPath = 'testCases/output0' + str(i) + '.txt'
    else:
        outputPath = 'testCases/output' + str(i) + '.txt'
    fo = open(outputPath, 'r')
    for line in fo:
        print line.strip()

# construct BN and Query function part
def constructBN(filepath):
    infile = open(filepath, "r")     # to be modified!

    net = {}

    # flags when parsing the input file.
    query = True
    table = False
    utl = False
    lines = [] # buffer

    for line in infile:
        if (query and line.strip() == '******'):
            queryList = parseQuery(lines)
            query = False
            table = True
            lines = []
        elif (table and line.strip() == '***'):
            parseTable(lines, net)
            # print '~~~~'
            lines = []
        elif (table and line.strip() == '******'):
            parseTable(lines, net)
            table = False
            utl = True
            lines = []
        else:
            lines.append(line.strip())

    # the last part need to be parsed
    uti = {}
    if utl:
        uti = parseUtl(lines)
        # print '-'
    else:
        parseTable(lines, net)

    # printNet(net)
    return net, queryList, uti

def parseTable(lines, net):
    # print "Node:"
    if len(lines) == 2:
        # only two lines, this is a node without parents
        var = lines[0]
        prob = 0
        if (lines[1] == 'decision'):
            # probability equals to -2.0 to present it as decision node
            prob = -2.0
        else:
            prob = float(lines[1])

        net[var] = {
            'parents' : [],
            'children' : [],
            'prob' : prob,
            'condprob' : {}
        }

    else:
        # have at least parents
        parts = lines[0].split()
        var = parts[0]
        parents = parts[2:]

        # add this node as children of its parents
        for p in parents:
            net[p]['children'].append(var)

        net[var] = {
            'parents' : parents,
            'children' : [],
            'prob' : -1.0,
            'condprob' : {}
        }

        # add conditional probability into table
        tempMap = {
            '+' : True,
            '-' : False
        }
        for line in lines[1:]:
            vals = line.split()
            truth, prob = vals[1:], float(vals[0])
            truth = tuple(True if x == '+' else False for x in truth)
            net[var]['condprob'][truth] = prob

def parseUtl(lines):
    # print "Util:"
    '''
    This function input a block of utilities info and return an utility object
    :param lines: block of utility info
    :return: an utility object
    '''
    utility = {}
    parents = lines[0].split()[2:]
    table = {}
    for line in lines[1:]:
        parts = line.split()
        truth = tuple(True if x =='+' else False for x in parts[1:])
        util = int(float(parts[0]))
        table[truth] = util
    utility['parents'] = parents
    utility['table'] = table
    # printUtility(utility)
    return utility

def parseQuery(buffer):
    '''
    This functino parses the query part lines and return a list of query object.

    The structure of a query object is:
    query = {
        'type' : 'P'|'E'|'M',
        'cond' : True|False,
        'pre' : a dictionary of value assign before sign '|'
        'after' : a dictionary of value assign after sign '|'
    }

    :param buffer:
    :return: a list of query object
    '''
    queryList = []
    for line in buffer:
        if line[0] == 'P':
            myType = 'P'
            part = line[2:len(line) - 1]
        elif line[0] == 'E':
            myType = 'E'
            part = line[3:len(line) - 1]
        else:
            myType = 'M'
            part = line[4:len(line) - 1]

        i = part.find("|")
        if i == -1:
            # no '|' char included
            cond = False
            pre = parseMEUPre(part) if myType == 'M' else parseValue(part)
            after = {}
        else:
            cond = True
            pre = parseMEUPre(part[0:i - 1]) if myType == 'M' else parseValue(part[0:i - 1])
            after = parseValue(part[i + 2:])
        query = {
            'type': myType,
            'cond': cond,
            'pre': pre,
            'after': after
        }
        queryList.append(query)
    return queryList

def parseValue(str):
    '''
    This function parses value in queries.

    e.g.
    parseValue('L = -, I = -')
    :param str:
    :return: a var-value dict of query object
    '''
    varValue = str.split(', ')
    a = {}
    for pair in varValue:
        parts = pair.split()
        a[parts[0]] = True if parts[2] == '+' else False
    return a

def parseMEUPre(part):
    decisions = part.split(', ')
    pre = []
    for decision in decisions:
        pre.append(decision)
    return pre

# Enumeration algorithm part
def enumeration_ask(X, e, BN):
    res = []
    for x in [True, False]:
        ex = copy.deepcopy(e)
        ex[X] = x
        variables = getTopologyOrder(BN)
        #variables = ['F', 'A', 'B', 'C', 'D']
        var = deleteBottomNodes(variables, ex, BN)
        # print var
        res.append(enumerate_all(var, ex, BN))

    # return normalize(res)
    # dist = []
    # for x in [False, True]:
    #     # make a copy of the evidence set
    #     e = copy.deepcopy(e)
    #
    #     # extend e with value of X
    #     e[X] = x
    #
    #     # topological sort
    #     variables = getTopologyOrder(BN)
    #
    #     # enumerate
    #     dist.append(enumerate_all(variables, e, BN))

    # normalize & return
    return normalize(res)

def deleteBottomNodes(variables, e, BN):
    waittList = list(e.keys())
    added = set()
    for var in waittList:
        added.add(var)
    while len(waittList) != 0:
        temp = []
        for one in waittList:
            for p in BN[one]['parents']:
                if p not in added:
                    temp.append(p)
                    added.add(p)
        waittList = temp

    finalList = []
    for var in variables:
        if var in added: finalList.append(var)

    return finalList

def normalize(res):
    total = sum(res)
    res[0] /= total
    res[1] /= total
    return res

def getTopologyOrder(BN):
    li = []
    nameSet = BN.keys()
    nameList = list(nameSet)
    length = len(nameList)
    nameList.sort()
    added = set()
    while len(li) != length:
        for name in nameList:
            if (name not in added):
                if (BN[name]['parents'] == []):
                    added.add(name)
                    li.append(name)
                else:
                    parentsIn = True
                    for p in BN[name]['parents']:
                        if p not in added:
                            parentsIn = False
                            break
                    if parentsIn:
                        added.add(name)
                        li.append(name)

    return li

def enumerate_all(variables, e, BN):
    if (len(variables) == 0): return 1.0
    Y = variables[0]

    # if Y has value y in e
    if (e.has_key(Y)):
        res = prob(Y, e, BN) * enumerate_all(variables[1:], e, BN)
    else:
        res = 0.0
        for y in [True, False]:
            ey = copy.deepcopy(e)
            ey[Y] = y
            res += prob(Y, ey, BN) * enumerate_all(variables[1:], ey, BN)

    # print res
    return res

def prob(Y, e, BN):
    if BN[Y]['prob'] == -2.0:
        # this is a decision node
        # then return probability 1.0 whether it is chosen or not.

        return 1.0

    if BN[Y]['prob'] != -1:
        prob = BN[Y]['prob'] if e[Y] else 1 - BN[Y]['prob']

        # Y has at least 1 parent
    else:
        # get the value of parents of Y
        parents = tuple(e[p] for p in BN[Y]['parents'])

        # query for prob of Y = y
        prob = BN[Y]['condprob'][parents] if e[Y] else 1 - BN[Y]['condprob'][parents]
    return prob

def probMarginalization(variableAssign, BN):
    '''
    This function calculates the probability of a conjunction of variables

    e.g.
    P(a, ~b, c, d) = probMarginalization(assign, BN)
    where assign = {
        'A' = True,
        'B' = False,
        'C' = True,
        'D' = True
    }

    :param variableAssign: An assignment of given variables
    :param BN: Bayesian Network
    :return: The probability of conjunction value.
    '''
    nameList = list(variableAssign.keys())
    if len(nameList) == 0: return 1.0
    if len(nameList) == 1:
        # to calculate prob for only one varaible
        return enumeration_ask(nameList[0], {}, BN)[0] if variableAssign[nameList[0]] else enumeration_ask(nameList[0], {}, BN)[1]
    var = nameList[0]
    truth = variableAssign[nameList[0]]
    del variableAssign[nameList[0]]
    if truth:
        i = 0
    else:
        i = 1
    left = enumeration_ask(var, variableAssign, BN)[i]
    right = probMarginalization(variableAssign, BN)
    return  left * right

def probCondition(preAssign, afterAssign, BN):
    assign = copy.deepcopy(afterAssign)
    return probMarginalization(dict(preAssign.items() + afterAssign.items()), BN) / probMarginalization(assign, BN)

# Solve Query Part
def answerQuery(queryList, BN, utl):
    for query in queryList:
        if query['type'] == 'P':
            result = answerP(query, BN)
            print '{:.2f}'.format(Decimal(str(result)))

        elif query['type'] == 'E':
            result = answerE(query, BN, utl)
            print '{:.0f}'.format(Decimal(str(result)))
            # print result
        else:
            print answerM(query, BN, utl)
            # print 'M query'

def answerP(query, BN):
    if len(query['pre']) == 1 and len(query['after']) > 0:
        # can be solved use only enumeration ask.
        var = list(query['pre'].keys())[0]
        truth = query['pre'][var]
        i = 0 if truth else 1
        return enumeration_ask(var, query['after'], BN)[i]
    if len(query['after']) == 0:
        # this is just marginalization prob
        return probMarginalization(query['pre'], BN)
    return probCondition(query['pre'], query['after'], BN)

def answerE(query, BN, utl):
    # print 'E query'
    # printUtility(utl)
    # evidence construction
    e = dict(query['pre'].items() + query['after'].items())
    res = []
    for case in list(utl['table'].keys()):
        res.append(calculateU(case, utl, BN, e))

    return sum(res)

def calculateU(case, utl, BN, e):
    '''
    Calculate utility in current case.
    :param case: current case: tuple(T, T, F) etc.
    :param BN: BN
    :return: Utility
    '''
    parents = utl['parents']
    pre = {}
    for i in range(len(parents)):
        if parents[i] in e.keys() and case[i] != e[parents[i]]:
            return 0.0
        if parents[i] not in e.keys():
            pre[parents[i]] = case[i]

    if len(pre) == 0:
        # This case is included in evidence, so the probability is 1.0
        p = 1.0
    else:
        # print 'evidence: ', e
        # print 'pre: ', pre
        e2 = copy.deepcopy(e)
        p = probCondition(pre, e2, BN)
    return p * utl['table'][case]

def answerM(query, BN, utl):
    # Basic idea is to convert MEU query into EU query.
    assignList = getAssignList(query['pre'])
    # after = copy.deepcopy(query['after'])
    maxAssign = {}
    maxValue = float('-inf')
    EQuery = copy.deepcopy(query)
    for assign in assignList:
        EQuery['pre'] = assign
        EU = answerE(EQuery, BN, utl)
        if EU > maxValue:
            maxValue = EU
            maxAssign = assign

    result = ''
    for de in query['pre']:
        if maxAssign[de]:
            result += '+ '
        else:
            result += '- '

    result += '{:.0f}'.format(Decimal(str(maxValue)))

    return result


def getAssignList(decisionList):
    '''
    Return a list of possible assignment of decision values
    e.g.

    {'I': True, 'D': True, 'L': True}
    {'I': True, 'D': True, 'L': False}
    {'I': True, 'D': False, 'L': True}
    {'I': True, 'D': False, 'L': False}
    {'I': False, 'D': True, 'L': True}
    {'I': False, 'D': True, 'L': False}
    {'I': False, 'D': False, 'L': True}
    {'I': False, 'D': False, 'L': False}

    :param decisionList:
    :return:
    '''
    assignList = []
    helper(decisionList, assignList, {})
    return assignList

def helper(decisionList, assignList, assign):
    if len(decisionList) == 0:
        # base case
        assignList.append(copy.deepcopy(assign))
        return
    for x in [True, False]:
        assign[decisionList[0]] = x
        helper(decisionList[1:], assignList, assign)

# debug function part:
def printNet(net):
    for item in net.keys():
        print "=================="
        print "Node Name: ", item
        print "Parents: ", net[item]['parents']
        print "Children: ", net[item]['children']
        if (net[item]['prob'] == 1):
            print "Decision Node."
        elif (net[item]['prob'] == -1):
            print "Condition Prob:"
            print net[item]['condprob']
        else:
            print "Probability: ", net[item]['prob']

def printQuery(queryList):
    i = 1
    for query in queryList:
        print '\nQuery No.', i
        i += 1
        print 'Type: ', query['type']
        print 'Is Condition:', query['cond']
        print 'Value Assign before \'|\':', query['pre']
        print 'Value Assign after \'|\':', query['after']

def printUtility(utl):
    print '\nUtility:'
    print 'Parents: ', utl['parents']
    for item in list(utl['table'].keys()):
        print item, ': ', utl['table'][item]

if __name__ == '__main__' :
    main()