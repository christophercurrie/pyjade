"""
A smarter {% if %} tag for django templates.

While retaining current Django functionality, it also handles equality,
greater than and less than operators. Some common case examples::

    {% if articles|length >= 5 %}...{% endif %}
    {% if "ifnotequal tag" != "beautiful" %}...{% endif %}
"""
import unittest
from django import template
from django.template.base import TemplateSyntaxError
from pyjade.runtime import iteration

register = template.Library()

@register.tag(name="__pyjade_attrs")
def do_evaluate(parser, token):
  '''Calls an arbitrary method on an object.'''
  code = token.contents
  firstspace = code.find(' ')
  if firstspace >= 0:
    code = code[firstspace+1:]
  return Evaluator(code)

class Evaluator(template.Node):
  '''Calls an arbitrary method of an object'''
  def __init__(self, code):
    self.code = code
    
  def render(self, context):
    '''Evaluates the code in the page and returns the result'''
    modules = {
      'pyjade': __import__('pyjade')
    }
    context['false'] = False
    context['true'] = True
    return str(eval('pyjade.runtime.attrs(%s)'%self.code,modules,context))

@register.tag(name="__pyjade_set")
def do_set(parser, token):
  '''Calls an arbitrary method on an object.'''
  code = token.contents
  firstspace = code.find(' ')
  if firstspace >= 0:
    code = code[firstspace+1:]
  return Setter(code)

class Setter(template.Node):
  '''Calls an arbitrary method of an object'''
  def __init__(self, code):
    self.code = code
    
  def render(self, context):
    '''Evaluates the code in the page and returns the result'''
    modules = {
    }
    context['false'] = False
    context['true'] = True
    new_ctx = eval('dict(%s)'%self.code,modules,context)
    context.update(new_ctx)
    return ''

register.filter('__pyjade_iter', iteration)

@register.tag(name="__pyjade_case")
def do_case(parser, token):
    var = parser.compile_filter(token.contents.split()[-1])
    cases = []
    default = None

    def next_block(parser):
        token = parser.next_token()
        if token.contents == '__pyjade_endcase':
            return None, None

        nodelist = parser.parse(('__pyjade_when','__pyjade_default','__pyjade_endcase'))
        return token, nodelist

    nodelist = parser.parse(('__pyjade_when','__pyjade_default','__pyjade_endcase'))
    if len(nodelist):
        raise TemplateSyntaxError("Cannot have content before the first when or default")
    token, block = next_block(parser)
    while token:
        if token.contents == '__pyjade_default':
            if default:
                raise TemplateSyntaxError("Cannot have multiple default blocks")
            default = block
        else:
            test = parser.compile_filter(token.contents.split()[-1])
            cases.append((test,block))
        token, block = next_block(parser)

    return CaseNode(var, cases, default)

class CaseNode(template.Node):
    def __init__(self, var, cases, default):
        self.var = var
        self.cases = cases
        self.default = default

    def render(self, context):
        val = self.var.resolve(context, True)
        for test, block in self.cases:
            if val == test.resolve(context, True):
                return block.render(context)
        return self.default.render(context) if self.default else None

if __name__ == '__main__':
    unittest.main()
