## Boot's Interpreter.match

Takes the root of a grammar tree and matches the input against it.

* and, args, body, output: run match against all children
* quantified: repeat between lower and upper or until error, revert to last input on error
* or: repeat until error, revert to original input on error
* token: skip whitespace, return token assuming it matches
* exactly: return string assuming it matches
* apply: find the rule with the name and match the body, optionally create node
* bound: create node from match
* negation: only return None if match is an error



