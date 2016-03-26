"""This is a Top Down Predictive Parser"""
from functools import update_wrapper
from string import split
import timeit, time, re

def grammar(description, whitespace=r'\s*'):
    """Convert a description to a grammar.  Each line is a rule for a
    non-terminal symbol; it looks like this:
        Symbol =>  A1 A2 ... | B1 B2 ... | C1 C2 ...
    where the right-hand side is one or more alternatives, separated by
    the '|' sign.  Each alternative is a sequence of atoms, separated by
    spaces.  An atom is either a symbol on some left-hand side, or it is
    a regular expression that will be passed to re.match to match a token.
    
    Notation for *, +, or ? not allowed in a rule alternative (but ok
    within a token). Use '\' to continue long lines.  You must include spaces
    or tabs around '=>' and '|'. That's within the grammar description itself.
    The grammar that gets defined allows whitespace between tokens by default;
    specify '' as the second argument to grammar() to disallow this (or supply
    any regular expression to describe allowable whitespace between tokens)."""
    G = {}
    description = description.replace('\t', ' ') # no tabs!
    for index, line in enumerate(split(description, '\n')):
        lhs, rhs = split(line, ' => ', 1)
        if index == 0:
            start_symbol = lhs #First non_terminal is taken as the start symbol
        alternatives = split(rhs, ' | ')
        G[lhs] = tuple(map(split, alternatives))
    return G, start_symbol

def decorator(d):
    "Make function d a decorator: d wraps a function fn."
    def _d(fn):
        return update_wrapper(d(fn), fn)
    update_wrapper(_d, d)
    return _d

@decorator
def memo(f):
    """Decorator that caches the return value for each call to f(args).
    Then when called again with same args, we can just look it up."""
    cache = {}
    def _f(*args):
        try:
            return cache[args]
        except KeyError:
            cache[args] = result = f(*args)
            return result
        except TypeError:
            # some element of args can't be a dict key
            return f(args)
    return _f

epsilon = '#'

g = ''
var = ''
print ''
print "Enter the grammar with each production in a line. When done enter just semicolon and hit enter"
print ''
g = raw_input()
if g[-1] != ';':
    while True:
        var = raw_input()
        if var == ';':
            break
        elif var[-1] == ';':
            g = g + '\n' + var[:-1]
            break
        else:
            g = g + '\n' + var
else:
    g = g[:-1]

print ''
print '\t' + ' '*17 + '-'*len('Grammar')
print '\t' + ' '*17 + "GRAMMAR" 
print '\t' + ' '*17 + '-'*len('Grammar') + '\n'
glist = split(g, '\n')
for x in glist:
	print '\t' + ' '*14 +  x
	

G, start_symbol = grammar(g)
non_terminals = G.keys()
non_terminals = list(set(non_terminals) - set([' ']))

def find_terminals(grammar):
    """Finds the set of terminals in the given grammar and returns the same."""
    result = []
    for i in grammar:
        for j in grammar[i]:
            for k in j:
                for x in k:
                    if x not in non_terminals:
                        result.append(x)
    return result

terminals = list(set(find_terminals(G)))
terminals.sort()
grammar_symbols = terminals + non_terminals
fswp = {}
for x in non_terminals:
    fswp[x] = {}
    
@memo
def first(grammar_symbol):
    """Finds the first of the grammar symbol. "#" is used as the symbol for epsilon."""
    result = []
    if grammar_symbol in terminals:
        return [grammar_symbol]
    else:
        productions = list(G[grammar_symbol])
        for i in productions:
            temp = []
            for j in i:
                if j[0] in terminals:
                    result.append(j[0])
                    temp.append(j[0])
                else:
                    for k in j:
                        if k in terminals:
                            result.append(k)
                            temp.append(k)
                            flag = 1
                            break
                        elif [epsilon] not in G[k]:
                            result = result + first(k)
                            temp = temp + first(k)
                            flag = 1
                            break
                        else:
                            flag = 0
                            result = result + first(k)
                            temp = temp + first(k)
                    if flag == 0:
                            temp.append(epsilon)
                            result.append(epsilon)
                    elif flag == 1:
                        if [epsilon] not in G[grammar_symbol]:
                            for x in range(result.count(epsilon)):
                                result.pop(result.index(epsilon))
                            for x in range(temp.count(epsilon)):
                                temp.pop(temp.index(epsilon))
            for x in temp:
                fswp[grammar_symbol][x] = i
    return list(set(result))

def compute_first():
    """Computes the first of all the grammar symbols in the given grammar"""
    return dict((x, first(x)) for x in grammar_symbols)

FIRST = compute_first()

def printfirst():
	"""Prints the FIRST of grammar symbol in a formatted way""" 
	print ''
	print '\t' + '-'*15, ' FIRST ', '-'*16
	width = len("SYMBOL")
	print ''
	print '\t' + ' '*12 + 'SYMBOL | FIRST'
	print ''
	for x in FIRST:
		print '\t' + ' '*12 + '%*s = %s'%(width, x, '{ ' + ', '.join(FIRST[x]) + ' }')	
	print ''
	print '\t' + '-'*40
	print ''

printfirst()

@memo
def follow(grammar_symbol):
    """Computes the follow of the non_terminal passed to the function."""
    assert grammar_symbol in non_terminals
    rhsproductions = [(x, z) for x in G for y in G[x] for z in y for m in z if grammar_symbol in m]
    if grammar_symbol == start_symbol:
        result = ['$']
    else:
        result = []
    try:
        for x in rhsproductions:
            rule3 = False
            variable, production = x
            index = production.index(grammar_symbol)
            if index == len(production)-1:
                if grammar_symbol != variable:
                    rule3 = True
            else:
                temp = production[index+1:]
                flag = 0
                for i in range(len(temp)):
                    result = result + FIRST[temp[i]]
                    if epsilon not in FIRST[temp[i]]:
                        flag = 1
                        break
                if flag == 0:
                    if grammar_symbol != variable:
                        rule3 = True
            if rule3:
                result = result + follow(variable)
        if epsilon in result:
            result = [x for x in result if x is not epsilon]
    except Exception, e:
        print "There was an error while computing FOLLOW(%s)" %(grammar_symbol)
    return result

def compute_follow():
    return dict((x, list(set(follow(x)))) for x in non_terminals)

FOLLOW = compute_follow()

def printfollow():
	#print ''
	print '\t' + '-'*15 , " FOLLOW ", '-'*15, '\n'
	width = len("NON TERMINAL")
	print '\t' + ' '*6 + "NON TERMINAL", "|", "FOLLOW"
	print ''	
	for x in FOLLOW:
		print '\t' + ' '*6 +  "%*s = %s" %(width, x, '{ '+', '.join(FOLLOW[x])+' }')
	print ''
	print '\t' + '-'*40
	print ''
		
printfollow()

def construct_parsing_table():
    table = {}
    for x in set(terminals+['$'])-set([epsilon]):
        table[x] = {}
    for x in non_terminals:
        for y in FIRST[x]:
            if y is not epsilon:
                if x in table[y]:
                    raise ValueError, "Grammar is ambiguous"
                table[y][x] = fswp[x][y]
            else:
                for k in FOLLOW[x]:
                    if x in table[k]:
                        raise ValueError, "Grammar is ambiguous"
                    table[k][x] = fswp[x][y]
    return table

parsing_table = construct_parsing_table()

def longestproduction():
	productions = [x.values()[0][0] for x in parsing_table.values()]
	productions = sorted(productions, key=len, reverse=True)
	return productions[0]
	
length = len(longestproduction())

def printparsingtable(length):
	print '\t' + '-'*13 + ' PARSING TABLE ' + '-'*12 
	print ''
	nt = sorted(non_terminals, reverse=True)
	nt.pop(nt.index(start_symbol))
	nt = [start_symbol] + nt
	print '\t ' + ' '*(length+3) + '|',
	for x in nt:
		print '%-*s |'%(length+3, x),
	print ''
	print ''
	for x in parsing_table:
		print '\t',
		print '%*s |'%(length+3, x),
		prod = parsing_table[x]
		for x in nt:
			if x in prod:
				print '%-*s |'%(length+3, x + '=>' + prod[x][0]),
			else:
				print '%-*s |'%(length+3, ''),
		print ''
	print ''
	print '\t' + '-'*40
	
printparsingtable(length)

def parse(text):
    stack = []
    w = text
    w = w + '$'
    print ''
    print '\t' + '-'*25 + ' PARSING ACTION ' + '-'*25
    print ''
    length = len(w) if len(w) > len('Matched') else len('Matched')
    stack.append('$')
    stack.append(start_symbol)
    matched = ''
    print '\t\t' + '%-*s | %*s | %*s | %s' %(length, 'Matched', length, 'Stack', length, 'Input', 'Action')
    print ''
    print '\t\t' + '%-*s | %*s | %*s | '%(length, matched, length, ''.join(stack[::-1]), length, w)
    while stack != ['$']:
        try:
            if stack[-1] == w[0]:
                stack.pop()
                matched = matched + w[0]
                letter = w[0]
                w = w[1:]
                print '\t\t' + '%-*s | %*s | %*s | Match %s' %(length, matched, length, ''.join(stack[::-1]), length, w, letter)
            elif parsing_table[w[0]][stack[-1]][0] == epsilon:
                top = stack[-1]
                stack.pop()
                print '\t\t' + '%-*s | %*s | %*s | Output %s => epsilon' %(length, matched, length, ''.join(stack[::-1]), length, w, top)
            elif parsing_table[w[0]][stack[-1]][0] != w[0] and parsing_table[w[0]][stack[-1]][0] in terminals:
                print "Parser error"
                return False
            else:
                top = stack[-1]
                production = parsing_table[w[0]][stack[-1]]
                stack.pop()
                production = production[0][::-1]
                for i in production:
                    stack.append(i)
                print '\t\t' + '%-*s | %*s | %*s | Output %s => %s' %(length, matched, length, ''.join(stack[::-1]), length, w, top, production[::-1])
        except KeyError:
            print '\n' + '\t' + "Parser error. Parsing table entry not found"
            return False
    print ''
    return True

print ''

def test():
    print "Enter the string to be parsed. It may include spaces between terminals\n"
    string = raw_input()
    string = string.replace(' ', '')
    start = time.time()
    value = parse(string)
    end = time.time()
    if value == True:
        print '\t' + '-'*66 + '\n' + '\t' + "Parsing successful" + '\n'
        print "Timing information: [Y|N]"
        letter = raw_input()
        if letter == 'y' or letter == 'Y':
            firsttime = timeit.timeit("compute_first()", setup="from __main__ import compute_first", number=1)
            followtime = timeit.timeit("compute_follow()", setup="from __main__ import compute_follow", number=1)
            parsetabletime = timeit.timeit("construct_parsing_table()", setup="from __main__ import construct_parsing_table", number=1)
            print "Time taken to compute FIRST : " + str(firsttime)
            print "Time taken to compute FOLLOW : " + str(followtime)
            print "Time taken to compute parsing table : " + str(parsetabletime)
            print "Time taken to parse the given input string is : " + str(end-start)
            print "Total time taken : " + str(firsttime + followtime + parsetabletime + end - start)
    else:
        print "Parsing un-successful"

test()
