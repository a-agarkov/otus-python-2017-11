# Decorators
### Description
This script is an excersise in Python decorators. 

### Decorator types and their description
According to the task, 6 decorators should be developed. See list of decorators and their description:

* `disable` - the decorator is used to disable another decorator by re-assigning the decorator's name to this function;
* `decorator` - this one allows another decorator to inherit docstrings and stuff from the function it's decorating;
* `countcalls` - counts calls made to the function decorated;
* `memo` - allows memoizing calls to a function with a given set of arguments and caching such calls to return values for faster future lookups;
* `n_ary` - given binary function f(x, y), returns an n_ary function such that f(x, y, z) = f(x, f(y,z)), etc., allows f(x) = x;
* `trace` - traces calls made to function decorated.

### Tests
No test suit was written for this task, since initial script already included run scenario.

### Code author
Алексей Агарков

slack: Alexey Agarkov (Alex_A)
