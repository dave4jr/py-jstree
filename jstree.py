import dictobj
import collections
import os

Path = collections.namedtuple('Path', ('path', 'id'))
    
class Node(dictobj.DictionaryObject):
  """
  This class exists as a helper to the JSTree.  Its "jsonData" method can
  generate sub-tree JSON without putting the logic directly into the JSTree.

  This data structure is only semi-immutable.  The JSTree uses a directly
  iterative (i.e. no stack is managed) builder pattern to construct a
  tree out of paths.  Therefore, the children are not known in advance, and
  we have to keep the children attribute mutable.
  """
  def __init__(self, data, **kwargs):
    """
    kwargs allows users to pass arbitrary information into a Node that
    will later be output in jsonData().  It allows for more advanced
    configuration than the default path handling that JSTree currently allows.
    For example, users may want to pass "attr" or "metadata" or some other
    valid jsTree options.
    
    Example:
      >>> import jstree
      >>> node = jstree.Node('a')
      >>> print node
      Node({'data': 'a', 'children': MutableDictionaryObject({})})

      >>> import jstree
      >>> node = jstree.Node('a', attr={'id':23})
      >>> print node
      Node({'data': 'a', 'children': MutableDictionaryObject({}), 'attr': DictionaryObject({'id': 23})})
    """
    super(Node, self).__init__()

    children = kwargs.get('children', {})
    if len(filter(lambda key: not isinstance(children[key], Node), children)):
      raise TypeError("One or more children were not instances of '%s'" % Node.__name__)
    if 'children' in kwargs:
      del kwargs['children']
    self._items['children'] = dictobj.MutableDictionaryObject(children)
      
    self._items.update(dictobj.DictionaryObject(**kwargs))
    self._items['data'] = data

  def jsonData(self):
    children = [self.children[k].jsonData() for k in sorted(self.children)]
    if len(children):
      return {'data':self.data, 'children':children}
    else:
      return {'data':self.data}

class JSTree(dictobj.DictionaryObject):
  """
  An immutable dictionary-like object that converts a list of "paths"
  into a tree structure suitable for jQuery's jsTree.
  """
  def __init__(self, paths, **kwargs):
    """
    Take a list of paths and put them into a tree.  Paths with the same prefix should
    be at the same level in the tree.

    kwargs may be standard jsTree options used at all levels in the tree.  These will be outputted
    in the JSON.
    
    Example (basic usage):
      >>> import jstree
      >>> paths = [Path("editor/2012-07/31/.classpath", 1), Path("editor/2012-07/31/.project", 2)]
      >>> t1 = jstree.JSTree(paths)
    """
    if len(filter(lambda p: not isinstance(p, Path), paths)):
      raise TypeError("All paths must be instances of '%s'" % Path.__name__)

    super(JSTree, self).__init__()
      
    root = Node('', **kwargs)
    for path in sorted(set(paths)):
      curr = root
      for subpath in path.split(os.path.sep):
        if subpath not in curr.children:
          curr.children[subpath] = Node(subpath, **kwargs)
        curr = curr.children[subpath]
    self._items['_root'] = root

  def pretty(self, root=None, depth=0, spacing=2):
    """
    Create a "pretty print" represenation of the tree with customized indentation at each
    level of the tree.
    
    Example:
    >>> import jstree
    >>> paths = ["editor/2012-07/31/.classpath", "editor/2012-07/31/.project"]
    >>> print jstree.JSTree(paths).pretty()
    /
      editor/
        2012-07/
          31/
            .classpath
            .project
    """
    if root is None:
      root = self._root
    fmt = "%s%s/" if root.children else "%s%s"
    s = fmt % (" "*depth*spacing, root.data)
    for child in root.children:
      child = root.children[child]
      s += "\n%s" % self.pretty(child, depth+1, spacing)
    return s

  def jsonData(self):
    """
    Returns a copy of the internal tree in a JSON-friendly format,
    ready for consumption by jsTree.  The data is represented as a
    list of dictionaries, each of which are our internal nodes.

    Examples:
    >>> import jstree
    >>> paths = ["editor/2012-07/31/.classpath", "editor/2012-07/31/.project"]
    >>> t = jstree.JSTree(paths)
    >>> d = t.jsonData()
    >>> print d
    [{'data': 'editor', 'children': [{'data': '2012-07', 'children': [{'data': '31', 'children': [{'data': '.classpath'}, {'data': '.project'}]}]}]}]
    >>> print d[0].children[0].children[0].children[1]
    {'data': '.project'}
    """
    return [self._root.children[k].jsonData() for k in sorted(self._root.children)]
