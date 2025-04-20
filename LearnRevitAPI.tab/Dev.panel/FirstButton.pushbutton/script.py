# -*- coding: utf-8 -*-
__title__ = "Rename Views"
__doc__   = """Version = 1.0
Date    = 19.04.2025
_____________________________________________________________________
Description:
Rename Views in Revit by using Find/Replace Logic.
_____________________________________________________________________
How-to:
-> Click on the button
-> Select Views
-> Define Renaming Rules
-> Rename Views
_____________________________________________________________________
Last update:
- [16.07.2024] - 1.1 Fixed an issue...
- [15.07.2024] - 1.0 RELEASE
_____________________________________________________________________
Author: Erik Frits"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝ IMPORTS
#==================================================
# Regular + Autodesk

from Autodesk.Revit.DB import *

# pyRevit
from pyrevit import revit, forms

# .NET Imports (You often need List import)
import clr
clr.AddReference("System")
from System.Collections.Generic import List

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝ VARIABLES
#==================================================
doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application

# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝ MAIN
#==================================================

#1️⃣ Select Views

sel_el_id = uidoc.Selection.GetElementIds()
sel_elem = [doc.GetElement(e_id) for e_id in sel_el_id]
sel_view = [el for el in sel_elem if issubclass(type(el), View)]

# If None Selcted - Promp SelectViews from pyrevit.forms.select_views()
if not sel_view:
    sel_view = forms.select_views()

# Ensure Views Selected
if not sel_view:
    forms.alert('No Views Selected. Please Try Again', exitscript=True)

# #2️⃣A Define Renaming Rules
# prefix  = 'pre-'
# find    = 'FloorPlan'
# replace = 'Level'
# suffix  = '-suf'

#2️⃣B Define Renaming Rules
from rpw.ui.forms import (FlexForm, Label, TextBox, Separator, Button)
components = [Label('Prefix:'),  TextBox('prefix'),
              Label('Find:'),    TextBox('find'),
              Label('Replace:'), TextBox('replace'),
              Label('Suffix:'),  TextBox('suffix'),
              Separator(),       Button('Rename Views')]

form = FlexForm('Title', components)
form.show()

user_inputs = form.values #type: dict
prefix      = user_inputs['prefix']
find        = user_inputs['find']
replace     = user_inputs['replace']
suffix      = user_inputs['suffix']


t = Transaction(doc, 'py-Rename Views')

t.Start()

for view in sel_view:
    # 3️⃣ Create new View Name
    old_name = view.Name
    new_name = prefix + old_name.replace(find, replace) + suffix

    #4️⃣ Rename Views (Ensure unique view name)
    for i in range(20):
        try:
            view.Name = new_name
            print('{} -> {}'.format(old_name, new_name))
            break
        except:
            new_name += '*'

t.Commit()

print('-'*50)
print('Done')

