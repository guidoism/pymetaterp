"""This is where we interpret the grammar that we will be using to
define and intrepret other more complex grammars -- This is known as
bootstrapping.

Let's start with the 'or' operator since that's easy to understand. We
will try each of the options, in order, and return the first match. We
use exceptions to backtrack when a match option fails. When match is
called we create a copy of the input and go back to that when a match
fails.

"""

from util import MatchError, Node

NAME, FLAGS, ARGS, BODY = [0, 1, 2, 3]
inf = float("inf")
# input is a pair (container, pos)

def pop(input):
    input[1] += 1
    try:
        return input[0][input[1]]
    except IndexError:
        raise MatchError("EOF")

def to_list(output):
    return output  if getattr(output, "name", None) == "And" else\
           []      if output is None else\
           [output]

class Interpreter:
    def __init__(self, grammar_tree):
        self.rules = {rule[NAME][0]:rule for rule in grammar_tree}
        self.join_str = True

    def match(self, root, new_input=None, new_pos=-1):
        """ >>> g.match(g.rules['grammar'][-1], "x='y'") """
        if new_input is not None:
            self.input = [new_input, new_pos]
        old_input = self.input[:]
        name = root.name
        print("matching %s:\n\t%s" % (name, root))
        if name in ["and", "args", "body", "output"]:
            outputs = [self.match(child) for child in root]
            # GUIDO: I think what the following means is: If any of
            # the nodes in root are "output" then filter out anthing
            # that's not "output". Yes? What is this for?
            if any(child.name == "output" for child in root):
                outputs = [output for child, output in zip(root, outputs)
                           if child.name == "output"]
        elif name == "quantified":
            #############################
            # GUIDO: Maybe this is cleaner?
            # r, q = root[0:2]
            # while len(o) < upper:
            #     last = dup(i)
            #     if m := match(r):
            #         o.append(m)
            #     else:
            #         i = dup(last)
            #         break
            #     if last == i:
            #         break # GUIDO: Why? Because it didn't match anything?
            #############################
            # GUIDO: What about this?
            # r, q = root[0:2]
            # last = None
            # while len(o) < upper and last != i:
            #     last = dup(i)
            #     if m := match(r):
            #         o.append(m)
            #     else:
            #         i = dup(last)
            #         break
            #############################
            # GUIDO: What about this?
            # Ok, so we want to repeat the rule until it fails with an exception or
            # it fails by not changing the input. If it fails with an exception then
            # we need to roll back the changes to the input (though, we can also do
            # this if there are no changes since it's a noop).
            # def rollback_on_exception(f, d):
            #     last = d[:]
            #     try:
            #         f()
            #         return True
            #     except:
            #        d = last[:]
            # def quantifier():
            #     while len(o) < upper:
            #         ...
            #     
            # while matching():
            #     pass
            #############################
            assert(root[1].name == "quantifier")
            # GUIDO: All those subscripts are difficult to comprehend -- Clean it up.
            lower, upper = {"*": (0, inf), "+": (1, inf), "?": (0, 1)}[root[1][0]]
            outputs = []
            while len(outputs) < upper:
                # GUIDO: Let's make dup/revert functions to make it easier to understand?
                last_input = self.input[:]
                try:
                    outputs.append(self.match(root[0]))
                except MatchError:
                    self.input = last_input[:]
                    break
                if last_input == self.input:
                    break
            if lower > len(outputs):
                raise MatchError("Matched %s < %s times" % (len(outputs), lower))
        elif name == "or":
            for child in root:
                try:
                    return self.match(child)
                except MatchError:
                    self.input = old_input[:]
            raise MatchError("All Or matches failed")
        elif name in ["exactly", "token"]:
            if name == "token":
                while pop(self.input) in ['\t', '\n', '\r', ' ']:
                    pass
                self.input[1] -= 1
            if pop(self.input) == root[0]:
                return root[0]
            else:
                raise MatchError("Not exactly %s" % root)
        elif name == "apply":
            #print "rule %s" % root[NAME]
            if root[NAME] == "anything":
                return pop(self.input)
            outputs = self.match(self.rules[root[NAME]][BODY])
            if root[NAME] == "escaped_char":
                chars = dict(["''", '""', "t\t", "n\n", "r\r",
                              "b\b", "f\f", "\\\\"])
                return chars[outputs]
            and_node = getattr(outputs, "name", None) == "And"
            make_node = "!" in self.rules[root[NAME]][FLAGS] or\
                        (and_node and len(outputs) > 1)
            if not make_node:
                return outputs
            return Node(root[NAME], to_list(outputs))
        elif name in "bound":
            return Node(root[1][0], to_list(self.match(root[0])))
        elif name == "negation":
            try:
                self.match(root[0])
            except MatchError:
                self.input = old_input
                return None
            raise MatchError("Negation true")
        else:
            raise Exception("Unknown operator %s" % name)

        outputs = [elem for output in outputs
                   for elem in to_list(output)]
        if len(outputs) == 1:
            return outputs[0]
        elif len(outputs) == 0:
            return None
        else:
            if self.join_str and all(type(output) == str for output in outputs):
                return "".join(outputs)
            return Node("And", outputs)
